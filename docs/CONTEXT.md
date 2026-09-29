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
