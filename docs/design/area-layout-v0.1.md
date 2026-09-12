---
id: DESIGN-AREA-LAYOUT-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Area layout v0.1

Этот документ фиксирует deterministic area layout algorithm Core 0.1.

## Scope

Поддерживается `layout.mode = geometry`, `shape = area`.

Canonical result — обычный `AreaGeometry`: один простой outer polygon без holes. Генератор может использовать внутреннюю опорную точку и radial construction, но эти runtime values не сериализуются в `LayoutCandidate`.

Итоговый контракт остаётся:

```yaml
type: area
boundary:
  - {x_km: ... , y_km: ...}
  - {x_km: ... , y_km: ...}
  - {x_km: ... , y_km: ...}
```

Boundary содержит минимум три vertices, первая vertex не повторяется в конце, canonical orientation — counter-clockwise.

## Required layout parameters

Area recipe v0.1 использует ровно три parameters:

- `vertex_count`: integer, `>= 3`;
- `radial_extent`: float, `0 < value <= 1`;
- `radial_irregularity`: float, `0 <= value <= 1`.

`radial_extent` — normalized generation control, а не сохранённый радиус области. Он определяет долю доступного расстояния от runtime generation center до domain boundary вдоль каждого vertex ray.

`radial_irregularity` управляет variation отдельных radial distances. Итоговая область всегда хранится только как polygon vertices.

## RNG namespaces

Geometry streams:

```text
stage = layout
scope = ("feature", feature_id, "geometry", "area")
purpose = "center"
```

```text
stage = layout
scope = ("feature", feature_id, "geometry", "area")
purpose = "rotation"
```

```text
stage = layout
scope = ("feature", feature_id, "geometry", "area")
purpose = "radial-variation"
```

Layout parameter sampling сохраняет общий namespace:

```text
stage = layout
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

Изменение `vertex_count` не меняет RNG streams center/rotation. Random draws соседних features также не влияют на area realization.

## Runtime generation center

Внутренняя generation point выбирается внутри rectangular domain:

```text
center.x = width_km  * uniform01()
center.y = height_km * uniform01()
```

Она используется только для построения polygon и не является serialized geometry field.

Она также не определяет `FeaturePart.CENTER`: semantic center area вычисляется позже как centroid итогового polygon.

## Rotation and ordered rays

Один rotation draw:

```text
rotation = 2*pi*uniform01()
```

Для `N = vertex_count`:

```text
angle_i = rotation + 2*pi*i/N
```

Vertices создаются в этом порядке. Angular order является canonical CCW construction order.

## Radial construction

Для каждого ray вычисляется `available_i`: расстояние от generation center до rectangular domain boundary вдоль direction `angle_i`.

Затем один draw из `radial-variation` stream:

```text
u_i = uniform01()
factor_i = radial_extent * (1 - radial_irregularity*u_i)
radius_i = available_i * factor_i
```

Vertex:

```text
vertex_i = center + direction(angle_i) * radius_i
```

При `radial_irregularity = 0` все rays используют одинаковую normalized extent fraction. При увеличении irregularity отдельные vertices могут располагаться ближе к generation center.

Никаких hidden retries, polygon repair или post-hoc vertex sorting нет.

## Why this construction

Произвольные independently sampled map points могут образовывать self-intersecting polygon. Equal angular ordering вокруг общей внутренней point даёт star-shaped construction и существенно сужает пространство malformed результатов.

Однако implementation не полагается только на конструктивное предположение: итоговая geometry всё равно проходит explicit engine validation.

## Area engine invariants

Layout validation проверяет:

- boundary содержит минимум 3 vertices;
- все vertices внутри/on domain;
- нет zero-length edges;
- signed shoelace area положительна и ненулевая;
- boundary counter-clockwise;
- non-adjacent edges не self-intersect.

Нарушение invariant отклоняет attempt. Geometry не repair-ится и не reroll-ится.

## Spatial parts

Для area:

- `whole` — polygon footprint;
- `boundary` — outer polygon ring;
- `center` — geometric polygon centroid.

Runtime generation center не используется как semantic `center` selector.

## Evaluators in this slice

Area v0.1 layout evaluator добавляет только однозначные операции:

- point inside/outside area through `contained_fraction` / `overlap_fraction`;
- point <-> area whole minimum distance, где point внутри/on polygon имеет distance `0`;
- point <-> area boundary minimum Euclidean distance до polygon edges;
- area `center` как point selector для уже поддерживаемых point measurements.

Area<->area boolean overlap, polygon containment fractions, crossing и polygon boolean operations в этот slice не входят.

## Domain boundary

Каждая generated vertex лежит на ray segment между runtime generation center и rectangular domain boundary. Итоговый polygon обязан находиться внутри/on domain.

В отличие от band influence footprint, `AreaGeometry` является самой footprint area и не предполагает скрытого продолжения за domain.

## Non-goals

Не входят:

- holes;
- multipolygons;
- area<->area boolean operations;
- placement `RegionSet` materialization;
- constraint-aware proposal generation;
- terrain/hydrology/surface algorithms.
