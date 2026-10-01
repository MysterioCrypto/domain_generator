# Rolling Context / Backlog

Этот файл — сжатая рабочая память проекта, а не журнал событий.

## Текущая опорная точка

```text
active:
  dev/0.2
  Terrain 0.2: ACCEPTED
  Hydrology 0.2: redesign in progress

kept river base:
  Priority-Flood
  MFD p=1.1 contributing area
  continuous MFD vector field
  dominant one-downstream skeleton
  H09-D2 additive source promotion
  lake supernodes / one canonical outlet

latest accepted direction:
  H09-D2 regional network = KEEP, not final Hydrology ACCEPT
  next = H09-E multiscale potential drainage hierarchy
```

`main` не является active development truth.

## Rejected / constrained history

- D8 canonical routing: rejected for lattice imprint.
- Two-receiver D∞ accumulation: rejected; grid bias remained in accumulation.
- Direct broad MFD threshold-mask channelization: rejected; 353 sources / 408 segments.
- H09-C thin skeleton: coherent but too sparse as sole drainage view.
- First H09-D multiplicative area-slope replacement: rejected; removed all normal headwaters.

These failures constrain the next work: do not reopen MFD, do not return to broad support as semantic channels, and do not replace the fixed-area baseline with a slope multiplier.

## H09-D2 regional base

Accepted design:
`docs/design/additive-terrain-aware-source-promotion-v0.2.md`

Same-world checkpoint:

```text
sources / semantic confluences: 16 / 4
segments:                        33
skeleton cells:                  610
river length:                    ~648.75 km
final grid-lock within 1°:       9.08%
baseline eligible cells:         283
terrain-promoted cells:          37
```

Automated state was green. Operator did not freeze Hydrology because the cumulative layout still looked somewhat procedural / under-branched, and exact sufficiency is better judged against real DEM + hydrography than fantasy map conventions.

Interpretation: H09-D2 is a good **regional river baseline**, but Hydrology should expose a denser potential drainage scaffold before climate/biomes decide what is perennial, seasonal, dry, or cartographically omitted.

## Accepted H09-E design

`docs/design/multiscale-drainage-hierarchy-v0.2.md`

Two nested scales:

```text
regional:
  current H09-D2 semantics, threshold T

potential:
  T_potential = 0.40 * T
  potential eligibility =
      unique_area >= T_potential
      OR regional eligibility
```

Potential channels use the same dominant one-downstream graph and continuous tracing. No new broad MFD semantic mask.

Compute Strahler order on the potential skeleton:

```text
headwater = order 1
equal-order merge m+m -> m+1
unequal merge -> max order
```

Lakes are transparent hierarchy supernodes: inflow orders aggregate through the accepted lake and continue at its one canonical outlet; no channel cells are drawn through lake interiors.

## Runtime boundary for H09-E

No public DomainData contract change yet.

Internal HydrologyState should gain:

```text
potential_channel_skeleton_mask
channel_strahler_order
potential_river_network
potential_segment_strahler_order
```

Current `river_network`, `stream_mask`, and water-depth semantics remain H09-D2 regional semantics. Potential hierarchy is a scaffold for later climate/biome classification and operator diagnostics.

## H09-E operator checkpoint

Exact same world:

```text
180 × 120 km
seed 2026091402
cell 1 km
regional threshold 250 km²
potential threshold 100 km²
same Terrain 0.2
same MFD
same accepted lakes
```

Need show:
1. regional H09-D2 rivers;
2. full potential drainage hierarchy;
3. regional over potential;
4. Strahler-order skeleton diagnostic;
5. accumulation + potential hierarchy;
6. regional/potential counts, lengths, order histogram, max order, grid-lock and regional coverage.

Primary acceptance question: does the potential network read as a plausible dendritic hierarchy without returning to H09-B parallel noise?

## H09-E implementation checkpoint

Accepted multiscale design is implemented in PR #72.

Representative same-world result:

```text
regional H09-D2 (unchanged):
  sources / confluences: 16 / 4
  segments:               33
  skeleton cells:         610
  total length:           ~648.75 km
  final grid-lock 1°:     ~9.08%

potential hierarchy:
  threshold:              100 km² = 0.40 × regional T
  sources:                43
  realized confluences:   10
  segments:               66
  skeleton cells:         783
  total vector length:    ~877.03 km
  final grid-lock 1°:     ~8.66%
  max Strahler order:     3
  regional coverage:      610 / 610 = 100%
```

