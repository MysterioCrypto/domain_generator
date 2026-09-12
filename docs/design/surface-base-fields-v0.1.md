---
id: DESIGN-SURFACE-BASE-FIELDS-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Surface Base Fields v0.1

Этот checkpoint создаёт базовые canonical runtime fields `moisture` и `vegetation_density` из immutable terrain + hydrology. Explicit surface-feature biases, climate/biome simulation и binary forest masks в этот slice не входят.

## Scope

Input:

```text
TerrainState.elevation_m
HydrologyState.water_depth_m
GenerationPlan.surface
attempt_index + RNG v1 factory (только environmental noise)
```

Output:

```text
SurfaceState
├── moisture             float32 [rows, columns]
└── vegetation_density   float32 [rows, columns]
```

Оба поля finite и в `[0,1]`.

Surface не мутирует terrain или hydrology.

## Semantic surface recipe

`DomainSpec.surface` и `GenerationPlan.surface` обязательны и содержат:

```yaml
surface:
  moisture_base: <float [0,1]>
  water_moisture_boost: <float [0,1]>
  water_moisture_decay_km: <float > 0>
  moisture_noise_amplitude: <float [0,1]>
  moisture_noise_scale_km: <float > 0>
  vegetation_slope_zero_deg: <float (0,90]>
```

Hidden defaults запрещены. Вся секция участвует в semantic plan fingerprint.

## Water mask

Canonical water cells определяются только как:

```text
HydrologyState.water_depth_m > 0
```

Никакие routing/fill intermediates напрямую moisture не определяют.

## Distance to water

Для каждой cell вычисляется Euclidean distance между canonical cell centers и ближайшим water-cell center, в километрах.

Если cell сама water-cell, distance `0`.

Если water cells отсутствуют во всём domain, distance logically infinite и water contribution определяется как `0` без попытки сериализовать infinity в runtime state.

Implementation v0.1 использует deterministic exact squared Euclidean distance transform на квадратном raster grid:

1. one-dimensional exact squared-distance transform по columns;
2. тот же transform по rows;
3. `sqrt(squared_cells) * cell_size_km`.

Алгоритм не меняет semantics и не использует RNG.

## Environmental moisture noise

Используется существующий world-space coherent value noise v1.

RNG namespace:

```text
stage   = surface
scope   = ("field", "moisture", "environmental-noise")
purpose = "value"
```

Noise оценивается в world-space центре каждой cell с `scale_km = moisture_noise_scale_km` и возвращает `n ∈ [-1,1]`.

```text
noise_term = moisture_noise_amplitude * n
```

Обход raster не является RNG stream и не влияет на результат.

## Moisture

Для dry cell:

```text
water_term =
  water_moisture_boost
  * exp(-distance_to_water_km / water_moisture_decay_km)
```

Если water cells в domain отсутствуют:

```text
water_term = 0
```

Далее:

```text
raw_moisture = moisture_base + water_term + noise_term
moisture = clamp(raw_moisture, 0, 1)
```

Для canonical water cell независимо от noise:

```text
moisture = 1
```

Computation float64, затем один final cast в float32.

Absolute elevation не вводит отдельный dryness penalty в v0.1: zero elevation является datum, а не sea level/climate datum.

## Slope

Slope — derived intermediate, не canonical SurfaceState field.

Для каждой cell и каждого существующего из 8 соседей:

```text
rise_m = abs(z_neighbor_m - z_cell_m)
run_m  = cell_size_km * 1000                 # orthogonal
run_m  = cell_size_km * 1000 * sqrt(2)       # diagonal
local_gradient = rise_m / run_m
```

Используется maximum local gradient среди существующих соседей:

```text
slope_deg = atan(max_local_gradient) * 180 / pi
```

Single-cell domain имеет slope `0`.

## Vegetation density

`vegetation_density` в Core 0.1 означает terrestrial vegetation density. Aquatic vegetation сюда не входит.

Для dry cell:

```text
slope_factor = clamp(
  1 - slope_deg / vegetation_slope_zero_deg,
  0,
  1
)

vegetation_density = moisture * slope_factor
```

Для canonical water cell:

```text
vegetation_density = 0
```

Computation float64, затем один final cast в float32.

## Runtime state

```text
SurfaceState
├── moisture             float32
└── vegetation_density   float32
```

Distance-to-water, slope и noise остаются derived intermediates и не сериализуются в SurfaceState v0.1.

## Validation

Surface validation v0.1 проверяет:

- upstream `TerrainState` существует;
- upstream `HydrologyState` существует;
- terrain elevation и hydrology water depth совпадают с grid shape и finite;
- `SurfaceState` существует;
- оба output arrays совпадают с grid shape;
- оба dtype exactly float32;
- оба finite;
- оба лежат в `[0,1]`;
- water cells имеют exact float32 moisture `1`;
- water cells имеют exact float32 vegetation density `0`;
- deterministic recomputation из upstream state + plan + attempt RNG совпадает с runtime outputs.

Несогласованность — engine invariant failure. Hidden repair/retry отсутствует.

## Causality

```text
Terrain + Hydrology
       ↓ read-only
Surface Base Fields
       ↓
SurfaceState
```

Surface не изменяет terrain/hydrology и не влияет задним числом на river/lake classification.

## Non-goals

Не входят:

- surface feature biases;
- forest/swamp binary masks;
- soil types;
- temperature;
- precipitation;
- latitude;
- biome classification;
- seasons;
- climate simulation;
- absolute-elevation climate penalty;
- aquatic vegetation;
- DomainData assembly/export.
