---
id: CONTRACT-LAYOUTCANDIDATE-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# LayoutCandidate v0.1 — черновик

`LayoutCandidate` фиксирует конкретную macro-spatial realization одного attempt. Он содержит уже реализованные structural geometries и materialized placement reservations, но не physical fields, hydrology, surface data или финальные dependent placements.

## Корень

```yaml
layout_version: "0.1"

source_plan:
  fingerprint: "sha256:..."

attempt_index: 3

geometry_realizations: {}
placement_reservations: {}
```

`attempt_index >= 0`. `source_plan.fingerprint` должен совпадать с семантическим `plan_fingerprint` используемого `GenerationPlan`.

## Реализованные geometries

Каждый feature с `layout.mode = geometry` получает конкретную geometry:

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

Attempt-local sampler inputs, noise seeds и параметры effect здесь не сохраняются; `LayoutCandidate` хранит результат macro geometry.

## Примитивы geometry

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

`AreaGeometry` Core 0.1 — один простой outer polygon без holes и self-intersections, минимум три вершины. Последняя вершина не дублирует первую; closing edge подразумевается. Canonical outer ring ориентирован против часовой стрелки.

## Семантика границы domain

Layout geometry не обязана целиком помещать свой footprint влияния внутрь domain:

- финальная point geometry должна находиться внутри domain или на boundary;
- centerline corridor/band должна находиться внутри domain или на boundary;
- footprint/influence band может выходить за boundary и при rasterization обрезается domain;
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

Концептуально:

```text
R0 = whole domain
R1 = R0 ∩ hard_condition_1
R2 = R1 - hard_exclusion_2
...
PlacementReservation = Rn
```

Soft constraints не сужают reservation и применяются позже как signals suitability/ranking.

## RegionSet

`RegionSet` допускает несколько несвязанных polygons и holes:

```yaml
type: region_set
polygons:
  - outer: [...]
    holes:
      - [...]
  - outer: [...]
    holes: []
```

Каноническое соглашение:

- outer rings ориентированы против часовой стрелки;
- holes — по часовой стрелке;
- rings простые и без self-intersection;
- paths используют мировые координаты в километрах.

`RegionSet` выразительнее обычного feature `AreaGeometry`, потому что materialized boolean geometry может стать несвязной или получить holes.

Reservation хранится как vector geometry, а не raster mask, чтобы macro layout не зависел от simulation resolution. Стадия placement может rasterize region для конкретного grid.

## Пустой reservation

Пустой region set структурно валиден:

```yaml
allowed_region:
  type: region_set
  polygons: []
```

Это означает корректно сформированный, но пространственно недопустимый candidate. Layout validation возвращает hard failure вроде `EMPTY_PLACEMENT_RESERVATION`; сама schema такой документ не отвергает.

## Deferred dependencies v0.1

Reservation может материализоваться только из hard spatial constraints, цели которых уже имеют geometry на стадии layout. Core 0.1 не поддерживает layout-hard dependencies вида deferred feature -> deferred feature или deferred feature -> будущая generated river network. Такие зависимости compiler отклоняет до запуска attempts.

Физические post-hydrology требования dependent POI выражаются через resolved `SiteProfile`.

## Чего здесь нет

`LayoutCandidate` не содержит:

- arrays elevation/water/moisture/vegetation;
- sampled terrain effect values и noise traces;
- river network;
- финальные координаты dependent POI;
- suitability scores;
- `ValidationResult`;
- статус accepted/rejected.

Validation остаётся отдельным неизменяемым diagnostic result.
