# Effective Surface Moisture v0.2

Status: **proposed design gate**
Target branch: `dev/0.2`
Checkpoint: C2-A
Depends on: accepted Terrain 0.2 + Hydrology 0.2 + C1 annual climate forcing

## 1. Problem

Surface 0.1 `moisture` is a deterministic heuristic built from a constant base, distance to canonical water and coherent noise. C1 intentionally left it unchanged while adding annual temperature and precipitation.

That leaves an explicit semantic mismatch:

```text
accepted climate forcing exists
but
canonical moisture does not use it
```

C2 replaces Core 0.2 canonical moisture with a climate-aware effective surface moisture index while keeping vegetation unchanged for one checkpoint.

## 2. Bounded scope

C2-A changes only Core 0.2 `moisture` semantics.

Keep unchanged:
- Terrain 0.2;
- Hydrology 0.2;
- C1 temperature / precipitation;
- current vegetation_density values;
- current surface feature biases;
- Placement / biome classification.

Core 0.1 moisture remains byte-for-byte legacy semantics.

During C2-A, Core 0.2 vegetation is deliberately computed from the legacy moisture path internally so the moisture field can be judged in isolation. C3 will redesign vegetation against accepted climate + effective moisture and then remove that temporary compatibility path.

## 3. Meaning of the field

`moisture` becomes a normalized **effective surface moisture index**, not literal volumetric soil-water content.

It combines four signals:

```text
annual precipitation
vs annual evaporative demand
+ local hydrologic concentration
+ proximity to actual canonical water
- steep-slope drainage / low retention
```

Range remains `[0,1]`.

Canonical water cells remain exactly `1.0`.

## 4. Climatic wetness

C2 uses a simple annual potential-evapotranspiration proxy inspired by Holdridge:

```text
T_bio = clamp(annual_mean_temperature_c, 0, 30)
PET_proxy_mm = 58.93 * T_bio
climatic_wetness = P / (P + PET_proxy_mm)
```

where `P` is C1 annual precipitation in mm/year.

Why this bounded proxy:
- the project currently has annual, not monthly, climate;
- FAO Penman-Monteith-quality PET would require radiation, humidity, wind and temporal climate unavailable in Core 0.2;
- the Holdridge annual approximation gives a transparent temperature-dependent evaporative-demand scale without pretending that C2 is a full soil-water model.

`climatic_wetness` is diagnostic and deterministic.

Important interpretation:
- cold cells can be climatically wet because annual evaporative demand is low;
- C2 does not claim that this water is biologically available year-round;
- C3 temperature suitability will handle vegetation limits from cold.

## 5. Local hydrologic signal

C2 uses two already-available upstream signals.

### 5.1 Canonical-water proximity

Reuse existing Surface parameters:

```text
water_proximity = exp(-distance_to_water_km / water_moisture_decay_km)
water_signal = water_moisture_boost * water_proximity
```

This represents local riparian / shoreline wetness around currently canonical water.

### 5.2 Contributing-area concentration

Use accepted Hydrology 0.2 contributing area and the accepted regional stream threshold as a natural scale:

```text
catchment_signal = A / (A + stream_threshold_km2)
```

`A` is contributing area in km².

Because terrain convergence alone cannot create water in an arid climate, gate this signal by climatic wetness:

```text
climate_gated_catchment = climatic_wetness * catchment_signal
```

### 5.3 Combined local signal

```text
local_hydrology = max(water_signal, climate_gated_catchment)
```

No additional moisture noise is introduced in Core 0.2 C2. Climate already contains coherent spatial variation, and hydrology/topography provide deterministic local structure.

## 6. Recharge combination

Local hydrology only fills part of the remaining climatic dryness:

```text
pre_slope_moisture =
    climatic_wetness
    + (1 - climatic_wetness) * local_hydrology
```

This guarantees that local drainage concentration cannot reduce climatic wetness.

## 7. Slope retention

Use the existing continuous slope field and a fixed parameter-free retention curve:

```text
slope_retention = cos(slope_rad)^2
effective_moisture = pre_slope_moisture * slope_retention
```

For ordinary terrain:
- 0° → retention 1.0;
- 30° → 0.75;
- 45° → 0.5;
- 90° → 0.0.

