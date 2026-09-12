---
id: DESIGN-WORLD-SPACE-VALUE-NOISE-V1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# World-space coherent value noise v1

Этот документ фиксирует минимальный reusable deterministic coherent-noise primitive для terrain/surface Core 0.1.

## Purpose

Noise существует в world coordinates и не зависит от raster traversal order, количества cells или наличия соседних consumers.

Первый consumer — terrain `ridge` operator. Primitive сам не знает о terrain feature type, operator name или конкретном caller.

## Inputs

```text
attempt_index
stage: RngStage
scope: non-empty semantic RNG scope prefix
purpose: non-empty semantic purpose
scale_km > 0
world point (x_km, y_km)
root RNG factory
```

Caller отвечает за stable semantic namespace. Noise primitive лишь добавляет lattice-node coordinates.

Для terrain ridge caller использует:

```text
stage = terrain
scope = ("feature", feature_id, "ridge-noise")
purpose = "value"
```

## Lattice

Для world point:

```text
g_x = x_km / scale_km
g_y = y_km / scale_km

i0 = floor(g_x)
j0 = floor(g_y)
i1 = i0 + 1
j1 = j0 + 1

f_x = g_x - i0
f_y = g_y - j0
```

Noise nodes находятся в `(integer_i * scale_km, integer_j * scale_km)`.

## Random-access node addressing

Каждый lattice node получает собственный RNG-v1 stream. К caller scope дописывается:

```text
("node", decimal(i), decimal(j))
```

Итоговый ridge example:

```text
stage = terrain
scope = (
  "feature", feature_id,
  "ridge-noise",
  "node", decimal(i), decimal(j)
)
purpose = "value"
```

`decimal(i)`/`decimal(j)` — canonical base-10 integer representation без leading zeroes, обычная decimal integer string.

Node value:

```text
u = first uniform01() from that stream
node_value = 2*u - 1
```

Следовательно `node_value in [-1, 1)`.

Каждый node адресуется независимо. Вычисление одного node не потребляет RNG другого node. Изменение grid size/traversal не изменяет значения уже существующих world-space nodes.

## Smooth interpolation

По каждой оси применяется cubic smoothstep:

```text
smooth(f) = f*f*(3 - 2*f)
```

Пусть:

```text
sx = smooth(f_x)
sy = smooth(f_y)

v00 = node(i0,j0)
v10 = node(i1,j0)
v01 = node(i0,j1)
v11 = node(i1,j1)
```

Сначала linear interpolation по x:

```text
a = lerp(v00, v10, sx)
b = lerp(v01, v11, sx)
```

Затем по y:

```text
noise = lerp(a, b, sy)
```

Итог остаётся в `[-1,1]` и непрерывен по value и first derivative на lattice boundaries.

## Semantics

- coordinates измеряются в km;
- `scale_km` — physical wavelength/control scale, а не cell count;
- stage/scope/purpose являются частью semantic caller namespace;
- noise не sample-ится из mutable raster-order stream;
- noise не округляет world coordinates;
- implementation использует Python float / IEEE-754 double semantics;
- changing node-addressing/interpolation protocol is a generator semantic change.

## Non-goals

Не входят:

- octave/fractal noise;
- Perlin gradients;
- ridged multifractal transforms;
- erosion;
- domain warping;
- hidden scale defaults.
