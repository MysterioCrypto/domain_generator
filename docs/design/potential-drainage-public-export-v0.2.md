# Potential Drainage Public Export v0.2

Status: **ACCEPTED / implemented / merged**
Target branch: `dev/0.2`
Checkpoint: H11-A
Depends on: accepted Hydrology 0.2 H09-E potential drainage hierarchy + accepted C1/C2/C3 environmental context

## 1. Why this slice exists

Hydrology 0.2 already contains two accepted network scales:

```text
regional river_network
potential_river_network
```

The regional network is canonical visible/water-depth authority.

The denser H09-E potential network was deliberately kept internal until later climate/biome/surface logic needed a drainage scaffold.

That later context now exists, but the project is not yet able to justify physically categorical labels such as perennial / seasonal / dry.

The immediate contract problem is therefore simpler:

> the accepted potential drainage scaffold exists at runtime but disappears at the public DomainData boundary.

H11-A exposes that already-accepted scaffold without changing its geometry or claiming flow permanence.

## 2. Readiness audit of previously deferred hydro-surface semantics

### Perennial / seasonal / dry low-order channels — still BLOCKED

Current Core has:
- annual mean temperature;
- annual precipitation;
- annual effective moisture;
- terrain/hydrologic contributing area;
- generic vegetation potential.

Current Core does not have:
- monthly/seasonal precipitation;
- dry-season duration;
- snow storage/melt seasonality;
- groundwater/baseflow state;
- infiltration/substrate storage.

Therefore a categorical `seasonal` or `perennial` label would currently be more precise than the modeled evidence supports.

Do not infer seasonal/perennial permanence from annual moisture alone.

### Standing lake vs wetland / playa / dry basin — still BLOCKED

Accepted lakes represent hydrologically coherent depression water geometry.

Distinguishing persistent lake, wetland, playa or dry basin requires additional water-balance/permanence semantics, and likely infiltration/substrate and/or seasonality.

Do not relabel accepted lakes from C1/C2/C3 alone.

### Delta / estuary / fan — still BLOCKED

A domain boundary is explicitly not assumed to be ocean.

Delta/estuary/fan morphology requires a known receiving environment and additional process context such as standing-water/coast type, sediment/discharge, or a slope-break receiving plain.

Do not invent such morphology at ordinary domain outlets.

### Diffuse headwater roots / low-order visibility — presentation-ready, not new hydrology

The potential network can already support later headwater visibility/fading.

That is a consumer/presentation interpretation of accepted geometry, not a reason to reroute or redraw Hydrology 0.2.

Public export of the potential scaffold is the prerequisite.

## 3. Public network semantics

For Core 0.2 DomainData:

```text
networks["rivers"]
    = accepted H09-D2 regional river network

networks["potential_drainage"]
    = accepted H09-E potential drainage RiverNetwork
```

Meaning of `potential_drainage`:

> terrain-consistent drainage paths that are hydrologically plausible enough to serve as a scaffold for later visibility, climate, biome or channel-regime interpretation.

It does **not** mean:
- permanently flowing water;
- a visible blue river;
- canonical water-depth authority;
- a legal replacement for `networks["rivers"]`;
- a biome or wetland classification.

## 4. Version boundary

### Core 0.1

No change:

```text
networks = {
    "rivers": regional river network
}
```

### Core 0.2

After H11-A:

```text
networks = {
    "rivers": regional river network,
    "potential_drainage": accepted H09-E potential network
}
```

The existing `DomainData.networks: dict[str, RiverNetwork]` contract already permits multiple named networks.

No new root DomainData version is required for this slice.

No new binary field payload is added.

## 5. Strahler semantics

HydrologyState already contains:
- `channel_strahler_order`;
- `potential_segment_strahler_order`.

H11-A does **not** extend public `RiverSegmentProperties`.

Reason:
- adding serialized segment metadata is a separate public-contract decision;
- the current purpose is to expose the accepted scaffold itself;
- topology/geometry export can be accepted independently from metadata evolution;
- consumers requiring explicit order can receive it in a later bounded design.

H11-A must not silently encode Strahler order into IDs, line width, catchment area, or geometry.

## 6. Assembly semantics

`assemble_domain(...)` may read the already-generated `HydrologyState.potential_river_network`.

For Core 0.2:
- if the accepted potential network is missing, assembly must fail explicitly rather than silently omit it;
- `networks["rivers"]` remains the existing regional network object/semantics;
- `networks["potential_drainage"]` is populated from `potential_river_network`.

