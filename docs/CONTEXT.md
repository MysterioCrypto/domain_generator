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

## Current checkpoint — C2-B Water-Proximity Retune

Normative design: `docs/design/effective-surface-moisture-v0.2.md`.

Design status: ACCEPTED.
Implementation: draft PR #83, branch `impl/v0.2-effective-surface-moisture`.
Current PR head: `d4c9eb947d7491352a3f05d96153d93318f7c440`.

Latest green operator workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36831586933`

Artifact:
`surface-v02-c2`

Do not download heavy Actions artifacts into chat/container unless the operator explicitly asks. Routine assistant review should use workflow logs, statistics and compact previews. When the operator needs the artifact, provide the direct workflow-run link.

### C2 semantics

Core 0.2 canonical `moisture` is now an annual **effective surface moisture index**, not literal volumetric soil moisture.

Climatic wetness:

```text
T_bio = clamp(T, 0, 30)
PET_proxy_mm = 58.93 * T_bio
climatic_wetness = P / (P + PET_proxy_mm)
```

Local hydrology:

```text
water_proximity =
    water_moisture_boost * exp(-distance_to_water / water_moisture_decay_km)

catchment_signal =
    A / (A + stream_threshold_km2)

climate_gated_catchment =
    climatic_wetness * catchment_signal

local_hydrology =
    max(water_proximity, climate_gated_catchment)
```

Combination:

```text
pre_slope =
    climatic_wetness
    + (1 - climatic_wetness) * local_hydrology

slope_retention = cos(slope)^2

effective_moisture =
    clamp(pre_slope * slope_retention + feature_moisture_bias, 0, 1)

canonical water = 1 exactly
```

No additional Core 0.2 moisture noise layer.

Compatibility boundary:
- Core 0.1 moisture/vegetation unchanged;
- C2-A vegetation remains deliberately legacy-compatible and is **not** yet driven by effective moisture;
- C3 will redesign vegetation only after C2 moisture is accepted.

### C2 automated state

M01–M10 guards are GREEN:
- precipitation ordering;
- thermal-demand ordering;
- canonical-water exactness;
- riparian decay;
- catchment monotonicity;
- slope drainage;
- dtype/range/replay;
- Terrain/Hydrology/C1 upstream immutability;
- C2-A vegetation compatibility;
- Core 0.1 compatibility.

Latest PR pytest and C2 workflow are GREEN.

### C2-A representative result

Land statistics:

```text
climatic wetness:
  p05 / median / p95   0.500 / 0.628 / 0.863
  mean                 0.642

effective moisture:
  min                  0.520
  p05 / median / p95   0.619 / 0.728 / 0.887
  max                  0.979
  mean                 0.734
  land >= 0.8          ~18.0%
  land <= 0.2          0%

local signals:
  water proximity mean ~0.249
  gated catchment mean ~0.039
  gated catchment p95  ~0.149

slope retention:
  mean                 ~0.99875
  min                  ~0.9777

effective-moisture correlations:
  precipitation         +0.712
  temperature           -0.691
  distance to water     -0.397
  legacy moisture       +0.281
  log1p accumulation    -0.036
```

Interpretation:
- macro wet/dry structure is now climate-driven rather than legacy distance/noise-driven;
- catchment contribution is subordinate and does not turn every drainage line into a saturated stripe;
- slope retention is weak on this 1 km representative terrain because slopes are gentle;
- the representative climate is deliberately cool/wet, so absence of very dry cells is not itself a defect;
- the main unresolved visual question is **actual-water proximity**: inherited `water_moisture_decay_km = 8` creates broad riparian wet halos around canonical rivers/lakes.

### C2-A operator decision — REJECT

C2-A is rejected on one bounded visual/physical defect only:

`water_moisture_decay_km = 8` makes actual-water influence extend as a broad, nearly uniform-width halo around canonical rivers and lakes.

Culprit assignment:
- **actual-water proximity scale: REJECTED / retune required**;
- climatic wetness: KEEP;
- catchment contribution: KEEP;
- slope retention: KEEP;
- effective-moisture combination semantics: KEEP.

This does not reopen Terrain 0.2, Hydrology 0.2 or C1.

The rejection is a calibration/spatial-scale correction inside the already accepted C2 design, not a return to legacy distance-to-water + noise moisture.

Repository-state audit before C2-B:
- PR #83 branch is 6 implementation commits ahead of its merge base;
- `dev/0.2` is 1 documentation-only commit ahead of that same merge base;
- therefore the implementation branch must be synchronized with current `dev/0.2` before further C2-B work;
- the C2 code/test/workflow slice itself is intact and green.

Next bounded experiment: reduce only the representative actual-water decay scale and rerun the same world. No other C2 component is to be retuned in the same slice.

## Current decision gate

```text
Terrain 0.2                 ACCEPTED
Hydrology 0.2               ACCEPTED
C1 annual climate           ACCEPTED
C2 effective moisture       C2-A REJECTED / C2-B RETUNE
```

Immediate next action:
1. synchronize PR #83 implementation branch with current `dev/0.2`;
2. retune only `water_moisture_decay_km` on the representative same-world checkpoint;
3. rerun automated guards + operator-visible C2 checkpoint;
4. if the corrected scale is accepted, freeze C2 and merge PR #83;
5. only then open INV-006 design for C3 vegetation / biome readiness.

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
