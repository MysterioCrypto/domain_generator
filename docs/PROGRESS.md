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
C3 vegetation / biome readiness — DESIGN GATE
└─ INV-006: document and accept semantics before runtime implementation
```

No C3 runtime implementation has started.

## NEXT

```text
1. create C3 vegetation / biome-readiness design
2. explicit design ACCEPT / REJECT
3. ACCEPT → implementation branch
4. automated C3 guardrails
5. representative operator-visible C3 checkpoint
6. explicit implementation ACCEPT / REJECT
7. later revisit deferred hydro-surface finishing with environmental context
8. then continue Placement
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
