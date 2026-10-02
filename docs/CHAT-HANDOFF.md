# Chat Handoff Snapshot

Generated for chat transfer. If this snapshot conflicts with `PROJECT.md`, `docs/CONTEXT.md` or `docs/PROGRESS.md`, those canonical files win.

## Copy into a new chat

Repository: `MysterioCrypto/domain_generator`.

Active development line: `dev/0.2`. Do **not** reconstruct current state from `main`.

First read, in order:

```text
PROJECT.md
docs/CONTEXT.md
docs/PROGRESS.md
docs/design/effective-surface-moisture-v0.2.md
docs/design/vegetation-biome-readiness-v0.2.md
```

Current checkpoint: **H12-A Marine / Coastal Boundary — design operator review**.

Accepted and frozen:
- Terrain 0.2;
- Hydrology 0.2 routing/network;
- C1 Annual Climate Forcing;
- C2 Effective Surface Moisture;
- C3 Climate-Aware Vegetation.

C3:
- design PR #84 merged;
- implementation PR #85 merged;
- merge commit: `37e213ebf5f82ebfae149d21088c07e08d836549`;
- V01–V11 GREEN;
- C3-A workflow GREEN and formally ACCEPTED:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36842261493`.

C3 semantics:
```text
accepted C2 moisture
× normalized annual thermal suitability
+ vegetation_bias
-> vegetation_density

canonical water = 0
```

`vegetation_density` is an abstract normalized ecological potential index, not percent canopy cover or literal NPP.

Mountain influence:
- C1 elevation/lapse-rate temperature;
- C1 windward/lee precipitation;
- C2 slope retention;
- terrain-shaped hydrology feeding C2;
- no second direct C3 slope penalty.

Hydro-surface readiness audit:
- perennial / seasonal / dry remains blocked by absent seasonality/baseflow/groundwater;
- lake vs wetland/playa/dry basin remains blocked by absent water-balance/permanence;
- delta/estuary/fan remains blocked by absent receiving-environment/process context;
- headwater visibility can use the accepted potential scaffold, but that scaffold is currently internal only.

H11-A design PR #86 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/86`

Merge commit:
`712dae3179605b894558a9e399cd6929ffcda459`

Accepted design:
```text
Core 0.2 networks["rivers"] = accepted regional H09-D2
Core 0.2 networks["potential_drainage"] = accepted H09-E potential network
```

No flow-permanence labels, no Strahler public metadata, no hydrology geometry changes.

H11-A implementation:
- PR #87 ACCEPTED / merged;
- merge commit: `cef91e81c86c64555ae1e1363d7ffaf2934ff6ce`;
- checkpoint: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`;
- Core 0.2 public networks: `rivers`, `potential_drainage`;
- Core 0.1 remains `rivers` only;
- potential network is a drainage scaffold, not a permanence class.

Physical hydro classifications still deferred:
- perennial / seasonal / dry;
- lake vs wetland/playa/dry basin;
- delta / estuary / fan.

Immediate next step:
- Placement readiness audit against accepted Core 0.2 environment;
- choose one bounded Placement slice;
- design before implementation if semantics materially change.

Do not reopen the accepted hydrology routing/network body without concrete evidence.

Process rule:
after every meaningful implementation/decision slice, update external context so a chat failure loses at most the current unfinished step.


## Placement readiness result

Existing Core 0.1 placement mechanics are retained:
- lattice/reservation/footprint;
- requirements;
- preferences;
- near-best;
- deterministic weighted selection.

Core 0.2 automatically gives new meaning to:
- `moisture_mean` via C2;
- `vegetation_density_mean` via C3.

P08-A design PR #88 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/88`

Merge commit:
`66003288e528fc340663d92f84ed14cbee88744b`

Accepted Core 0.2-only metrics:
```text
temperature_mean
annual_precipitation_mean
distance_to_potential_drainage
```

