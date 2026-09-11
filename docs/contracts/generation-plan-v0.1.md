---
id: CONTRACT-GENERATIONPLAN-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# GenerationPlan v0.1 — draft

`GenerationPlan` — immutable internal serialized resolved recipe между `DomainSpec` и attempt-specific realization. После compilation pipeline не должен обращаться к preset registry или исходному DomainSpec для определения поведения.

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

features: []
constraints: []
```

`spec_id` — provenance и не влияет на RNG. Child RNG seeds не хранятся в Plan.

## ResolvedFeature

После compilation preset как runtime behavior исчезает. Layout recipe и effect recipe разделены явно.

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
- pipeline не угадывает владельца параметра по имени.

`metadata` сохраняется для provenance/output, но не влияет скрытым образом на generation semantics.

## Layout recipe

`layout.mode` v0.1:

- `geometry` — layout создаёт concrete macro geometry;
- `reservation` — layout создаёт `PlacementReservation`, а final geometry выбирается позднее.

Structural example:

```yaml
layout:
  mode: geometry
  shape: band
  parameters: {...}
```

Dependent point example:

```yaml
layout:
  mode: reservation
  final_shape: point
```

Core 0.1 реализует dependent placement только для final shape `point`, хотя архитектура не запрещает более общие формы позже.

## Effect recipe

`effect.stage` v0.1 отражает downstream stage, где feature оказывает основной эффект/получает final realization:

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

Operator id — stable semantic id, не Python import path и не callable.

## Resolved parameters

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

Plan хранит sampler recipe, но не attempt-specific sampled value. Sampling выполняется владельцем recipe через независимый RNG namespace.

## POI SiteProfile

Dependent POI хранит fully resolved site profile внутри `effect`:

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

Hard site requirements фильтруют sites. Intrinsic site preferences выбирают физически подходящее место внутри одного candidate и не участвуют автоматически в global candidate ranking.

## CompiledConstraint

Semantic relations DomainSpec компилируются в generic evaluator + hard predicate либо soft scoring recipe.

Hard example:

```yaml
- id: fort-near-gorge
  source_relation: near
  strength: hard

  evaluator:
    type: distance
    subject:
      type: feature
      feature_id: fort-01
      part: whole
    target:
      type: feature
      feature_id: gorge-01
      part: endpoints

  predicate:
    type: less_or_equal
    value: 3.0
  unit: km
```

Soft example:

```yaml
- id: mountains-near-center
  source_relation: near
  strength: soft
  weight: 0.5

  evaluator:
    type: distance
    subject:
      type: feature
      feature_id: mountain-01
      part: center
    target:
      type: point
      x_km: 60.0
      y_km: 50.0

  scoring:
    type: linear_preference
    ideal: 0.0
    worst: 20.0
  unit: km
```

`source_relation` optional provenance only. Runtime behavior определяется compiled evaluator/predicate/scoring.

Compiler приводит built-in anchors/regions и normalized literals к physical primitives. Geometry-part semantics определены контрактом `DomainSpec` и не переинтерпретируются downstream modules.

## Dependent constraint boundary

Core 0.1 materializes layout reservations только из hard spatial constraints, цели которых уже имеют geometry на layout stage. Поэтому deferred feature не может иметь layout-hard dependency на другой deferred feature или ещё не существующую generated hydrology network. Такие specs compiler отклоняет как unsupported для Core 0.1; post-hydrology физические требования выражаются `SiteProfile`.

## Compiler guarantees

Если `GenerationPlan` создан успешно, уже проверено:

- все preset/operator ids известны;
- family/shape/operator совместимы;
- layout/effect parameter overrides и resolved domains валидны;
- feature/constraint ids и references валидны;
- selector parts совместимы с geometry shapes;
- deferred dependency boundary соблюдена;
- grid dimensions согласованы с physical dimensions;
- compiled constraint recipes исполнимы поддерживаемым registry.

Pipeline не повторяет эту semantic validation на каждом attempt.

## Fingerprints

Различаются два fingerprint:

- `spec_fingerprint` — fingerprint normalized source `DomainSpec`, включая metadata документа;
- `plan_fingerprint` — SHA-256 canonical **executable projection** Plan.

В semantic `plan_fingerprint` входят seed, grid/domain semantics, feature identities, layout/effect recipes, site profiles и compiled constraints. Не входят presentation/provenance-only данные вроде `label`, `tags`, `source_preset`, `spec_id` и generator debug metadata.

Это гарантирует, что косметическое переименование не меняет procedural identity Plan. Сам fingerprint не включается в fingerprinted payload. `LayoutCandidate` ссылается на `plan_fingerprint`.

## Чего в Plan нет

`GenerationPlan` не содержит:

- concrete centerline/boundary текущего attempt;
- attempt-specific sampled values;
- raster arrays;
- final coordinates dependent POI;
- Python callable;
- child RNG seeds;
- current attempt index;
- `max_attempts`, `target_valid_candidates` и другие execution-policy settings;
- debug/output settings.

`GenerationConfig` относится к execution policy, а не к описанию мира.
