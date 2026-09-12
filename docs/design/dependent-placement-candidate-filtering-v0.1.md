---
id: DESIGN-DEPENDENT-PLACEMENT-CANDIDATE-FILTERING-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: true
---

# Dependent Placement Candidate Filtering v0.1

Этот checkpoint реализует первую половину runtime dependent placement после materialized `PlacementReservation` и Site Metrics v0.1.

В scope входят:

```text
PlacementReservation
+ dependent-placement feature recipe
+ TerrainState
+ HydrologyState
+ SurfaceState
-> deterministic world-space candidate lattice
-> reservation containment
-> canonical candidate order
-> site metrics
-> hard SiteProfile requirements
-> valid sites
```

Preference scoring, near-best filtering, weighted final selection и `PlacementState.final_points` не входят в этот checkpoint.

## Candidate spacing

Dependent-placement operator обязан иметь resolved semantic parameter:

```text
candidate_spacing_km
```

Он должен разрешаться в finite float `> 0`.

Sampling использует standard parameter namespace:

```text
stage   = placement
scope   = ("feature", feature_id, "parameter", "candidate_spacing_km")
purpose = "sample"
```

Параметр не выводится из raster cell size и не является hidden constant.

## Rotated square lattice

Для feature `<id>` используются два независимых streams:

```text
stage = placement
scope = ("feature", id, "site-candidates")
purpose = "rotation"

stage = placement
scope = ("feature", id, "site-candidates")
purpose = "phase"
```

Пусть `s = candidate_spacing_km`.

Rotation stream делает один draw:

```text
theta = uniform01 * (pi / 2)
```

Период `pi/2` достаточен для square lattice: повороты на 90 градусов задают ту же решётку.

Phase stream делает ровно два draw:

```text
phase_u = uniform01 * s
phase_v = uniform01 * s
```

В rotated coordinates lattice points:

```text
u = phase_u + i*s
v = phase_v + j*s
```

World coordinates:

```text
x = cos(theta)*u - sin(theta)*v
y = sin(theta)*u + cos(theta)*v
```

`i` и `j` — все integers, необходимые для покрытия axis-aligned domain rectangle. Для finite enumeration domain corners переводятся обратным rotation в `(u,v)`, после чего integer ranges вычисляются через `ceil`/`floor`.

Никаких retries, jitter, clamping, snapping или adaptive density нет.

## Domain and reservation filtering

После lattice enumeration остаются только точки, удовлетворяющие:

```text
0 <= x <= domain.width_km
0 <= y <= domain.height_km
```

Затем candidate должен лежать inside/on:

```text
PlacementReservation.allowed_region
```

Containment использует polygonal `covers` semantics: outer boundary разрешена, boundary hole не считается interior hole и также покрывается polygon boundary semantics backend-а.

Пустой reservation даёт пустой candidate set.

Core не создаёт fallback point и не ослабляет reservation.

## Canonical order

После filtering candidate points сортируются по exact runtime doubles:

```text
(x_km, y_km)
```

Duplicates удаляются по exact pair `(x_km, y_km)` до сортировки.

Iteration order lattice enumeration не является semantic.

## Candidate evaluation

Каждый retained candidate оценивается через `Dependent Placement Site Metrics v0.1` с:

```text
feature.effect.site_profile.footprint_radius_km
```

Attempt-global `SiteMetricContext` создаётся один раз и переиспользуется всеми candidates.

## Hard requirements

Core 0.1 поддерживает только:

```text
less_or_equal
greater_or_equal
```

Requirement:

```text
metric evaluator value
```

применяется к metric registry Site Metrics v0.1.

Unknown metric id или evaluator — explicit placement capability error.

Semantics:

```text
less_or_equal:    metric <= value
greater_or_equal: metric >= value
```

IEEE `+inf` для `distance_to_water` сохраняет обычные comparisons. Поэтому при domain без воды:

```text
+inf <= finite -> false
+inf >= finite -> true
```

Candidate valid только если проходят все requirements.

Если requirements отсутствуют, все retained candidates valid.

## Empty valid set

Пустой valid-site set является semantic placement failure, а не capability error и не вызывает hidden retry.

В этом checkpoint runtime helper возвращает пустой tuple. Последующий complete placement stage переведёт это состояние в attempt rejection.

## Runtime representation

Runtime-only:

```text
EvaluatedSite
  point: PointGeometry
  metrics: dict[str, float]
```

Он не является serialized Core contract и не попадает в `DomainData`.

## Non-goals

Не входят:

- preference scoring;
- maximize/minimize/preferred_range;
- suitability composite;
- near-best filtering;
- final weighted choice;
- `PlacementState`;
- adaptive lattice spacing;
- Poisson-disc/blue-noise placement;
- inter-dependent deferred POI;
- non-point deferred geometry;
- raster-center candidate generation.
