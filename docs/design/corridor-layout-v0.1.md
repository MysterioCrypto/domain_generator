---
id: DESIGN-CORRIDOR-LAYOUT-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Corridor layout v0.1

Этот документ фиксирует первый deterministic corridor layout algorithm Core 0.1.

## Scope

Поддерживается `layout.mode = geometry`, `shape = corridor`.

Canonical result — `CorridorGeometry` с ordered polyline `centerline`. Serialized geometry не хранит spline/Bezier representation.

## Required layout parameters

Corridor recipe v0.1 использует ровно два layout parameters:

- `control_point_count`: integer, `>= 0`;
- `curvature`: float в `[0, 1]`.

Они остаются обычными `ResolvedParameter` recipes и sample-ятся attempt-local runtime sampler'ом.

## RNG namespaces

Endpoint streams изолированы от control-point stream:

```text
stage = layout
scope = ("feature", feature_id, "geometry", "corridor")
purpose = "start"
```

```text
stage = layout
scope = ("feature", feature_id, "geometry", "corridor")
purpose = "end"
```

```text
stage = layout
scope = ("feature", feature_id, "geometry", "corridor")
purpose = "control-points"
```

Layout parameter sampling использует отдельный namespace на parameter:

```text
stage = layout
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

Изменение `control_point_count` не должно менять sampled start/end.

## Endpoints

Start и end выбираются независимо внутри rectangular domain:

```text
x = width_km  * uniform01()
y = height_km * uniform01()
```

Никаких hidden retries или constraint-aware steering нет.

## Internal control points

Для `N = control_point_count` internal points базовый position parameter:

```text
t_i = i / (N + 1), i = 1..N
```

Base point — linear interpolation между start/end.

Для ненулевой длины corridor вычисляется unit normal к start→end. Control point смещается вдоль normal.

Envelope:

```text
envelope(t) = 4 * t * (1 - t)
```

Он равен 0 на endpoints и достигает 1 в середине.

Для каждого internal point один draw:

```text
r = uniform(-1, +1)
```

Доступное расстояние до domain boundary вычисляется вдоль positive/negative normal отдельно. Signed offset:

```text
strength = curvature * envelope(t)

if r >= 0:
    offset = r * strength * available_positive
else:
    offset = (-r) * strength * available_negative
    offset = -offset
```

Итоговая point = base + normal * offset.

Domain прямоугольный и выпуклый; если каждая vertex centerline находится внутри/on boundary, все polyline segments также находятся внутри/on boundary.

## Degenerate corridor

Если Euclidean distance между start и end `<= 1e-12 km`, geometry создаётся без hidden reroll, но layout validation отклоняет attempt engine invariant `layout-corridor-nondegenerate`.

При degenerate endpoints internal control points не вычисляются через normal; centerline может содержать совпадающие vertices только как rejected candidate representation.

## Generic parameter sampling

Core runtime sampler v0.1 поддерживает:

- fixed → value без RNG draw;
- float range + uniform → `uniform(min,max)`;
- integer range + integer_uniform → inclusive `integer_uniform(min,max)`;
- choice + categorical → `choice(values)`;
- float range + triangular → inverse-CDF formula ниже.

Triangular sampler:

```text
u = uniform01()
span = max - min
c = (mode - min) / span

if u < c:
    x = min + sqrt(u * span * (mode - min))
else:
    x = max - sqrt((1-u) * span * (max - mode))
```

Если `min == max`, возвращается это значение без RNG draw.

Изменение triangular mapping требует нового `rng_version`, потому что sampler mapping является частью semantic RNG protocol.

## Constraints

Corridor generator не steering-ится hard constraints. Pipeline:

```text
generate geometry
-> evaluate supported hard constraints
-> PASS or reject whole attempt
```

Layout evaluator v0.1 для corridor slice должен уметь как минимум:

- resolve corridor `start`, `end`, `center`, `whole`;
- point↔point distance;
- point↔corridor minimum distance;
- corridor↔point minimum distance;
- corridor vertices/domain engine invariants.

`center` corridor определяется как point на 50% total polyline arc length, не как middle vertex.

Unsupported evaluator/geometry combination — capability error, не failed hard constraint.

## Non-goals

Не входят в этот slice:

- band;
- area;
- placement reservation boolean geometry;
- constraint-aware proposal generation;
- spline serialization;
- terrain/hydrology/surface algorithms.