Strahler skeleton-cell distribution:

```text
order 1: 483 cells
order 2: 266 cells
order 3:  34 cells
```

### Trace/skeleton consistency defect found and fixed

Initial H09-E exposed six raster-proposed confluence markers that were not realized as true merges by continuous MFD vector traces:

```text
initial vector confluence indegrees:
  indegree 0: 1
  indegree 1: 5
  indegree 2: 9
  indegree 4: 1
```

A strict attempt to force free streamlines to declared raster terminals was rejected during implementation because a continuous trace could physically enter a different accepted lake than the dominant raster projection declared.

Final correction keeps continuous routing authoritative for final vector topology and normalizes only false semantic confluence markers after tracing:

- indegree 0 confluence marker and its unused downstream stub are removed;
- indegree 1 marker is collapsed by concatenating its upstream/downstream continuous segments;
- indegree >= 2 merge remains a semantic confluence;
- no downstream bifurcation is introduced.

Final topology:

```text
confluence indegrees:
  2: 9
  4: 1

confluences with indegree < 2: 0
nodes with outdegree > 1:      0
```

This reduced the potential network from 72 to 66 semantic segments without deleting source traces or changing regional H09-D2 semantics.

Automated status:
- representative H09-E: engine invariants green;
- hard constraints green;
- full pytest push run green;
- regional network and water-depth authority unchanged.

## Assessment against real-network references

The H09-E potential scaffold is intentionally scale-dependent. This is consistent with USGS guidance that Strahler order changes with cartographic source density, and with HydroSHEDS comparisons showing that finer DEM/network extraction produces denser river networks.

The potential raster hierarchy is:

```text
order-1 cells / all hierarchy cells ≈ 61.7%
```

As a loose external plausibility check, USGS reports that order-1 streams account for 57% of Potomac network length. This is not a calibration target—the basin and extraction scale differ—but it supports that H09-E is no longer obviously deficient in first-order hierarchy.

Visual assessment:
- substantially more dendritic than regional H09-D2 alone;
- far below H09-B's parallel-channel explosion;
- higher-order trunks align with strong accumulation corridors;
- remaining raster stair-step structure is primarily an internal skeleton diagnostic, while final vector geometry stays low-bias;
- lakes now stand out more clearly as the next likely source of procedural/artificial appearance.

H09-E river-hierarchy slice is **formally ACCEPTED by the operator**. Freeze MFD + H09-D2 regional rivers + H09-E potential hierarchy unless a later concrete defect directly implicates them.

## New operator observation: rivers feel unfinished at the ends

After reviewing H09-E from GitHub Actions, the operator identified a more precise residual visual issue:

> the body of the river is no longer the main problem; a smooth segment can feel unfinished because it has neither diffuse headwater roots nor a developed receiving end/delta where such a receiver is actually present on the map.

Interpretation:

- do **not** reopen the main continuous river body because of this;
- diffuse headwater roots / minor tributaries depend on potential low-order drainage plus later climate/biome visibility;
- delta / estuary / alluvial-fan semantics require knowing the receiving environment;
- a river leaving the current domain remains a `domain_outlet`, not a fake delta;
- if a real lake/coast/other receiving water exists, endpoint morphology can be added in a later hydro-surface finishing pass.

This is therefore a **deferred completion layer**, likely after climate/biome/surface semantics are available, not part of the current river-hierarchy acceptance criterion.

## Operator decision: H09-E ACCEPT

The operator explicitly accepted the H09-E river-hierarchy slice.

Frozen for the next bounded task:

```text
Priority-Flood
MFD p=1.1 accumulation
continuous MFD vector field
H09-D2 regional rivers
H09-E potential hierarchy
Strahler ordering
continuous vector geometry
false-confluence normalization
```

Do not retune these during the lake pass.

## Next

```text
1. Design bounded lake count / size / shape / catchment pass.
2. INV-006 design gate before production implementation.
3. Representative same-world lake checkpoint.
4. Operator ACCEPT / REJECT for lake slice.
5. Then Hydrology 0.2 final review.
6. Later climate/biomes may finish low-order headwaters and receiving-end morphology.
```


