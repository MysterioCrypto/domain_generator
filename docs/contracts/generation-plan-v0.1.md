---
id: CONTRACT-GENERATIONPLAN-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# GenerationPlan v0.1 — черновик

`GenerationPlan` — неизменяемый внутренний сериализуемый разрешённый recipe между `DomainSpec` и realization конкретного attempt. После компиляции pipeline не должен обращаться к preset registry или исходному `DomainSpec` для определения поведения.

## Верхний уровень

```yaml
plan_version: "0.1"

source:
  spec_id: example-domain-01
  spec_schema_version: "0.1"
  spec_fingerprint: "sha256:..."
  generator_version: "0.1.0"

seed: 1847291

domain:
  width_km: 120.0
  height_km: 100.0

grid:
  cell_size_km: 0.25
  rows: 400
  columns: 480

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

Числа в примерах ненормативны.

`spec_id` — provenance и не влияет на RNG. Child RNG seeds не хранятся в Plan.

`hydrology` — полностью разрешённый semantic recipe для downstream hydrology classification/network/water-depth generation. `surface` — полностью разрешённый semantic recipe для базовой генерации moisture/vegetation. Они не являются execution policy и включаются в semantic plan fingerprint.

## Рецепт Hydrology

```yaml
hydrology:
  stream_threshold_km2: 25.0
  lake_min_area_km2: 1.0
  lake_min_depth_m: 2.0
  river_depth_at_threshold_m: 0.5
  river_depth_exponent: 0.30
```

Все значения конечны. `stream_threshold_km2`, `lake_min_area_km2`, `lake_min_depth_m` и `river_depth_at_threshold_m` строго положительны; `river_depth_exponent >= 0`.

- `stream_threshold_km2` применяется к canonical `flow_accumulation_km2` как `>= threshold`;
- `lake_min_area_km2` фильтрует 8-connected components физической depression mask по площади;
- `lake_min_depth_m` фильтрует те же components по максимальной физической fill depth;
- `river_depth_at_threshold_m` задаёт proxy river depth при catchment area, равной stream threshold;
- `river_depth_exponent` задаёт степень роста proxy river depth с catchment area.

Для stream cell вне accepted lake:

```text
river_depth_m = river_depth_at_threshold_m
                * (flow_accumulation_km2 / stream_threshold_km2)
                  ** river_depth_exponent
```

Это детерминированный proxy для canonical `water_depth`, а не симуляция discharge/hydraulics.

Алгоритмы hydrology routing/network остаются частью семантики версии generator: Plan хранит намерение и конфигурацию мира, но не сериализует внутренний Priority-Flood heap, состояние tie-break, routing arrays, realization `RiverNetwork` или array `water_depth`.

## Рецепт Surface

```yaml
surface:
  moisture_base: 0.35
  water_moisture_boost: 0.55
  water_moisture_decay_km: 8.0
  moisture_noise_amplitude: 0.10
  moisture_noise_scale_km: 12.0
  vegetation_slope_zero_deg: 45.0
```

Все значения конечны. `moisture_base`, `water_moisture_boost`, `moisture_noise_amplitude` лежат в `[0,1]`; два scale-параметра строго положительны; `vegetation_slope_zero_deg` лежит в `(0,90]`.

Базовая генерация Surface использует canonical upstream `water_depth` и terrain elevation:

```text
water cells = water_depth > 0

dry moisture = clamp(
    moisture_base
  + water_moisture_boost * exp(-distance_to_water_km / water_moisture_decay_km)
  + moisture_noise_amplitude * coherent_noise,
  0,
  1
)

