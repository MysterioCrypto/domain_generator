---
id: DESIGN-DEPENDENT-PLACEMENT-SITE-SELECTION-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: true
---

# Dependent Placement Site Selection v0.1

Этот документ фиксирует семантику финального point placement для deferred POI после materialized `PlacementReservation` и после появления upstream terrain/hydrology/surface state.

## Pipeline position

```text
PlacementReservation
+ TerrainState
+ HydrologyState
+ SurfaceState
-> candidate sites
-> hard SiteProfile requirements
-> valid sites
-> intrinsic SiteProfile preferences
-> near-best set
-> deterministic weighted selection
-> PlacementState.final_points
```

Placement не мутирует layout, terrain, hydrology или surface.

## Candidate representation

Core 0.1 не использует raster-cell centers как canonical site candidates.

Кандидаты генерируются в world coordinates через rotated lattice с явным physical spacing `candidate_spacing_km`.

`candidate_spacing_km` является resolved semantic parameter dependent-placement operator и хранится в `GenerationPlan`; это не hidden constant и не выводится из `grid.cell_size_km`.

Lattice имеет два независимых stochastic degrees of freedom:

```text
rotation
phase
```

После построения остаются только lattice points, лежащие в `PlacementReservation.allowed_region`.

Candidate points canonical-сортируются по `(x_km, y_km)` до последующей оценки, поэтому iteration order не является semantic.

Точная numerical mapping `rotation + phase + candidate_spacing_km -> square lattice`, reservation covers semantics и hard filtering зафиксированы в:

`docs/design/dependent-placement-candidate-filtering-v0.1.md`.

## RNG namespaces

Для feature `<id>`:

```text
stage = placement
scope = ["feature", id, "site-candidates"]
purpose = "rotation"

stage = placement
scope = ["feature", id, "site-candidates"]
purpose = "phase"

stage = placement
scope = ["feature", id, "parameter", "candidate_spacing_km"]
purpose = "sample"

stage = placement
scope = ["feature", id, "parameter", "near_best_delta"]
purpose = "sample"

stage = placement
scope = ["feature", id, "site-selection"]
purpose = "weighted-choice"
```

Candidate generation, semantic parameter sampling и final choice используют независимые streams.

## Footprint semantics

Каждый candidate оценивается через `SiteProfile.footprint_radius_km`.

Site metric измеряется по circular footprint вокруг candidate point, а не только в одной raster cell.

Raster fields могут использоваться как numerical representation upstream state, но candidate coordinates остаются world-space.

Точная numerical footprint semantics, containing-cell tie-breaks и metric formulas определены в:

`docs/design/dependent-placement-site-metrics-v0.1.md`.

## Core 0.1 site metrics

Минимальный generic metric registry:

- `slope_mean`;
- `water_fraction`;
- `elevation_mean`;
- `local_relief`;
- `relative_elevation`;
- `moisture_mean`;
- `vegetation_density_mean`;
- `distance_to_water`.

Metric identifiers generic и не содержат setting/campaign-specific semantics.

Все numerical definitions этого registry являются нормативно зафиксированными `Dependent Placement Site Metrics v0.1` и не должны переопределяться placement evaluator-ами.

## Hard requirements

`SiteProfile.requirements` фильтруют physically invalid sites.

Core 0.1 evaluators:

- `less_or_equal`;
- `greater_or_equal`.

Candidate valid только если проходят все requirements.

Если `valid_sites` пуст, attempt отклоняется. Hidden retries, requirement relaxation или адаптация по предыдущим attempts запрещены.

## Intrinsic preferences

Core 0.1 preference evaluators:

- `maximize`;
- `minimize`;
- `preferred_range`.

Preference score всегда нормализуется в `[0,1]`.

### maximize / minimize

Нормализация производится относительно metric range среди текущих valid sites.

```text
maximize:
  score = (value - observed_min) / (observed_max - observed_min)

minimize:
  score = (observed_max - value) / (observed_max - observed_min)
```

Если все valid sites имеют одинаковое значение metric, score для всех равен `1.0`. Это также покрывает no-water case, где `distance_to_water = +inf` одинаков для всех candidates: preference не создаёт искусственного различия.

