---
id: CONTRACT-GENERATIONPLAN-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# GenerationPlan v0.1 — draft

`GenerationPlan` — внутренний сериализуемый resolved recipe между пользовательским `DomainSpec` и конкретной realization попыткой.

## Роль

После compilation в плане не должно оставаться зависимости от пользовательских preset-файлов как runtime-источника поведения. Preset уже раскрыт в generic geometry/operator definitions, parameter domains и compiled constraints.

## Верхний уровень

Концептуально:

```yaml
plan_version: "0.1"
source:
  domain_spec_id: example-domain-01
  domain_spec_schema: "0.1"
seed: 1847291

domain:
  width_km: 120.0
  height_km: 100.0

grid:
  cell_size_km: 0.25
  rows: 400
  columns: 480

features: {}
constraints: {}
```

В отличие от `DomainSpec`, план уже содержит вычисленные `rows/columns`.

## ResolvedFeature

Resolved feature содержит как минимум:

- `family`;
- geometry recipe (`shape` + geometry parameter domains);
- generic operator id;
- operator parameter domains;
- sampling policies;
- tags/metadata, не влияющие скрытым образом на поведение.

Примерно:

```yaml
central_mountains:
  family: terrain
  geometry:
    shape: band
    parameters:
      width_km:
        allowed: {min: 15.0, max: 30.0}
        sampling: {type: triangular, mode: 24.0}
      curvature:
        allowed: {min: 0.05, max: 0.30}
        sampling: {type: uniform}
  operation:
    id: ridge
    parameters:
      elevation_delta_m:
        allowed: {min: 800.0, max: 1800.0}
        sampling: {type: triangular, mode: 1250.0}
```

Конкретные значения ещё не обязаны быть выбраны.

## CompiledConstraint

Semantic relation компилируется в generic evaluator/predicate. Например `near` может стать `distance <= threshold`, а `inside` — containment predicate.

Примерно:

```yaml
fort-near-gorge:
  evaluator: distance
  subject:
    source: feature
    id: frontier_fort
    geometry_part: whole
  target:
    source: feature
    id: main_gorge
    geometry_part: endpoints
  predicate:
    operator: less_or_equal
    value: 3.0
    unit: km
  strength: hard
```

Слова `near`, `southwest` и названия presets не обязаны оставаться исполняемыми понятиями после compilation.

## Чего в плане нет

`GenerationPlan` не содержит:

- конкретную centerline текущей попытки;
- конкретные sampled values текущей попытки;
- heightmap/water/moisture arrays;
- координату окончательно размещённого dependent POI;
- Python callable;
- `max_attempts` и другие execution-budget settings.

Количество attempts относится к отдельному `GenerationConfig`, а не к описанию мира.