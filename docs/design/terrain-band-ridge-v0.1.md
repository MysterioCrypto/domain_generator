---
id: DESIGN-TERRAIN-BAND-RIDGE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Terrain Band / Ridge v0.1

Этот документ фиксирует второй additive operator terrain Core 0.1: `BandGeometry + ridge`.

## Область действия

Поддерживается terrain feature с:

- concrete `BandGeometry`;
- effect stage `terrain`;
- operator `ridge`;
- effect parameters ровно:
  - `height_m`
  - `profile_power`
  - `roughness`
  - `roughness_scale_km`

Operator создаёт отдельный float64 structural contribution и суммируется с другими additive terrain contributions в порядке отсортированных id features.

## Ограничения parameters

После sampling для конкретного attempt:

```text
height_m > 0
profile_power > 0
0 <= roughness <= 1
roughness_scale_km > 0
```

Все значения обязаны быть конечными float.

RNG parameters использует существующий protocol parameters terrain:

```text
stage = terrain
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

При `roughness = 0` coherent noise не влияет на contribution; скрытой подмены scale нет.

## Ближайшая точка на centerline

Для каждой cell domain берётся canonical world-space center cell `P`.

Centerline band интерпретируется как упорядоченная polyline. Для каждого segment ненулевой длины вычисляется closest point с clamped scalar projection `s in [0,1]`.

Выбирается segment/point с минимальным squared Euclidean distance. При exact tie выбирается **самый ранний segment по порядку centerline**.

Zero-length internal segments пропускаются. Layout-level invariant nondegenerate гарантирует положительную общую длину дуги у валидного band.

Для выбранной point `Q` определяется расстояние вдоль полной длины дуги polyline:

```text
arc_q = prefix_length_before_segment + s * segment_length
t = arc_q / total_centerline_length
```

Следовательно `t in [0,1]` — normalized total arc length, а не fraction индекса segment.

## Интерполяция width

Canonical `BandGeometry.width_profile` уже хранит полную width и samples по normalized `t`.

Для найденного `t` локальная полная width `W(t)` получается линейной интерполяцией между соседними width samples.

```text
half_width = W(t) / 2
```

Width profile не модифицируется стадией terrain.

## Расстояние поперёк band

```text
d = distance(P,Q)
u = d / half_width
```

`u=0` на centerline, `u=1` на nominal edge band.

## Базовый профиль ridge

Без roughness:

```text
base(u) = (1-u)^profile_power,  0 <= u <= 1
base(u) = 0,                    u > 1
```

Contribution:

```text
height_m * base(u)
```

Peak centerline всегда равен `height_m` до additive combination с другими features.

## Coherent roughness

Roughness использует универсальный `world-space coherent value noise v1`, документированный отдельно в `docs/design/world-space-value-noise-v1.md`.

Ridge задаёт namespace caller-а:

```text
stage = terrain
scope = ("feature", feature_id, "ridge-noise")
purpose = "value"
```

Noise primitive добавляет к scope `("node", decimal(i), decimal(j))` для каждого node lattice.

Для center cell:

```text
n(P) in [-1,1]
denominator = 1 + roughness * 0.35 * n(P)
u_rough = u / denominator
```

Так как `roughness <= 1`, denominator >= 0.65 и всегда положителен.

Финальный contribution:

```text
if u_rough > 1:
    contribution = 0
else:
    contribution = height_m * (1-u_rough)^profile_power
```

Roughness деформирует поперечный footprint/slopes, но не добавляет независимую высоту далеко от band и не меняет peak centerline (`u=0`).

## Семантика domain

Width band может выходить за domain, как уже принято contract layout. Terrain вычисляет contribution только для существующих cells domain; отдельный polygon footprint и clipping geometry не materialize-ятся.

## Аддитивная интеграция

Structural phase terrain:

```text
BaseField(0m)
+ area/raise contribution
+ band/ridge contribution
+ other future additive contributions
= float64 StructuralElevation
```

Features применяются в детерминированном порядке `sorted(feature.id)`.

После additive phase текущего slice выполняется один cast в canonical `float32 TerrainState.elevation_m`.

## Поведение при неподдерживаемых конструкциях

Явный `TerrainCapabilityError`, если:

- operator `ridge` используется не с `BandGeometry`;
- набор required parameters отличается;
- type/result parameter не является конечным float;
- sampled values нарушают ranges;
- centerline band не имеет положительной полной длины;
- интерполяция width обнаруживает invalid/non-positive width как defensive invariant failure.

Ни один terrain feature не игнорируется молча.

## Что не входит

- longitudinal height variation;
- asymmetric left/right slopes;
- multiple crests;
- erosion ridge;
- domain warping;
- octave/fractal noise;
- materialization polygon footprint;
- shaping operators (`flatten`, `blend`);
- hydrology.