This is an intentionally simple retention/drainage proxy, not a soil model. It avoids adding another tuning parameter before soils exist.

Finally:

```text
effective_moisture = clamp(effective_moisture, 0, 1)
water cells = 1 exactly
```

## 8. Versioned compatibility

For Core 0.1:
- existing moisture algorithm unchanged;
- existing moisture noise unchanged;
- existing vegetation unchanged.

For Core 0.2:
- public/canonical `moisture` becomes C2 effective moisture;
- legacy `moisture_base`, `moisture_noise_amplitude` and `moisture_noise_scale_km` no longer control canonical moisture;
- `water_moisture_boost` and `water_moisture_decay_km` retain useful meaning as local actual-water influence;
- current `vegetation_density` remains temporarily legacy for C2-A only.

No public field rename in C2.

## 9. Why vegetation is not changed in C2-A

If moisture and vegetation change in the same checkpoint, a bad vegetation map cannot tell us whether the defect comes from:
- climate wetness;
- hydrologic concentration;
- slope retention;
- vegetation response.

C2-A therefore accepts/rejects moisture independently.

C3 will use accepted C1 + C2 fields for temperature suitability and vegetation potential.

## 10. Automated guardrails

### M01 — dry/wet climate ordering
At equal temperature/topography/hydrology, higher precipitation gives higher effective moisture.

### M02 — thermal-demand ordering
At equal precipitation/topography/hydrology, warmer annual temperature within 0..30 C gives lower climatic/effective moisture.

### M03 — canonical water exactness
Every canonical water cell has moisture exactly 1.0.

### M04 — riparian decay
On flat terrain with equal climate, moisture decreases monotonically away from isolated canonical water when catchment signal is disabled/constant.

### M05 — catchment concentration
At equal climate, slope and water distance, larger contributing area cannot produce lower moisture.

### M06 — slope drainage
At equal climate/hydrology, increasing slope cannot increase effective moisture.

### M07 — range / dtype / replay
Core 0.2 moisture is finite float32, within [0,1], and deterministic for same plan/attempt.

### M08 — upstream immutability
Terrain, Hydrology, temperature and precipitation are unchanged by C2.

### M09 — vegetation compatibility
C2-A keeps vegetation_density bit-identical to the pre-C2 Core 0.2 implementation for the same upstream state/plan.

### M10 — Core 0.1 compatibility
Core 0.1 moisture and vegetation remain bit-identical.

## 11. Operator checkpoint C2-A

Use the same 180×120 km accepted Terrain/Hydrology/C1 world.

Required views:
1. climatic_wetness only;
2. local water-proximity signal;
3. climate-gated catchment signal;
4. slope_retention;
5. final effective moisture;
6. old legacy moisture vs new effective moisture side-by-side;
7. effective moisture with regional rivers/lakes overlaid;
8. statistics with min/percentiles/max and correlations against precipitation, temperature, slope, accumulation and distance-to-water.

Operator questions:
- does macro wet/dry structure follow climate rather than arbitrary water-distance noise?
- do valleys/riparian corridors become wetter without turning every drainage line into a saturated stripe?
- do steep mountains lose local surface moisture without becoming uniformly desert-like?
- does the field retain regional continuity rather than looking like a hydrology mask?
- are canonical rivers/lakes influencing nearby land at a plausible spatial scale?

## 12. Stop rules

- Do not tune C1 precipitation to fix C2 moisture unless evidence points upstream.
- Do not add biome labels or vegetation redesign in C2-A.
- Do not add soil types yet.
- Do not add a second arbitrary moisture noise layer.
- Do not fit moisture to satellite colors; later vegetation/biomes will transform this field strongly.
- If Holdridge-derived climatic wetness behaves badly for cold or hot domains, reject the proxy and redesign demand rather than patching vegetation.
- If accumulation dominates the map, diagnose the catchment combination rather than smoothing the output.

## 13. External rationale

- Holdridge-style annual PET uses approximately 58.93 × biotemperature and relates PET to annual precipitation.
- FAO soil-water balance separates precipitation input from evapotranspiration, runoff, deep drainage, capillary rise and storage change.
- C2 is explicitly a reduced annual index because Core 0.2 does not yet model monthly climate, soil storage, radiation, humidity or groundwater depth.