P08-A implementation:
- PR #89 ACCEPTED / merged;
- merge commit: `57e77c8de6ac8668ddd09e25167e30aa773cf645`;
- P01–P11 GREEN;
- checkpoint: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`;
- Core 0.1 registry remains 8 metrics;
- Core 0.2 adds temperature_mean, annual_precipitation_mean, distance_to_potential_drainage;
- existing Placement mechanics remain unchanged.

Immediate next step:
- audit remaining Placement boundaries;
- choose one bounded Core 0.2 follow-up slice;
- design before implementation if semantics change.


## Placement closure / A08 hardening

Post-P08-A audit found no additional base Placement contract gap. New Core 0.2 metrics already pass through normal preset/compiler SiteProfile strings.

Placement current scope is complete.

Hardening PR #90:
`https://github.com/MysterioCrypto/domain_generator/pull/90`

A08 is a full Core 0.2 acceptance fixture using P08-A metrics through a real preset. Initial baseline is intentionally PENDING so CI can emit the exact deterministic snapshot before pinning.

No new world semantics are introduced by PR #90.


## A08 integrated acceptance

PR #90 merged:
`568eeff9676ee387d5837cfb1fca1a8ff087e99b`

A08 is frozen and GREEN:
- full Core 0.2 pipeline;
- P08-A metrics through preset/compiler;
- exact replay;
- canonical bundle;
- regional + potential networks.

Release-readiness audit now focuses on stale package/docs version metadata. Independent contract versions remain independent unless a concrete shape break requires a bump.


## Core 0.2 release-candidate readiness

PR #91 merged:
`5cafb8119050f19765447d65dcef022ebebe052b`

Generator identity:
`0.2.0.dev0`

Merge-head pytest GREEN:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36853774759`

A01–A08 are GREEN. Version re-sign changed only DomainData provenance hashes; world fields/geometry/networks/placement remained identical.

No known blocker remains inside accepted Core 0.2 scope.

Operator formally ACCEPTED the release candidate.

Frozen release:
- branch: `release/0.2-prealpha`;
- exact freeze commit: `c69c1af010a085fb80d248af703a77471fc6c9d7`;
- generator identity: `0.2.0.dev0`.

The release branch is frozen. New semantic work continues only on `dev/0.2`.

Immediate next step:
- choose the next post-release semantic layer;
- open a new INV-006 design gate before material implementation;
- do not reopen accepted Core 0.2 semantics without concrete evidence.


## Post-release C4-A seasonality

Dependency audit rejected immediate biome classification because current climate is annual-only.

Design PR #92:
`https://github.com/MysterioCrypto/domain_generator/pull/92`

Proposal:
- optional explicit 12-month climatological envelope;
- monthly temperature preserves annual mean;
- monthly precipitation preserves annual total;
- explicit peak months and amplitudes;
- no hemisphere/latitude inference;
- no new monthly noise or seasonal wind changes;
- C2/C3 unchanged during C4-A;
- no biome or stream-permanence labels yet;
- no seasonality recipe means frozen prealpha-compatible annual behavior.

C4-A design PR #92 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/92`

Merge commit:
`e729d836d29df790fa1c0056e7b686d6189703f9`

C4-A implementation:
- PR #93 ACCEPTED / merged: `https://github.com/MysterioCrypto/domain_generator/pull/93`;
- accepted semantic head: `5b9b4e7341bfb3c8b496f25b3e9f741128f31b2a`;
- merge commit: `570a5c4730419d17bce69f9e804b805125343fa5`;
- S01–S13 GREEN;
- schema snapshots GREEN;
- push/PR full pytest GREEN;
- representative checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36959449118`;
- exactly 24 monthly derived fields;
- annual C1/C2/C3 canonical outputs exact-unchanged;
- features/networks unchanged.

Important compatibility fix:
- absent seasonality initially altered frozen A08 fingerprints because the new optional field serialized as null;
- this was fixed by omitting only absent seasonality from fingerprint payloads;
- frozen A08 fingerprints are explicitly pinned by S10;
- explicit seasonality still changes semantic fingerprint.

Representative conservation after float32 persistence:
- temperature max error ~4.77e-7 C;
- precipitation max error ~1.91e-4 mm.

Operator formally ACCEPTED C4-A implementation.

Immediate next step:
- perform a fresh post-C4 dependency audit;
- choose exactly one next bounded semantic layer;
- open a new INV-006 design gate before implementation;
- do not assume biome or flow-permanence is ready without checking its remaining dependencies.

`release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Post-C4 audit / C5-A

