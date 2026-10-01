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
Hydro-surface finishing — DONE
├─ readiness audit — DONE
├─ H11-A design PR #86 — ACCEPTED / MERGED
├─ H11-A implementation PR #87 — ACCEPTED / MERGED
├─ X01–X08 — GREEN
└─ public potential_drainage export — FROZEN

Placement continuation — CURRENT SCOPE COMPLETE
└─ P08-A environmental site metrics — ACCEPTED / MERGED

Core 0.2 integrated acceptance — IN PROGRESS
├─ A01–A07 historical Core 0.1 baselines — KEEP
├─ A08 Core 0.2 integrated fixture — ADDED
├─ hardening PR #90 — draft/open
└─ deterministic baseline — PENDING
```

Accepted hydrology routing/network remains frozen.

## NEXT

```text
1. run A08 pending baseline
2. diagnose integration failures, if any
3. pin deterministic A08 baseline
4. full pytest + exact replay + bundle checks
5. merge hardening PR #90
6. only then choose the next new semantic layer
```

Do not bundle all deferred hydrology finishing into one change.

## Deferred candidates

```text
perennial / seasonal / dry low-order channel classification
diffuse headwater roots / low-order visibility
standing lake vs wetland / playa / dry basin
delta / estuary / fan morphology
biome labels
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


P08-A design PR:
`https://github.com/MysterioCrypto/domain_generator/pull/88`


P08-A checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`
