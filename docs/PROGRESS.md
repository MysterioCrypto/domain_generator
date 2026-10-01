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
C2 effective surface moisture — OPERATOR REVIEW
├─ design PR #82 — ACCEPTED / merged
├─ implementation PR #83 — draft/open
├─ effective-moisture core — IMPLEMENTED
├─ M01–M10 guards — GREEN
├─ push/PR pytest — GREEN
├─ C2-A workflow — GREEN
└─ operator ACCEPT / REJECT — PENDING
```

Latest workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36831586933`

Artifact:
`surface-v02-c2`

Main review question:
`water_moisture_decay_km = 8` creates broad wet halos around rivers/lakes. Decide whether that scale reads plausibly before retuning.

## NEXT

If C2-A = ACCEPT:

```text
1. freeze C2 moisture
2. merge PR #83
3. INV-006 design C3 vegetation / biome readiness
4. implement vegetation only after design acceptance
5. later revisit deferred hydro-surface finishing
6. then continue Placement
```

If C2-A = REJECT:

```text
identify one concrete defect:
  climatic wetness
  actual-water proximity scale
  catchment contribution
  slope retention

then make one bounded correction;
do not reopen Terrain/Hydrology/C1 without evidence.
```

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
