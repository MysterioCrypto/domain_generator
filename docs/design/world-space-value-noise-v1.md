---
id: DESIGN-WORLD-SPACE-VALUE-NOISE-V1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Coherent value noise в мировом пространстве v1

Этот документ фиксирует минимальный reusable deterministic primitive coherent noise для terrain/surface Core 0.1.

## Назначение

Noise существует в мировых координатах и не зависит от порядка обхода raster, количества cells или наличия соседних consumers.

Первый consumer — operator terrain `ridge`. Сам primitive не знает о типе terrain feature, имени operator-а или конкретном caller-е.

## Входные данные

```text
attempt_index
stage: RngStage
scope: non-empty semantic RNG scope prefix
purpose: non-empty semantic purpose
scale_km > 0
world point (x_km, y_km)
root RNG factory
```

Caller отвечает за стабильный semantic namespace. Primitive noise лишь добавляет coordinates nodes lattice.

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

Nodes noise находятся в `(integer_i * scale_km, integer_j * scale_km)`.

## Random-access addressing nodes

Каждый node lattice получает собственный RNG-v1 stream. К scope caller-а дописывается:

```text
("node", decimal(i), decimal(j))
```

Итоговый пример ridge:

```text
stage = terrain
scope = (
  "feature", feature_id,
  "ridge-noise",
  "node", decimal(i), decimal(j)
)
purpose = "value"
```

`decimal(i)`/`decimal(j)` — каноническое представление integer в base-10 без leading zeroes, обычная decimal integer string.

Значение node:

```text
u = first uniform01() from that stream
node_value = 2*u - 1
```

Следовательно `node_value in [-1, 1)`.

Каждый node адресуется независимо. Вычисление одного node не потребляет RNG другого node. Изменение размера grid или порядка traversal не меняет значения уже существующих world-space nodes.

## Плавная интерполяция

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

Сначала линейная интерполяция по x:

```text
a = lerp(v00, v10, sx)
b = lerp(v01, v11, sx)
```

Затем по y:

```text
noise = lerp(a, b, sy)
```

Результат остаётся в `[-1,1]` и непрерывен по value и first derivative на boundaries lattice.

## Семантика

- coordinates измеряются в km;
- `scale_km` — физический wavelength/control scale, а не cell count;
- stage/scope/purpose являются частью semantic namespace caller-а;
- noise не sample-ится из mutable stream, зависящего от порядка raster;
- noise не округляет world coordinates;
- implementation использует Python float / IEEE-754 double semantics;
- изменение protocol addressing/interpolation nodes является семантическим изменением generator.

## Что не входит

- octave/fractal noise;
- gradients Perlin;
- ridged multifractal transforms;
- erosion;
- domain warping;
- скрытые defaults scale.