water moisture = 1
```

World-space moisture noise использует фиксированный semantic RNG namespace:

```text
stage   = surface
scope   = ("field", "moisture", "environmental-noise")
purpose = "value"
```

Базовая terrestrial vegetation:

```text
slope_factor = clamp(1 - slope_deg / vegetation_slope_zero_deg, 0, 1)
vegetation_density = moisture * slope_factor
```

Water cells получают `vegetation_density = 0`.

Plan не вводит climate penalty по абсолютной elevation: абсолютный ноль elevation — это datum. Climate/biome/temperature/precipitation/seasons не входят в surface recipe Core 0.1.

Distance-to-water, slope, samples noise, arrays `SurfaceState` и contributions surface features не сериализуются в Plan.

## ResolvedFeature

После компиляции preset как runtime behavior исчезает. Layout recipe и effect recipe разделены явно.

```yaml
- id: mountain-01

  metadata:
    label: Центральный горный пояс
    tags: [major_landform]
    source_preset: mountain_range

  family: terrain

  layout:
    mode: geometry
    shape: band
    parameters:
      width_km:
        kind: range
        type: float
        min: 15.0
        max: 30.0
        sampler:
          type: triangular
          mode: 24.0

      curvature:
        kind: range
        type: float
        min: 0.05
        max: 0.30
        sampler:
          type: uniform

  effect:
    stage: terrain
    operator: ridge
    parameters:
      elevation_delta_m:
        kind: range
        type: float
        min: 900.0
        max: 1700.0
        sampler:
          type: triangular
          mode: 1300.0

      roughness:
        kind: fixed
        type: float
        value: 0.7
```

Разделение означает:

- `layout` отвечает только за macro geometry либо reservation;
- `effect` отвечает за stage-specific realization после layout;
- pipeline не угадывает владельца parameter по имени.

`metadata` сохраняется для provenance/output, но не влияет скрытым образом на семантику generation.

## Layout recipe

`layout.mode` v0.1:

- `geometry` — layout создаёт конкретную macro geometry;
- `reservation` — layout создаёт `PlacementReservation`, а финальная geometry выбирается позднее.

Пример structural feature:

```yaml
layout:
  mode: geometry
  shape: band
  parameters: {...}
```

Пример dependent point:

```yaml
layout:
  mode: reservation
  final_shape: point
```

Core 0.1 реализует dependent placement только для final shape `point`, хотя архитектура не запрещает более общие формы позже.

## Effect recipe

`effect.stage` v0.1 отражает downstream stage, где feature оказывает основной эффект или получает финальную realization:

```text
terrain
surface
dependent_placement
```

Примеры:

```yaml
# terrain feature
effect:
  stage: terrain
  operator: ridge
  parameters: {...}

# surface feature
effect:
  stage: surface
  operator: vegetation_bias
  parameters: {...}

# dependent POI
effect:
  stage: dependent_placement
  operator: suitability_placement
  site_profile: {...}
```

Id operator-а — стабильный семантический id, а не Python import path или callable.

## Разрешённые parameters

Resolved parameter использует один из видов:

```yaml
# fixed
roughness:
  kind: fixed
  type: float
  value: 0.7

# range
width_km:
  kind: range
  type: float
  min: 15.0
  max: 30.0
  sampler:
    type: triangular
    mode: 24.0

# choice
profile:
  kind: choice
  type: enum
  values: [smooth, rugged]
  sampler:
    type: categorical
```

Plan хранит sampler recipe, но не sampled value конкретного attempt. Sampling выполняется владельцем recipe через независимый RNG namespace.

## SiteProfile для POI

Dependent POI хранит полностью разрешённый site profile внутри `effect`:

```yaml
- id: fort-01
  metadata:
    label: Пограничный форт
    source_preset: fort
  family: poi
  layout:
    mode: reservation
    final_shape: point
  effect:
    stage: dependent_placement
    operator: suitability_placement
    site_profile:
      footprint_radius_km: 0.6
      requirements:
        - metric: water_fraction
          evaluator: less_or_equal
          value: 0.05
        - metric: buildable_fraction
          evaluator: greater_or_equal
          value: 0.65
      preferences:
        - metric: mean_slope
          evaluator: lower_is_better
          weight: 0.6
        - metric: relative_elevation_m
          evaluator: preferred_range
          min: 10.0
          max: 80.0
          weight: 0.4
