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
implementation PR #87   OPERATOR REVIEW
```

Design merge commit:
`712dae3179605b894558a9e399cd6929ffcda459`

Implementation PR #87:
`https://github.com/MysterioCrypto/domain_generator/pull/87`

Semantic head:
`b77d3247577c552117ba6bf4567d4e7563f062b1`

Implemented boundary:
```text
Core 0.1:
  networks["rivers"] only

Core 0.2:
  networks["rivers"]
  networks["potential_drainage"]
```

Runtime contract correction discovered during checkpoint:
- the `DomainData.networks` field type/schema already allowed multiple named RiverNetwork values;
- a historical model validator still rejected every network other than `rivers`, regardless of 0.2 provenance;
- H11-A makes the validator version-aware while keeping 0.1 unchanged and allowing only the exact additional `potential_drainage` ID for 0.2;
- no root DomainData version bump.

Checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`

Evidence:
```text
network keys              ["rivers", "potential_drainage"]

regional runtime           58 nodes / 33 segments
regional export            58 nodes / 33 segments
regional exact equality    true

potential runtime          111 nodes / 66 segments
potential export           111 nodes / 66 segments
potential exact equality   true

upstream hashes unchanged  true
```

Automation:
- X01–X08 GREEN;
- push pytest GREEN;
- PR pytest GREEN;
- H11-A checkpoint GREEN.

No spatial rerender is required because H11-A does not alter accepted H09-E geometry.

H11-A implementation status:
```text
implementation PR #87   ACCEPTED / MERGED
merge commit             cef91e81c86c64555ae1e1363d7ffaf2934ff6ce
```

Accepted public boundary:
- Core 0.1 exports only `networks["rivers"]`;
- Core 0.2 exports `rivers` and `potential_drainage`;
- `potential_drainage` is a drainage scaffold, not a flow-permanence class;
- canonical water authority remains `rivers`;
- routing/network geometry, lakes, water depth, C1/C2/C3 remain unchanged.

H11-A is frozen unless a concrete export/contract defect appears.

Unsupported physical classifications remain deferred:
- perennial / seasonal / dry;
- standing lake vs wetland / playa / dry basin;
- delta / estuary / fan.

## Current checkpoint — Placement continuation / readiness audit

The hydro-surface finishing slice is closed at the current model fidelity. The project now returns to Placement as previously planned.

Placement readiness-audit result:

KEEP unchanged:
- rotated world-space candidate lattice;
- explicit candidate spacing;
- reservation containment;
- circular raster footprint;
- hard requirements;
- preference scoring;
- near-best filtering;
- deterministic weighted selection;
- RNG namespace separation;
- no hidden retries/relaxation.

Existing metrics retained:
- slope_mean;
- water_fraction;
- elevation_mean;
- local_relief;
- relative_elevation;
- moisture_mean;
- vegetation_density_mean;
- distance_to_water.

Core 0.2 upstream meaning:
- `moisture_mean` now evaluates accepted C2 effective moisture;
- `vegetation_density_mean` now evaluates accepted C3 vegetation.

Chosen bounded slice: **P08-A Placement Environmental Site Metrics v0.2**.

Design PR #88:
`https://github.com/MysterioCrypto/domain_generator/pull/88`

Proposed Core 0.2-only additions:
- `temperature_mean`;
- `annual_precipitation_mean`;
- `distance_to_potential_drainage`.

Potential-drainage distance is explicitly geometric proximity to the accepted H09-E scaffold, not water permanence/access.

No candidate lattice, requirement evaluator, scoring, near-best or final selection changes.

P08-A design status:
```text
design PR #88           ACCEPTED / MERGED
implementation PR #89   OPERATOR REVIEW
```

Design merge commit:
`66003288e528fc340663d92f84ed14cbee88744b`

Implementation PR #89:
`https://github.com/MysterioCrypto/domain_generator/pull/89`

Semantic head:
`ec59e0b6693c10fb6064ebf4b68d7f8c019097e8`

Implemented:
- version-aware site metric registry;
- Core 0.1 remains exactly the historical eight metrics;
- Core 0.2 additionally exposes `temperature_mean`, `annual_precipitation_mean`, `distance_to_potential_drainage`;
- climate metrics aggregate accepted C1 arrays over the existing footprint cells;
- potential-drainage distance is exact world-space point-to-centerline distance minus footprint radius, clamped at zero;
- no Placement RNG or selection-semantics change.

Checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`

Artifact:
`placement-v02-p08`

Representative diagnostic:
```text
candidates                      148
valid                           133
near-best                       1
selected x/y                    ~23.326 / 38.308 km
selected suitability            ~0.895

temperature_mean range          ~2.96 .. 11.34 C
temperature_mean median         ~8.24 C
annual precipitation range      ~302 .. 3243 mm/year
annual precipitation median     ~794 mm/year
potential drainage distance     0 .. ~23.69 km
potential drainage median       ~4.38 km
```

Selected fixture-only site:
```text
temperature_mean                ~6.42 C
annual_precipitation_mean       ~2159.8 mm/year
distance_to_potential_drainage  ~6.86 km
moisture_mean                   ~0.853
vegetation_density_mean         ~0.345
distance_to_water                7 km
```

Integrity:
- P01–P11 GREEN;
- push pytest GREEN;
- PR pytest GREEN;
- upstream canonical hashes unchanged;
- potential drainage unchanged.

Assistant review:
- climate metrics visibly correspond to accepted C1 fields;
- potential-drainage metric follows accepted H09-E geometry;
- canonical water distance and potential drainage remain semantically distinct;
- no concrete blocker identified.

P08-A implementation status:
```text
implementation PR #89   ACCEPTED / MERGED
merge commit             57e77c8de6ac8668ddd09e25167e30aa773cf645
```

Accepted boundary:
- Core 0.1 site metric registry remains unchanged;
- Core 0.2 adds only `temperature_mean`, `annual_precipitation_mean`, `distance_to_potential_drainage`;
- C2/C3-backed legacy metric IDs remain stable;
- potential drainage proximity is not canonical-water proximity;
- existing Placement candidate/selection mechanics remain frozen.

P08-A is frozen unless a concrete metric/contract defect appears.

## Placement 0.2 — current scope complete

Post-P08-A audit result:
- the preset/plan SiteProfile contract already accepts metric IDs as explicit strings;
- Core 0.2 environmental metrics therefore work through the existing compiler path without another schema redesign;
- candidate generation and site selection already consume the version-aware runtime registry;
- no additional base Placement semantic slice is required at the current Core 0.2 scope.

Still deferred as higher-layer work:
- deferred-to-deferred POI interactions;
- roads/accessibility networks;
- human geography;
- settlement-specific hidden defaults or heuristics.

These must not be smuggled into generic Core Placement merely because environmental metrics now exist.

## Current checkpoint — Core 0.2 integrated acceptance hardening

Historical acceptance cases A01–A07 are Core 0.1 fixtures. Core 0.2 has strong component checkpoints but no single frozen end-to-end acceptance case.

Hardening PR #90:
`https://github.com/MysterioCrypto/domain_generator/pull/90`

A08 exercises:
```text
DomainSpec 0.2
→ PresetCatalog
→ compiler
→ Terrain 0.2
→ Hydrology 0.2
→ C1/C2/C3
→ Placement using P08-A metrics
→ DomainData rivers + potential_drainage
→ canonical bundle
→ exact replay
```

This is test/integration hardening only. It does not introduce new world semantics and therefore does not require a new INV-006 semantic design gate.

A08 status:
```text
hardening PR #90        MERGED
merge commit            568eeff9676ee387d5837cfb1fca1a8ff087e99b
full pytest             GREEN
exact replay            GREEN
bundle checks           GREEN
```

Frozen representative A08:
- accepted attempt 0;
- 6 canonical Core 0.2 fields;
- 4 generated lakes;
- regional network 49 nodes / 31 segments;
- potential drainage 104 nodes / 73 segments;
- P08-A metrics used through a normal preset/site_profile;
- DomainData deterministic baseline pinned.

## Current checkpoint — Core 0.2 release hardening

Release-readiness audit found documentation/version consistency debt, not a procedural world-state defect:
- package version still says `0.1.0.dev0`;
- README still presents Core 0.1 as current;
- canonical architecture document frontmatter/title still targets Core 0.1;
- Core 0.2 runtime/schema/acceptance state is otherwise integrated.

