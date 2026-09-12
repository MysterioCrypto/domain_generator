---
id: DESIGN-SURFACE-BASE-FIELDS-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Базовые поля Surface v0.1

Этот checkpoint создаёт базовые canonical runtime fields `moisture` и `vegetation_density` из неизменяемых terrain + hydrology. Явные biases surface features, симуляция climate/biome и binary forest masks в этот slice не входят.

## Область действия

Вход:

```text
TerrainState.elevation_m
HydrologyState.water_depth_m
GenerationPlan.surface
attempt_index + RNG v1 factory (только environmental noise)
```

Выход:

```text
SurfaceState
├── moisture             float32 [rows, columns]
└── vegetation_density   float32 [rows, columns]
```

Оба поля конечны и лежат в `[0,1]`.

Surface не мутирует terrain или hydrology.

## Семантический recipe surface

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

Скрытые defaults запрещены. Вся секция участвует в semantic plan fingerprint.

## Water mask

Canonical water cells определяются только как:

```text
HydrologyState.water_depth_m > 0
```

Никакие промежуточные routing/fill напрямую moisture не определяют.

## Расстояние до воды

Для каждой cell вычисляется Euclidean distance между canonical centers cells и center ближайшей water cell, в километрах.

Если cell сама является water cell, distance `0`.

Если water cells отсутствуют во всём domain, distance логически бесконечна и contribution воды определяется как `0` без попытки сериализовать infinity в runtime state.

Implementation v0.1 использует детерминированный exact squared Euclidean distance transform на квадратном raster grid:

1. одномерный exact squared-distance transform по columns;
2. тот же transform по rows;
3. `sqrt(squared_cells) * cell_size_km`.

Алгоритм не меняет семантику и не использует RNG.

## Environmental moisture noise

Используется существующий world-space coherent value noise v1.

RNG namespace:

```text
stage   = surface
scope   = ("field", "moisture", "environmental-noise")
purpose = "value"
```

Noise оценивается в world-space center каждой cell с `scale_km = moisture_noise_scale_km` и возвращает `n ∈ [-1,1]`.

```text
noise_term = moisture_noise_amplitude * n
```

Порядок обхода raster не является RNG stream и не влияет на результат.

## Moisture

Для сухой cell:

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

Вычисления выполняются в float64, затем один финальный cast в float32.

Absolute elevation не вводит отдельный dryness penalty в v0.1: нулевая elevation является datum, а не sea level/climate datum.

## Slope

Slope — derived intermediate, а не canonical field `SurfaceState`.

Для каждой cell и каждого существующего из 8 neighbors:

```text
rise_m = abs(z_neighbor_m - z_cell_m)
run_m  = cell_size_km * 1000                 # orthogonal
run_m  = cell_size_km * 1000 * sqrt(2)       # diagonal
local_gradient = rise_m / run_m
```

Используется максимальный local gradient среди существующих neighbors:

```text
slope_deg = atan(max_local_gradient) * 180 / pi
```

Domain из одной cell имеет slope `0`.

## Плотность vegetation

`vegetation_density` в Core 0.1 означает плотность terrestrial vegetation. Aquatic vegetation сюда не входит.

Для сухой cell:

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

Вычисления выполняются в float64, затем один финальный cast в float32.

## Runtime state

```text
SurfaceState
├── moisture             float32
└── vegetation_density   float32
```

Distance-to-water, slope и noise остаются derived intermediates и не сериализуются в `SurfaceState` v0.1.

## Validation

Validation Surface v0.1 проверяет:

- upstream `TerrainState` существует;
- upstream `HydrologyState` существует;
- terrain elevation и hydrology water depth совпадают с shape grid и конечны;
- `SurfaceState` существует;
- оба output arrays совпадают с shape grid;
- оба dtype ровно float32;
- оба конечны;
- оба лежат в `[0,1]`;
- water cells имеют exact float32 moisture `1`;
- water cells имеют exact float32 vegetation density `0`;
- детерминированный recomputation из upstream state + plan + attempt RNG совпадает с runtime outputs.

Несогласованность — нарушение engine invariant. Скрытые repair/retry отсутствуют.

## Причинность

```text
Terrain + Hydrology
       ↓ read-only
Surface Base Fields
       ↓
SurfaceState
```

Surface не изменяет terrain/hydrology и не влияет задним числом на classification rivers/lakes.

## Что не входит

- biases surface features;
- binary masks forest/swamp;
- soil types;
- temperature;
- precipitation;
- latitude;
- biome classification;
- seasons;
- climate simulation;
- climate penalty по absolute elevation;
- aquatic vegetation;
- assembly/export `DomainData`.