## Lake diagnostic checkpoint before semantic changes

Diagnostic-only instrumentation was added on the implementation branch before changing lake semantics.

Same H09-E world:

```text
domain area:              21,600 km²
accepted routing lakes:   13
lake raster areas:
  8, 13, 21, 25, 32, 36, 38, 52, 70, 103, 114, 156, 222 km²
total raster lake area:   890 km²
limnicity:                ~4.12%
median lake area:         38 km²
lakes >100 km²:           4
catchment/lake area:      ~5.6 ... 136
```

The four largest lakes have catchment/lake ratios ~7.6, 8.9, 13.5, 27.8. This is not enough evidence to arbitrarily shrink/delete them.

Important implementation fact:

```text
current visible lake geometry
= exact union of accepted 1 km raster-cell squares
```

So raster/blocky shoreline is a confirmed upstream semantic geometry limitation, not merely renderer style.

## Proposed H10-A design gate

PR #78:
`docs/design/lake-shoreline-morphology-v0.2.md`

Status: **ACCEPTED by operator**.

Bounded idea:

```text
accepted routing lake basin
→ deterministic 4× sub-cell terrain-aware shoreline
→ refined vector HydroFeature geometry
→ exact river inflow/outlet positions on refined shoreline
```

Keep in H10-A:

- same accepted routing lakes;
- same canonical outlet receiver cells;
- same MFD / accumulation;
- same H09-D2 regional network semantics;
- same H09-E potential hierarchy semantics;
- no global lake-count or size-distribution fitting.

Reason for not shrinking/count-tuning yet:
- global lake density varies strongly by geomorphic history;
- current catchment ratios are not obviously pathological;
- first isolate the confirmed raster shoreline defect.

H10-A must report raster area vs refined area, catchment ratio, shoreline development, and all lake/river endpoint consistency.

Stop rule:
if refined shorelines still leave obviously oversized/compound lakes, the next bounded design is nested-depression hierarchy / partial-fill semantics, not arbitrary area clipping.

Operator explicitly accepted PR #78 / H10-A design. Production implementation may proceed. Heavy GitHub Actions artifacts should not be downloaded into the chat/container unless the operator explicitly asks; inspect workflow logs, compact previews, and statistics first.


## H10-A implementation slice 1

Implemented on PR #72 implementation branch:

```text
accepted routing lake basin
→ deterministic 4× sub-cell sampling
→ terrain-aware wet sub-cells at 250 m scale
→ canonical refined RegionSet shoreline
```

Legacy materialization remains unchanged when no terrain is supplied; Core 0.2 can now request refined shoreline geometry and use refined vector area in LakeProperties.

This is only the first implementation slice. Still pending before H10-A checkpoint:

- bind Core 0.2 generation to refined lake features;
- project lake inflow/outlet nodes to refined shoreline;
- add L01–L08 validation/tests;
- render H10-A diagnostics.

Heavy GitHub Actions artifacts are not to be downloaded into the chat/container unless explicitly requested by the operator.


## H10-A implementation slice 2

Implemented on PR #72 implementation branch:

```text
refined lake RegionSet
→ canonical HydroFeature area
→ lake_inflow endpoint projected to refined shoreline
→ lake_outlet endpoint projected to refined shoreline
→ regional + potential networks use the same refined lake geometry
```

Core 0.2 now requests 4× shoreline refinement during lake materialization. Legacy materialization without terrain remains unchanged.

Still pending before H10-A checkpoint:

- automated L01–L08 guards / regression tests;
- validate all v0.2 lake endpoints against refined boundaries;
- H10-A old-vs-refined lake diagnostics and close-ups;
- same-world Actions checkpoint and operator review.

Heavy Actions artifacts remain remote unless the operator explicitly requests a download.


## H10-A implementation slice 3

Added automated guards on the implementation branch:

```text
L01/L03:
  refined shoreline deterministic
  refined area > 0
  refined area <= routing-basin area

L05/L06:
  lake_inflow and lake_outlet semantic nodes lie on refined shoreline

L08:
  raster lake water-depth ownership remains unchanged
```

Core v0.2 validation now includes:
- refined lake feature ids/areas valid;
- lake inflow/outlet endpoints on referenced refined shorelines.