Independent contract versions such as DomainData 0.1, GenerationConfig 0.1 and PresetCatalog 0.1 are not automatically release blockers. Their versions are intentionally independent from DomainSpec/generator versions.

Immediate next action:
1. align package/generator development version with Core 0.2;
2. refresh README current-state guidance;
3. update canonical architecture to document the accepted Core 0.2 delta while preserving historical 0.1 architecture rules that remain valid;
4. add consistency guardrails where useful;
5. run full pytest/A08 again before any release-branch decision.

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


### Release metadata hardening PR #91

`https://github.com/MysterioCrypto/domain_generator/pull/91`

The generator development identity is being aligned from `0.1.0.dev0` to `0.2.0.dev0`.

Because generator version is semantic provenance and participates in `plan_fingerprint`, A01–A08 baselines must be re-signed. Allowed delta is limited to provenance/fingerprint-derived values; world arrays, features, networks, placement and validation semantics must remain unchanged.

First CI intentionally uses PENDING baselines to emit exact snapshots before pinning.


## Core 0.2 release-candidate gate

Release metadata hardening PR #91:
- merged at `5cafb8119050f19765447d65dcef022ebebe052b`;
- generator/package identity now `0.2.0.dev0`;
- README and canonical architecture aligned with active Core 0.2;
- A01–A08 re-signed after version change;
- every baseline changed only in `domain_data_sha256`; all field hashes, geometry/network summaries, attempts, ranking and validation remained identical.

Merge-head pytest:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36853774759`
— GREEN.

No concrete blocker remains inside current Core 0.2 release scope.

Deferred work is explicitly outside this candidate:
- environmental seasonality / true biome classification;
- flow-permanence and basin-permanence hydrology;
- receiving-environment delta/estuary/fan morphology;
- roads / human geography / interdependent POI graph.

Operator decision: **CORE 0.2 RELEASE CANDIDATE ACCEPTED**.

Frozen release:
```text
branch        release/0.2-prealpha
freeze commit c69c1af010a085fb80d248af703a77471fc6c9d7
generator     0.2.0.dev0
```

The release branch was created exactly from the accepted `dev/0.2` head. Subsequent canonical-document updates on `dev/0.2` are post-release bookkeeping and are not part of the frozen release snapshot.

Release scope remains exactly the accepted Core 0.2 scope:
- Terrain 0.2;
- Hydrology 0.2;
- C1 annual climate;
- C2 effective moisture;
- C3 climate-aware vegetation;
- H11-A public potential drainage;
- P08-A environmental Placement metrics;
- A08 integrated acceptance;
- release metadata/provenance hardening.

Deferred work stays outside `release/0.2-prealpha`:
- seasonality / true biome classification;
- flow-permanence and basin-permanence hydrology;
- delta/estuary/fan morphology;
- roads / human geography / interdependent POI graph.

## Current checkpoint — C4-A Environmental Seasonality design

Post-release dependency audit:
- C3 explicitly records that annual-only climate is not sufficient for defensible biome labels;
- flow-permanence classification still lacks seasonality plus baseflow/groundwater;
- therefore biome labels and channel permanence remain deferred;
- the next bounded layer is an explicit climatological monthly envelope.

Design PR #92:
`https://github.com/MysterioCrypto/domain_generator/pull/92`

Proposed C4-A semantics:
```text
optional climate.seasonality:
  temperature_seasonal_amplitude_c
  temperature_peak_month
  precipitation_seasonality_log_amplitude
  precipitation_peak_month

annual temperature
→ 12 monthly temperature means
→ exact annual-mean conservation

annual precipitation
→ 12 monthly precipitation totals
→ exact annual-total conservation
```

Boundary:
- regional explicit seasonality; no latitude/hemisphere inference;
- no additional monthly noise;
- no seasonal moisture-transport rotation;
- accepted annual C1 remains canonical;
- C2 moisture and C3 vegetation remain unchanged in C4-A;
- monthly fields are derived, not replacements for annual canonical fields;
- no biome labels;
- no channel permanence labels.

Compatibility:
- no seasonality recipe → frozen annual-only prealpha behavior;
- release branch remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.

