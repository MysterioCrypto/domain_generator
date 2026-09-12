---
id: CONTRACT-DOMAINSPEC-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# DomainSpec v0.1 — draft

Этот документ фиксирует согласованный дизайн пользовательского контракта Core 0.1. Canonical machine-readable contract публикуется как generated JSON Schema; этот Markdown описывает принятую семантику человеческим языком.

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

hydrology:
  stream_threshold_km2: 25.0
  lake_min_area_km2: 1.0
  lake_min_depth_m: 2.0
  river_depth_at_threshold_m: 0.5
  river_depth_exponent: 0.30

surface:
  moisture_base: 0.35
  water_moisture_boost: 0.55
  water_moisture_decay_km: 8.0
  moisture_noise_amplitude: 0.10
  moisture_noise_scale_km: 12.0
  vegetation_slope_zero_deg: 45.0

features: []
constraints: []
```

Все числовые значения в примерах ненормативны.

Поля: `schema_version`, `id`, optional `label`, `seed`, `domain`, `simulation`, `hydrology`, `surface`, `features`, `constraints`.

Правила:

- `seed` обязателен в canonical DomainSpec;
- top-level `id` — identity документа/домена и не участвует в RNG;
- `label` — только отображаемое имя;
- размеры мира и cell size задаются в физических единицах;
- `width_km / cell_size_km` и `height_km / cell_size_km` должны давать целое число клеток; silent rounding запрещён;
- пользователь не задаёт raster row/column или CRS;
- world coordinates: origin southwest, `+x` east, `+y` north;
- `hydrology` и `surface` — обязательные semantic части мира, а не execution/debug settings.

## Hydrology recipe

```yaml
hydrology:
  stream_threshold_km2: 25.0
  lake_min_area_km2: 1.0
  lake_min_depth_m: 2.0
  river_depth_at_threshold_m: 0.5
  river_depth_exponent: 0.30
```

Все пять значений обязательны и finite. Первые четыре строго положительны; `river_depth_exponent >= 0`.

- `stream_threshold_km2` — minimum upstream catchment area, при которой raster cell классифицируется как stream cell;
- `lake_min_area_km2` — minimum physical area connected depression component для сохранения как lake candidate;
- `lake_min_depth_m` — minimum maximum physical fill depth connected depression component для сохранения как lake candidate;
- `river_depth_at_threshold_m` — deterministic proxy depth stream cell ровно на пороге `stream_threshold_km2`;
- `river_depth_exponent` — exponent роста proxy river depth с увеличением catchment area.

Для stream cell вне accepted lake:

```text
A  = flow_accumulation_km2
A0 = stream_threshold_km2
D0 = river_depth_at_threshold_m
p  = river_depth_exponent

river_depth_m = D0 * (A / A0)^p
```

Это явная deterministic proxy-модель для canonical `water_depth`, а не physical discharge/hydraulic simulation.

Эти значения не являются hidden defaults Core. Они входят в semantic `GenerationPlan` и его fingerprint. Изменение любого из них может менять hydrology result при неизменном terrain.

В v0.1 recipe не задаёт rainfall, runoff, erosion, sea level, physical river width, lake evaporation или климатическую модель.

## Surface recipe

```yaml
surface:
  moisture_base: 0.35
  water_moisture_boost: 0.55
  water_moisture_decay_km: 8.0
  moisture_noise_amplitude: 0.10
  moisture_noise_scale_km: 12.0
  vegetation_slope_zero_deg: 45.0
```

Все шесть значений обязательны и finite. Примерные числа выше ненормативны.

- `moisture_base` — базовый уровень локальной влажности, `[0,1]`;
- `water_moisture_boost` — максимальная добавка влажности от близости canonical water, `[0,1]`;
- `water_moisture_decay_km > 0` — physical decay scale влияния воды;
- `moisture_noise_amplitude` — amplitude coherent environmental noise, `[0,1]`;
- `moisture_noise_scale_km > 0` — world-space scale этого noise;
- `0 < vegetation_slope_zero_deg <= 90` — slope, при котором базовый terrestrial vegetation factor становится нулём.

Для dry cell базовая moisture semantics:

```text
water_term = water_moisture_boost
             * exp(-distance_to_water_km / water_moisture_decay_km)

