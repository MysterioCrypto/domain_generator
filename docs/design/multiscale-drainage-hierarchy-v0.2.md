# Multiscale Drainage Hierarchy v0.2

Status: **accepted experimental design gate**  
Target branch: `dev/0.2`

Operator decision: keep H09-D2 as the regional river baseline, but add a denser internal potential drainage network with explicit hierarchy before the separate lake pass.

## 1. Problem

H09-D2 is coherent enough to keep:

```text
16 sources
4 semantic confluences
33 segments
~649 km regional rivers
final grid-lock within 1°: ~9.08%
```

The remaining visual defect is cumulative rather than one obvious broken line: the network still reads as several long independent threads with too little branching hierarchy for a neutral, geology-agnostic regional drainage pattern.

The goal is **not** to make every potential channel a permanent visible river. Climate, biome, substrate and later rendering may suppress or reclassify minor channels.

Hydrology should first provide a plausible drainage scaffold at more than one cartographic scale.

## 2. Reference semantics

Use Strahler stream order for hierarchy.

USGS describes the standard rule:

- outermost unbranched tributaries are order 1;
- when two streams of equal order merge, downstream order increments by one;
- when unequal orders merge, downstream keeps the larger order.

USGS also notes that stream order is sensitive to the scale/density of the mapped source network. That is useful here: Core must make its extraction scale explicit rather than pretending there is one universal first-order channel definition.

This experiment therefore has two nested drainage scales.

## 3. Two network layers

### Regional network

Keep the accepted H09-D2 source semantics unchanged:

```text
regional baseline:
    unique_area >= T

OR regional terrain promotion:
    unique_area < T
    AND convergence > 1
    AND slope > 0.02
    AND unique_area * (slope / 0.02)^1.65 >= T

T = stream_threshold_km2
```

This continues to populate the current serialized/runtime `river_network` and current `stream_mask` used for water depth.

### Potential drainage network

Add a denser internal network used as the hydrologic scaffold for later climate/biome classification.

For one bounded experiment:

```text
T_potential = 0.40 * T

potential eligibility =
    unique_area >= T_potential
    OR regional eligibility
```

No extra terrain-promotion formula is added below `T_potential` in this batch.

The fixed factor `0.40` is an internal extraction-scale choice for the experiment, not a physical constant and not a user-facing parameter.

## 4. Why potential drainage is separate from permanent rivers

The potential network means:

> terrain and upstream topology support a concentrated drainage path here.

It does **not** yet mean:

> this is a perennial visible blue river on the final fantasy map.

Later climate/biome/surface logic may interpret low-order potential channels as:

- perennial small streams;
- seasonal/intermittent channels;
- wet valley axes;
- dry gullies;
- omitted cartographic detail.

This prevents Hydrology 0.2 from encoding future rainfall/vegetation assumptions prematurely.

## 5. Dominant graph and skeleton

Both scales use the same accepted ingredients:

- Priority-Flood conditioned surface;
- MFD p=1.1 contributing area;
- the same deterministic dominant one-downstream channel projection;
- accepted lake supernodes and canonical outlets;
- one-cell-wide merge-only skeleton activation;
- continuous world-space vector tracing.

The potential network must therefore remain a tree/DAG of merges, not a return to the broad H09-B threshold mask.

Regional skeleton must be a subset of, or hydrologically represented within, the potential scaffold. The experiment may move the apparent first-order start farther upstream, but must not delete a regional drainage path.

## 6. Strahler ordering

Compute Strahler order on the **potential** skeleton.

For ordinary potential channel cells:

```text
no upstream channel        → order 1

upstream orders:
  max = m
  two-or-more upstream branches with order m
                            → order m + 1
  otherwise                 → order m
```

### Lakes

Lakes are transparent hierarchy supernodes rather than order resets.

Potential inflow branches terminate at the lake supernode. The lake aggregates their incoming Strahler orders using the same rule. Its canonical outlet continues downstream with the resulting order.