C4-A status:
```text
design PR #92           ACCEPTED / MERGED
implementation PR #93   ACCEPTED / MERGED
```

Design merge commit:
`e729d836d29df790fa1c0056e7b686d6189703f9`

Implementation PR #93:
`https://github.com/MysterioCrypto/domain_generator/pull/93`

Semantic head:
`5b9b4e7341bfb3c8b496f25b3e9f741128f31b2a`

Implemented:
- optional `climate.seasonality` contract;
- deterministic 12-month temperature envelope;
- deterministic 12-month precipitation redistribution;
- internal float32 monthly runtime arrays;
- 24 public derived 2D monthly fields;
- annual C1 fields remain canonical;
- C2/C3 unchanged;
- no biome or flow-permanence classification.

S10 compatibility correction:
- first full-suite run showed that the newly modeled absent value `seasonality: null` changed historical Core 0.2 fingerprints;
- this was rejected as a real compatibility defect rather than accepted as a provenance re-sign;
- fingerprint payload normalization now omits only absent seasonality, reproducing the frozen A08 spec/plan fingerprints exactly;
- explicit seasonality remains in the hash and changes semantic plan identity.

Checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36959449118`

Artifact:
`surface-v02-c4`

Automation:
- S01–S13 GREEN;
- schema snapshots GREEN;
- push full pytest GREEN;
- PR full pytest GREEN;
- C4-A checkpoint GREEN.

Representative recipe:
```text
temperature_seasonal_amplitude_c       7
temperature_peak_month                 7
precipitation_seasonality_log_amplitude 1
precipitation_peak_month               1
```

Representative evidence:
```text
monthly derived descriptors            24
canonical annual fields unchanged      true
features unchanged                     true
networks unchanged                     true

temperature conservation max error     ~4.77e-7 C
precipitation conservation max error   ~1.91e-4 mm

annual temperature                     ~1.64 .. 11.50 C
month 07 temperature                    ~8.64 .. 18.50 C
month 01 temperature                    ~-5.36 .. 4.50 C

precipitation fraction month 01         ~0.17892
precipitation fraction month 07         ~0.02421
```

Visual review:
- spatial climate structure is preserved between months;
- temperature curves are smooth sinusoidal envelopes;
- precipitation fractions are smooth and peak/trough at configured months;
- no additional spatial climate noise appears;
- fixed regional phase remains visibly a bounded climatological model rather than weather simulation.

Operator decision: **C4-A IMPLEMENTATION ACCEPTED**.

Implementation merge commit:
`570a5c4730419d17bce69f9e804b805125343fa5`

Accepted C4-A guarantees:
- explicit seasonality remains opt-in;
- annual climate fields remain canonical;
- 24 monthly public fields remain derived;
- annual-only Core 0.2 requests retain frozen prealpha behavior and fingerprints;
- C2/C3 remain unchanged;
- no biome/permanence semantics were smuggled into this slice.

Current gate:
```text
C4-A implementation   ACCEPTED / MERGED
release/0.2-prealpha  STILL FROZEN
next                  POST-C4 DEPENDENCY AUDIT
```

Immediate next action:
1. audit remaining dependencies for the deferred candidates;
2. select exactly one bounded next semantic layer;
3. open a new INV-006 design gate before material implementation;
4. do not reopen accepted C4-A semantics without concrete evidence.


## Current checkpoint — C5-A Köppen–Geiger Climate Regimes design

Post-C4 dependency audit:

```text
perennial/seasonal/dry channels   BLOCKED
  missing groundwater/baseflow/storage

lake/wetland/playa/dry basin      BLOCKED
  missing basin water balance/infiltration/permanence

delta/estuary/fan                 BLOCKED
  missing known receiving environment/process context

direct biome labels               DEFERRED
  avoid conflating climate regime with vegetation/substrate policy
```

The newly available C4 monthly climatology does make climate regionalization directly implementable.

Design PR #94:
`https://github.com/MysterioCrypto/domain_generator/pull/94`

Scientific basis:
- Peel et al. (2007) Köppen–Geiger criteria;
- Beck et al. (2018) 30-class ordering.

