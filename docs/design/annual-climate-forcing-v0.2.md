# Annual Climate Forcing v0.2

Status: **proposed design gate**
Target branch: `dev/0.2`
Checkpoint: C1
Depends on: accepted Terrain 0.2 + Hydrology 0.2

## 1. Problem

Surface 0.1 currently derives `moisture` mainly from a constant base, Euclidean distance to canonical water and coherent noise, then derives terrestrial vegetation from moisture × slope.

That is sufficient as a deterministic infrastructure baseline but not as a plausible regional climate model:
- rainfall is not primarily a distance-to-river/lake field;
- mountain windward/leeward contrast is absent;
- elevation does not affect temperature;
- climate and local surface wetness are conflated.

C1 introduces explicit annual climate forcing without yet rewriting soil/surface moisture or vegetation.

## 2. Bounded scope

C1 adds two canonical environmental fields for schema/plan 0.2:

```text
annual_mean_temperature_c      float32 [rows, columns]
annual_precipitation_mm        float32 [rows, columns]
```

Keep unchanged in C1:
- accepted Terrain 0.2;
- accepted Hydrology 0.2;
- existing moisture and vegetation_density semantics;
- existing surface feature biases;
- pipeline stage ordering;
- Placement.

Moisture/vegetation will be redesigned in a later C2 using the accepted climate fields. C1 must not silently reinterpret them.

## 3. Contract extension

`SurfaceSpec` / `PlanSurface` gain a required `climate` recipe for schema/plan 0.2 and forbid it for 0.1.

Conceptual recipe:

```yaml
surface:
  climate:
    mean_temperature_c: <finite float>
    north_minus_south_temperature_c: <finite float>
    temperature_noise_amplitude_c: <float >= 0>
    mean_annual_precipitation_mm: <float > 0>
    moisture_transport_bearing_deg: <float [0,360)>
    orographic_scale_km: <float > 0>
    orographic_strength: <float >= 0>
    precipitation_noise_log_amplitude: <float >= 0>
    climate_noise_scale_km: <float > 0>
```

No hidden climate defaults. All recipe values participate in the semantic plan fingerprint.

## 4. Temperature field

Let `y_norm = y_km / domain_height_km` and `z_mean` be the arithmetic mean Terrain 0.2 elevation over the domain.

Use the NOAA-reported global-average environmental lapse rate as a fixed Core 0.2 experiment constant:

```text
L = 6.5 °C / km
```

Before coherent noise:

```text
T_gradient = mean_temperature_c
             + north_minus_south_temperature_c * (y_norm - 0.5)

T_orographic = T_gradient
               - 6.5 * (elevation_m - z_mean) / 1000
```

Then add deterministic world-space coherent temperature noise with configured amplitude and shared climate noise scale.

`mean_temperature_c` therefore describes the regional thermal center rather than sea-level temperature; this avoids inventing a sea-level datum when the generated domain may not contain an ocean.

## 5. Precipitation field

C1 models a deliberately simple annual orographic precipitation potential. It is not a weather simulator.

### 5.1 Wind convention

`moisture_transport_bearing_deg` is the direction **toward which** moisture-bearing air moves, clockwise from world north:

```text
0   = toward north
90  = toward east
180 = toward south
270 = toward west
```

### 5.2 Continuous upwind terrain reference

For each cell center, sample original Terrain 0.2 elevation continuously along the upwind ray using bilinear interpolation.

Use an exponentially decaying kernel over configured `orographic_scale_km` to obtain `z_upwind`.

This is a world-space directional calculation, not a raster-neighbor walk.

### 5.3 Orographic contrast

```text
relative_relief_km = (elevation_m - z_upwind) / 1000

log_weight = orographic_strength * relative_relief_km
             + precipitation_noise_log_amplitude * coherent_noise

raw_weight = exp(log_weight)
```

Positive relative relief increases precipitation potential on terrain rising into the moisture flow. Negative relative relief produces a lee/rain-shadow reduction that relaxes with the configured upwind scale.

Finally normalize over non-water domain cells so the spatial mean equals the explicit request value:

```text
annual_precipitation_mm =
    mean_annual_precipitation_mm * raw_weight / mean(raw_weight_land)
```

