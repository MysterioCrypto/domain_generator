---
id: DESIGN-TERRAIN-BAND-RIDGE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Terrain Band / Ridge v0.1

Этот документ фиксирует второй additive terrain operator Core 0.1: `BandGeometry + ridge`.

## Scope

Поддерживается terrain feature с:

- concrete `BandGeometry`;
- effect stage `terrain`;
- operator `ridge`;
- effect parameters ровно:
  - `height_m`
  - `profile_power`
  - `roughness`
  - `roughness_scale_km`

Operator создаёт отдельный float64 structural contribution и суммируется с другими additive terrain contributions в sorted feature-id order.

## Parameter constraints

После attempt-local sampling:

```text
height_m > 0
profile_power > 0
0 <= roughness <= 1
roughness_scale_km > 0
```

Все значения обязаны быть finite float.

Parameter RNG использует существующий terrain parameter protocol:

```text
stage = terrain
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

При `roughness = 0` coherent noise не влияет на contribution; hidden replacement scale отсутствует.

## Nearest point on centerline

Для каждого domain cell берётся canonical world-space cell center `P`.

Band centerline интерпретируется как ordered polyline. Для каждого non-zero-length segment вычисляется closest point с clamped scalar projection `s in [0,1]`.

Выбирается segment/point с минимальной squared Euclidean distance. При exact tie выбирается **самый ранний segment по centerline order**.

Zero-length internal segments пропускаются. Layout-level nondegenerate invariant гарантирует положительную total arc length у валидного band.

Для выбранной точки `Q` определяется distance along total polyline arc length:

```text
arc_q = prefix_length_before_segment + s * segment_length
t = arc_q / total_centerline_length
```

Следовательно `t in [0,1]` — normalized total arc length, а не segment index fraction.

## Width interpolation

Canonical `BandGeometry.width_profile` уже хранит full width и samples по normalized `t`.

Для найденного `t` local full width `W(t)` получается linear interpolation между соседними width samples.

```text
half_width = W(t) / 2
```

Width profile не модифицируется terrain stage.

## Cross-band distance

```text
d = distance(P,Q)
u = d / half_width
```

`u=0` на centerline, `u=1` на nominal band edge.

## Base ridge profile

Без roughness:

```text
base(u) = (1-u)^profile_power,  0 <= u <= 1
base(u) = 0,                    u > 1
```

Contribution:

```text
height_m * base(u)
```

Centerline peak всегда равен `height_m` до additive combination с другими features.

## Coherent roughness

Roughness использует `world-space coherent value noise v1`, документированный отдельно в `docs/design/world-space-value-noise-v1.md`.

Для cell center:

```text
n(P) in [-1,1]
denominator = 1 + roughness * 0.35 * n(P)
u_rough = u / denominator
```

Так как `roughness <= 1`, denominator >= 0.65 и всегда положителен.

Final contribution:

```text
if u_rough > 1:
    contribution = 0
else:
    contribution = height_m * (1-u_rough)^profile_power
```

Roughness деформирует поперечную footprint/slopes, но не добавляет независимую высоту далеко от band и не изменяет centerline peak (`u=0`).

## Domain semantics

Band width может выходить за domain, как уже принято layout contract. Terrain вычисляет contribution только для existing domain cells; отдельный polygon footprint и clipping geometry не materialize-ятся.

## Additive integration

Terrain structural phase:

```text
BaseField(0m)
+ area/raise contribution
+ band/ridge contribution
+ other future additive contributions
= float64 StructuralElevation
```

Features применяются в deterministic `sorted(feature.id)` order.

После additive phase текущего slice выполняется один cast в canonical `float32 TerrainState.elevation_m`.

## Capability behavior

Explicit `TerrainCapabilityError`, если:

- operator `ridge` используется не с `BandGeometry`;
- required parameter set отличается;
- parameter type/result не finite float;
- sampled values нарушают ranges;
- band centerline не имеет положительной total length;
- width interpolation обнаруживает invalid/non-positive width (defensive invariant failure).

Ни один terrain feature silently ignored не бывает.

## Non-goals

Не входят:

- longitudinal height variation;
- asymmetric left/right slopes;
- multiple crests;
- ridge erosion;
- domain warping;
- octave/fractal noise;
- polygon footprint materialization;
- shaping operators (`flatten`, `blend`);
- hydrology.
