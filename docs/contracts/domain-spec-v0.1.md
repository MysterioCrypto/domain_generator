---
id: CONTRACT-DOMAINSPEC-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# DomainSpec v0.1 — draft

Этот документ фиксирует принятый дизайн пользовательского контракта. Он ещё не является JSON Schema и остаётся draft до закрытия M1.

## Корень

```yaml
schema_version: "0.1"
id: example-domain-01
label: Пример домена
seed: 1847291

domain:
  size:
    width_km: 120.0
    height_km: 100.0

simulation:
  cell_size_km: 0.25

features: []
constraints: []
```

Поля: `schema_version`, `id`, optional `label`, `seed`, `domain`, `simulation`, `features`, `constraints`.

Правила:

- `seed` обязателен в canonical DomainSpec;
- top-level `id` — identity документа/домена и не участвует в RNG;
- `label` — только отображаемое имя;
- размер мира и cell size задаются в физических единицах;
- `width_km / cell_size_km` и `height_km / cell_size_km` должны давать целое число клеток; silent rounding запрещён;
- пользователь не задаёт raster row/column или CRS;
- world coordinates: origin southwest, `+x` east, `+y` north.

## FeatureSpec

```yaml
- id: mountain-01
  label: Центральный горный пояс
  preset: mountain_range
  parameters:
    width_km:
      min: 15.0
      max: 30.0
  tags:
    - major_landform
```

`id` и `preset` обязательны; `label`, `parameters`, `tags` optional.

Feature `id` — стабильная machine identity. Она используется в constraints, references и RNG namespace. Косметическое переименование делается через `label`; сознательная смена `id` означает новую identity и может изменить realization.

В `FeatureSpec v0.1` нет `family`, `shape`, `operator`, `placement`, sampler или `presence`: они либо следуют из preset, либо выражаются constraints. Все явно перечисленные features обязательны. Tags — metadata only и не влияют на Core скрытым образом.

## Parameter overrides

Разрешены три формы:

```yaml
# fixed
width_km: 22.0

# allowed numeric domain
width_km:
  min: 15.0
  max: 30.0

# allowed enum choices
profile:
  one_of: [smooth, rugged]
```

Один override использует ровно одну форму. `min/max` задаёт allowed domain, а не автоматически uniform sampling. Sampling policy приходит из preset definition и после compilation переносится в `GenerationPlan`.

Базовые parameter types Core 0.1: float, integer, boolean, enum.

## ConstraintSpec

```yaml
- id: fort-near-gorge
  relation: near
  subject:
    feature: fort-01
  target:
    feature: gorge-01
    part: endpoints
  strength: hard
  parameters:
    max_distance_km: 3.0
```

Общая модель:

```text
relation + SpatialSelector(subject) + SpatialSelector(target)
```

`id`, `relation`, `subject`, `target`, `strength` обязательны. `parameters` optional. `weight` разрешён только для `soft`; default weight для soft = `1.0`.

`hard` constraint нельзя компенсировать score. `soft` constraint участвует в ranking.

### Relations v0.1

Начальный registry:

- `near`;
- `far_from`;
- `inside`;
- `outside`;
- `crosses`;
- `overlaps`;
- `adjacent`;
- `connects`.

`transitions_to`, специальные `near_endpoint` и другие составные relation не входят в primitive registry v0.1.

Relation определяет допустимые parameters. Примеры:

- `near` → `max_distance_km`;
- `far_from` → `min_distance_km`;
- `overlaps` → `minimum_fraction` (fraction считается относительно площади subject);
- `adjacent` → `max_gap_km`;
- `crosses` может иметь optional minimum crossing length.

## SpatialSelector

Selector содержит ровно один source.

Feature:

```yaml
subject:
  feature: mountain-01
  part: start
```

Built-in point anchor:

```yaml
target:
  domain_anchor: center
```

Built-in region:

```yaml
target:
  domain_region: southwest
```

Literal point in km:

```yaml
target:
  point:
    x_km: 50.0
    y_km: 65.0
```

Literal normalized point:

```yaml
target:
  point:
    normalized:
      x: 0.42
      y: 0.68
```

Literal normalized region:

```yaml
target:
  region:
    normalized:
      x: {min: 0.15, max: 0.40}
      y: {min: 0.55, max: 0.80}
```

Literal region in km:

```yaml
target:
  region:
    x_km: {min: 18.0, max: 48.0}
    y_km: {min: 55.0, max: 80.0}
```

Custom polygons в DomainSpec v0.1 не поддерживаются.

### Feature parts

Начальный набор: `whole` (default), `center`, `start`, `end`, `endpoints`, `boundary`.

Совместимость проверяется semantic validator/compiler:

- point: `whole`, `center`;
- corridor: `whole`, `center`, `start`, `end`, `endpoints`;
- band: `whole`, `center`, `start`, `end`, `endpoints`, `boundary`;
- area: `whole`, `center`, `boundary`.

## Built-in anchors and regions

Имена: `southwest`, `south`, `southeast`, `west`, `center`, `east`, `northwest`, `north`, `northeast`.

`domain_anchor` — точка в normalized coordinates; например `center=(0.5,0.5)`, `southwest=(0,0)`.

`domain_region` — соответствующая область сетки 3×3; например `southwest` region: `x=0..1/3`, `y=0..1/3`.

Compiler переводит normalized/anchor/region concepts в физические geometry primitives.

## Иллюстративный пример

```yaml
schema_version: "0.1"
id: example-domain-01
label: Пример пограничного домена
seed: 123456

domain:
  size:
    width_km: 120.0
    height_km: 100.0

simulation:
  cell_size_km: 0.25

features:
  - id: mountain-01
    preset: mountain_range
    parameters:
      width_km: {min: 15.0, max: 30.0}

  - id: gorge-01
    preset: gorge

  - id: foothills-01
    preset: rolling_hills

  - id: foothill-forest-01
    preset: forest

  - id: fort-01
    preset: fort

constraints:
  - id: mountains-start-sw
    relation: inside
    subject: {feature: mountain-01, part: start}
    target: {domain_region: southwest}
    strength: hard

  - id: mountains-end-ne
    relation: inside
    subject: {feature: mountain-01, part: end}
    target: {domain_region: northeast}
    strength: hard

  - id: gorge-crosses-mountains
    relation: crosses
    subject: {feature: gorge-01}
    target: {feature: mountain-01}
    strength: hard

  - id: fort-near-gorge
    relation: near
    subject: {feature: fort-01}
    target: {feature: gorge-01, part: endpoints}
    strength: hard
    parameters: {max_distance_km: 3.0}

  - id: forest-overlaps-foothills
    relation: overlaps
    subject: {feature: foothill-forest-01}
    target: {feature: foothills-01}
    strength: hard
    parameters: {minimum_fraction: 0.7}
```

Пример ненормативный и не создаёт implicit rules Core.