moisture = clamp(
    moisture_base
  + water_term
  + moisture_noise_amplitude * coherent_noise,
  0,
  1
)
```

Canonical water cells получают `moisture = 1`. При полном отсутствии canonical water `water_term = 0`.

Base terrestrial vegetation:

```text
slope_factor = clamp(1 - slope_deg / vegetation_slope_zero_deg, 0, 1)
vegetation_density = moisture * slope_factor
```

Canonical water cells получают `vegetation_density = 0`.

Absolute elevation не вводит implicit dryness penalty: `0 m` в Core 0.1 — datum, а не sea/climate level. Climate, biome, precipitation, temperature и seasons в этот recipe не входят.

Surface recipe входит в semantic `GenerationPlan` и его fingerprint. Hidden defaults запрещены.

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

Feature `id` — стабильная machine identity. Она используется в constraints, references и RNG namespace. Косметическое переименование делается через `label`; сознательная смена `id` означает новую procedural identity и может изменить realization.

В `FeatureSpec v0.1` нет `family`, `shape`, `operator`, `placement`, sampler или `presence`: они следуют из preset либо выражаются constraints. Все явно перечисленные features обязательны. Tags — metadata only и не влияют на Core скрытым образом.

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

`id`, `relation`, `subject`, `target`, `strength` обязательны. `parameters` optional. `weight` разрешён только для `soft`; default `1.0`, допустимый диапазон `0 < weight <= 1`.

`hard` constraint нельзя компенсировать score. `soft` constraint участвует в ranking valid candidates.

### Relations v0.1

Начальный registry:

- `near`;
- `far_from`;
- `inside`;
- `outside`;
- `crosses`;
- `overlaps`;
- `adjacent`.

`connects`, `transitions_to`, специальные `near_endpoint` и другие составные relations не входят в primitive registry v0.1. `connects` отложен до появления явной network/route semantics.

Relation определяет допустимые parameters. Базовая семантика:

- `near` → minimum distance между выбранными geometries `<= max_distance_km`;
- `far_from` → minimum distance `>= min_distance_km`;
- `inside` → subject полностью содержится в target;
- `outside` → subject не пересекает interior target;
- `overlaps` → `area(subject ∩ target) / area(subject) >= minimum_fraction`;
- `adjacent` → minimum boundary-to-boundary distance `<= max_gap_km`; containment сам по себе не считается adjacency;
- `crosses` v0.1 применяется к поддерживаемым line-like/area-like combinations и требует реального прохода через interior, а не простого касания boundary.

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

Точная семантика:

- point: `whole` и `center` — сама точка;
- corridor: `whole` — polyline; `start`/`end` — первая/последняя точка centerline; `endpoints` — обе; `center` — точка на 50% длины centerline;
- band: `whole` — footprint band; `start`/`end`/`endpoints`/`center` определяются по centerline; `boundary` — boundary footprint;
- area: `whole` — polygon; `center` — geometric centroid; `boundary` — polygon boundary.

Compiler проверяет совместимость part с resolved geometry shape.

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

hydrology:
  stream_threshold_km2: 25.0
  lake_min_area_km2: 1.0
  lake_min_depth_m: 2.0
  river_depth_at_threshold_m: 0.5
  river_depth_exponent: 0.30

surface:
  moisture_base: 0.35
  water_moisture_boost: 0.55
  water_moisture_decay_km: 8.0
  moisture_noise_amplitude: 0.10
  moisture_noise_scale_km: 12.0
  vegetation_slope_zero_deg: 45.0

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