Pending:
- CI result for these guards;
- H10-A visual diagnostics / same-world checkpoint;
- operator review.


## H10-A implementation slice 4

Added the operator-visible H10-A checkpoint diagnostics on the implementation branch:

```text
13-lake-raster-vs-refined.png
14-refined-lakes-regional-rivers.png
15-refined-lakes-potential-hierarchy.png
16-lake-contact-sheet.png
17-lake-endpoints.png
```

Checkpoint statistics now report:
- routing-basin area vs refined shoreline area;
- refined/routing area ratio;
- refined perimeter;
- refined shoreline-development index;
- catchment relation using refined visible lake area.

GitHub Actions compact previews are configured to emit the H10-A lake views into workflow logs. Full artifacts remain remote and must not be downloaded into the chat/container unless explicitly requested.


## H10-A checkpoint render fix

The first H10-A visual workflow run reached rendering successfully but failed in statistics post-processing because the diagnostic sort still referenced the pre-H10 field name `area_km2`. The code now sorts by `routing_basin_area_km2`.

No semantic hydrology/lake behavior changed in this fix. Next step remains rerun CI/checkpoint and inspect only logs/compact previews unless a full artifact is explicitly requested.


## H10-A same-world checkpoint

Implementation commit checkpoint:
`34d33ae8d58af31023b00a17758c32aefb1665fb`

GitHub Actions:
- H10-A checkpoint workflow: GREEN;
- full pytest: GREEN;
- engine invariants: GREEN;
- hard constraints: GREEN.

No full artifact was downloaded into the chat/container. Review used workflow logs + compact previews only.

Representative lake metrics:

```text
accepted routing lakes:        13
routing-basin total area:      890.0 km²
refined visible total area:    836.5625 km²
refined/domain area:           ~3.873%
refined/routing total ratio:   ~0.940

per-lake refined/routing ratio:
  min:                         0.859
  median:                      0.902
  max:                         0.965
```

Largest lakes:

```text
routing → refined
222 → 214.125 km²
156 → 149.000 km²
114 → 108.625 km²
103 →  96.938 km²
 70 →  65.438 km²
```

Visual checkpoint:
- exact 1 km raster-cell shoreline is gone from semantic HydroFeature geometry;
- lake inflow/outlet nodes now lie on refined shoreline and validation passes;
- 250 m sub-cell reconstruction reduces edge coarseness and area by ~6% overall;
- however large lakes retain broadly rounded / basin-fill silhouettes and remain visually prominent;
- contact-sheet close-ups still show noticeable 250 m stair-step geometry;
- therefore H10-A fixes a confirmed geometry defect but does **not** obviously solve the larger question of whether full-spill basins are too broad/compound.

Assistant assessment:
- KEEP refined shoreline semantics and exact endpoint alignment;
- H10-A alone is not yet a convincing final lake-slice acceptance;
- if operator agrees, next bounded design should investigate nested-depression / partial-fill semantics rather than globally clipping lake area or reopening accepted river hierarchy.

Heavy Actions artifacts remain remote unless explicitly requested.


## Operator decision after H10-A

Operator accepted the proposed next step: try nested-depression analysis.

Recorded decision:

```text
H10-A refined shoreline semantics: KEEP
H10-A as final lake solution: REJECT
H10-B nested-depression diagnostic: ACCEPTED design
```

PR #79 merged to dev/0.2.

Important semantic correction before implementation:
a partial lake with a maintained downstream surface outlet is not physically self-consistent without a water-balance/loss model. Therefore H10-B is diagnostic first, not an immediate partial-fill implementation.

H10-B will determine whether the suspicious broad lakes are:
- genuinely compound nested depressions with multiple significant child basins; or
- single broad basins implied by Terrain 0.2.

Frozen during H10-B:
- all accepted river routing/hierarchy semantics;
- lake ids and canonical outlets;
- H10-A refined shorelines;
- raster water-depth semantics.

Heavy Actions artifacts remain remote unless explicitly requested.


## H10-B implementation slice 1

Implemented on PR #72 implementation branch:

