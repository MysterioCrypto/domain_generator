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
