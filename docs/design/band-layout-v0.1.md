---
id: DESIGN-BAND-LAYOUT-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Band layout v0.1

Этот документ фиксирует детерминированный алгоритм band layout Core 0.1.

## Область действия

Поддерживается `layout.mode = geometry`, `shape = band`.

Канонический результат — `BandGeometry`:

- упорядоченная polyline `centerline`;
- упорядоченный `width_profile`;
- `width_km` означает полную ширину band;
- между width samples применяется линейная интерполяция.

Polygon footprint/boundary в этом slice не materialize-ится.

## Обязательные параметры layout

Recipe band v0.1 использует ровно четыре параметра layout:

- `control_point_count`: integer, `>= 0`;
- `curvature`: float в `[0, 1]`;
- `width_km`: float resolved parameter, каждое sampled значение должно быть `> 0`;
- `width_sample_count`: integer, `>= 2`.

`control_point_count` и `curvature` определяют centerline. `width_km` — recipe, который может sample-иться несколько раз вдоль одного band. `width_sample_count` задаёт число materialized width samples.

## Centerline

Centerline band использует ту же геометрическую конструкцию, что corridor v0.1:

- независимые streams start/end;
- внутренние control points на `t=i/(N+1)`;
- смещение вдоль normal;
- envelope `4*t*(1-t)`;
- displacement ограничен расстоянием до boundary прямоугольного domain;
- скрытые retries и steering с учётом constraints отсутствуют.

Но RNG namespace band отделён от corridor:

```text
stage = layout
scope = ("feature", feature_id, "geometry", "band")
purpose = "start" | "end" | "control-points"
```

Поэтому corridor и band с одинаковым feature id не обязаны иметь одинаковую realization centerline.

Вырожденные start/end обрабатываются так же: без reroll; validation layout отклоняет attempt как нарушение engine invariant.

## Позиции width samples

Для `K = width_sample_count`, `K >= 2`:

```text
t_i = i / (K - 1), i = 0..K-1
```

Следовательно, `t=0` и `t=1` всегда присутствуют, samples строго возрастают и полностью соответствуют существующему contract `BandGeometry`.

## Изоляция RNG для width

Ширины endpoints изолированы от числа внутренних samples:

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

Все внутренние width samples используют отдельный stream:

```text
stage = layout
scope = ("feature", feature_id, "geometry", "band")
purpose = "width-internal"
```

Изменение `width_sample_count` не должно менять sampled width при `t=0` и `t=1`.

## Семантика recipe width

`width_km` использует универсальный sampler resolved parameters Core 0.1.

Если recipe fixed, каждый width sample равен одному fixed значению и RNG draw не нужен.

Если recipe stochastic (`uniform`, `triangular`, `integer_uniform`, где это структурно допустимо, либо другой уже поддерживаемый resolved recipe), materialization width sample выполняется независимо по указанным width streams.

Для band v0.1 итоговое sampled значение `width_km` обязано быть числовым и `> 0`. Неподдерживаемый, нечисловой или неположительный recipe width — capability error либо ошибка compiler/preset validation, а не скрытое исправление.

## Семантика границы domain

Только centerline обязана находиться внутри или на boundary прямоугольного domain.

Influence/footprint band может выходить за domain. Будущий rasterizer обрезает effect по domain. Поэтому width profile не уменьшается автоматически возле границы.

## Части selector

В этом slice band может разрешать:

- `start` — первая point centerline;
- `end` — последняя point centerline;
- `center` — point на 50% общей длины дуги centerline.

`whole` и `boundary` означают настоящий footprint/boundary band и не подменяются centerline. Пока footprint не materialize-ится, combinations evaluator-а, требующие `whole` или `boundary`, возвращают `LayoutCapabilityError`.

`endpoints` также пока не materialize-ится как составное значение geometry в evaluator layer.

## Инварианты validation

Validation layout проверяет как минимум:

- полный набор поддерживаемых geometry features;
- vertices centerline внутри или на boundary domain;
- невырожденную centerline band;
- `width_profile` содержит `t=0` и `t=1`;
- `t` строго возрастают;
- все `width_km > 0`.

Validation не мутирует и не исправляет geometry.

## Что не входит в этот slice

- materialization polygon footprint;
- evaluators band `whole`/`boundary`;
- rasterization band;
- генерация area;
- placement reservations;
- proposal generation с учётом constraints;
- алгоритмы terrain/hydrology/surface.