- new internal module hydrology/depression_hierarchy.py;
- deterministic level-set sweep inside each accepted routing lake;
- equal-elevation cells are activated as one batch before merge interpretation;
- leaf depressions and merge/meta-depressions are recorded as an acyclic tree;
- each node stores minimum, birth level, spill level, area-at-spill and storage proxy;
- significance uses only the existing lake_min_area / lake_min_depth thresholds;
- no lake/routing/river semantics changed.

Added synthetic guards for:
- deterministic two-leaf merge;
- equal-elevation plateau stability;
- single-bowl one-root hierarchy.

Pending:
- CI;
- same-world hierarchy statistics;
- H10-B contact sheet / large-lake close-ups;
- operator interpretation.

Heavy Actions artifacts remain remote unless explicitly requested.


## H10-B implementation slice 1b

Nested-depression diagnostic nodes now retain deterministic birth/saddle cell sets in addition to birth elevation. This supports the accepted H10-B checkpoint requirement to show internal merge locations, including equal-elevation saddle plateaus.

No production hydrology semantics changed.


## H10-B implementation slice 2

Added same-world operator diagnostics on the implementation branch:

- nested hierarchy summary for every accepted lake;
- significant leaf basin area/storage fractions;
- contact sheet for all 13 lakes;
- dedicated close-ups for the four largest lakes;
- leaf minima and internal merge/saddle cell markers;
- H10-B JSON diagnostics embedded in statistics.json;
- compact Actions previews updated to H10-B views.

No full Actions artifact is to be downloaded into the chat/container without explicit operator request.

Pending:
- CI/checkpoint result;
- inspect H10-B statistics and compact previews;
- decide whether the broad lakes are compound or single-basin.


## H10-B same-world result

Implementation checkpoint:
`1e572096f7d67aacbae37c10c0380533397754d7`

CI:
- H10-B checkpoint workflow: GREEN;
- pull-request pytest: GREEN;
- push pytest: GREEN;
- engine invariants: GREEN;
- hard constraints: GREEN.

No full Actions artifact was downloaded into the chat/container. Review used workflow logs + compact previews only.

### Structural result

All 13 accepted routing lakes produced the same hierarchy pattern:

```text
node_count:                    1
leaf_count:                    1
threshold_significant leaves:  1
merge_node_count:              0
multiple significant children: false
largest leaf area fraction:    1.0
largest leaf storage fraction: 1.0
```

This includes all four largest lakes:

```text
222 km² → one basin, no internal merge
156 km² → one basin, no internal merge
114 km² → one basin, no internal merge
103 km² → one basin, no internal merge
```

Therefore the H10-B hypothesis is falsified for this representative world:

> the broad lake shapes are NOT caused by Priority-Flood merging multiple meaningful nested sub-basins.

The broadness is already present in the underlying Terrain 0.2 basin geometry and/or in the hydrology-only assumption that every threshold-qualified depression is represented at full spill.

### Consequence

Do not implement nested-depression splitting or partial-fill cascades for Core 0.2 on the basis of this checkpoint. There is no structural evidence for it.

Keep:
- H10-A refined 250 m shoreline geometry;
- exact lake inflow/outlet contact;
- current one-supernode / one-outlet routing semantics;
- accepted H09-E river hierarchy.

Remaining questions such as whether a basin is a perennial lake, seasonal lake, wetland, playa or dry depression require climate/surface/water-balance context and are deferred.

Assistant recommendation: treat H10-A + current full-spill routing basins as the **Hydrology 0.2 base**, stop lake algorithm tuning here, and move to final Hydrology operator review. Reopen Terrain 0.2 only if a later layer provides a concrete cross-layer defect, not because a neutral lake-rich representative world looks unusual.

Heavy Actions artifacts remain remote unless explicitly requested.


## Operator decision: Hydrology 0.2 ACCEPT

The operator formally accepted Hydrology 0.2 without separately reopening the lake artifact.

Accepted Hydrology 0.2 base:

```text
Priority-Flood conditioning
MFD p=1.1 contributing area
continuous MFD vector field
H09-D2 regional river network
H09-E potential drainage hierarchy
Strahler ordering
one-supernode / one-outlet lake routing
H10-A refined shoreline geometry
exact river/lake shoreline contacts
```

H10-B remains diagnostic evidence only: nested-lake splitting is not part of production semantics.