Core-specific adaptation:
- published summer/winter half-year tests cannot use map latitude because Core has no geographic hemisphere;
- C5-A therefore defines a local warm half-year as months `peak-3 .. peak+2` around the explicit C4 temperature peak month;
- cold half-year is the complementary six months;
- the adaptation is exposed in scheme id `koppen_geiger_local_season_v1`, not hidden.

Proposed public output:
```text
field id   climate_regime_koppen_geiger
role       derived
dtype      uint8
unit       koppen_geiger_local_season_v1
codes      1..30
```

The fixed codebook follows the Beck ordering:
Af, Am, Aw, BWh, BWk, BSh, BSk, Csa..Cfc, Dsa..Dfd, ET, EF.

Contract is opt-in:
```text
surface.climate.classification:
  scheme: koppen_geiger_local_season_v1
```

Classification requires C4 seasonality. Existing C4 requests without classification remain unchanged.

C5-A status:
```text
design PR #94           ACCEPTED / MERGED
implementation PR #95   ACCEPTED / MERGED
```

Design merge commit:
`d75b2f6f55b53a14b048a38bb2a69d339c8cf44e`

Accepted universality boundary:
- C4 seasonal parameters remain explicit inputs;
- no hidden north/south hemisphere assumption;
- Köppen classification is optional and Earth-derived;
- non-Earthlike worlds can use C1/C4 without any categorical classifier;
- future alternative classifiers may use different explicit scheme ids.

Scientific boundary:
- exact Beck/Peel C/D/E thermal threshold retained;
- `Thot > 10 C` for C/D;
- `Thot <= 10 C` for E.

Implementation PR #95:
`https://github.com/MysterioCrypto/domain_generator/pull/95`

Semantic head:
`43519587fac92e94cb8bbbb64222c876d7579882`

Implemented:
- optional `surface.climate.classification`;
- only scheme `koppen_geiger_local_season_v1`;
- classification requires C4 seasonality;
- isolated deterministic classifier consumes persisted float32 C4 climate through float64 views;
- fixed codes 1..30;
- one derived public `uint8` field;
- absence of classification preserves C4 fingerprint semantics.

Scientific rules checked against Peel/Beck:
- B precedence;
- C/D: `Thot > 10 C`;
- E: `Thot <= 10 C`;
- C/D split: `Tcold = 0 C`;
- s/w overlap resolved by total cold-vs-warm half-year precipitation.

Checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36968143576`

Artifact:
`surface-v02-c5`

Automation:
- K01–K15 GREEN;
- schema snapshots GREEN;
- push full pytest GREEN;
- PR full pytest GREEN;
- representative renderer GREEN.

Integrity:
- every pre-existing C4 field exact-equal classification-off vs classification-on;
- features exact-equal;
- networks exact-equal;
- output dtype/role/unit exact.

Representative used classes:
```text
Csb  76.93%
Dsc  10.40%
Dsb   7.40%
Dfc   3.24%
ET    1.49%
Cfb   0.33%
Dfb   0.22%
```

Interpretation:
- the diagnostic C4 recipe intentionally has month-07 thermal peak and month-01 precipitation peak, so broad dry-summer Csb is expected;
- colder mountain structures produce D/ET transitions;
- categorical boundaries follow continuous accepted climate rather than stochastic class noise;
- this result does not become a default world climate.

Operator decision: **C5-A IMPLEMENTATION ACCEPTED**.

Implementation merge commit:
`8af34da0c66c48b62172b8654edc5876d9414085`

Accepted guarantees:
- classifier is opt-in;
- Köppen remains an Earth-derived interpretation rather than canonical climate truth;
- non-Earthlike/fantasy worlds may omit it entirely;
- the classifier consumes accepted C4 climate and does not alter generation;
- one derived `uint8` field with fixed codes 1..30 is exported when enabled;
- C1/C2/C3/C4 and all accepted spatial/network state remain unchanged;
- no biome labels or hydrologic-permanence semantics are introduced.

Current gate:
```text
C5-A implementation   ACCEPTED / MERGED
release/0.2-prealpha  STILL FROZEN
next                  POST-C5 DEPENDENCY AUDIT
```

Immediate next action:
1. audit remaining dependencies again with accepted C5 available;
2. select exactly one bounded next semantic layer;
3. open a new design gate before implementation;
4. do not reopen accepted C5-A semantics without concrete evidence.


## Current checkpoint — H12-A Marine / Coastal Boundary design

Post-C5 dependency audit:

```text
direct biome labels               DEFERRED
  C5 is optional Earth-derived classification, not universal biome truth
  C3 is potential/density, not literal land cover
  soil/substrate/disturbance remain absent

