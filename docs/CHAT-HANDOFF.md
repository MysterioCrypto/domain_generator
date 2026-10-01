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
```

Current checkpoint: **C3 vegetation / biome readiness — INV-006 design gate**.

Accepted and frozen:
- Terrain 0.2;
- Hydrology 0.2;
- C1 Annual Climate Forcing;
- C2 Effective Surface Moisture.

C2:
- design accepted;
- implementation PR #83 merged;
- C2-A representative 8 km actual-water decay was rejected for broad artificial halos;
- C2-B changed only representative `water_moisture_decay_km` to 2 km;
- C2-B accepted after green pytest + same-world checkpoint and visual review;
- the 2 km value is representative calibration, not a universal hardcoded constant;
- `water_moisture_decay_km` remains a required semantic input.

Accepted C2-B workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36837227248`

PR #83 merge commit:
`de5646a1af9c9057fe13cf1e7eb92bb1a3728e46`

C2 accepted representative:
- effective moisture p05 / median / p95 ~0.548 / 0.658 / 0.864;
- mean ~0.673;
- land >=0.8 ~10.4%;
- precipitation correlation ~+0.820;
- temperature correlation ~-0.747;
- distance-to-water correlation ~-0.069;
- water-proximity mean ~0.068.

Core 0.1 remains unchanged.

C2-A vegetation compatibility was temporary. C3 may now redesign Core 0.2 `vegetation_density` against accepted C1 + C2.

INV-006 means substantial architecture/semantic changes must be documented and accepted before implementation.

Immediate next step:
- create bounded C3 vegetation / biome-readiness design;
- explicit design ACCEPT / REJECT;
- no C3 runtime implementation before design acceptance.

Process rule:
after every meaningful implementation/decision slice, update external context so a chat failure loses at most the current unfinished step.