Hydrology is now frozen unless a later cross-layer defect provides concrete evidence requiring reopening it.

Artifact workflow policy:
- do not download heavy Actions artifacts into chat/container unless explicitly requested;
- when an operator artifact is needed, provide the direct GitHub Actions workflow-run link so the operator can download it from GitHub;
- routine assistant review should use logs, statistics and compact previews.

## Next active layer

Move to Core 0.2 Surface / climate / biome foundation.

Before production implementation:
- inspect the existing Surface 0.1 semantics/contracts;
- write a bounded INV-006 design;
- preserve accepted Terrain/Hydrology;
- include operator-visible diagnostics before acceptance.

Deferred hydro finishing to revisit only after this layer:
- standing lake vs wetland/playa/dry depression;
- perennial vs seasonal low-order drainage;
- diffuse headwater roots;
- estuary/delta/fan morphology where a receiving environment is known.


## Hydrology implementation merge

PR #72 merged into dev/0.2 after formal operator ACCEPT.

Hydrology 0.2 is now part of the active development baseline, not an open implementation branch.

## C1 proposed design gate

PR #80:
`docs/design/annual-climate-forcing-v0.2.md`

Status: **PROPOSED / awaiting explicit operator ACCEPT / REJECT**.

Bounded C1 proposal:

```text
Terrain 0.2 + Hydrology 0.2
        ↓ read-only
annual mean temperature
  - explicit regional mean
  - north/south macro gradient
  - 6.5 C/km elevation lapse experiment
  - deterministic coherent noise

annual precipitation
  - explicit domain mean
  - explicit moisture-transport bearing
  - continuous upwind terrain exposure
  - windward / lee contrast
  - deterministic coherent noise
        ↓
SurfaceState climate forcing fields
```

C1 deliberately does **not** rewrite existing moisture / vegetation yet. That is reserved for C2 after operator acceptance of the climate forcing fields.

Proposed schema 0.2 climate recipe has no hidden defaults. The current design adds explicit mean temperature, north-south thermal delta, precipitation mean, moisture transport bearing, orographic scale/strength and noise controls.

Operator artifact policy is now part of working context:
- heavy Actions artifacts stay on GitHub unless explicitly requested;
- when an operator checkpoint is generated, provide the direct workflow-run link for download;
- assistant routine review uses statistics / logs / compact previews.


## Operator decision: C1 Annual Climate Forcing ACCEPT

The operator explicitly accepted PR #80 / annual-climate-forcing-v0.2.

PR #80 merged into dev/0.2. Production implementation may proceed.

Frozen during C1:
- Terrain 0.2;
- Hydrology 0.2;
- existing moisture / vegetation semantics;
- existing surface feature biases.

C1 implementation target:
- annual_mean_temperature_c;
- annual_precipitation_mm;
- explicit schema/plan 0.2 climate recipe;
- deterministic replay;
- operator-visible climate checkpoint.

Heavy Actions artifacts remain remote; provide direct workflow-run links for operator download instead of copying large artifacts into chat.


## C1 implementation slice 1 — contracts

PR #81 opened on branch `impl/v0.2-surface-climate`.

Implemented:
- explicit `ClimateSpec` / `PlanClimate`;
- schema/plan 0.2 requires a climate recipe;
- schema/plan 0.1 forbids climate recipe;
- Core 0.1 semantic fingerprints explicitly omit the new optional climate field, preserving legacy fingerprint semantics;
- v0.2 compiler injects the accepted climate recipe after compiling the legacy-compatible shadow;
- representative Terrain/Hydrology request now carries an explicit C1 climate recipe.

No climate fields are generated yet in this slice. Terrain/Hydrology and existing moisture/vegetation remain unchanged.


## C1 implementation slice 2 — climate fields

Implemented on PR #81:

- deterministic annual mean temperature field;
- fixed experimental lapse rate 6.5 C/km around domain mean elevation;
- explicit north/south thermal macro-gradient;
- independent coherent temperature noise;
- deterministic annual precipitation field;
- explicit moisture-transport bearing;
- continuous bilinear upwind terrain sampling;
- exponential upwind kernel over 4 orographic scales;
- windward/lee log-weight contrast;
- land-mean precipitation normalization;
- independent coherent precipitation noise;
- SurfaceState carries climate fields for Core 0.2 while Core 0.1 remains climate-free;
- Core 0.2 DomainData exports canonical `temperature` and `annual_precipitation`;
- existing moisture and vegetation computation remains unchanged in C1.