perennial/seasonal/dry channels  BLOCKED
  missing groundwater/baseflow/storage

lake/wetland/playa/dry basin     BLOCKED
  missing basin water balance/infiltration/permanence

delta/estuary/fan                BLOCKED
  missing known receiving environment/process context
```

Universality audit exposed a more basic missing world type:
Core has no explicit sea/ocean/coastline semantics.

Current behavior:
- negative elevation is just terrain elevation;
- no explicit sea level exists;
- edge cells are generic drainage outlets;
- rivers cannot terminate in a known marine receiving feature;
- an archipelago/coastal domain is therefore not represented semantically.

Selected next bounded slice:
**H12-A Marine / Coastal Boundary Semantics**.

Design PR #96:
`https://github.com/MysterioCrypto/domain_generator/pull/96`

Proposed opt-in contract:
```text
hydrology:
  marine:
    sea_level_m: <explicit finite float>
```

Marine classification:
```text
below_sea = elevation < sea_level

marine =
  below-sea components
  connected to domain boundary
  by 4-neighbour edge connectivity
```

Consequences:
- no hidden 0 m sea level;
- inland worlds omit the recipe and stay exact-compatible;
- enclosed below-sea basins are not flooded merely because they are below datum;
- marine water and lakes remain distinct;
- canonical water depth gains explicit sea depth;
- marine coastline is refined at fixed 4× sub-cell resolution;
- public `MarineFeature` and derived `marine_mask` make the distinction explicit;
- regional/potential rivers terminate at a new `marine_outlet` on the refined coastline.

H12-A intentionally does not add:
- tides/waves/salinity;
- ocean temperature moderation;
- submarine channels;
- delta/estuary/fan morphology.

The known marine receiving environment is intended to remove one prerequisite blocker for later coastal-process design.

H12-A design status:
```text
design PR #96           ACCEPTED / MERGED
runtime implementation  NEXT
```

Design merge commit:
`f8efae6e24cdda68fb10960f13ca69d342a61a7b`

Immediate next action:
1. create separate H12-A implementation branch;
2. implement opt-in marine contract/runtime/coastline/outlet semantics;
3. add O01–O13;
4. run full pytest;
5. render dedicated coastal/archipelago checkpoint;
6. do not merge implementation before explicit ACCEPT / REJECT.


### H12-A implementation clarification — canonical-water propagation

Marine is part of canonical `water_depth`, while accepted C2/C3 already consume canonical water.

Therefore:
- H12-A does not change C2/C3 algorithms or parameters;
- newly marine cells use existing semantics: C2 moisture = 1 exactly, C3 vegetation = 0 exactly;
- outside marine-affected water support, C2/C3 remain exact-unchanged;
- C1/C4/C5 climate remains exact-unchanged everywhere;
- Placement algorithms remain unchanged, although existing water-dependent metric values may observe the new marine water.

This resolves an internal contradiction in the original H12 design text; it is not a new ecological model.


### H12-A implementation clarification — coastal dependency propagation

C2 uses distance to canonical water. Therefore adding marine water can change C2 moisture on nearby non-marine coastal land, and C3 can change through accepted C2 moisture.

Correct isolation rule:
- Terrain exact-unchanged;
- C1/C4/C5 climate exact-unchanged;
- C2/C3 algorithms and parameters unchanged;
- Placement algorithms unchanged;
- C2/C3/Placement values may change only through already accepted dependencies whose inputs changed because marine water became canonical;
- no new marine-specific ecology term is allowed in H12-A.


### H12-A recovery checkpoint after interrupted implementation

Implementation PR #97:
`https://github.com/MysterioCrypto/domain_generator/pull/97`

Recovered implementation branch:
`impl/v0.2-marine-coastal-boundary`

The interrupted iteration had already completed more work than the visible chat showed:
- marine contract/compiler/runtime/public feature work exists;
- O01–O13 test module exists;
- marine-aware runtime invariants exist;
- draft PR #97 exists.

