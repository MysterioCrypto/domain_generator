# Project Progress Tree

Purpose: compact handoff state. For reasoning read `docs/CONTEXT.md`; for normative semantics read accepted `docs/design/*`.

## DONE

```text
Core 0.1 infrastructure
├─ contracts/compiler
├─ deterministic semantic RNG
├─ attempts/ranking/validation
├─ DomainData/DomainBundle
├─ CLI/application boundary
├─ Codex + GitHub remote generation
└─ exact replay

Core 0.2
├─ Terrain 0.2 — ACCEPTED
├─ Hydrology 0.2 — ACCEPTED / MERGED
│  ├─ MFD p=1.1
│  ├─ H09-D2 regional rivers
│  ├─ H09-E potential hierarchy + Strahler
│  ├─ H10-A refined lake shorelines
│  └─ H10-B nested split hypothesis rejected by evidence
└─ C1 annual climate forcing — ACCEPTED / MERGED
   ├─ annual temperature
   ├─ annual precipitation
   ├─ windward/lee forcing
   └─ C01–C09 guards
```

## IN PROGRESS

```text
C2 effective surface moisture — C2-B RETUNE
├─ design PR #82 — ACCEPTED / merged
├─ implementation PR #83 — draft/open
├─ effective-moisture core — IMPLEMENTED
├─ M01–M10 guards — GREEN
├─ push/PR pytest — GREEN
├─ C2-A workflow — GREEN
├─ C2-A operator decision — REJECT
│  └─ culprit: actual-water proximity scale (8 km decay halo)
└─ C2-B bounded water-proximity correction — IN PROGRESS
```

Latest workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36831586933`

Artifact:
`surface-v02-c2`

C2-A decision:
`water_moisture_decay_km = 8` is rejected as the representative generic actual-water scale because it creates broad artificial-looking halos around rivers/lakes.

Keep unchanged:
climatic wetness, catchment contribution, slope retention, Terrain, Hydrology and C1.

## NEXT

```text
1. sync PR #83 implementation branch with current dev/0.2
2. retune only representative water_moisture_decay_km
3. rerun same-world C2 checkpoint
4. model/operator review of corrected proximity scale
5. ACCEPT → freeze C2 and merge PR #83
6. INV-006 design C3 vegetation / biome readiness
```

Do not reopen Terrain/Hydrology/C1 without new concrete evidence.

## Deferred

```text
perennial / seasonal / dry channel classification
headwater visual roots
standing lake vs wetland/playa/dry basin
delta / estuary / fan morphology
biome labels
Placement continuation
```

## Acceptance boundary

```text
green automation
+ operator-visible output
+ explicit operator ACCEPT
= accepted spatial semantic layer
```
