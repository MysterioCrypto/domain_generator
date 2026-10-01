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
├─ C2 effective surface moisture — ACCEPTED / MERGED
└─ C3 climate-aware vegetation — ACCEPTED / MERGED
   ├─ design PR #84
   ├─ implementation PR #85
   ├─ V01–V11 GREEN
   └─ C3-A operator checkpoint ACCEPTED
```

C3-A workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36842261493`

PR #85 merge:
`37e213ebf5f82ebfae149d21088c07e08d836549`

## IN PROGRESS

```text
Hydro-surface finishing — H11-A OPERATOR REVIEW
├─ readiness audit — DONE
├─ design PR #86 — ACCEPTED / MERGED
├─ implementation PR #87 — draft/open
├─ X01–X08 — GREEN
├─ push/PR pytest — GREEN
└─ H11-A contract checkpoint — GREEN
```

Accepted hydrology routing/network remains frozen.

## NEXT

```text
1. explicit H11-A implementation ACCEPT / REJECT
2. ACCEPT → freeze/merge PR #87
3. keep unsupported physical hydro classifications deferred
4. then continue Placement
5. later add additional environment/process models only when required by a concrete feature
```

Do not bundle all deferred hydrology finishing into one change.

## Deferred candidates

```text
perennial / seasonal / dry low-order channel classification
diffuse headwater roots / low-order visibility
standing lake vs wetland / playa / dry basin
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


H11-A design PR:
`https://github.com/MysterioCrypto/domain_generator/pull/86`


H11-A checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`