```

Hard site requirements фильтруют sites. Внутренние site preferences выбирают физически подходящее место внутри одного candidate и не участвуют автоматически в глобальном ranking candidates.

## CompiledConstraint

Семантические relations `DomainSpec` компилируются в универсальный evaluator + hard predicate либо soft scoring recipe.

Пример hard constraint:

```yaml
- id: fort-near-gorge
  source_relation: near
  strength: hard
  evaluator:
    type: distance
    subject: {type: feature, feature_id: fort-01, part: whole}
    target: {type: feature, feature_id: gorge-01, part: endpoints}
  predicate: {type: less_or_equal, value: 3.0}
  unit: km
```

Пример soft constraint:

```yaml
- id: mountains-near-center
  source_relation: near
  strength: soft
  weight: 0.5
  evaluator:
    type: distance
    subject: {type: feature, feature_id: mountain-01, part: center}
    target: {type: point, x_km: 60.0, y_km: 50.0}
  scoring:
    type: linear_preference
    ideal: 0.0
    worst: 20.0
  unit: km
```

`source_relation` — только необязательный provenance. Runtime behavior определяется compiled evaluator/predicate/scoring.

Compiler приводит встроенные anchors/regions и normalized literals к физическим primitives geometry. Семантика geometry-part определена контрактом `DomainSpec` и не переинтерпретируется downstream modules.

## Граница dependent constraints

Core 0.1 материализует layout reservations только из hard spatial constraints, цели которых уже имеют geometry на стадии layout. Поэтому deferred feature не может иметь layout-hard dependency на другой deferred feature или ещё не существующую generated hydrology network. Такие specs compiler отклоняет как неподдерживаемые для Core 0.1; post-hydrology физические требования выражаются `SiteProfile`.

## Гарантии compiler

Если `GenerationPlan` создан успешно, уже проверено:

- все id preset/operator известны;
- family/shape/operator совместимы;
- переопределения parameters layout/effect и resolved domains валидны;
- id features/constraints и references валидны;
- selector parts совместимы с geometry shapes;
- граница deferred dependencies соблюдена;
- размеры grid согласованы с физическими размерами;
- hydrology recipe присутствует и имеет валидные physical thresholds/proxy parameters;
- surface recipe присутствует и имеет валидные normalized/physical parameters;
- compiled constraint recipes исполнимы поддерживаемым registry.

Pipeline не повторяет эту semantic validation на каждом attempt.

## Fingerprints

Различаются два fingerprint:

- `spec_fingerprint` — fingerprint нормализованного исходного `DomainSpec`, включая metadata документа;
- `plan_fingerprint` — SHA-256 canonical **executable projection** Plan.

В semantic `plan_fingerprint` входят seed, семантика grid/domain, hydrology recipe, surface recipe, идентичности features, layout/effect recipes, site profiles и compiled constraints. Не входят данные только для presentation/provenance: `label`, `tags`, `source_preset`, `spec_id` и debug metadata generator.

Это гарантирует, что косметическое переименование не меняет procedural identity Plan. Сам fingerprint не включается в fingerprinted payload. `LayoutCandidate` ссылается на `plan_fingerprint`.

## Чего в Plan нет

`GenerationPlan` не содержит:

- конкретную centerline/boundary текущего attempt;
- sampled values конкретного attempt;
- raster arrays;
- routing/fill elevation arrays;
- stream mask или cells lake candidate;
- realization `RiverNetwork`;
- arrays canonical `water_depth`, `moisture` или `vegetation_density`;
- derived arrays distance-to-water/slope;
- финальные координаты dependent POI;
- Python callable;
- child RNG seeds;
- текущий attempt index;
- `max_attempts`, `target_valid_candidates` и другие settings execution policy;
- debug/output settings.

`GenerationConfig` относится к политике исполнения, а не к описанию мира.