Mixed finite/non-finite values для одного preference metric являются capability error.

### preferred_range

Внутри `[min,max]` score = `1.0`.

Ниже preferred range:

```text
score = (value - observed_min) / (min - observed_min)
```

Выше preferred range:

```text
score = (observed_max - value) / (observed_max - max)
```

Результат clamp-ится в `[0,1]`.

Если observed range не предоставляет различия между candidates, preference не создаёт искусственное различие и даёт score `1.0` в математически вырожденном случае.

## Composite suitability

Если preferences существуют:

```text
suitability = sum(score_i * weight_i) / sum(weight_i)
```

Если preferences отсутствуют:

```text
suitability = 1.0
```

Sites canonical-сортируются по `(x_km, y_km)` до scoring. Intrinsic suitability не является user soft-constraint score и не участвует напрямую в global candidate ranking.

## Near-best set

Dependent-placement operator содержит semantic parameter:

```text
near_best_delta in [0,1]
```

Core 0.1 `suitability_placement` требует exact effect parameter set:

```text
candidate_spacing_km
near_best_delta
```

`near_best_delta` sample-ится один раз на feature/attempt через собственный semantic parameter RNG stream.

Пусть:

```text
best = max(suitability)
```

В near-best входят все valid sites:

```text
suitability >= best - near_best_delta
```

Граница inclusive. Это намеренно позволяет выбирать не только абсолютный argmax.

## Final weighted selection

Из canonical-sorted near-best set выбирается одна точка через отдельный deterministic weighted-choice RNG stream.

Вес candidate:

```text
weight = suitability
```

Если `sum(weight) > 0`:

```text
u = uniform01()
target = u * sum(weight)
selected = first candidate whose cumulative_weight > target
```

Так как `uniform01() < 1`, normal path всегда попадает в один из cumulative intervals; последний candidate используется только как defensive floating-point fallback.

Если сумма весов равна нулю, используется RNG-protocol-v1 `choice()` по canonical-sorted near-best sites.

Если preferences отсутствуют, все suitability = `1.0`, поэтому cumulative intervals имеют одинаковую длину и выбор uniform.

Final selection stream не зависит от candidate-generation streams, parameter sampling streams или feature iteration order.

## Runtime state

Финальная точка не записывается обратно в `LayoutCandidate`.

Runtime state:

```text
PlacementState
  final_points: dict[feature_id, PointGeometry]
```

`CandidateState` хранит `placement: PlacementState | None` как attempt-local runtime output.

Assembler позднее переносит selected points в `DomainData.features`.

## Validation

Placement validation проверяет как минимум:

- upstream layout/terrain/hydrology/surface существуют;
- layout относится к текущему attempt;
- каждый required reservation feature получил ровно одну final point;
- нет unknown placement feature ids;
- final points finite и внутри domain;
- final point находится внутри/on `allowed_region`;
- selected site проходит все hard `SiteProfile.requirements`;
- у каждой required feature существовал хотя бы один valid site;
- deterministic recomputation при тех же semantic inputs/RNG даёт тот же `PlacementState`.

Если хотя бы одна required feature не имеет valid site, `PlacementState` может быть частичным runtime result, но placement validation отклоняет весь attempt. Hidden fallback point, reroll внутри stage или requirement relaxation запрещены.

Invalid/unsupported placement recipe является capability error и не маскируется как обычный attempt rejection.

## Non-goals

Не входят в v0.1:

- deferred non-point shapes;
- adaptive candidate density;
- Poisson-disc / blue-noise placement;
- inter-dependent deferred POI;
- user soft constraints как intrinsic site preference;
- hidden retry при отсутствии valid site;
- привязка candidate coordinates к raster cell centers;
- запись final point обратно в `LayoutCandidate`;
- DomainData assembly.

## Implementation status

Core 0.1 dependent point placement runtime реализован полностью до границы DomainData assembly:

```text
reservation
-> rotated/phase-shifted world-space lattice
-> canonical ordering
-> site metrics
-> hard requirements
-> valid sites
-> preference scores
-> composite suitability
-> near-best
-> deterministic weighted selection
-> PlacementState.final_points
-> placement validation / attempt rejection
```
