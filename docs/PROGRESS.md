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
├─ C1 annual climate forcing — ACCEPTED / MERGED
│  ├─ annual temperature
│  ├─ annual precipitation
│  ├─ windward/lee forcing
│  └─ C01–C09 guards
└─ C2 effective surface moisture — ACCEPTED / MERGED
   ├─ PR #83
   ├─ M01–M10 guards GREEN
   ├─ C2-A 8 km proximity scale REJECTED
   └─ C2-B 2 km representative proximity scale ACCEPTED
```

Accepted C2-B workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36837227248`

PR #83 merge:
`de5646a1af9c9057fe13cf1e7eb92bb1a3728e46`

## IN PROGRESS

```text
C3 vegetation / biome readiness — OPERATOR REVIEW
├─ design PR #84 — ACCEPTED / MERGED
├─ implementation PR #85 — draft/open
├─ climate-aware vegetation core — IMPLEMENTED
├─ V01–V11 — GREEN
├─ push/PR pytest — GREEN
├─ C3-A workflow — GREEN
└─ implementation ACCEPT / REJECT — PENDING
```

Design PR:
`https://github.com/MysterioCrypto/domain_generator/pull/84`

Merge commit:
`2ad695d059b4f198b5f06c6451b005c0d630fbc9`

Acceptance is formal project/operator acceptance, not expert ecological validation.

C3-A workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36842261493`

Artifact:
`surface-v02-c3`

No merge until explicit implementation ACCEPT / REJECT.

## NEXT

```text
1. operator review C3-A checkpoint
2. explicit implementation ACCEPT / REJECT
3. ACCEPT → freeze/merge PR #85
4. REJECT → identify one concrete C3 component before retuning
5. later revisit deferred hydro-surface finishing with environmental context
6. then continue Placement
```

Do not reopen Terrain/Hydrology/C1/C2 without new concrete evidence.

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
accepted design
+ green automation
+ operator-visible output
+ explicit operator ACCEPT
= accepted spatial semantic layer
```