Last completed failing CI before recovery:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36974958442`

Result:
```text
489 passed
13 failed
```

Failure groups:
1. compatibility/snapshot:
   - Core 0.1 acceptance fingerprints changed because absent additive `marine=None` leaked into legacy fingerprint payloads;
   - C5 K15 reconstruction needed the same omission;
   - generated schema snapshots are not yet aligned.
2. runtime:
   - O08/O11/O12/O13 fail at one H12 topology point:
     `potential skeleton has an interior downstream discontinuity`.

Recovery changes already written to implementation branch:
- absent marine removed from legacy 0.1 spec/plan fingerprints;
- C5 K15 updated to reconstruct the same additive-field omission;
- detailed coordinates added to the skeleton discontinuity error for deterministic diagnosis.

Current action:
- rerun CI at implementation head;
- use exact `cell -> target` diagnostic to fix the topology defect without weakening the invariant;
- schema snapshots only after runtime semantics are stable.

PR #97 remains draft/unmerged.


### H12-A recovery checkpoint — targeted gate GREEN

Implementation PR #97 targeted workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36978575264`

Current implementation head at this gate:
`b891da9eb0d4ddea9c765ddde43d5a61f1729621`

Resolved recovery defects:
- absent additive `marine=None` no longer changes Core 0.1 / pre-H12 fingerprints;
- marine terminal mask is now passed consistently into Strahler hierarchy;
- H12 preserves accepted no-marine routing/accumulation as the upstream authority;
- C1 precipitation normalization uses an internal pre-marine water baseline, keeping C1 forcing exact-unchanged;
- C2/C3 still consume canonical marine water through their already accepted dependencies;
- generated v0.2 JSON Schema snapshots are synchronized.

Targeted result:
```text
schema snapshots   GREEN
O01-O13            GREEN
```

Next:
- finish full pytest gate;
- render dedicated H12 coastal/archipelago operator checkpoint;
- keep PR #97 draft/unmerged until explicit implementation ACCEPT / REJECT.


### H12-A implementation — operator review gate

Implementation PR #97:
`https://github.com/MysterioCrypto/domain_generator/pull/97`

Semantic head:
`4dc897906d2e67ae7c3bccb2c9ef49934339f4a6`

Final technical evidence:
```text
schema snapshots          GREEN
O01-O13                  GREEN
PR full pytest            502 passed
push full pytest          502 passed
coastal/archipelago render GREEN
```

Workflows:
- H12 checkpoint: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161098`
- PR full pytest: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161043`
- push full pytest: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36979156078`

Artifact:
`hydrology-v02-h12`

Representative report:
```text
domain area                         4536 km²
marine component count             1
marine raster area                 1934 km²
marine refined area                1922.25 km²
marine fraction                    42.64%
island holes                       1
shoreline length                   294 km
lakes                              2
regional marine outlets            35
potential marine outlets           101
enclosed below-sea basin marine?   false
engine invariants                  GREEN
hard constraints                   GREEN
```

Operator-visible assessment:
- coastline is refined below 1 km cells and follows terrain;
- fixed 4× design produces visible ~250 m stair steps, but not 1 km cell-block coastline;
- island hole remains intact;
- enclosed below-sea basin remains inland;
- regional/potential channels terminate at marine shoreline;
- no channel continues through open marine support;
- marine and lake geometry remain contractually/visually distinct.

Implementation recovery is complete:
- historical no-marine fingerprints restored;
- Strahler receives marine terminal support consistently;
- routing/accumulation remains the accepted no-marine upstream authority;
- C1 forcing remains exact-isolated through pre-marine normalization baseline;
- C2/C3 changes are limited to accepted canonical-water dependency propagation.

Current gate:
```text
H12-A implementation   OPERATOR REVIEW
PR #97                draft/open/unmerged
merge                 BLOCKED pending explicit ACCEPT / REJECT
```

Immediate next action:
1. explicit H12-A implementation ACCEPT / REJECT;
2. ACCEPT → freeze and merge PR #97;
3. REJECT → identify a concrete marine/coastline/topology defect;
4. do not expand H12-A into tides, waves, salinity, estuary or delta morphology.
