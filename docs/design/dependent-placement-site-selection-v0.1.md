---
id: DESIGN-DEPENDENT-PLACEMENT-SITE-SELECTION-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: true
---

# Выбор места для dependent placement v0.1

Этот документ фиксирует семантику финального point placement для deferred POI после materialized `PlacementReservation` и после появления upstream state terrain/hydrology/surface.

## Положение в pipeline

```text
PlacementReservation
+ TerrainState
+ HydrologyState
+ SurfaceState
-> candidate sites
-> hard requirements SiteProfile
-> valid sites
-> intrinsic preferences SiteProfile
-> near-best set
-> deterministic weighted selection
-> PlacementState.final_points
```

Placement не мутирует layout, terrain, hydrology или surface.

## Представление candidates

Core 0.1 не использует centers raster cells как canonical site candidates.

Candidates генерируются в мировых координатах через rotated lattice с явным физическим шагом `candidate_spacing_km`.

`candidate_spacing_km` является resolved semantic parameter operator-а dependent-placement и хранится в `GenerationPlan`; это не скрытая константа и не выводится из `grid.cell_size_km`.

Lattice имеет две независимые стохастические степени свободы:

```text
rotation
phase
```

После построения остаются только points lattice, лежащие в `PlacementReservation.allowed_region`.

Points candidates канонически сортируются по `(x_km, y_km)` до последующей оценки, поэтому порядок iteration не является семантическим.

Точное численное отображение `rotation + phase + candidate_spacing_km -> square lattice`, semantics reservation `covers` и hard filtering зафиксированы в:

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

Генерация candidates, sampling semantic parameters и финальный choice используют независимые streams.

## Семантика footprint

Каждый candidate оценивается через `SiteProfile.footprint_radius_km`.

Site metric измеряется по circular footprint вокруг point candidate, а не только в одной raster cell.

Raster fields могут использоваться как численное представление upstream state, но coordinates candidate остаются мировыми.

Точная численная семантика footprint, tie-breaks containing cell и формулы metrics определены в:

`docs/design/dependent-placement-site-metrics-v0.1.md`.

## Site metrics Core 0.1

Минимальный универсальный registry metrics:

- `slope_mean`;
- `water_fraction`;
- `elevation_mean`;
- `local_relief`;
- `relative_elevation`;
- `moisture_mean`;
- `vegetation_density_mean`;
- `distance_to_water`.

Идентификаторы metrics универсальны и не содержат семантики конкретного сеттинга или кампании.

Все численные определения этого registry нормативно зафиксированы в `Dependent Placement Site Metrics v0.1` и не должны переопределяться evaluators placement.

## Hard requirements

`SiteProfile.requirements` фильтруют физически недопустимые sites.

Evaluators Core 0.1:

- `less_or_equal`;
- `greater_or_equal`.

Candidate валиден только если проходят все requirements.

Если `valid_sites` пуст, attempt отклоняется. Скрытые retries, ослабление requirements или адаптация по предыдущим attempts запрещены.

## Внутренние preferences

Evaluators preferences Core 0.1:

- `maximize`;
- `minimize`;
- `preferred_range`.

Score preference всегда нормализуется в `[0,1]`.

### maximize / minimize

Нормализация производится относительно диапазона metric среди текущих valid sites.

```text
maximize:
  score = (value - observed_min) / (observed_max - observed_min)

minimize:
  score = (observed_max - value) / (observed_max - observed_min)
```

Если все valid sites имеют одинаковое значение metric, score для всех равен `1.0`. Это также покрывает случай отсутствия воды, где `distance_to_water = +inf` одинаков для всех candidates: preference не создаёт искусственного различия.

Смешение конечных и non-finite values для одной preference metric является capability error.

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

Результат ограничивается в `[0,1]`.

Если observed range не даёт различия между candidates, preference не создаёт искусственного различия и даёт score `1.0` в математически вырожденном случае.

## Составная suitability

Если preferences существуют:

```text
suitability = sum(score_i * weight_i) / sum(weight_i)
```

Если preferences отсутствуют:

```text
suitability = 1.0
```

Sites канонически сортируются по `(x_km, y_km)` до scoring. Внутренняя suitability не является score пользовательского soft constraint и не участвует напрямую в глобальном ranking candidate.

## Множество near-best

Operator dependent-placement содержит semantic parameter:

```text
near_best_delta in [0,1]
```

Core 0.1 `suitability_placement` требует точный набор effect parameters:

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

Граница включительная. Это намеренно позволяет выбирать не только абсолютный argmax.

## Финальный weighted selection

Из канонически отсортированного множества near-best выбирается одна point через отдельный deterministic weighted-choice RNG stream.

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

Так как `uniform01() < 1`, обычный path всегда попадает в один из cumulative intervals; последний candidate используется только как defensive floating-point fallback.

Если сумма weights равна нулю, используется `choice()` RNG-protocol-v1 по канонически отсортированным near-best sites.

Если preferences отсутствуют, все suitability = `1.0`, поэтому cumulative intervals имеют одинаковую длину и выбор равномерен.

Stream финального selection не зависит от streams генерации candidates, sampling parameters или порядка обхода features.

## Runtime state

Финальная point не записывается обратно в `LayoutCandidate`.

Runtime state:

```text
PlacementState
  final_points: dict[feature_id, PointGeometry]
```

`CandidateState` хранит `placement: PlacementState | None` как runtime output конкретного attempt.

Assembler позднее переносит selected points в `DomainData.features`.

## Validation

Validation placement проверяет как минимум:

- upstream layout/terrain/hydrology/surface существуют;
- layout относится к текущему attempt;
- каждый required reservation feature получил ровно одну final point;
- нет неизвестных id placement features;
- final points finite и внутри domain;
- final point находится внутри или на `allowed_region`;
- selected site проходит все hard `SiteProfile.requirements`;
- у каждого required feature существовал хотя бы один valid site;
- deterministic recomputation при тех же semantic inputs/RNG даёт тот же `PlacementState`.

Если хотя бы один required feature не имеет valid site, `PlacementState` может быть частичным runtime result, но validation placement отклоняет весь attempt. Скрытый fallback point, reroll внутри stage или ослабление requirements запрещены.

Некорректный или неподдерживаемый recipe placement является capability error и не маскируется как обычное отклонение attempt.

## Что не входит в v0.1

- deferred shapes, отличные от point;
- adaptive candidate density;
- Poisson-disc / blue-noise placement;
- взаимозависимые deferred POI;
- пользовательские soft constraints как внутренние site preference;
- скрытый retry при отсутствии valid site;
- привязка coordinates candidate к centers raster cells;
- запись final point обратно в `LayoutCandidate`;
- сборка `DomainData`.

## Состояние реализации

Runtime dependent point placement Core 0.1 реализован полностью до границы сборки `DomainData`:

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
