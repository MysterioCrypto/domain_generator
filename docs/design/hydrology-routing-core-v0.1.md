---
id: DESIGN-HYDROLOGY-ROUTING-CORE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Hydrology Routing Core v0.1

Этот документ фиксирует первый hydrology vertical slice: deterministic drainage routing поверх canonical terrain без изменения canonical elevation.

## Scope

Pipeline:

```text
TerrainState.elevation_m
        ↓ copy to float64
Priority-Flood conditioning
        ↓
RoutingSurface
        ↓
deterministic D8 receivers
        ↓
flow accumulation (km²)
        ↓
HydrologyState
```

В этот slice не входят stream extraction, `water_depth`, lakes, vector rivers, river width/discharge, runoff/climate model, erosion или surface moisture.

`stream_threshold_km2` намеренно отложен: это semantic hydrology parameter, но GenerationPlan v0.1 пока не имеет принятого hydrology-recipe contract. Hidden constant запрещена.

## Upstream immutability

Hydrology читает canonical `TerrainState.elevation_m` и никогда его не мутирует.

Все depression corrections происходят только в runtime `routing_elevation_m`.

## Runtime HydrologyState

```text
HydrologyState
├── routing_elevation_m       float64 [rows, columns]
├── flow_direction            int8    [rows, columns]
└── flow_accumulation_km2     float64 [rows, columns]
```

`flow_direction` codes:

```text
-1 = outlet / leaves domain
 0 = N
 1 = NE
 2 = E
 3 = SE
 4 = S
 5 = SW
 6 = W
 7 = NW
```

Grid convention remains canonical: row 0 is north, +column is east.

## Open boundary

Every edge cell is an outlet and has `flow_direction = -1`.

The domain edge is not water/ocean. It means flow may leave the modeled domain.

Priority-Flood seeds every edge cell using canonical terrain elevation.

## Priority-Flood conditioning

Input terrain is converted to float64 without changing numeric values.

Use a min-heap ordered by:

```text
(routing_elevation_m, row, column)
```

All edge cells are inserted once. Neighbors are the 8-connected grid neighbors in canonical D8 order.

When an unvisited neighbor is reached from processed cell `current`:

```text
if terrain[neighbor] > routing[current]:
    routing[neighbor] = terrain[neighbor]
else:
    routing[neighbor] = nextafter(routing[current], +infinity)
```

This is a minimal representable positive gradient, not an arbitrary epsilon constant.

Consequences:

- depressions are raised only in routing surface;
- filled flats receive a deterministic infinitesimal drainage gradient toward an outlet;
- canonical terrain remains unchanged;
- `routing_elevation_m - terrain_elevation_m` preserves candidate depression/fill information for future lake extraction.

No RNG is used.

## D8 routing

Every non-edge cell selects one of its 8 neighbors using routing elevation.

Canonical neighbor order and code:

```text
0 N  = (-1,  0)
1 NE = (-1, +1)
2 E  = ( 0, +1)
3 SE = (+1, +1)
4 S  = (+1,  0)
5 SW = (+1, -1)
6 W  = ( 0, -1)
7 NW = (-1, -1)
```

For each neighbor with strictly lower routing elevation:

```text
slope = (routing[current] - routing[neighbor]) / distance_km
```

where orthogonal distance is `cell_size_km` and diagonal distance is `cell_size_km * sqrt(2)`.

Select maximum positive slope. Exact ties use the earliest direction in canonical order above.

A valid conditioned interior cell must have at least one strictly lower neighbor. Failure is a hydrology invariant/capability failure, never an RNG retry.

## Flow accumulation

Core v0.1 assumes spatially uniform unit runoff only for catchment-area accounting. Accumulation therefore represents contributing area, not discharge.

Each cell initially contributes exactly:

```text
cell_area_km2 = cell_size_km²
```

Implementation accumulates **integer upstream cell counts** through the D8 receiver graph, then converts once:

```text
flow_accumulation_km2 = upstream_cell_count * cell_area_km2
```

This avoids floating-order drift while retaining physical units.

Cells are processed in deterministic descending routing-elevation order, tie-broken by `(row, column)`. Because every non-outlet receiver is strictly lower, the graph is acyclic.

## Runtime / canonical boundary

`routing_elevation_m`, `flow_direction`, and `flow_accumulation_km2` are runtime/derived hydrology data in this slice.

They are not yet declared final `DomainData` canonical river/lake outputs.

Future hydrology slices will use them to derive:

```text
candidate depressions -> lakes / water_depth
catchment threshold -> stream graph -> vector RiverNetwork
```

## Validation

Hydrology validation v0.1 checks:

- upstream TerrainState exists;
- terrain shape matches grid and values are finite;
- HydrologyState exists;
- all arrays match grid shape;
- routing dtype float64 and finite;
- routing elevation is never below canonical terrain;
- flow_direction dtype int8 and codes are in `[-1,7]`;
- all edge cells are outlets;
- every interior cell has a valid receiver direction;
- every directed receiver is strictly lower in routing elevation;
- accumulation dtype float64, finite, and at least one cell area everywhere.

Hydrology uses no RNG in this slice.

## Non-goals

Not included:

- stream threshold storage/selection;
- stream mask;
- water depth;
- lakes;
- river vectorization/network topology;
- precipitation/runoff coefficients;
- flow discharge;
- erosion;
- terrain mutation;
- D-infinity or multiple-flow-direction routing.
