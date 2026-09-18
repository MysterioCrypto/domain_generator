# Channel Skeleton Extraction v0.2

Status: **accepted experimental design gate**  
Target branch: `dev/0.2`  
Operator decision: H09-B MFD accumulation kept as promising; final semantic network rejected because channel extraction over-fragmented the broad MFD support field.

## 1. Problem

The H09-B MFD experiment reduced directional lattice bias in the underlying flow field and final vector geometry, but it produced an unusable semantic river graph:

```text
MFD accumulation
→ broad threshold support
→ many adjacent threshold-crossing cells
→ hundreds of semantic sources
→ parallel / redundant rivers
```

The failure is therefore no longer primarily the accumulation field. It is the assumption that every threshold-supported raster cell can participate directly in semantic channel topology.

A river channel is a one-dimensional semantic object embedded inside a broader contributing-area field. Diffuse MFD hillslope flux and channel topology must be separated.

## 2. External reference pattern

This bounded redesign follows an established GIS/hydrology pattern rather than pure image thinning.

GRASS `r.stream.extract` supports MFD flow accumulation but extracts a thinned stream network from it; it also supports switching to single-flow behaviour for concentrated flow and pruning short first-order streams. It explicitly treats stream extraction as a distinct step after accumulation.

The Core implementation does not copy GRASS internals, but adopts the same separation:

```text
diffuse hillslope transport != semantic channel graph
```

## 3. Scope

Keep:

- Terrain 0.2;
- Priority-Flood conditioning;
- MFD p=1.1 contributing-area transport;
- MFD-derived continuous flow vector field;
- accepted-lake supernodes and one canonical spill outlet;
- `flow_accumulation_km2` as canonical contributing-area diagnostic;
- raw threshold support as a diagnostic layer;
- world-space vector tracing for final RiverSegment geometry.

Replace only semantic channel extraction:

```text
raw threshold support
→ dominant channel-routing graph
→ unique channel-source threshold crossings
→ thin downstream skeleton
→ semantic sources / confluences
→ continuous world-space traces
```

No artistic smoothing is allowed as a substitute for topology.

## 4. Dominant channel-routing graph

MFD remains authoritative for contributing area. Channel topology gets a separate deterministic single-downstream projection used only for channel extraction.

For each ordinary cell with positive MFD receivers:

1. prefer receivers that remain inside the raw threshold support when the current cell is supported;
2. score each candidate by transmitted contributing area:

```text
channel_flux_i = accumulation(current) * fraction_i
```

3. tie-break by receiver accumulation, then fixed neighbour direction order;
4. choose exactly one downstream channel receiver.

If a supported cell has no supported positive receiver, follow the strongest positive MFD receiver until support resumes or a terminal/lake is reached. This prevents an artificial interior channel dead end caused only by MFD dispersion.

This projection is **not** a replacement for MFD accumulation. It exists only to define a one-dimensional channel topology.

## 5. Unique source initiation area

The H09-B failure occurred because overlapping MFD catchments allowed many neighbouring cells to exceed the same `stream_threshold_km2`.

For source initiation only, compute a unique contributing area on the dominant channel-routing graph:

```text
channel_area(cell)
  = own cell area
  + Σ channel_area(unique dominant upstream cells)
```

This partitions upstream cells instead of counting overlapping fractional catchments several times.

A normal channel source is initiated at a cell where:

```text
channel_area(cell) >= stream_threshold_km2
AND
every dominant upstream predecessor has channel_area < stream_threshold_km2
```

This restores the intended interpretation of `stream_threshold_km2`: a source should represent roughly one minimum-sized unique drainage basin, not one of many overlapping MFD threshold crossings.

Final RiverSegment `catchment_area_km2` continues to use canonical MFD contributing area, not the source-initiation helper area.

## 6. Thin skeleton

Starting from all accepted source cells plus qualifying lake outlets, follow the dominant channel receiver downstream.

