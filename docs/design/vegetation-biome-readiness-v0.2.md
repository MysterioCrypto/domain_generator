# Vegetation / Biome Readiness v0.2

Status: **ACCEPTED design gate; runtime implementation authorized but not yet accepted**
Target branch: `dev/0.2`
Checkpoint: C3
Depends on: accepted Terrain 0.2 + Hydrology 0.2 + C1 annual climate forcing + C2 effective surface moisture

## 1. Problem

Core 0.2 now has accepted annual temperature, annual precipitation and climate-aware effective surface moisture, but canonical `vegetation_density` is still intentionally held on the Core 0.1 legacy path.

That temporary compatibility boundary was useful during C2 because it isolated moisture acceptance, but it now creates the next explicit semantic mismatch:

```text
accepted C1 temperature
+ accepted C2 effective moisture
exist
but
Core 0.2 vegetation still follows legacy moisture + legacy slope response
```

C3 replaces only Core 0.2 canonical terrestrial `vegetation_density` with a climate-aware vegetation-potential field suitable as an upstream input for later biome classification.

C3 does **not** classify biomes.

## 2. Bounded scope

C3 changes only Core 0.2 `vegetation_density` semantics.

Keep unchanged:
- Terrain 0.2;
- Hydrology 0.2;
- C1 annual temperature / precipitation;
- C2 canonical effective moisture;
- existing `vegetation_bias` feature semantics;
- canonical water vegetation = 0;
- Placement;
- biome vocabulary / biome labels;
- Core 0.1 vegetation.

Do not add:
- monthly seasonality;
- soils;
- solar radiation;
- humidity;
- groundwater depth;
- disturbance/fire/succession;
- species or land-cover classes;
- agricultural/human land use;
- aquatic vegetation.

## 3. Meaning of the field

Core 0.2 `vegetation_density` remains a normalized `[0,1]` **terrestrial vegetation-potential / density index**.

It is not:
- literal leaf-area index;
- fractional canopy cover;
- biomass in physical units;
- NPP in gC/m²/year;
- a biome class.

The field answers a bounded question:

> given accepted annual climate and effective surface moisture, how favorable is this cell for generic terrestrial vegetation?

This gives a continuous ecological input for later biome classification without pretending that annual climate is sufficient to determine a biome by itself.

## 4. Inputs

C3 uses only already accepted Core 0.2 canonical inputs:

```text
annual_mean_temperature_c
effective surface moisture
existing explicit vegetation feature bias
canonical water mask
```

C3 does not read annual precipitation directly.

Reason: precipitation already contributes to accepted C2 effective moisture. Adding precipitation again in C3 would double-count the same annual water forcing and would bypass the hydrologic/local-retention semantics accepted in C2.

C3 also does not read contributing area or distance-to-water directly. Their bounded influence is already represented in canonical C2 moisture.

## 5. Thermal suitability

C2 intentionally allows cold cells to be climatically wet because annual evaporative demand is low. C3 therefore needs an independent cold/productivity limitation.

Use the temperature-response shape from the classic Miami annual NPP proxy, but normalize it as a dimensionless suitability rather than treating the result as literal NPP.

First:

```text
T_veg = min(annual_mean_temperature_c, 30)
```

Define the Miami temperature response without the physical 3000 multiplier:

```text
miami_temperature_response(T) =
    1 / (1 + exp(1.315 - 0.119 * T))
```

Normalize against the same response at 30 °C:

```text
thermal_reference =
    miami_temperature_response(30)

thermal_suitability =
    clamp(
        miami_temperature_response(T_veg) / thermal_reference,
        0,
        1
    )
```

Representative values:

```text
T = -10 °C  -> thermal suitability ~0.10
T =   0 °C  -> ~0.23
T =   5 °C  -> ~0.36
T =  10 °C  -> ~0.52
T =  20 °C  -> ~0.82
T >= 30 °C  -> 1.00
```

Interpretation:
- cold annual climates suppress generic vegetation potential even when moisture is high;
- warmth becomes progressively less limiting;
- C3 does not invent a high-temperature mortality curve from annual mean temperature alone;
- temperature above 30 °C does not keep increasing suitability because the current annual-only model cannot resolve heat stress, seasonality or humidity well enough to justify that behavior.

