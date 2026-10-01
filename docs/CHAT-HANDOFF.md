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

Current checkpoint: **H11-A potential drainage public export — implementation operator review**.

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
- draft PR #87: `https://github.com/MysterioCrypto/domain_generator/pull/87`;
- semantic head: `b77d3247577c552117ba6bf4567d4e7563f062b1`;
- X01–X08 GREEN;
- push/PR pytest GREEN;
- checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`;
- exported keys: `rivers`, `potential_drainage`;
- regional runtime/export = 58 nodes / 33 segments exactly;
- potential runtime/export = 111 nodes / 66 segments exactly;
- upstream canonical hashes unchanged.

A historical DomainData validator had to be made version-aware: Core 0.1 still permits only `rivers`; Core 0.2 additionally permits only `potential_drainage`.

Immediate next step:
- explicit H11-A implementation ACCEPT / REJECT;
- no merge before that decision.

Do not reopen the accepted hydrology routing/network body without concrete evidence.

Process rule:
after every meaningful implementation/decision slice, update external context so a chat failure loses at most the current unfinished step.
