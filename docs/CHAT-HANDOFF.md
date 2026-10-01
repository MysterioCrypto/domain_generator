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

Current checkpoint: **C4-A Environmental Seasonality — design operator review**.

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

Immediate next step:
- explicit C4-A design ACCEPT / REJECT;
- no runtime implementation before design acceptance.

`release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.
