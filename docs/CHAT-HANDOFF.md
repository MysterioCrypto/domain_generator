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

Current checkpoint: **C2-B Effective Surface Moisture — bounded water-proximity retune**.

Accepted and frozen:
- Terrain 0.2;
- Hydrology 0.2;
- C1 Annual Climate Forcing.

Hydrology notes:
- H09-E hierarchy accepted;
- H10-A refined lake shoreline kept;
- H10-B showed all 13 representative lakes are single basins, so nested splitting was rejected;
- river/lake finishing that needs environmental context is deferred.

C1 notes:
- annual temperature + annual precipitation accepted;
- C1 is regional atmospheric forcing;
- precipitation moisture supply is external to the regional domain model;
- local rivers/lakes do not directly generate C1 atmospheric precipitation.

C2 design is accepted and implementation exists on draft PR #83:
`https://github.com/MysterioCrypto/domain_generator/pull/83`

Latest green C2-A workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36831586933`

Artifact:
`surface-v02-c2`

Do not download heavy Actions artifacts into the chat/container unless explicitly requested. Give the operator the direct workflow-run link instead.

C2 effective moisture:

```text
climatic_wetness = P / (P + 58.93 * clamp(T,0,30))

water proximity
+
climate-gated contributing-area signal
→ local hydrology

pre_slope =
  climatic_wetness
  + (1 - climatic_wetness) * local_hydrology

moisture =
  clamp(pre_slope * cos(slope)^2 + feature bias, 0, 1)

canonical water = 1
```

No extra C2 moisture noise. Core 0.1 is unchanged. Vegetation is intentionally still legacy-compatible during C2-A.

Representative C2-A:
- moisture p05 / median / p95 ~0.619 / 0.728 / 0.887;
- ~18% of land >=0.8;
- correlation with precipitation +0.712;
- with temperature -0.691;
- with distance to water -0.397;
- catchment contribution is subordinate;
- slope retention is weak on this 1 km world.

C2-A operator decision:
**REJECT**.

Concrete culprit:
- inherited representative `water_moisture_decay_km = 8` produces a broad artificial-looking actual-water halo;
- climatic wetness, catchment contribution and slope retention are kept;
- Terrain/Hydrology/C1 remain frozen.

Repository-state audit:
- PR #83 implementation branch is one documentation-only `dev/0.2` commit behind and must be synchronized before further work.

Immediate next step:
- sync PR #83 branch with current `dev/0.2`;
- retune only the representative actual-water decay scale;
- rerun the same-world C2 checkpoint;
- ACCEPT corrected scale → freeze C2, merge PR #83, then design C3 vegetation / biome readiness.

Process rule:
after every meaningful implementation/decision slice, update external context so a chat failure loses at most the current unfinished step.