After C4:
- channel permanence is still blocked by groundwater/baseflow/storage;
- lake/wetland/playa/dry-basin semantics are still blocked by basin permanence/water balance;
- delta/estuary/fan remains blocked by receiving-environment context;
- direct biome labels remain deferred.

Selected next bounded layer:
**C5-A Köppen–Geiger climate regionalization**.

Design PR #94:
`https://github.com/MysterioCrypto/domain_generator/pull/94`

Proposal:
- opt-in scheme `koppen_geiger_local_season_v1`;
- derived `uint8` field `climate_regime_koppen_geiger`;
- fixed 30-class codebook;
- local warm/cold half-year anchored on explicit C4 temperature peak month;
- climate classification only, not biome classification.

No runtime implementation before explicit C5-A design ACCEPT.


C5-A design PR #94 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/94`

Merge commit:
`d75b2f6f55b53a14b048a38bb2a69d339c8cf44e`

Important:
- Köppen remains opt-in Earth-derived interpretation only;
- C4 climate parameters are explicit inputs, not hard-coded geography;
- fantasy/non-Earthlike worlds may omit classification entirely;
- exact Beck/Peel 10 C boundary retained.

C5-A implementation:
- PR #95 ACCEPTED / merged: `https://github.com/MysterioCrypto/domain_generator/pull/95`;
- accepted semantic head: `43519587fac92e94cb8bbbb64222c876d7579882`;
- merge commit: `8af34da0c66c48b62172b8654edc5876d9414085`;
- K01–K15 GREEN;
- schema snapshots GREEN;
- push/PR full pytest GREEN;
- representative checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36968143576`;
- all pre-existing C4 fields/features/networks exact-unchanged;
- output is one optional derived uint8 climate-regime field.

Representative map uses 7 of the 30 possible classes and is dominated by Csb because the diagnostic input is intentionally winter-wet / warm-season-dry. This is test input behavior, not a hidden default.

Operator formally ACCEPTED C5-A implementation.

Immediate next step:
- perform a fresh post-C5 dependency audit;
- select exactly one next bounded semantic layer;
- open a new design gate before implementation;
- keep `release/0.2-prealpha` frozen.


## Post-C5 audit / H12-A

Post-C5 audit found:
- direct biome labels still deferred;
- channel permanence still blocked by groundwater/baseflow/storage;
- basin permanence/type still blocked by water balance/infiltration;
- delta/estuary/fan still blocked by receiving-environment/process context.

Universality audit exposed a more fundamental missing capability: no sea/ocean/coastline semantics exist.

Design PR #96:
`https://github.com/MysterioCrypto/domain_generator/pull/96`

Proposal:
- optional explicit `hydrology.marine.sea_level_m`;
- no hidden sea level;
- marine = boundary-connected below-sea terrain using 4-neighbour connectivity;
- enclosed below-sea basins remain inland;
- derived `marine_mask`;
- refined 4× coastline;
- distinct `MarineFeature`;
- `marine_outlet` river nodes;
- regional/potential rivers stop at first coastline intersection;
- no tides/waves/salinity/delta/estuary semantics yet.

Immediate next step:
- explicit H12-A design ACCEPT / REJECT;
- no runtime implementation before design acceptance.