Implementation detail:
if a domain contains no dry land cells, precipitation normalization falls back to the whole domain rather than failing. Normal mixed land/water domains normalize on land only as designed.

Pending:
- C01–C09 tests / regression guards;
- schema snapshots / any contract fixture updates revealed by CI;
- operator-visible C1 checkpoint.

Heavy Actions artifacts remain remote; future checkpoint response must include direct workflow-run link.


## C1 implementation slice 3 — guardrails

Added dedicated C01–C09 climate tests on PR #81:

- C01 flat/no-noise uniform climate baseline;
- C02 6.5 C/km elevation lapse;
- C03 north/south world-space macro-gradient;
- C04 windward > lee precipitation on a synthetic ridge;
- C05 rotational consistency when terrain + moisture transport rotate together;
- C06 requested land-mean precipitation conservation;
- C07 deterministic replay / attempt-noise variation;
- C08 Terrain/Hydrology upstream immutability;
- C09 C1 compatibility: existing moisture and vegetation are unchanged.

Existing Core 0.2 terrain/hydrology test fixtures were updated with explicit neutral climate recipes. Application-boundary test now expects climate field files in the canonical bundle.

Known remaining maintenance item:
schema snapshots must be regenerated/updated for the new ClimateSpec / PlanClimate contract structure.


## C1 implementation slice 4 — schema snapshots

Updated Core v0.2 schema snapshots for:
- DomainSpec / ClimateSpec;
- GenerationPlan / PlanClimate;
- GenerationRequest transitive DomainSpec structure.

The schema change is structural only; conditional requirements (0.2 requires climate, 0.1 forbids it) remain enforced by model validators rather than JSON Schema conditionals.

Pending:
- CI stabilization;
- any C01–C09 implementation defects revealed by tests;
- C1 operator checkpoint.


## C1 implementation slice 5 — operator checkpoint

Added C1-A operator checkpoint tooling on PR #81:

Artifacts:
- 01-terrain-temperature.png
- 02-terrain-precipitation.png
- 03-precipitation-wind.png
- 04-along-wind-cross-section.png
- 05-temperature-elevation.png
- statistics.json

Workflow:
`.github/workflows/surface-v02-c1-checkpoint.yml`

The workflow uploads a GitHub Actions artifact named `surface-v02-c1` and emits compact previews into logs.

Operator artifact policy:
- do not materialize/download the full artifact into chat unless explicitly requested;
- once the run is green, provide the direct workflow-run URL so the operator can download the artifact from GitHub.


## C1-A same-world checkpoint

Implementation checkpoint:
`c3bd467acab0365a0ba75afd9d1d6b723a5d0e14`

GitHub Actions:
- C1 checkpoint workflow: GREEN;
- pull-request pytest: GREEN;
- push pytest: GREEN.

Direct operator workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36827241394`

Artifact:
`surface-v02-c1`

The full artifact was NOT downloaded into chat/container. Assistant inspection used workflow statistics and compact previews only.

Representative recipe:

```text
mean temperature:                 8 °C
north-minus-south delta:         -4 °C
temperature noise amplitude:      1.5 °C
mean land precipitation:        900 mm/year
moisture transport:              90° / eastward
orographic scale:                45 km
orographic strength:              2.0
precipitation log-noise:          0.22
climate noise scale:             60 km
```

Representative statistics:

```text
temperature:
  min / p05 / median / p95 / max
  1.64 / 4.41 / 8.19 / 10.52 / 11.50 °C
  mean ~7.91 °C
  elevation correlation ~-0.774

precipitation:
  land mean exactly 900 mm/year
  min / p05 / median / p95 / max
  259 / 473 / 796 / 1647 / 3954 mm/year
  whole-domain mean ~883 mm/year
  std ~363 mm/year

synthetic ridge:
  windward ~2352 mm/year
  lee       ~730 mm/year
  ratio     ~3.22
  C04       PASS