Canonical water cells may carry the same atmospheric precipitation field; normalization uses land only so lake area does not change the requested terrestrial mean.

## 6. Noise and RNG

Use existing world-space coherent value noise with independent semantic namespaces:

```text
surface/climate/temperature
surface/climate/precipitation
```

Iteration order must not affect either field. Same plan + seed + attempt must replay exactly.

## 7. Runtime and output

`SurfaceState` gains:

```text
annual_mean_temperature_c
annual_precipitation_mm
```

For schema 0.2 both are required finite float32 arrays matching the grid.

`DomainData.fields` exports both as canonical fields:

```text
temperature            unit = degC
annual_precipitation   unit = mm/year
```

Existing `moisture` and `vegetation_density` remain exported unchanged in C1 and are explicitly considered legacy surface semantics pending C2.

## 8. Why C1 does not classify biomes yet

Biome/vegetation plausibility depends on at least temperature plus effective water availability. Effective water availability is not identical to precipitation: evapotranspiration, runoff, slope, drainage, local water and eventually seasonality matter.

C1 therefore stops at climate forcing. C2 will combine accepted temperature/precipitation with hydrology/topography into effective surface moisture and vegetation suitability.

## 9. Automated guardrails

### C01 — flat/no-noise baseline
Flat terrain + zero north/south gradient + zero noise gives spatially uniform temperature and precipitation exactly at configured means.

### C02 — elevation lapse
On otherwise equal cells, +1000 m terrain elevation changes temperature by -6.5 °C within tolerance.

### C03 — north/south gradient
`north_minus_south_temperature_c` produces the exact configured north-minus-south thermal delta before terrain/noise terms.

### C04 — windward/leeward ridge
On a synthetic ridge with eastward moisture transport and zero precipitation noise, windward/rising cells receive more precipitation than corresponding lee cells.

### C05 — rotational consistency
Rotate synthetic terrain and wind bearing together by 90°. Rotated precipitation field must match within numeric tolerance after inverse rotation.

### C06 — mean precipitation conservation
Land-cell arithmetic mean precipitation equals `mean_annual_precipitation_mm` within float tolerance.

### C07 — deterministic replay
Same plan/seed/attempt is bit-identical; changing only attempt changes climate noise but not contract semantics.

### C08 — upstream immutability
Terrain and Hydrology fingerprints/arrays are unchanged by climate generation.

### C09 — C1 compatibility boundary
Existing C1 generation does not change moisture or vegetation_density relative to pre-C1 Surface 0.1 computation for the same upstream state and surface parameters.

## 10. Operator checkpoint C1-A

Use the accepted 180×120 km Terrain/Hydrology world with one explicit representative climate recipe; do not tune against multiple screenshots in the same iteration.

Required views:
1. terrain + annual mean temperature;
2. terrain + annual precipitation;
3. precipitation + prevailing-wind arrow;
4. west/east or along-wind cross-section across the main massif;
5. temperature vs elevation scatter / binned diagnostic;
6. statistics JSON with configured means, actual means, min/max/percentiles and windward/lee synthetic-fixture result.

Operator questions:
- does high terrain become cooler without looking like an elevation recolor only?
- is the north/south macro gradient visible but not overpowering?
- does precipitation respond to the massif with a plausible windward/lee pattern?
- are there obvious raster-aligned artifacts?
- is precipitation contrast too weak or unrealistically extreme?

## 11. Stop rules

- Do not change Terrain or Hydrology to make climate maps prettier.
- Do not derive rainfall from distance to rivers/lakes.
- Do not classify biomes in C1.
- Do not use temperature to rewrite lake permanence yet.
- Do not tune the orographic model by sweeping parameters on one representative map.
- If the upwind-reference model produces implausible artifacts, reject C1 and redesign precipitation transport rather than smoothing the output.

## 12. External rationale

- NOAA gives ~6.5 °C/km as the global-average environmental temperature lapse rate.
- UCAR meteorology material explicitly describes higher elevations as colder and leeward mountain regions as typically warmer/drier than windward regions because of orographic ascent/descent.
- FAO water-balance guidance distinguishes precipitation from effective moisture and evapotranspiration; this supports keeping C1 climate forcing separate from later C2 surface-water/vegetation semantics.