The Miami temperature curve is used only as a parsimonious response shape. C3 is not a Miami NPP implementation.

## 6. Climate-aware vegetation potential

Base terrestrial vegetation potential:

```text
vegetation_potential =
    effective_moisture * thermal_suitability
```

Why multiplication:
- moisture and thermal availability are both necessary;
- zero effective moisture yields zero base vegetation potential;
- severe cold suppresses even a wet cell;
- moisture gradients remain visible inside the same thermal regime;
- no second precipitation model is introduced.

This is deliberately simpler than a biome/productivity model.

## 7. Slope semantics

C3 does **not** apply the legacy Core 0.1 factor

```text
1 - slope / vegetation_slope_zero_deg
```

again.

Reason:
- accepted C2 effective moisture already contains a continuous slope-retention term;
- applying a second independent strong linear slope penalty would count steepness twice before soils/substrate exist;
- the old factor was part of the rejected Core 0.1 world-generation semantics, retained only for C2-A compatibility.

For Core 0.2 after C3:
- `vegetation_slope_zero_deg` becomes legacy-compatibility input only and does not control canonical vegetation;
- it remains active for Core 0.1;
- removing it from the shared public schema is out of scope for C3 and can be handled by a later versioned contract cleanup.

## 8. Feature-bias semantics

Existing explicit `vegetation_bias` remains additive after climate-aware vegetation potential:

```text
vegetation_density =
    clamp(
        vegetation_potential
        + feature_vegetation_bias,
        0,
        1
    )
```

Existing `moisture_bias` affects C3 indirectly because it already changes canonical C2 `moisture`.

This preserves the distinction:

```text
moisture_bias
  -> changes environmental moisture
  -> vegetation responds through the normal C3 path

vegetation_bias
  -> explicit direct vegetation override
```

No new vegetation noise is added.

## 9. Canonical water

Canonical water remains non-terrestrial:

```text
water_depth_m > 0
-> vegetation_density = 0 exactly
```

Aquatic vegetation is deferred and must not be represented by weakening this invariant.

## 10. Versioned compatibility

### Core 0.1

Byte-compatible semantics remain:

```text
legacy moisture
* legacy slope factor
+ existing vegetation bias
-> vegetation_density
```

### Core 0.2

After C3:

```text
accepted C2 effective moisture
* normalized annual thermal suitability
+ existing vegetation bias
-> vegetation_density

canonical water -> 0
```

Core 0.2 vegetation must no longer depend on:
- legacy moisture base;
- legacy moisture environmental noise;
- legacy moisture noise scale;
- `vegetation_slope_zero_deg`.

The accepted C2 actual-water parameters remain relevant because they affect canonical C2 moisture.

## 11. Why C3 stops before biome labels

A biome classifier requires categorical boundaries and policy choices that are not necessary to validate vegetation potential.

Separating the layers keeps diagnosis possible:

```text
C1 climate
-> C2 effective moisture
-> C3 vegetation potential
-> later biome classification
```

If a future biome map is wrong, the project can determine whether the defect is climate, moisture, vegetation response or classification rather than changing all of them together.

C3 is therefore **biome-ready**, not a biome generator.

## 12. Automated guardrails

### V01 — moisture ordering

At equal temperature/bias/water state, greater effective moisture cannot produce lower base vegetation potential.

### V02 — cold limitation

At equal effective moisture and for temperatures below 30 °C, increasing annual mean temperature cannot reduce thermal suitability or base vegetation potential.

### V03 — warm saturation

At annual mean temperature >=30 °C, further warming does not increase thermal suitability.

### V04 — dry limit

With effective moisture exactly 0 and no vegetation bias, base terrestrial vegetation potential is exactly 0.

### V05 — canonical-water exactness

Every canonical water cell has `vegetation_density == 0.0` exactly.

### V06 — feature-bias semantics

Existing vegetation bias remains additive before clamping. Existing moisture bias influences vegetation only through canonical moisture.

### V07 — range / dtype / replay

