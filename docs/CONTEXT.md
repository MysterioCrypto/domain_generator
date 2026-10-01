# Rolling Context — Core 0.2

This file is the canonical rolling semantic context. It is intentionally rewritten at major checkpoints rather than kept as a commit-by-commit diary.

Read order:

```text
PROJECT.md
→ docs/CONTEXT.md
→ docs/PROGRESS.md
→ relevant accepted docs/design/*
→ code/tests
```

Active development line: `dev/0.2`. Do not infer current state from `main`.

## Stable accepted base

### Terrain 0.2 — ACCEPTED

```text
continuous multi-scale base elevation
+ smooth semantic Band spine
+ massif-scale ridge modifier
+ blended Area raise/depress
```

Do not reopen Terrain without a concrete cross-layer defect.

### Hydrology 0.2 — ACCEPTED / merged

Accepted production line:

```text
Priority-Flood conditioning
→ MFD p=1.1 contributing area
→ continuous MFD vector field
→ dominant one-downstream channel skeleton
→ H09-D2 regional river network
→ H09-E potential drainage hierarchy
→ Strahler ordering
→ continuous world-space geometry
```

Representative accepted hierarchy:
- regional H09-D2: 16 sources, 4 confluences, 33 segments;
- H09-E potential: 43 sources, 10 realized confluences, 66 segments;
- max Strahler order 3;
- potential vector grid-lock ~8.66%;
- regional skeleton coverage 100%.

Lakes:
- one routing supernode / one canonical outlet per accepted lake;
- H10-A refined 250 m semantic shoreline: KEEP;
- exact river inflow/outlet contact with shoreline: KEEP;
- H10-B nested-depression diagnostic found all 13 representative lakes to be single basins, so nested splitting / partial-fill cascade was rejected by evidence.

Deferred hydro-surface finishing until environmental context exists:
- perennial / seasonal / dry low-order drainage;
- diffuse headwater roots;
- standing lake vs wetland / playa / dry depression;
- delta / estuary / fan only where receiving environment is known.

### C1 annual climate forcing — ACCEPTED / merged

Normative design: `docs/design/annual-climate-forcing-v0.2.md`.

Accepted semantics:
- explicit annual mean temperature field;
- explicit north/south macro thermal gradient;
- fixed C1 experiment lapse rate 6.5 °C/km around domain mean elevation;
- deterministic climate noise;
- explicit annual precipitation forcing;
- explicit moisture-transport bearing;
- continuous upwind terrain exposure with windward / lee redistribution;
- land-mean precipitation normalized to requested value.

Important scope boundary:
- C1 is **regional atmospheric forcing**, not a planetary moisture-source simulation;
- requested mean annual precipitation represents moisture supplied to the domain from outside the modeled atmospheric system;
- rivers and ordinary lakes do not themselves generate the atmospheric precipitation field in C1;
- later layers must diagnose their own defects before reopening C1.

Representative C1-A:
- mean T ~7.91 °C, range ~1.64..11.50 °C;
- temperature/elevation correlation ~-0.774;
- requested/actual land mean precipitation = 900 mm/year;
- precipitation p05 / median / p95 ~473 / 796 / 1647 mm/year;
- maximum ~3954 mm/year;
- synthetic windward/lee ratio ~3.22.

Operator accepted C1 because the maps were coherent enough and no concrete climate-domain blocker was identified. This is not a claim of expert climatological validation.

## C2 effective surface moisture — ACCEPTED / merged

Normative design: `docs/design/effective-surface-moisture-v0.2.md`.

Implementation PR #83 is merged into `dev/0.2`.
Merge commit:
`de5646a1af9c9057fe13cf1e7eb92bb1a3728e46`

Accepted semantics:

```text
T_bio = clamp(T, 0, 30)
PET_proxy = 58.93 * T_bio
climatic_wetness = P / (P + PET_proxy)

water_proximity =
    water_moisture_boost * exp(-distance_to_water / water_moisture_decay_km)

catchment_signal =
    A / (A + stream_threshold_km2)

climate_gated_catchment =
    climatic_wetness * catchment_signal

local_hydrology =
    max(water_proximity, climate_gated_catchment)

pre_slope =
    climatic_wetness + (1 - climatic_wetness) * local_hydrology

moisture =
    clamp(pre_slope * cos(slope)^2 + feature_moisture_bias, 0, 1)

canonical water = 1 exactly
```

No extra Core 0.2 moisture noise. Core 0.1 remains unchanged.

C2-A reference with representative `water_moisture_decay_km = 8` was rejected on one bounded defect: broad actual-water halos. Climatic wetness, catchment contribution and slope retention were explicitly kept.

C2-B changed only the representative actual-water decay to `2 km`.

Accepted C2-B workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36837227248`

Automation:
- pytest GREEN;
- C2 checkpoint GREEN;
- M01–M10 remain GREEN.

Representative accepted C2-B:
```text
effective moisture:
  min                  ~0.395
  p05 / median / p95   ~0.548 / 0.658 / 0.864
  max                  ~0.974
  mean                 ~0.673
  land >= 0.8          ~10.4%
  land <= 0.2           0%

water proximity mean   ~0.068
catchment mean         ~0.039

correlations:
  precipitation         +0.820
  temperature           -0.747
  distance to water     -0.069
  legacy moisture       +0.025
  log1p accumulation    -0.090

slope retention:
  mean                 ~0.99875
  min                  ~0.9777