```

Visual assessment from compact previews:
- temperature forms a smooth cool mountain belt plus regional gradient/noise, with no obvious lattice imprint;
- precipitation responds coherently to the massif and produces visible rain-shadow structure;
- the along-wind cross-section confirms precipitation rises on approaches/crests and falls sharply into lee terrain;
- precipitation hotspots near major crests are visually strong and reach ~4,000 mm/year. This is not automatically wrong, but it is the main C1-A sufficiency question for a setting-agnostic regional baseline.

Assistant recommendation:
**review C1-A visually before any retuning.** The mechanism is coherent enough to keep; whether the representative orographic contrast is too strong is an operator-facing calibration judgment.

Do not merge PR #81 until explicit operator ACCEPT / REJECT.


## Operator decision: C1-A ACCEPT

The operator formally accepted C1 annual climate forcing.

Acceptance note:
the operator considers the maps coherent enough and has no climate-domain blocker to raise; acceptance does not claim climate-model expert validation.

PR #81 merged into dev/0.2.

Accepted C1 semantics:

```text
explicit regional annual temperature forcing
+
explicit regional annual precipitation forcing
+
terrain-driven lapse / orographic redistribution
```

Important scope boundary now frozen:
- C1 does not infer remote oceans or atmospheric moisture sources from map water;
- the requested mean annual precipitation represents regional atmospheric moisture supply entering the modeled domain;
- rivers and ordinary lakes are not direct precipitation sources;
- future global/continental atmospheric transport may supersede this boundary in another scale/model, but not inside Core 0.2 regional C1.

Do not retune C1 merely because a later biome looks unexpected. First diagnose whether the defect belongs to climate forcing, effective moisture, vegetation response, or biome classification.

## Next active design question

C2 should replace the legacy Surface 0.1 moisture heuristic with a climate-aware **effective surface moisture** layer while keeping C1, Terrain and Hydrology frozen.

The next bounded design must distinguish:
- atmospheric precipitation;
- evaporative/climatic demand;
- local hydrologic access / capillary-wetness proxy;
- terrain drainage/slope;
- effective surface moisture.

Vegetation / biome classification should remain a later step unless the moisture field itself is accepted first.


## C2-A proposed design gate

PR #82:
`docs/design/effective-surface-moisture-v0.2.md`

Status: **PROPOSED / awaiting explicit operator ACCEPT / REJECT**.

C2-A proposal replaces only Core 0.2 canonical moisture semantics:

```text
C1 precipitation + temperature
        ↓
Holdridge-inspired annual PET proxy
        ↓
climatic wetness
        +
canonical-water proximity
        +
climate-gated contributing-area concentration
        ↓
slope retention
        ↓
effective surface moisture [0,1]
```

Key bounded choices:
- no new arbitrary moisture noise in Core 0.2;
- existing water_moisture_boost / decay retain meaning for actual-water proximity;
- accepted stream threshold scales the contributing-area signal;
- slope retention uses a fixed cos²(slope) curve rather than a new tuning parameter;
- canonical water remains moisture = 1;
- Core 0.1 moisture remains unchanged;
- vegetation_density is intentionally kept bit-identical during C2-A using the temporary legacy-moisture path internally.

External rationale used for the design:
- Holdridge annual PET approximation ~58.93 × biotemperature;
- FAO water-balance separation of precipitation, evapotranspiration, runoff/drainage and storage.

C2-A is intentionally an annual effective-moisture index, not literal soil volumetric water content and not a monthly soil-water simulation.

Do not implement production C2 until operator accepts PR #82.


## Operator decision: C2 Effective Surface Moisture ACCEPT

The operator explicitly accepted PR #82 / effective-surface-moisture-v0.2.

PR #82 merged into dev/0.2. Production implementation may proceed.

Frozen during C2-A:
- Terrain 0.2;
- Hydrology 0.2;
- C1 annual temperature and precipitation;
- current vegetation_density semantics;
- Core 0.1 moisture/vegetation behavior.

C2-A implementation target:
- replace only Core 0.2 canonical moisture with climate-aware effective moisture;
- keep canonical water exactly moisture=1;
- combine climatic wetness, actual-water proximity, climate-gated catchment concentration and slope retention;
- no extra moisture noise layer;
- preserve legacy vegetation via temporary compatibility path until C3.

Heavy Actions artifacts remain remote; operator checkpoints should provide direct workflow-run links.
