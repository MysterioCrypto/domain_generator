---
id: DESIGN-DEPENDENT-PLACEMENT-SITE-METRICS-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Метрики места для dependent placement v0.1

Этот checkpoint фиксирует и реализует только численную оценку world-space candidate point относительно upstream state terrain/hydrology/surface.

Он не генерирует candidate lattice, не фильтрует requirements, не считает scores preferences и не выбирает финальную point.

## Входные данные

```text
GenerationPlan.grid/domain
TerrainState.elevation_m
HydrologyState.water_depth_m
SurfaceState.moisture
SurfaceState.vegetation_density
candidate PointGeometry
footprint_radius_km
```

Derived fields уровня attempt:

```text
slope_deg
exact distance_to_water_km
```

Они вычисляются один раз в `SiteMetricContext` и переиспользуются всеми candidate sites данного attempt.

## Координаты candidate

Candidate остаётся world-space point и не обязан совпадать с center raster cell.

Допустимые coordinates включают boundary domain:

```text
0 <= x_km <= domain.width_km
0 <= y_km <= domain.height_km
```

## Правило containing cell

Для fallback и `relative_elevation` candidate сопоставляется ровно одной raster cell.

На внутренних boundaries:

```text
vertical boundary   -> eastern cell
horizontal boundary -> northern cell
```

На внешних north/east boundaries выбирается последняя внутренняя cell.

Это соответствует half-open partition мирового пространства с явным clamp внешней границы.

## Cells footprint

Для `footprint_radius_km > 0` выбираются все raster cells, centers которых удовлетворяют:

```text
distance(cell_center, candidate) <= footprint_radius_km
```

Cells за domain отсутствуют; footprint автоматически обрезается boundary domain.

Канонический порядок cells:

```text
(row, column)
```

Если круг не содержит ни одного raster center, используется containing cell candidate.

Для `footprint_radius_km == 0` используется только containing cell.

Footprint не использует sub-cell integration и не меняет coordinate candidate.

## Реестр metrics

Core 0.1 поддерживает ровно следующие id metrics:

```text
slope_mean
water_fraction
elevation_mean
local_relief
relative_elevation
moisture_mean
vegetation_density_mean
distance_to_water
```

### slope_mean

Арифметическое среднее derived `slope_deg` по cells footprint.

Единица: degrees.

### water_fraction

```text
count(water_depth_m > 0 in footprint) / footprint_cell_count
```

Диапазон `[0,1]`.

### elevation_mean

Арифметическое среднее `TerrainState.elevation_m` по cells footprint.

Единица: meters.

### local_relief

```text
max(elevation_m in footprint) - min(elevation_m in footprint)
```

Единица: meters.

### relative_elevation

```text
elevation_m[containing_cell(candidate)] - elevation_mean
```

Единица: meters.

Положительное значение означает, что containing cell candidate выше средней elevation footprint.

### moisture_mean

Арифметическое среднее `SurfaceState.moisture` по cells footprint.

Диапазон `[0,1]`.

### vegetation_density_mean

Арифметическое среднее `SurfaceState.vegetation_density` по cells footprint.

Диапазон `[0,1]`.

### distance_to_water

Минимальное точное `distance_to_water_km` среди cells footprint.

Единица: kilometers.

Поскольку upstream exact distance field измеряет расстояние от center каждой cell до center ближайшей canonical water cell, эта metric обозначает минимальное доступное расстояние до воды в support footprint candidate.

Если canonical water отсутствует во всём domain:

```text
distance_to_water = +inf
```

Это runtime-derived sentinel и не сериализуется в `DomainData`.

## Численные правила

- aggregation metrics выполняется в float64;
- upstream canonical fields не мутируются;
- RNG не используется;
- порядок cells footprint не влияет на арифметический результат;
- некорректные shapes, non-finite upstream arrays, candidate вне domain и отрицательный radius являются явными capability errors;
- upstream arrays moisture и vegetation должны оставаться в `[0,1]`;
- water depth должна быть finite и non-negative.

## Runtime API

```text
SiteMetricContext.from_states(plan, terrain, hydrology, surface)
footprint_cells(context.adapter, candidate, footprint_radius_km)
evaluate_site_metrics(context, candidate, footprint_radius_km)
```

`SiteMetricContext` предварительно вычисляет derived arrays уровня attempt ровно один раз.

## Что не входит

- генерация candidate lattice;
- containment reservation;
- containment footprint внутри reservation;
- evaluation `SiteRequirement`;
- normalization/scoring `SitePreference`;
- фильтрация near-best;
- финальный weighted selection;
- `PlacementState`;
- sub-cell raster integration;
- adaptive footprint sampling;
- metrics конкретного сеттинга.
