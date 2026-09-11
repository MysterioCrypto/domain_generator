---
id: CONTRACT-DOMAINSPEC-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# DomainSpec v0.1 — draft

Этот документ фиксирует принятый на checkpoint пользовательский формат. Он ещё не является JSON Schema и может быть уточнён до закрытия M1.

## Корень

```yaml
schema_version: "0.1"
id: example-domain-01
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

Правила:

- `seed` обязателен в canonical DomainSpec;
- `id` не влияет на RNG;
- размер мира и cell size задаются в физических единицах;
- `width_km / cell_size_km` и `height_km / cell_size_km` должны давать целое число клеток;
- пользователь не задаёт raster row/column или CRS;
- world coordinates: origin southwest, `+x` east, `+y` north.

## FeatureSpec

Минимальная форма:

```yaml
- id: central_mountains
  preset: mountain_range
  parameters:
    width_km:
      min: 15.0
      max: 30.0
  tags:
    - major_landform
```

В `FeatureSpec v0.1` нет `family`, `shape`, `operator`, `placement` или `presence`: они либо следуют из preset, либо выражаются constraints.

Все явно перечисленные features обязательны. Tags не влияют на генерацию скрытым образом.

Параметр может быть фиксированным значением либо allowed domain, например диапазоном `min/max`. `min/max` не означает автоматически uniform sampling: sampling policy приходит из preset/operator definition.

## ConstraintSpec

```yaml
- id: fort-near-gorge
  relation: near

  subject:
    feature: frontier_fort

  target:
    feature: main_gorge
    part: endpoints

  strength: hard

  parameters:
    max_distance_km: 3.0
```

Модель:

```text
relation + SpatialSelector(subject) + SpatialSelector(target)
```

Selectors v0.1 могут ссылаться на:

- feature и optional geometry `part`;
- `domain_anchor`;
- `domain_region`;
- literal point;
- literal region.

Поддерживаемые geometry parts должны соответствовать shape. Базовый набор: `whole`, `center`, `start`, `end`, `endpoints`, `boundary`.

`hard` constraint нельзя компенсировать score. `soft` использует `weight`.

## Встроенные ориентиры

`domain_anchor` — точка в нормализованных координатах. `domain_region` — область встроенной сетки 3×3. Например `southwest` region — юго-западная треть домена, а `southwest` anchor — точка `(0,0)`.

## Пример направления гор

```yaml
constraints:
  - id: mountains-start-sw
    relation: inside
    subject:
      feature: central_mountains
      part: start
    target:
      domain_region: southwest
    strength: hard

  - id: mountains-end-ne
    relation: inside
    subject:
      feature: central_mountains
      part: end
    target:
      domain_region: northeast
    strength: hard
```

Это задаёт композиционное намерение, а не прямую геометрическую линию.