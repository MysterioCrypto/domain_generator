---
id: DESIGN-CORRIDOR-LAYOUT-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Corridor layout v0.1

Этот документ фиксирует первый детерминированный алгоритм corridor layout Core 0.1.

## Область действия

Поддерживается `layout.mode = geometry`, `shape = corridor`.

Канонический результат — `CorridorGeometry` с упорядоченной polyline `centerline`. Сериализованная geometry не хранит spline/Bezier representation.

## Обязательные параметры layout

Recipe corridor v0.1 использует ровно два параметра layout:

- `control_point_count`: integer, `>= 0`;
- `curvature`: float в `[0, 1]`.

Они остаются обычными recipes `ResolvedParameter` и sample-ятся runtime sampler-ом конкретного attempt.

## RNG namespaces

Streams endpoints изолированы от stream control points:

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

Sampling параметров layout использует отдельный namespace на parameter:

```text
stage = layout
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

Изменение `control_point_count` не должно менять sampled start/end.

## Конечные точки

Start и end выбираются независимо внутри прямоугольного domain:

```text
x = width_km  * uniform01()
y = height_km * uniform01()
```

Скрытых retries или steering с учётом constraints нет.

## Внутренние контрольные точки

Для `N = control_point_count` базовый параметр положения внутренних points:

```text
t_i = i / (N + 1), i = 1..N
```

Базовая point — линейная интерполяция между start/end.

Для ненулевой длины corridor вычисляется unit normal к start→end. Control point смещается вдоль normal.

Envelope:

```text
envelope(t) = 4 * t * (1 - t)
```

Он равен 0 на endpoints и достигает 1 в середине.

Для каждой внутренней point выполняется один draw:

```text
r = uniform(-1, +1)
```

Доступное расстояние до boundary domain вычисляется отдельно вдоль positive/negative normal. Signed offset:

```text
strength = curvature * envelope(t)

if r >= 0:
    offset = r * strength * available_positive
else:
    offset = (-r) * strength * available_negative
    offset = -offset
```

Итоговая point = base + normal * offset.

Domain прямоугольный и выпуклый; если каждая vertex centerline находится внутри или на boundary, все segments polyline также находятся внутри или на boundary.

## Вырожденный corridor

Если Euclidean distance между start и end `<= 1e-12 km`, geometry создаётся без скрытого reroll, но validation layout отклоняет attempt по engine invariant `layout-corridor-nondegenerate`.

При degenerate endpoints внутренние control points не вычисляются через normal; centerline может содержать совпадающие vertices только как representation отклонённого candidate.

## Универсальный sampling parameters

Runtime sampler Core v0.1 поддерживает:

- fixed → value без RNG draw;
- float range + uniform → `uniform(min,max)`;
- integer range + integer_uniform → включительный `integer_uniform(min,max)`;
- choice + categorical → `choice(values)`;
- float range + triangular → формулу inverse-CDF ниже.

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

Изменение triangular mapping требует нового `rng_version`, потому что mapping sampler-а является частью семантического RNG protocol.

## Constraints

Генератор corridor не выполняет steering по hard constraints. Pipeline:

```text
generate geometry
-> evaluate supported hard constraints
-> PASS or reject whole attempt
```

Evaluator layout v0.1 для corridor slice должен уметь как минимум:

- разрешать corridor `start`, `end`, `center`, `whole`;
- distance point↔point;
- minimum distance point↔corridor;
- minimum distance corridor↔point;
- engine invariants vertices corridor/domain.

`center` corridor определяется как point на 50% общей длины дуги polyline, а не как middle vertex.

Неподдерживаемое сочетание evaluator/geometry — capability error, а не failed hard constraint.

## Что не входит в этот slice

- band;
- area;
- boolean geometry placement reservation;
- proposal generation с учётом constraints;
- сериализация spline;
- алгоритмы terrain/hydrology/surface.