For Core 0.1:
- potential drainage is not required;
- output remains unchanged.

Assembly does not regenerate, modify, simplify, reclassify or smooth either network.

## 7. Spatial immutability

H11-A is a public-boundary/export change, not a new spatial generation algorithm.

The following must remain identical to pre-H11-A Core 0.2 generation:
- terrain;
- routing/fill;
- MFD accumulation;
- regional stream mask;
- regional river network;
- potential river network geometry/topology;
- Strahler diagnostics;
- lakes;
- water depth;
- C1 temperature/precipitation;
- C2 moisture;
- C3 vegetation;
- Placement.

## 8. Automated guardrails

### X01 — regional network identity

`DomainData.networks["rivers"]` equals the runtime accepted regional `HydrologyState.river_network`.

### X02 — potential network identity

For Core 0.2, `DomainData.networks["potential_drainage"]` equals runtime `HydrologyState.potential_river_network`.

### X03 — Core 0.1 compatibility

Core 0.1 DomainData network keys and serialized output remain unchanged.

### X04 — no canonical-water promotion

Exporting potential drainage does not change `water_depth`, regional `stream_mask`, lake geometry or canonical river network.

### X05 — no spatial mutation

Assembly/export performs no network generation, rerouting, smoothing, clipping or geometry reconstruction.

### X06 — deterministic bundle

Identical accepted candidate + plan produces byte-stable network serialization under existing deterministic bundle rules.

### X07 — missing potential network is explicit

A Core 0.2 candidate missing `potential_river_network` fails assembly with an explicit error.

### X08 — network names are semantic

The exact public IDs are:
- `rivers`;
- `potential_drainage`.

No aliases such as `streams`, `minor_rivers` or `seasonal_rivers` are emitted.

## 9. Acceptance checkpoint

Because H11-A does not change spatial geometry, it does not require a new hydrology render to re-accept H09-E geometry.

Required operator-visible evidence:
1. DomainData network key list;
2. regional network node/segment counts;
3. potential network node/segment counts;
4. exact runtime-vs-export equality checks;
5. confirmation that canonical fields and regional network are unchanged.

The accepted H09-E visual checkpoint remains the spatial acceptance evidence for potential geometry.

Green tests alone are still insufficient if the exported semantic naming/boundary is wrong.

## 10. Stop rules

- Do not classify potential segments as perennial / seasonal / dry in H11-A.
- Do not add Strahler metadata to public segment properties in this slice.
- Do not change H09-E extraction threshold.
- Do not change river centerlines.
- Do not change water depth.
- Do not expose internal raster masks as new canonical fields just to support this export.
- Do not treat domain outlets as coastlines.
- Do not use renderer behavior to mutate world state.

## 11. What this unlocks

After H11-A, downstream consumers can explicitly choose between:

```text
regional visible/canonical rivers
vs
full potential drainage scaffold
```

That makes later bounded work possible without reopening Hydrology geometry:
- headwater visibility/fading;
- future channel-regime classification once seasonality/baseflow exists;
- biome-aware cartographic interpretation;
- setting-specific map renderers.

If no additional environmental model is added in Core 0.2, H11-A is sufficient to close the deferred low-order-drainage exposure problem without inventing unsupported flow permanence.


## 12. Design acceptance

Operator decision: **ACCEPTED**.

PR #86 merged into `dev/0.2` at:
`712dae3179605b894558a9e399cd6929ffcda459`.

Implementation is authorized only for the bounded public-export semantics above. Unsupported channel permanence, basin-regime and receiving-environment classifications remain deferred.


## 13. Implementation acceptance

H11-A implementation was formally ACCEPTED and merged through PR #87.

Merge commit:
`cef91e81c86c64555ae1e1363d7ffaf2934ff6ce`

Accepted checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`

X01–X08 and full pytest were green.

Accepted representative export:
- `rivers`: 58 nodes / 33 segments, exact runtime/export equality;
- `potential_drainage`: 111 nodes / 66 segments, exact runtime/export equality;
- upstream canonical-state hashes unchanged.

The implementation required one bounded contract correction: the runtime `DomainData` validator became provenance-version-aware. Core 0.1 still permits only `rivers`; Core 0.2 additionally permits exactly `potential_drainage`.

H11-A is frozen unless later evidence identifies a concrete public-contract defect.
