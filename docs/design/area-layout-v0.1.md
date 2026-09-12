---
id: DESIGN-AREA-LAYOUT-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Area layout v0.1

Этот документ фиксирует детерминированный алгоритм area layout Core 0.1.

## Область действия

Поддерживается `layout.mode = geometry`, `shape = area`.

Канонический результат — обычный `AreaGeometry`: один простой outer polygon без holes. Генератор может использовать внутреннюю опорную точку и radial construction, но эти runtime values не сериализуются в `LayoutCandidate`.

Итоговый контракт остаётся:

```yaml
type: area
boundary:
  - {x_km: ... , y_km: ...}
  - {x_km: ... , y_km: ...}
  - {x_km: ... , y_km: ...}
```

Boundary содержит минимум три vertices, первая vertex не повторяется в конце, canonical orientation — против часовой стрелки.

## Обязательные параметры layout

Recipe area v0.1 использует ровно три parameters:

- `vertex_count`: integer, `>= 3`;
- `radial_extent`: float, `0 < value <= 1`;
- `radial_irregularity`: float, `0 <= value <= 1`.

`radial_extent` — normalized control генерации, а не сохраняемый радиус области. Он определяет долю доступного расстояния от runtime generation center до boundary domain вдоль каждого ray vertex.

`radial_irregularity` управляет variation отдельных radial distances. Итоговая область всегда хранится только как vertices polygon.

## RNG namespaces

Streams geometry:

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

Sampling parameters layout сохраняет общий namespace:

```text
stage = layout
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

Изменение `vertex_count` не меняет RNG streams center/rotation. Random draws соседних features также не влияют на realization area.

## Внутренний центр генерации

Внутренняя generation point выбирается внутри прямоугольного domain:

```text
center.x = width_km  * uniform01()
center.y = height_km * uniform01()
```

Она используется только для построения polygon и не является serialized geometry field.

Она также не определяет `FeaturePart.CENTER`: semantic center area вычисляется позже как centroid итогового polygon.

## Rotation и упорядоченные rays

Один draw rotation:

```text
rotation = 2*pi*uniform01()
```

Для `N = vertex_count`:

```text
angle_i = rotation + 2*pi*i/N
```

Vertices создаются в этом порядке. Angular order является canonical CCW construction order.

## Радиальная конструкция

Для каждого ray вычисляется `available_i`: расстояние от generation center до boundary прямоугольного domain вдоль direction `angle_i`.

Затем выполняется один draw из stream `radial-variation`:

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

Скрытых retries, polygon repair или post-hoc сортировки vertices нет.

## Почему используется такая конструкция

Произвольные независимо sampled map points могут образовывать self-intersecting polygon. Равномерный angular order вокруг общей внутренней point даёт star-shaped construction и существенно сужает пространство некорректных результатов.

Однако implementation не полагается только на конструктивное предположение: итоговая geometry всё равно проходит явную engine validation.

## Engine invariants area

Validation layout проверяет:

- boundary содержит минимум 3 vertices;
- все vertices внутри или на domain;
- нет zero-length edges;
- signed shoelace area положительна и ненулевая;
- boundary ориентирована против часовой стрелки;
- non-adjacent edges не self-intersect.

Нарушение invariant отклоняет attempt. Geometry не исправляется и не reroll-ится.

## Пространственные части

Для area:

- `whole` — footprint polygon;
- `boundary` — outer polygon ring;
- `center` — geometric polygon centroid.

Runtime generation center не используется как semantic selector `center`.

## Evaluators этого slice

Evaluator area v0.1 добавляет только однозначные операции:

- point inside/outside area через `contained_fraction` / `overlap_fraction`;
- minimum distance point <-> area whole, где point внутри или на polygon имеет distance `0`;
- minimum Euclidean distance point <-> area boundary до edges polygon;
- area `center` как point selector для уже поддерживаемых point measurements.

Area<->area boolean overlap, fractions polygon containment, crossing и boolean operations polygon в этот slice не входят.

## Граница domain

Каждая generated vertex лежит на ray segment между runtime generation center и boundary прямоугольного domain. Итоговый polygon обязан находиться внутри или на domain.

В отличие от influence footprint band, `AreaGeometry` является самой footprint area и не предполагает скрытого продолжения за domain.

## Что не входит в этот slice

- holes;
- multipolygons;
- boolean operations area<->area;
- materialization placement `RegionSet`;
- proposal generation с учётом constraints;
- алгоритмы terrain/hydrology/surface.
