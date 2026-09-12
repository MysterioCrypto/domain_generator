---
id: DESIGN-PLACEMENT-RESERVATION-MATERIALIZATION-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Placement Reservation Materialization v0.1

Этот документ фиксирует materialization `PlacementReservation.allowed_region` для deferred point POI в Core 0.1.

## Scope

Reservation layout v0.1 применяется только к feature, у которого:

- `layout.mode = reservation`;
- `final_shape = point`;
- `family = poi`;
- effect stage = `dependent_placement`.

Reservation не выбирает финальную точку. Он materialize-ит vector `RegionSet`, внутри которого поздняя placement stage имеет право выбирать point.

Deferred-to-deferred hard dependencies не поддерживаются. Reservation строится только из уже materialized geometry и literal/domain compiled selectors.

## Pipeline position

```text
GenerationPlan
  -> geometry materialization (point/corridor/band/area)
  -> placement reservation materialization
  -> layout validation
  -> later terrain/hydrology/surface
  -> dependent placement
```

Reservation materialization является частью layout stage. Она не использует RNG.

## Initial region

Для каждого reservation feature:

```text
allowed = entire rectangular domain
```

Domain преобразуется в polygon `[SW, SE, NE, NW]`.

## Constraints that participate

В reservation v0.1 учитываются только hard constraints, где deferred feature является `evaluator.subject` целиком (`part = whole` или `center`, которые эквивалентны для point final shape).

Soft constraints не изменяют reservation.

Hard constraint, где deferred feature находится только в target, не materialize-ится этим slice и является capability error, если pipeline пытается использовать его для deferred placement semantics.

Поддерживаются четыре relation/evaluator semantics:

### inside

Compiled form:

```text
evaluator = contained_fraction
predicate = greater_or_equal 1.0
```

Operation:

```text
allowed = allowed INTERSECTION target_region
```

Target должен materialize-иться как area-like region: literal rectangle или `AreaGeometry.whole`.

### outside

Compiled form:

```text
evaluator = overlap_fraction
predicate = less_or_equal 0.0
```

Operation:

```text
allowed = allowed DIFFERENCE target_region
```

Target должен materialize-иться как area-like region: literal rectangle или `AreaGeometry.whole`.

### near

Compiled form:

```text
evaluator = distance
predicate = less_or_equal distance_km
```

Operation:

```text
allowed = allowed INTERSECTION BUFFER(target, distance_km)
```

Target может быть point-like, corridor whole, area whole/boundary, literal point или literal rectangle.

`BandGeometry.whole` и `BandGeometry.boundary` пока capability errors, потому что canonical band footprint ещё не materialize-ится.

Band/corridor `start`, `end`, `center` разрешаются как point-like target.

### far_from

Compiled form:

```text
evaluator = distance
predicate = greater_or_equal distance_km
```

Operation:

```text
allowed = allowed DIFFERENCE BUFFER(target, distance_km)
```

Target support совпадает с `near`.

## Unsupported relations

Для deferred point reservation `crosses`, `overlaps` (за пределами exact outside compiled form) и `adjacent` не materialize-ятся в Core 0.1. Unsupported evaluator/predicate combination — capability error, а не silently ignored constraint.

## Boolean geometry backend

Contracts не зависят от Shapely/GEOS. Внутренний backend выполняет:

- polygon intersection;
- polygon difference;
- positive buffer;
- conversion between Core geometry and backend geometry.

Первый backend — **Shapely 2.1.2**. Package dependency фиксируется exact pin `shapely==2.1.2`; обновление backend версии является осознанным generator change. Официальные Shapely 2.1.2 wheels включают GEOS 3.13.1.

Dependency boundary:

```text
contracts.RegionSet
        ^
        | canonical conversion
        |
Core geometry adapter
        ^
        |
Shapely / GEOS
```

Shapely objects никогда не попадают в Pydantic contracts, fingerprints или serialized artifacts.

## Buffer semantics

Core 0.1 явно фиксирует polygonal approximation:

```text
quad_segs = 8
cap_style = round
join_style = round
single_sided = false
```

Не полагаться на library defaults.

Изменение этих параметров меняет semantic geometry и требует отдельного generator-version decision.

## Canonical RegionSet

Любой backend result преобразуется в Core `RegionSet`.

Canonicalization v0.1:

1. допускаются только Polygon/MultiPolygon polygonal components;
2. empty result -> `RegionSet(polygons=())`;
3. repeated closing coordinate удаляется;
4. outer rings oriented CCW;
5. hole rings oriented CW;
6. каждый ring циклически поворачивается так, чтобы lexicographically smallest `(x_km, y_km)` vertex был первым;
7. holes сортируются lexicographically по canonical vertex tuples;
8. polygons сортируются по canonical `(outer, holes)` representation.

Никакого произвольного rounding/precision grid в v0.1 нет. Все coordinates остаются double precision backend results. Precision policy может быть добавлена только отдельным design decision.

Non-polygonal remnants после boolean operations (точка/линия при касании) не являются допустимой площадью для placement point и отбрасываются при conversion в RegionSet.

## Source constraints

`PlacementReservation.source_constraints` содержит IDs hard constraints, реально применённых к allowed region, в deterministic sorted order.

Constraints, не относящиеся к данному reservation feature, туда не входят.

## Empty reservation

Empty `RegionSet` структурно валиден:

```text
allowed_region.polygons = ()
```

Но layout validation добавляет engine invariant и отклоняет attempt, если reservation для required deferred feature пуст.

Никаких hidden retries или automatic constraint relaxation нет.

## Determinism

Materialization не использует RNG. Determinism обеспечивается:

- exact input geometry;
- fixed buffer semantics;
- exact pinned Shapely backend version;
- own canonical RegionSet serialization;
- deterministic constraint order by constraint id.

Observability/debug paths не могут менять boolean operation sequence или geometry.

## Non-goals

Не входят в этот slice:

- фактический выбор final POI point;
- SiteProfile evaluation;
- band footprint materialization;
- general polygon-polygon overlap/crossing constraint engine;
- deferred-to-deferred reservations;
- arbitrary CRS/geodesic buffering;
- precision snapping/rounding;
- soft constraint scoring.
