---
id: DESIGN-PLACEMENT-RESERVATION-MATERIALIZATION-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Materialization PlacementReservation v0.1

Этот документ фиксирует materialization `PlacementReservation.allowed_region` для deferred point POI в Core 0.1.

## Область действия

Reservation layout v0.1 применяется только к feature, у которого:

- `layout.mode = reservation`;
- `final_shape = point`;
- `family = poi`;
- stage effect = `dependent_placement`.

Reservation не выбирает финальную точку. Он materialize-ит vector `RegionSet`, внутри которого поздняя stage placement имеет право выбирать point.

Hard dependencies deferred-to-deferred не поддерживаются. Reservation строится только из уже materialized geometry и literal/domain compiled selectors.

## Положение в pipeline

```text
GenerationPlan
  -> geometry materialization (point/corridor/band/area)
  -> placement reservation materialization
  -> layout validation
  -> later terrain/hydrology/surface
  -> dependent placement
```

Materialization reservation является частью стадии layout. Она не использует RNG.

## Начальная область

Для каждого reservation feature:

```text
allowed = entire rectangular domain
```

Domain преобразуется в polygon `[SW, SE, NE, NW]`.

## Constraints, участвующие в reservation

В reservation v0.1 учитываются только hard constraints, где deferred feature является `evaluator.subject` целиком (`part = whole` или `center`, которые эквивалентны для point final shape).

Soft constraints не изменяют reservation.

Hard constraint, где deferred feature находится только в target, не materialize-ится этим slice и является capability error, если pipeline пытается использовать его для semantics deferred placement.

Поддерживаются четыре semantics relation/evaluator:

### inside

Compiled form:

```text
evaluator = contained_fraction
predicate = greater_or_equal 1.0
```

Операция:

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

Операция:

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

Операция:

```text
allowed = allowed INTERSECTION BUFFER(target, distance_km)
```

Target может быть point-like, corridor whole, area whole/boundary, literal point или literal rectangle.

`BandGeometry.whole` и `BandGeometry.boundary` пока являются capability errors, потому что canonical footprint band ещё не materialize-ится.

Band/corridor `start`, `end`, `center` разрешаются как point-like target.

### far_from

Compiled form:

```text
evaluator = distance
predicate = greater_or_equal distance_km
```

Операция:

```text
allowed = allowed DIFFERENCE BUFFER(target, distance_km)
```

Поддерживаемые target совпадают с `near`.

## Неподдерживаемые relations

Для deferred point reservation `crosses`, `overlaps` за пределами exact outside compiled form и `adjacent` не materialize-ятся в Core 0.1. Неподдерживаемая комбинация evaluator/predicate — capability error, а не молча проигнорированный constraint.

## Backend boolean geometry

Contracts не зависят от Shapely/GEOS. Внутренний backend выполняет:

- intersection polygons;
- difference polygons;
- positive buffer;
- conversion между geometry Core и backend geometry.

Первый backend — **Shapely 2.1.2**. Dependency package фиксируется exact pin `shapely==2.1.2`; обновление версии backend является осознанным изменением generator. Официальные wheels Shapely 2.1.2 включают GEOS 3.13.1.

Граница dependency:

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

Objects Shapely никогда не попадают в Pydantic contracts, fingerprints или serialized artifacts.

## Семантика buffer

Core 0.1 явно фиксирует polygonal approximation:

```text
quad_segs = 8
cap_style = round
join_style = round
single_sided = false
```

Не следует полагаться на defaults библиотеки.

Изменение этих параметров меняет semantic geometry и требует отдельного решения о версии generator.

## Канонический RegionSet

Любой результат backend преобразуется в Core `RegionSet`.

Canonicalization v0.1:

1. допускаются только polygonal components `Polygon`/`MultiPolygon`;
2. пустой result -> `RegionSet(polygons=())`;
3. повторная closing coordinate удаляется;
4. outer rings ориентируются против часовой стрелки;
5. hole rings ориентируются по часовой стрелке;
6. каждый ring циклически поворачивается так, чтобы лексикографически минимальная vertex `(x_km, y_km)` была первой;
7. holes сортируются лексикографически по canonical tuples vertices;
8. polygons сортируются по canonical representation `(outer, holes)`.

Произвольного rounding/precision grid в v0.1 нет. Все coordinates остаются double-precision results backend. Precision policy может быть добавлена только отдельным design decision.

Non-polygonal remnants после boolean operations — точка или линия при касании — не являются допустимой площадью для placement point и отбрасываются при conversion в `RegionSet`.

## Source constraints

`PlacementReservation.source_constraints` содержит id hard constraints, реально применённых к allowed region, в детерминированном отсортированном порядке.

Constraints, не относящиеся к данному reservation feature, туда не входят.

## Пустой reservation

Пустой `RegionSet` структурно валиден:

```text
allowed_region.polygons = ()
```

Но validation layout добавляет engine invariant и отклоняет attempt, если reservation для required deferred feature пуст.

Скрытых retries или автоматического ослабления constraints нет.

## Детерминированность

Materialization не использует RNG. Детерминированность обеспечивается:

- точной входной geometry;
- фиксированной семантикой buffer;
- точно закреплённой версией backend Shapely;
- собственной canonical serialization `RegionSet`;
- детерминированным порядком constraints по `constraint.id`.

Observability/debug paths не могут менять sequence boolean operations или geometry.

## Что не входит в этот slice

- фактический выбор финальной point POI;
- evaluation `SiteProfile`;
- materialization footprint band;
- общий engine overlap/crossing constraints polygon-polygon;
- reservations deferred-to-deferred;
- arbitrary CRS/geodesic buffering;
- precision snapping/rounding;
- scoring soft constraints.