The union of these paths is the semantic raster skeleton.

Properties:

- one cell wide by construction;
- every ordinary skeleton cell has at most one downstream skeleton receiver;
- paths may merge but may not bifurcate;
- confluence = skeleton cell with at least two upstream skeleton predecessors;
- no ordinary interior skeleton dead ends;
- lake interiors contain no skeleton;
- accepted lake outlets remain explicit semantic nodes;
- deterministic, no RNG.

The raw MFD threshold mask remains available only as a diagnostic backdrop.

## 7. Lake outlets

Accepted lake semantics stay unchanged.

A lake outlet participates in the skeleton even when it is not a normal threshold-crossing source, because an accepted lake already represents concentrated surface water with a declared spill point.

Its downstream path follows the dominant channel graph and merges with the ordinary skeleton when they meet.

## 8. No arbitrary cosmetic pruning in the first pass

The first implementation pass deliberately does **not** add:

- freehand smoothing;
- arbitrary source spacing radius;
- hand-tuned minimum branch length;
- morphology-only image thinning.

If the thin dominant skeleton still creates implausibly short first-order tributaries, that defect is measured and handled in a later bounded gate. GRASS-style first-order length pruning is a legitimate next option, but it must not be hidden in this experiment.

## 9. Diagnostics H09-C

Use the same representative world:

```text
180 × 120 km
seed 2026091402
cell size 1 km
stream threshold 250 km²
same Terrain 0.2 request/presets
```

Show:

1. terrain + final rivers;
2. MFD continuous flow vectors;
3. MFD accumulation + final rivers;
4. raw threshold support + final rivers;
5. dominant thin skeleton diagnostic;
6. statistics.

The operator should be able to see the distinction:

```text
broad hydrological support
vs
thin semantic channel network
```

## 10. Automated guards

Tests are guardrails, not acceptance.

### S01 — unique source threshold

On a synthetic branching catchment, adjacent MFD-supported cells may exist, but source initiation on the dominant graph must produce only the expected unique headwater sources.

### S02 — no downstream bifurcation

Every ordinary skeleton cell has at most one downstream receiver.

### S03 — confluence semantics

A confluence requires at least two upstream skeleton branches and one downstream branch.

### S04 — source-area threshold

Normal source cells meet `stream_threshold_km2` under unique dominant channel area; their immediate dominant upstream predecessors do not.

### S05 — lake continuity

Accepted lake has one spill outlet and that outlet joins or exits through the skeleton without internal lake channels.

## 11. Operator acceptance

H09-C is compared with both previous failed checkpoints:

```text
H09   — two-receiver D∞: grid/lattice dominated
H09-B — MFD: accumulation improved, semantic network exploded
H09-C — MFD + thin dominant channel skeleton
```

Primary questions:

- Did the hundreds of adjacent/parallel source traces collapse into coherent dendritic networks?
- Do confluences look like merges rather than arbitrary crossings?
- Are short first-order rivers still excessive?
- Does the final vector line remain aligned with the bright MFD accumulation corridor?
- Did the skeleton reintroduce visible 0/45/90° grid bias?
- Are lakes and outlets still coherent?

Only explicit operator `ACCEPT` permits Hydrology 0.2 acceptance.

## 12. Stop rules

If H09-C remains strongly grid-aligned, do not smooth it. The next design must replace the cell-neighbour dominant skeleton with a more continuous ridge/flow-tube extraction.

If source count remains too high but topology is otherwise coherent, the next bounded question is channel initiation/pruning rather than accumulation.

If final traces leave the accumulation corridors, fix trace/skeleton consistency rather than tuning presentation.

## 13. Compatibility

- no public request-schema change;
- no DomainData / DomainBundle contract change;
- MFD accumulation semantics remain as accepted experimental basis;
- exact replay retained within exact generator version;
- Surface / Placement remain blocked until Hydrology acceptance.
