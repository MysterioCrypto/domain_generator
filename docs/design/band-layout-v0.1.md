---
id: DESIGN-BAND-LAYOUT-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Band layout v0.1

Этот документ фиксирует deterministic band layout algorithm Core 0.1.

## Scope

Поддерживается `layout.mode = geometry`, `shape = band`.

Canonical result — `BandGeometry`:

- ordered polyline `centerline`;
- ordered `width_profile`;
- `width_km` означает полную ширину band;
- между width samples применяется линейная интерполяция.

Polygon footprint/boundary в этом slice не материализуется.

## Required layout parameters

Band recipe v0.1 использует ровно четыре layout parameters:

- `control_point_count`: integer, `>= 0`;
- `curvature`: float в `[0, 1]`;
- `width_km`: float resolved parameter, каждое sampled значение должно быть `> 0`;
- `width_sample_count`: integer, `>= 2`.

`control_point_count` и `curvature` определяют centerline. `width_km` — recipe, который может sample-иться несколько раз вдоль одного band. `width_sample_count` задаёт число materialized width samples.

## Centerline

Band centerline использует ту же geometric construction, что corridor v0.1:

- independent start/end streams;
- internal control points на `t=i/(N+1)`;
- normal displacement;
- envelope `4*t*(1-t)`;
- displacement ограничен расстоянием до rectangular domain boundary;
- hidden retries и constraint-aware steering отсутствуют.

Но RNG namespace band отдельный от corridor:

```text
stage = layout
scope = ("feature", feature_id, "geometry", "band")
purpose = "start" | "end" | "control-points"
```

Поэтому corridor и band с одинаковым feature id не обязаны иметь одинаковую centerline realization.

Degenerate start/end обрабатываются так же: без reroll; layout validation отклоняет attempt как engine invariant failure.

## Width sample positions

Для `K = width_sample_count`, `K >= 2`:

```text
t_i = i / (K - 1), i = 0..K-1
```

Следовательно, `t=0` и `t=1` всегда присутствуют, samples строго возрастают и полностью соответствуют существующему `BandGeometry` contract.

## Width RNG isolation

Endpoint widths изолированы от числа внутренних samples:

```text
stage = layout
scope = ("feature", feature_id, "geometry", "band")
purpose = "width-start"
```

```text
stage = layout
scope = ("feature", feature_id, "geometry", "band")
purpose = "width-end"
```

Все internal width samples используют отдельный stream:

```text
stage = layout
scope = ("feature", feature_id, "geometry", "band")
purpose = "width-internal"
```

Изменение `width_sample_count` не должно менять sampled width при `t=0` и `t=1`.

## Width recipe semantics

`width_km` использует generic resolved-parameter sampler Core 0.1.

Если recipe fixed, каждый width sample равен одному fixed значению и RNG draw не нужен.

Если recipe stochastic (`uniform`, `triangular`, `integer_uniform` где structurally допустимо, либо другое уже поддерживаемое resolved recipe), width sample materialization выполняется независимо по указанным width streams.

Для band v0.1 итоговое sampled значение `width_km` обязано быть numeric и `> 0`. Неподдерживаемая/нечисловая/неположительная width recipe — capability error либо compiler/preset validation error, а не silent repair.

## Domain boundary semantics

Только centerline обязана находиться внутри/on rectangular domain.

Band influence/footprint может выходить за domain. Будущий rasterizer клиппит effect к domain. Width profile поэтому не уменьшается автоматически возле границы.

## Selector parts

В этом slice band может разрешать:

- `start` — первый point centerline;
- `end` — последний point centerline;
- `center` — point на 50% total centerline arc length.

`whole` и `boundary` означают настоящий band footprint/boundary и не подменяются centerline. Пока footprint не материализован, evaluator combinations, требующие `whole` или `boundary`, возвращают `LayoutCapabilityError`.

`endpoints` также пока не materialize-ится как составной geometry value в evaluator layer.

## Validation invariants

Layout validation проверяет как минимум:

- полный набор supported geometry features;
- centerline vertices внутри/on domain;
- nondegenerate band centerline;
- `width_profile` содержит `t=0` и `t=1`;
- `t` строго возрастают;
- все `width_km > 0`.

Validation не mutate-ит и не repair-ит geometry.

## Non-goals

Не входят в этот slice:

- polygon footprint materialization;
- `whole`/`boundary` band evaluators;
- band rasterization;
- area generation;
- placement reservations;
- constraint-aware proposal generation;
- terrain/hydrology/surface algorithms.
