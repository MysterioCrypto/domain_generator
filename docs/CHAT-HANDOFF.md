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

Current checkpoint: **P08-A Placement environmental site metrics — implementation operator review**.

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
- draft PR #89: `https://github.com/MysterioCrypto/domain_generator/pull/89`;
- semantic head: `ec59e0b6693c10fb6064ebf4b68d7f8c019097e8`;
- P01–P11 GREEN;
- push/PR pytest GREEN;
- checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`;
- Core 0.1 registry remains 8 metrics;
- Core 0.2 adds temperature_mean, annual_precipitation_mean, distance_to_potential_drainage;
- upstream state/network unchanged.

Diagnostic fixture: 148 candidates / 133 valid / 1 near-best; selected point ~23.326, 38.308 km. Fixture rules are test evidence only.

Immediate next step:
- explicit P08-A implementation ACCEPT / REJECT;
- no merge before that decision.
