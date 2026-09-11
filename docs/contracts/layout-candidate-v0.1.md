---
id: CONTRACT-LAYOUTCANDIDATE-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# LayoutCandidate v0.1 — draft

`LayoutCandidate` фиксирует конкретную macro-spatial realization одного attempt. Он содержит уже реализованные structural geometries и materialized placement reservations, но не physical fields, hydrology, surface data или final dependent placements.

## Корень

```yaml
layout_version: "0.1"

source_plan:
  fingerprint: "sha256:..."

attempt_index: 3

geometry_realizations: {}
placement_reservations: {}
```

`attempt_index >= 0`. `source_plan.fingerprint` должен совпадать с semantic `plan_fingerprint` используемого `GenerationPlan`.

## Geometry realizations

Каждый feature с `layout.mode = geometry` получает concrete geometry:

```yaml
geometry_realizations:
  mountain-01:
    type: band
    centerline:
      - {x_km: 5.2, y_km: 7.4}
      - {x_km: 59.3, y_km: 52.0}
      - {x_km: 116.0, y_km: 96.1}
    width_profile:
      - {t: 0.0, width_km: 18.2}
      - {t: 0.5, width_km: 24.7}
      - {t: 1.0, width_km: 20.4}
```

Attempt-local sampler inputs, noise seeds и effect parameters здесь не сохраняются; LayoutCandidate хранит outcome macro geometry.

## Geometry primitives

### Point

```yaml
type: point
x_km: 43.7
y_km: 19.8
```

### Corridor

```yaml
type: corridor
centerline:
  - {x_km: 10.0, y_km: 20.0}
  - {x_km: 40.0, y_km: 50.0}
```

Centerline содержит минимум две точки. Порядок значим: первая точка — `start`, последняя — `end`.

### Band

```yaml
type: band
centerline:
  - {x_km: 10.0, y_km: 20.0}
  - {x_km: 40.0, y_km: 50.0}
width_profile:
  - {t: 0.0, width_km: 18.0}
  - {t: 1.0, width_km: 23.0}
```

`width_km` — полная ширина band. `t` находится в `[0,1]`, samples отсортированы; `t=0` и `t=1` обязательны. Между samples используется линейная интерполяция. Footprint выводится из centerline и width profile по versioned geometry implementation.

### Area

```yaml
type: area
boundary:
  - {x_km: 8.0, y_km: 44.0}
  - {x_km: 29.0, y_km: 38.0}
  - {x_km: 14.0, y_km: 16.0}
```

Core 0.1 `AreaGeometry` — один простой outer polygon без holes и self-intersections, минимум три вершины. Последняя вершина не дублирует первую; closing edge подразумевается. Canonical outer ring ориентирован counter-clockwise.

## Domain boundary semantics

Layout geometry не обязана целиком помещать свой influence footprint внутрь domain:

- final point geometry должна находиться внутри domain или на boundary;
- corridor/band centerline должна находиться внутри domain или на boundary;
- band footprint/influence может выходить за boundary и при rasterization клиппится domain;
- raster effects вычисляются только внутри domain.

Это позволяет структурным объектам естественно продолжаться за пределами рассматриваемого региона.

## PlacementReservation

Каждый feature с `layout.mode = reservation` получает materialized allowed region:

```yaml
placement_reservations:
  fort-01:
    final_shape: point
    source_constraints:
      - fort-near-gorge
    allowed_region:
      type: region_set
      polygons:
        - outer:
            - {x_km: 55.0, y_km: 22.0}
            - {x_km: 68.0, y_km: 22.0}
            - {x_km: 68.0, y_km: 35.0}
            - {x_km: 55.0, y_km: 35.0}
          holes: []
```

Reservation хранит результат применения hard spatial constraints, а не повторяет symbolic relations из `GenerationPlan`.

Conceptually:

```text
R0 = whole domain
R1 = R0 ∩ hard_condition_1
R2 = R1 - hard_exclusion_2
...
PlacementReservation = Rn
```

Soft constraints не сужают reservation и применяются позже как suitability/ranking signals.

## RegionSet

`RegionSet` допускает несколько disconnected polygons и holes:

```yaml
type: region_set
polygons:
  - outer: [...]
    holes:
      - [...]
  - outer: [...]
    holes: []
```

Canonical convention:

- outer rings counter-clockwise;
- holes clockwise;
- rings simple and non-self-intersecting;
- paths use world coordinates in km.

`RegionSet` сильнее обычного feature `AreaGeometry`, потому что materialized boolean geometry может стать disconnected или получить holes.

Reservation хранится как vector geometry, не raster mask, чтобы macro layout не зависел от simulation resolution. Placement stage может rasterize region для конкретного grid.

## Empty reservation

Пустой region set структурно валиден:

```yaml
allowed_region:
  type: region_set
  polygons: []
```

Это означает well-formed, но spatially invalid candidate. Layout validation возвращает hard failure вроде `EMPTY_PLACEMENT_RESERVATION`; схема сама по себе такой документ не отвергает.

## Deferred dependencies v0.1

Reservation может материализоваться только из hard spatial constraints, цели которых уже имеют geometry на layout stage. Core 0.1 не поддерживает layout-hard dependencies вида deferred feature -> deferred feature или deferred feature -> future generated river network. Такие зависимости отклоняются compiler до attempts.

Физические post-hydrology требования dependent POI выражаются через resolved `SiteProfile`.

## Чего здесь нет

`LayoutCandidate` не содержит:

- elevation/water/moisture/vegetation arrays;
- sampled terrain effect values и noise traces;
- river network;
- final coordinates dependent POI;
- suitability scores;
- `ValidationResult`;
- accepted/rejected status.

Validation остаётся отдельным immutable diagnostic result.