An accepted lake with no mapped potential inflow starts its outlet at order 1.

No potential skeleton is drawn through lake interior cells.

## 7. Runtime representation

No public DomainData contract change in this experiment.

Add internal HydrologyState diagnostics/semantics:

```text
potential_channel_skeleton_mask
channel_strahler_order
potential_river_network
potential_segment_strahler_order
```

Current public/runtime `river_network` remains the H09-D2 regional network until climate/biome visibility semantics are designed.

This avoids prematurely serializing experimental hierarchy fields.

## 8. Geometry

Potential channel centerlines use the same continuous MFD-derived vector tracing as regional rivers.

No raster centerline geometry and no smoothing layer are introduced.

If the potential skeleton is topologically plausible but vector geometry leaves accumulation corridors, treat that as a tracing-consistency defect.

## 9. H09-E operator checkpoint

Use the exact same representative world:

```text
180 × 120 km
seed 2026091402
cell size 1 km
regional T = 250 km²
potential T = 100 km²
same Terrain 0.2
same MFD p=1.1
same accepted lakes
same H09-D2 regional source rule
```

Required views:

1. terrain + unchanged regional H09-D2 rivers;
2. terrain + full potential drainage hierarchy;
3. regional rivers over potential hierarchy;
4. potential skeleton colored/labeled by Strahler order;
5. MFD accumulation + potential hierarchy;
6. statistics:
   - regional vs potential sources/confluences/segments/length;
   - Strahler order histogram;
   - maximum order;
   - grid-lock for potential vector geometry;
   - regional-skeleton coverage by potential scaffold.

Line weight in the hierarchy diagnostic may reflect Strahler order. This is diagnostic encoding, not geometry manipulation.

## 10. Automated guardrails

### M01 — regional preservation

Every regional skeleton cell is either in the potential skeleton or lies on the same downstream path represented by it. No H09-D2 drainage branch disappears.

### M02 — Strahler equal-order merge

Two order-1 branches merging produce order 2.

### M03 — Strahler unequal-order merge

Order 1 merging into order 2 remains order 2.

### M04 — merge-only topology

Potential ordinary cells have at most one downstream receiver. No bifurcation is introduced.

### M05 — lake hierarchy continuity

Potential inflow order is aggregated through the lake supernode and emitted at the canonical outlet; lake interior remains channel-free.

### M06 — regional semantics unchanged

Adding potential hierarchy must not change the current regional `river_network`, regional `stream_mask`, or water-depth semantics.

Automated checks are guardrails, not acceptance.

## 11. Operator questions

Compare H09-D2 regional view against H09-E hierarchy:

- Does the potential network now read as a believable dendritic drainage tree rather than isolated strings?
- Are first-order branches numerous enough to establish hierarchy without becoming H09-B parallel noise?
- Do higher-order trunks occupy the strongest accumulation corridors?
- Do branch merges visually make sense against terrain?
- Does the network still look strongly procedural from repeated spacing/angles?
- Do lakes sit coherently inside the hierarchy, or do they now stand out as the next obvious defect?

## 12. Stop rules

If potential drainage returns to H09-B-like redundant parallel channels:
- reject the extraction scale;
- do not hide them with arbitrary pruning in the same iteration.

If the network is still too sparse:
- the next question is potential extraction scale / branch-scale valley detection, not MFD.

If hierarchy looks acceptable but lakes dominate the artificial look:
- freeze river hierarchy and proceed to the planned bounded lake pass.

If H09-E is acceptable:
- keep regional + potential hierarchy as Hydrology base;
- then perform the separate lake size/shape/catchment iteration;
- only after that decide Hydrology 0.2 acceptance.

## 13. Compatibility

- no public request-schema change;
- no DomainData / DomainBundle contract change;
- exact replay remains required;
- Surface / Placement remain blocked;
- H09-D2 regional network remains the water-depth authority in this batch.
