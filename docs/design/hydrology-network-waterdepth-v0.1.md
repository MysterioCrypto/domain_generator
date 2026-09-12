---
id: DESIGN-HYDROLOGY-NETWORK-WATERDEPTH-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Hydrology Network + WaterDepth v0.1

Этот checkpoint превращает runtime stream/lake classification в directed `RiverNetwork` и canonical raster `water_depth_m`, не вводя physical river width и не vectorize-ит lake polygons.

## Scope

Input:

```text
TerrainState.elevation_m
HydrologyState.routing_elevation_m
HydrologyState.fill_elevation_m
HydrologyState.flow_direction
HydrologyState.flow_accumulation_km2
HydrologyState.stream_mask
HydrologyState.lake_candidates
GenerationPlan.hydrology
```

Output additions to runtime `HydrologyState`:

```text
river_network: RiverNetwork
water_depth_m: float32[rows, columns]
```

No RNG is used.

## Semantic hydrology recipe extension

`DomainSpec.hydrology` and `GenerationPlan.hydrology` additionally require:

```yaml
river_depth_at_threshold_m: <float > 0>
river_depth_exponent: <float >= 0>
```

These are semantic inputs and participate in spec/plan fingerprints.

No hidden defaults.

## Stable lake ids

Accepted lake candidates are already canonically ordered.

Assign ids by canonical candidate order:

```text
lake-0001
lake-0002
lake-0003
...
```

These ids are runtime references for `RiverNode.feature_id` and later DomainData hydro-feature assembly.

The current checkpoint does not materialize lake `AreaGeometry`.

## River raster graph

A stream cell is a cell where `stream_mask == true`.

A stream-to-stream directed edge exists from stream cell `A` to its D8 receiver `B` iff:

- `A` is not an accepted lake cell;
- `B` is inside the domain;
- `B` is a stream cell;
- `B` is not an accepted lake cell.

Accepted lake cells suppress internal visible river edges even though D8 still exists for routing.

For every stream cell outside accepted lakes define **effective visible indegree** as:

```text
ordinary upstream stream-to-stream edges
+ incoming lake_outlet transitions
```

This prevents a lake outlet and an ordinary tributary from joining the same downstream stream cell without a confluence node.

## Network nodes

A river node is created at each topological break in the visible stream graph.

### source

A stream cell outside lakes with effective visible indegree `0`.

Position: canonical world-space cell center.

### confluence

A stream cell outside lakes with effective visible indegree `>= 2`.

Position: canonical world-space cell center.

### domain_outlet

A stream path that reaches an edge-cell outlet creates a `domain_outlet` node on the actual domain boundary.

The segment includes the edge cell center and then the boundary point.

Boundary point is the orthogonal projection of the edge-cell center onto its selected domain side.

For a corner edge cell, canonical side precedence is:

```text
north, east, south, west
```

`boundary_side` follows the selected side.

### lake_inflow

When a stream cell outside a lake has its D8 receiver inside accepted lake `L`, create a `lake_inflow` node with `feature_id = lake-id(L)`.

Position is the midpoint between the outside stream-cell center and the inside lake-cell center.

Multiple inflows per lake are allowed.

### lake_outlet

When a lake cell has a D8 receiver outside the same accepted lake and the receiver is a stream cell, create a `lake_outlet` node with that lake id.

Position is the midpoint between the inside lake-cell center and the outside stream-cell center.

Multiple outlets per lake are allowed if routing produces them.

Internal D8 edges inside accepted lakes never become river segments.

## Segment extraction

Segments connect river nodes along the downstream raster graph.

Starting from each node's downstream continuation, follow unique stream successors until another node condition is reached.

Each segment centerline is an ordered tuple of world-space points from upstream node position to downstream node position.

Intermediate raster stream points are canonical cell centers.

No smoothing/spline simplification is applied in v0.1.

Segment ids are assigned after canonical sorting:

```text
river-segment-0001
river-segment-0002
...
```

Canonical segment sort key:

```text
(from_node_id, to_node_id, centerline coordinates)
```

Node ids are assigned after sorting node descriptors by:

```text
(kind, position.x_km, position.y_km, boundary_side-or-empty, feature_id-or-empty)
```

with ids:

```text
river-node-0001
river-node-0002
...
```

## Segment catchment property

`RiverSegment.properties.catchment_area_km2` equals `flow_accumulation_km2` at the last raster stream cell in the segment before its downstream node transition.

For a segment ending at a domain outlet, use the terminal edge stream cell.

For a segment ending at lake inflow, use the outside stream cell immediately before entering the lake.

For a segment ending at a confluence, use the last upstream raster stream cell before the confluence. If a `lake_outlet` segment enters a confluence immediately, use the last lake cell before the outlet transition; the confluence receiver accumulation is not used because it already includes the other incoming branches.

For a segment beginning at lake outlet and continuing through ordinary outside stream cells, downstream accumulation follows that outside stream path until the next node transition.

## River depth proxy

For stream cells outside accepted lakes:

```text
A  = flow_accumulation_km2
A0 = stream_threshold_km2
D0 = river_depth_at_threshold_m
p  = river_depth_exponent

river_depth_m = D0 * (A / A0) ** p
```

Because stream cells satisfy `A >= A0`, the ratio is at least 1.

This is an explicit deterministic proxy, not discharge/hydraulic simulation.

## Lake depth

For accepted lake cells:

```text
lake_depth_m = fill_elevation_m - terrain_elevation_m
```

Only accepted lake candidate cells become canonical lake water in this checkpoint. Sub-threshold depressions remain dry in canonical `water_depth_m`.

## Canonical water depth

For every grid cell:

```text
if cell belongs to accepted lake candidate:
    water_depth = fill - terrain
elif stream_mask[cell]:
    water_depth = river depth proxy
else:
    water_depth = 0
```

Lake classification has precedence over stream classification, suppressing technical D8 river lines inside lakes.

Computation is float64. Exactly one final cast produces canonical runtime:

```text
water_depth_m.dtype == float32
```

All values must be finite and >= 0.

## Runtime state

```text
HydrologyState
├── routing_elevation_m
├── fill_elevation_m
├── flow_direction
├── flow_accumulation_km2
├── stream_mask
├── lake_candidates
├── river_network
└── water_depth_m
```

`river_network` uses the existing serialized-compatible `contracts.data.RiverNetwork` type, but remains runtime output until DomainData assembly.

## Validation

Hydrology validation additionally checks:

- `water_depth_m` shape matches grid;
- dtype exactly float32;
- all finite and non-negative;
- accepted lake cells equal physical fill depth;
- stream cells outside accepted lakes equal the exact river-depth proxy after float32 cast;
- non-lake/non-stream cells equal zero;
- river-network node ids/segment ids canonical and references valid;
- source nodes correspond to effective visible indegree 0;
- confluence nodes correspond to effective visible indegree >= 2;
- domain outlets lie on the declared boundary side;
- lake nodes reference canonical accepted lake ids;
- segment centerlines follow downstream D8 stream topology and never traverse accepted-lake interior;
- segment catchment property matches terminal raster accumulation semantics.

Any topology inconsistency is an engine invariant/capability failure. No hidden repair/retry.

## Non-goals

Not included:

- physical river width;
- sub-cell river rasterization;
- discharge/runoff model;
- precipitation/climate model;
- channel erosion;
- meandering/smoothing;
- lake polygon vectorization;
- HydroFeature materialization;
- DomainData assembler/export.
