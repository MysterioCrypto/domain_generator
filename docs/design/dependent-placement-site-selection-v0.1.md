---
id: DESIGN-DEPENDENT-PLACEMENT-SITE-SELECTION-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: false
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
scope = ["feature", id, "site-selection"]
purpose = "weighted-choice"
```

Candidate generation и final choice используют независимые streams.

## Footprint semantics

Каждый candidate оценивается через `SiteProfile.footprint_radius_km`.

Site metric измеряется по circular footprint вокруг candidate point, а не только в одной raster cell.

Raster fields могут использоваться как numerical representation upstream state, но candidate coordinates остаются world-space.

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

Metric identifiers generic и не содержат campaign-specific semantics.

Точная numerical definition каждой metric должна быть отдельно зафиксирована рядом с соответствующим upstream field/state до реализации placement.

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

Если все valid sites имеют одинаковое значение metric, score для всех равен `1.0`.

### preferred_range

Внутри `[min,max]` score = `1.0`.

За пределами preferred range score линейно уменьшается относительно observed valid-site metric range на соответствующей стороне.

Если observed range не предоставляет различия между candidates, preference не создаёт искусственное различие и даёт score `1.0` там, где это математически вырождено.

## Composite suitability

Если preferences существуют:

```text
suitability = sum(score_i * weight_i) / sum(weight_i)
```

Если preferences отсутствуют:

```text
suitability = 1.0
```

Intrinsic suitability не является user soft-constraint score и не участвует напрямую в global candidate ranking.

## Near-best set

Dependent-placement operator содержит semantic parameter:

```text
near_best_delta in [0,1]
```

Пусть:

```text
best = max(suitability)
```

В near-best входят все valid sites:

```text
suitability >= best - near_best_delta
```

Это намеренно позволяет выбирать не только абсолютный argmax.

## Final weighted selection

Из near-best set выбирается одна точка через отдельный deterministic weighted-choice RNG stream.

Вес candidate:

```text
weight = suitability
```

Если сумма весов равна нулю, используется uniform choice по canonical-sorted near-best sites.

Если preferences отсутствуют, все suitability = 1.0, поэтому выбор uniform.

## Runtime state

Финальная точка не записывается обратно в `LayoutCandidate`.

Runtime state:

```text
PlacementState
  final_points: dict[feature_id, PointGeometry]
```

Assembler позднее переносит selected points в `DomainData.features`.

## Validation

Placement validation должна как минимум проверить:

- каждый required reservation feature получил ровно одну final point;
- final point находится внутри/on `allowed_region`;
- selected site прошёл все hard SiteProfile requirements;
- final point finite и внутри domain;
- никаких unknown placement feature ids.

## Non-goals

Не входят в v0.1:

- deferred non-point shapes;
- adaptive candidate density;
- Poisson-disc / blue-noise placement;
- inter-dependent deferred POI;
- user soft constraints как intrinsic site preference;
- hidden retry при отсутствии valid site;
- привязка candidate coordinates к raster cell centers.

## Implementation gate

Эта семантика намеренно документируется до runtime implementation.

Placement implementation блокируется до появления и фиксации upstream numerical semantics для terrain/hydrology/surface fields и site metrics. Следующий реализуемый vertical slice начинается с `TerrainState` и canonical elevation field.