Core 0.2 vegetation is finite `float32`, lies in `[0,1]`, and is deterministic for identical plan/attempt.

### V08 — upstream immutability

C3 does not change Terrain, Hydrology, annual temperature, annual precipitation or accepted C2 moisture arrays.

### V09 — Core 0.1 compatibility

Core 0.1 moisture and vegetation remain bit-identical to their existing path.

### V10 — legacy-parameter independence in Core 0.2

Holding accepted C1/C2 canonical inputs fixed, changing legacy-only:
- `moisture_base`;
- `moisture_noise_amplitude`;
- `moisture_noise_scale_km`;
- `vegetation_slope_zero_deg`;

cannot change Core 0.2 C3 vegetation.

### V11 — no hidden vegetation noise

C3 vegetation contains no additional stochastic/coherent-noise field beyond structure already present in accepted upstream climate/moisture and explicit features.

## 13. Operator checkpoint C3-A

Use the same accepted 180×120 km representative world and accepted C2-B calibration.

Required views:
1. annual mean temperature;
2. thermal suitability;
3. accepted C2 effective moisture;
4. raw vegetation potential;
5. final vegetation density;
6. legacy vegetation vs C3 vegetation side-by-side;
7. C3 vegetation with accepted rivers/lakes overlaid;
8. temperature-vs-thermal-response curve;
9. statistics and correlations against temperature, moisture, precipitation, slope, distance-to-water and legacy vegetation.

Operator questions:
- do cold/wet cells stop looking implausibly lush?
- do wet temperate cells remain visibly more vegetated than dry cells?
- does the vegetation map preserve broad climate continuity rather than turning into a temperature mask?
- are riparian/valley effects present only through accepted moisture rather than a second water-distance halo?
- are mountains reduced where climate/moisture justify it without a second arbitrary slope wipeout?
- does the field look like a useful continuous ecological input rather than premature biome coloring?

## 14. Acceptance criteria

C3 implementation may be accepted only if:
- V01–V11 are green;
- Terrain/Hydrology/C1/C2 remain unchanged;
- representative C3-A render is operator-visible;
- no obvious temperature-only banding or residual legacy-water-noise structure dominates;
- the operator explicitly accepts the vegetation layer.

Green CI alone is not acceptance.

## 15. Stop rules

- Do not modify C1 or C2 merely to improve vegetation appearance without concrete upstream evidence.
- Do not add a direct precipitation term to C3.
- Do not reintroduce arbitrary vegetation noise.
- Do not add biome labels in C3.
- Do not add soil types yet.
- Do not add monthly/growing-season behavior while only annual climate exists.
- Do not invent high-temperature mortality from annual mean temperature alone.
- Do not restore the legacy linear slope factor to fix a visual problem without evidence.
- Do not classify deferred hydrology types inside C3.
- If the annual thermal proxy fails on a concrete representative climate, redesign the thermal response rather than patching biome thresholds.

## 16. External rationale

The classic Miami model is a parsimonious annual climate-productivity proxy in which potential NPP is limited by separate temperature and precipitation response curves. Its temperature branch is:

```text
NPP_T = 3000 / (1 + exp(1.315 - 0.119*T))
```

C3 borrows only this monotonic annual temperature-response shape.

C3 deliberately does not use the Miami precipitation branch because accepted C2 already combines precipitation demand balance, actual-water proximity, contributing-area concentration and slope retention into canonical effective moisture.

This remains a reduced annual ecological index. More mechanistic vegetation productivity would require additional inputs such as radiation, monthly climate, soils and disturbance that Core 0.2 does not yet model.


## 17. Design acceptance

Operator decision: **ACCEPTED**.

PR #84 merged into `dev/0.2` at:
`2ad695d059b4f198b5f06c6451b005c0d630fbc9`.

Acceptance qualification:
- this is formal project/operator acceptance under INV-006;
- the operator explicitly noted insufficient subject-matter expertise for independent expert ecological validation;
- implementation is authorized under the bounded semantics above;
- implementation still requires V01–V11, green automation, an operator-visible C3-A checkpoint, and explicit implementation acceptance before merge.
