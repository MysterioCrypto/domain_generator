---
id: CONTRACT-GENERATIONPLAN-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# GenerationPlan v0.1 — draft

`GenerationPlan` — immutable internal serialized resolved recipe between `DomainSpec` and attempt-specific realization. После compilation pipeline не должен обращаться к preset registry или исходному DomainSpec для определения поведения.

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

После compilation preset как runtime behavior исчезает. Feature хранит resolved execution data:

```yaml
- id: mountain-01
  source_preset: mountain_range

  family: terrain
  shape: band

  lifecycle:
    layout_mode: geometry
    realization_stage: terrain

  operator: ridge

  parameters:
    width_km:
      kind: range
      type: float
      min: 15.0
      max: 30.0
      sampler:
        type: triangular
        mode: 24.0

    elevation_delta_m:
      kind: range
      type: float
      min: 900.0
      max: 1700.0
      sampler:
        type: triangular
        mode: 1300.0
```

`source_preset` сохраняется только как provenance/debug metadata; executable pipeline зависит от resolved `family`, `shape`, lifecycle, operator и parameter recipes.

### Lifecycle

`layout_mode` v0.1:

- `geometry` — layout создаёт concrete macro geometry;
- `reservation` — layout создаёт PlacementReservation, финальная geometry выбирается позднее.

`realization_stage` описывает стадию, где feature оказывает свой основной effect/получает финальную realization. Примеры:

```yaml
# terrain structural feature
lifecycle:
  layout_mode: geometry
  realization_stage: terrain

# surface feature
lifecycle:
  layout_mode: geometry
  realization_stage: surface

# dependent POI
lifecycle:
  layout_mode: reservation
  realization_stage: dependent_placement
```

### Parameters

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

Plan хранит sampler recipe, но не attempt-specific sampled value. Sampling выполняется соответствующей realization stage через независимый RNG namespace.

## POI SiteProfile

Dependent POI может содержать полностью resolved site profile:

```yaml
- id: fort-01
  source_preset: fort
  family: poi
  shape: point
  lifecycle:
    layout_mode: reservation
    realization_stage: dependent_placement
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

Hard site requirements фильтруют допустимые sites. Preferences формируют suitability score. Placement operator не обращается обратно к preset registry.

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

Compiler по возможности приводит relations к измерениям:

- distance;
- containment/contained fraction;
- subject overlap fraction;
- intersection/crossing length;
- boundary gap и т. п.

Built-in anchors/regions и normalized literals к этому моменту уже превращены в physical primitives (`point`, axis-aligned rectangle и feature references).

## Compiler guarantees

Если `GenerationPlan` создан успешно, уже проверено:

- все preset/operator ids известны;
- family/shape/operator совместимы;
- parameter overrides и resolved domains валидны;
- feature/constraint ids и references валидны;
- selector parts совместимы с geometry shapes;
- grid dimensions согласованы с physical dimensions;
- compiled constraint recipes исполнимы поддерживаемым registry.

Pipeline не повторяет эту semantic validation на каждом attempt.

## Fingerprint

Canonical serialization Plan fingerprintится SHA-256. Сам fingerprint не включается в fingerprinted payload. `LayoutCandidate` ссылается на `plan_fingerprint`, чтобы replay/debug не смешивал realization с другим Plan.

## Чего в Plan нет

`GenerationPlan` не содержит:

- concrete centerline/boundary текущего attempt;
- attempt-specific sampled values;
- raster arrays;
- окончательные coordinates dependent POI;
- Python callable;
- child RNG seeds;
- current attempt index;
- `max_attempts`, `target_valid_candidates` и другие execution-policy settings;
- debug/output settings.

`GenerationConfig` относится к execution policy, а не к описанию мира.
