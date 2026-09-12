---
id: DESIGN-DEPENDENT-PLACEMENT-SITE-METRICS-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Dependent Placement Site Metrics v0.1

Этот checkpoint фиксирует и реализует только численную оценку world-space candidate point относительно upstream terrain/hydrology/surface state.

Он не генерирует candidate lattice, не фильтрует requirements, не считает preference scores и не выбирает final point.

## Inputs

```text
GenerationPlan.grid/domain
TerrainState.elevation_m
HydrologyState.water_depth_m
SurfaceState.moisture
SurfaceState.vegetation_density
candidate PointGeometry
footprint_radius_km
```

Derived attempt-global fields:

```text
slope_deg
exact distance_to_water_km
```

Они вычисляются один раз в `SiteMetricContext` и переиспользуются всеми candidate sites данного attempt.

## Candidate coordinates

Candidate остаётся world-space point и не обязан совпадать с raster cell center.

Допустимые coordinates включают boundary domain:

```text
0 <= x_km <= domain.width_km
0 <= y_km <= domain.height_km
```

## Containing-cell rule

Для fallback и `relative_elevation` candidate сопоставляется ровно одной raster cell.

На внутренних boundaries:

```text
vertical boundary   -> eastern cell
horizontal boundary -> northern cell
```

На внешних north/east boundaries выбирается последняя внутренняя cell.

Это соответствует half-open world partition с явным clamp внешней границы.

## Footprint cells

Для `footprint_radius_km > 0` выбираются все raster cells, чьи centers удовлетворяют:

```text
distance(cell_center, candidate) <= footprint_radius_km
```

Cells за domain отсутствуют; footprint автоматически clipping-ится domain boundary.

Canonical ordering cells:

```text
(row, column)
```

Если circle не содержит ни одного raster center, используется containing cell candidate.

Для `footprint_radius_km == 0` используется только containing cell.

Footprint не использует sub-cell integration и не меняет candidate coordinate.

## Metric registry

Core 0.1 поддерживает ровно следующие metric ids:

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

Arithmetic mean derived `slope_deg` по footprint cells.

Unit: degrees.

### water_fraction

```text
count(water_depth_m > 0 in footprint) / footprint_cell_count
```

Range `[0,1]`.

### elevation_mean

Arithmetic mean `TerrainState.elevation_m` по footprint cells.

Unit: meters.

### local_relief

```text
max(elevation_m in footprint) - min(elevation_m in footprint)
```

Unit: meters.

### relative_elevation

```text
elevation_m[containing_cell(candidate)] - elevation_mean
```

Unit: meters.

Positive value means candidate containing cell is above mean footprint elevation.

### moisture_mean

Arithmetic mean `SurfaceState.moisture` по footprint cells.

Range `[0,1]`.

### vegetation_density_mean

Arithmetic mean `SurfaceState.vegetation_density` по footprint cells.

Range `[0,1]`.

### distance_to_water

Minimum exact `distance_to_water_km` among footprint cells.

Unit: kilometers.

Because the upstream exact distance field measures each cell center to nearest canonical water-cell center, this metric measures the nearest water distance available anywhere in the candidate footprint support.

Если canonical water отсутствует во всём domain:

```text
distance_to_water = +inf
```

Это runtime-derived sentinel и не сериализуется в `DomainData`.

## Numerical rules

- metric aggregation выполняется в float64;
- upstream canonical fields не мутируются;
- no RNG is used;
- footprint-cell ordering не влияет на arithmetic result;
- invalid shapes/non-finite upstream arrays/out-of-domain candidate/negative radius are explicit capability errors;
- moisture and vegetation upstream arrays must remain in `[0,1]`;
- water depth must be finite and non-negative.

## Runtime API

```text
SiteMetricContext.from_states(plan, terrain, hydrology, surface)
footprint_cells(context.adapter, candidate, footprint_radius_km)
evaluate_site_metrics(context, candidate, footprint_radius_km)
```

`SiteMetricContext` precomputes attempt-global derived arrays exactly once.

## Non-goals

Not included:

- candidate lattice generation;
- reservation containment;
- footprint containment inside reservation;
- SiteRequirement evaluation;
- SitePreference normalization/scoring;
- near-best filtering;
- weighted final selection;
- PlacementState;
- sub-cell raster integration;
- adaptive footprint sampling;
- setting-specific metrics.