```

Interpretation:
- macro moisture is climate-driven;
- actual-water influence is now localized rather than a domain-scale river halo;
- catchment concentration remains subordinate;
- the accepted `2 km` is a representative calibration at 1 km cell size, not a universal physical riparian width;
- `water_moisture_decay_km` remains an explicit required plan/spec parameter.

C2-A temporary vegetation compatibility has served its purpose. C3 may now redesign Core 0.2 vegetation against accepted C1 + C2 while Core 0.1 stays frozen.

## C3 climate-aware vegetation — ACCEPTED / merged

Normative design:
`docs/design/vegetation-biome-readiness-v0.2.md`

Design PR #84 merged:
`2ad695d059b4f198b5f06c6451b005c0d630fbc9`

Implementation PR #85 merged:
`37e213ebf5f82ebfae149d21088c07e08d836549`

Accepted Core 0.2 semantics:

```text
thermal_suitability =
    normalized Miami-style annual temperature response

vegetation_potential =
    accepted C2 effective moisture
    * thermal_suitability

vegetation_density =
    clamp(
        vegetation_potential
        + feature_vegetation_bias,
        0,
        1
    )

canonical water = 0 exactly
```

Boundaries:
- no direct precipitation term in C3;
- no extra vegetation noise;
- no second legacy linear slope penalty;
- Core 0.1 remains legacy-compatible;
- no biome labels yet;
- `vegetation_density` is an abstract normalized ecological potential/density index, not physical canopy-cover percentage and not literal NPP.

C3-A workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36842261493`

Automation:
- V01–V11 GREEN;
- push pytest GREEN;
- PR pytest GREEN;
- C3-A checkpoint GREEN.

Representative C3-A:
```text
vegetation p05 / median / p95  ~0.261 / 0.297 / 0.348
mean                           ~0.299
min / max                      ~0.181 / 0.400

correlations:
  effective moisture            +0.369
  temperature                   +0.330
  precipitation                 +0.290
  slope                         -0.169
  distance to water             -0.178
  legacy vegetation             +0.360
```

Operator formally accepted C3-A. As with the C3 design, this is project/operator acceptance and not independent expert ecological validation.

### How mountains affect vegetation

There is no extra C3 rule saying "mountain => less vegetation".

Instead terrain acts through accepted upstream environmental mechanisms:
- relative elevation changes C1 annual temperature through the 6.5 °C/km lapse-rate experiment;
- topography redistributes C1 precipitation through windward/lee forcing;
- slope changes C2 moisture retention through `cos(slope)^2`;
- terrain-derived drainage changes C2 catchment and water-proximity context;
- C3 then consumes the resulting temperature and effective moisture.

This preserves mountain influence while avoiding a second arbitrary slope penalty.

## Current checkpoint — deferred hydro-surface finishing

Terrain/Hydrology/C1/C2/C3 now provide the environmental context that earlier hydrology finishing explicitly waited for.

Deferred candidates now eligible for design:
- perennial / seasonal / dry low-order channel semantics;
- diffuse headwater roots / low-order visibility;
- standing lake vs wetland / playa / dry basin semantics;
- delta / estuary / fan morphology where receiving environment is actually known.

The accepted Hydrology 0.2 routing/network body remains frozen. The next slice must classify or finish accepted structure rather than reroute rivers.

Readiness audit result:
- perennial / seasonal / dry low-order classification: still BLOCKED by absent seasonality/baseflow/groundwater semantics;
- lake vs wetland / playa / dry basin: still BLOCKED by absent water-balance/permanence semantics;
- delta / estuary / fan: still BLOCKED by absent known receiving-environment/process context;
- diffuse headwater/low-order visibility: presentation-ready, but requires public access to the already accepted H09-E potential scaffold.

Chosen bounded slice: **H11-A public potential-drainage export**.

Design PR #86:
`https://github.com/MysterioCrypto/domain_generator/pull/86`

Proposed semantics:
```text
Core 0.2 DomainData:
networks["rivers"]
    = existing accepted regional H09-D2 RiverNetwork

networks["potential_drainage"]
    = existing accepted H09-E potential RiverNetwork
```

Contract finding:
- `DomainData.networks` already supports arbitrary named `RiverNetwork` values;
- no root DomainData version bump or new binary field is required for H11-A;
- Core 0.1 output remains unchanged;
- no Strahler metadata extension is included in this slice.

H11-A design status:
```text
design PR #86           ACCEPTED / MERGED
runtime implementation  NEXT
```

Design merge commit:
`712dae3179605b894558a9e399cd6929ffcda459`

Immediate next action:
1. create a separate H11-A implementation branch from current `dev/0.2`;
2. export the existing runtime `potential_river_network` as `DomainData.networks["potential_drainage"]` for Core 0.2 only;
3. add X01–X08 guardrails;
4. run full pytest;
5. produce lightweight operator-visible network key/count/equality evidence;
6. do not merge implementation before explicit ACCEPT / REJECT.

## Rejected / constrained paths that must not silently return

- Core 0.1 world-generation semantics as the 0.2 baseline;
- renderer smoothing as a fix for upstream world-state defects;
- D8 canonical river routing;
- two-receiver D∞ accumulation as final routing;
- direct broad MFD support as semantic river network;
- H09-C sparse skeleton as the sole drainage view;
- multiplicative terrain-aware source rule that deletes the fixed-area baseline;
- nested-lake splitting / partial-fill cascades without structural evidence;
- distance-to-water + arbitrary coherent noise as the canonical Core 0.2 moisture model.

## Process invariant

For spatial/procedural semantics:

```text
accepted design
→ implementation
→ automated guardrails
→ representative operator-visible checkpoint
→ explicit ACCEPT / REJECT
```

Green CI is necessary but not sufficient. Operator-visible output is necessary for visual/semantic acceptance.
