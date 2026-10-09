# Project Progress Tree

Purpose: **current** DONE / IN PROGRESS / NEXT tree for chat recovery. For the dependency/context map and rejected hypotheses read `docs/CONTEXT.md`; for normative semantics read accepted `docs/design/*`.

**Active line:** `dev/0.2` · **checkpoint:** H13-A DESIGN — OPERATOR REVIEW · **H12-A:** ACCEPTED / MERGED PR #97 (`3d275466ec5bfdb74f5dcb88bea6c8b641347f70`).
Historical checkpoint notes below are not current gates.

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

Post-release (dev/0.2)
├─ C4-A Environmental Seasonality — ACCEPTED / MERGED #93
├─ C5-A optional Köppen–Geiger climate regimes — ACCEPTED / MERGED #95
└─ H12-A optional marine/coastal boundary — ACCEPTED / MERGED #97
   ├─ O01–O13 + schema sync — GREEN
   ├─ full push/PR pytest — 502 passed
   ├─ coastal/archipelago operator checkpoint — GREEN
   └─ merge 3d275466ec5bfdb74f5dcb88bea6c8b641347f70
```

C3-A workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36842261493`

PR #85 merge:
`37e213ebf5f82ebfae149d21088c07e08d836549`

## IN PROGRESS

```text
Post-H12 dependency audit — DONE
├─ H12-A implementation acceptance / merge — DONE
├─ updated context/dependency map — DONE
├─ review deferred candidates against marine receiving environment — DONE
├─ choose exactly one bounded next design — DONE: H13-A
└─ H13-A gross catchment precipitation design PR #98 — OPERATOR REVIEW
   ├─ INV-006 design document — PROPOSED
   ├─ runtime implementation — NOT STARTED
   └─ formal design ACCEPT / REJECT — PENDING
```

Historical already-completed milestones below (not current work):

```text
Hydro-surface finishing — DONE
├─ readiness audit — DONE
├─ H11-A design PR #86 — ACCEPTED / MERGED
├─ H11-A implementation PR #87 — ACCEPTED / MERGED
├─ X01–X08 — GREEN
└─ public potential_drainage export — FROZEN

Placement continuation — CURRENT SCOPE COMPLETE
└─ P08-A environmental site metrics — ACCEPTED / MERGED

Core 0.2 integrated acceptance — DONE
├─ A01–A07 historical Core 0.1 baselines — KEEP
├─ A08 Core 0.2 integrated fixture — FROZEN
├─ hardening PR #90 — MERGED
├─ exact replay / bundle — GREEN
└─ full pytest — GREEN

Core 0.2 release hardening — DONE
├─ PR #91 — MERGED
├─ generator identity 0.2.0.dev0 — DONE
├─ README / architecture alignment — DONE
├─ A01–A08 provenance re-sign — DONE
└─ merge-head pytest — GREEN

Core 0.2 release candidate — ACCEPTED / FROZEN
├─ release/0.2-prealpha — CREATED
└─ freeze commit — c69c1af010a085fb80d248af703a77471fc6c9d7

Post-release C4-A Environmental Seasonality — ACCEPTED / DONE
├─ dependency audit — DONE
├─ design PR #92 — ACCEPTED / MERGED
├─ implementation PR #93 — ACCEPTED / MERGED
├─ implementation merge — 570a5c4730419d17bce69f9e804b805125343fa5
├─ S01–S13 — GREEN
├─ schema snapshots — GREEN
├─ push/PR full pytest — GREEN
└─ C4-A representative checkpoint — GREEN
```

Accepted hydrology routing/network remains frozen.

## NEXT

```text
1. operator review of H13-A design PR #98
2. explicit design ACCEPT / REJECT
3. ACCEPT → merge design, update context DAG, open separate implementation branch
4. H13 implementation only with G01–G15, full pytest, wet/dry + coastal operator checkpoint and separate implementation ACCEPT
5. keep release/0.2-prealpha frozen at c69c1af010a085fb80d248af703a77471fc6c9d7
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


## Historical checkpoint log (not current gates)

H11-A design PR:
`https://github.com/MysterioCrypto/domain_generator/pull/86`


H11-A checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`


P08-A design PR:
`https://github.com/MysterioCrypto/domain_generator/pull/88`


P08-A checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`


C4-A checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36959449118`


Post-C4 dependency audit — DONE

```text
channel permanence             BLOCKED: groundwater/baseflow/storage
basin permanence/type          BLOCKED: water balance/infiltration
delta/estuary/fan              BLOCKED: receiving-environment context
direct biome labels            DEFERRED
C5-A climate regionalization   ACCEPTED / DONE
```

C5-A design PR:
`https://github.com/MysterioCrypto/domain_generator/pull/94`


C5-A design PR #94 — ACCEPTED / MERGED
`d75b2f6f55b53a14b048a38bb2a69d339c8cf44e`


C5-A implementation PR #95 — ACCEPTED / MERGED

Implementation merge:
`8af34da0c66c48b62172b8654edc5876d9414085`

```text
K01-K15                 GREEN
schema snapshots         GREEN
push full pytest         GREEN
PR full pytest           GREEN
representative checkpoint GREEN
```

C5-A checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36968143576`


Post-C5 dependency audit — DONE

```text
direct biome labels             DEFERRED
channel permanence              BLOCKED: groundwater/baseflow/storage
basin permanence/type           BLOCKED: water balance/infiltration
delta/estuary/fan               BLOCKED: receiving-environment/process context
marine/coastline semantics      DESIGN OPERATOR REVIEW
```

H12-A design PR:
`https://github.com/MysterioCrypto/domain_generator/pull/96`


H12-A design PR #96 — ACCEPTED / MERGED
`f8efae6e24cdda68fb10960f13ca69d342a61a7b`


H12-A implementation — IN PROGRESS

```text
PR #97                  draft/open
marine contract          DONE
marine classification    DONE
coastline geometry       DONE
marine water depth       DONE
marine outlet topology   DONE
O01-O13                  ADDED / CI RUNNING
schema snapshots          PENDING
coastal checkpoint        PENDING
implementation acceptance BLOCKED
```

PR:
`https://github.com/MysterioCrypto/domain_generator/pull/97`


H12-A implementation recovery:
```text
PR #97                       DRAFT / UNMERGED
O01-O13 module               PRESENT
last full pytest             489 PASS / 13 FAIL
legacy fingerprint fix       DONE on implementation branch
topology discontinuity       IN DIAGNOSIS
schema snapshots             PENDING after runtime fix
coastal checkpoint           NOT YET ACCEPTANCE-READY
```


H12-A targeted recovery gate:
```text
schema snapshots             GREEN
O01-O13                      GREEN
routing/accumulation freeze  PINNED
C1 exact isolation           PINNED
full pytest                  RUNNING
coastal checkpoint           NEXT
```

Workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36978575264`


H12-A implementation — OPERATOR REVIEW
```text
PR #97                       DRAFT / UNMERGED
semantic head                4dc897906d2e67ae7c3bccb2c9ef49934339f4a6
schema snapshots             GREEN
O01-O13                      GREEN
PR full pytest               502 passed
push full pytest             502 passed
coastal checkpoint           GREEN
implementation acceptance    PENDING OPERATOR
```

Checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161098`

Next:
1. explicit H12-A implementation ACCEPT / REJECT;
2. ACCEPT → merge PR #97;
3. keep `release/0.2-prealpha` frozen.


## Latest accepted checkpoint — H12-A

```text
H12-A design #96                 ACCEPTED / MERGED
H12-A implementation #97         ACCEPTED / MERGED
merge SHA                        3d275466ec5bfdb74f5dcb88bea6c8b641347f70
O01–O13 / schema                 GREEN
full pytest push/PR              502 passed
coastal/archipelago workflow     GREEN
next gate                        POST-H12 DEPENDENCY AUDIT
```

Operator workflow: https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161098

No further implementation is authorized implicitly by H12 acceptance.


## Latest design gate — H13-A

```text
Post-H12 dependency audit     DONE
H13-A chosen design           PROPOSED / OPERATOR REVIEW
PR #98                        DRAFT / OPEN / UNMERGED
G01–G15                       DESIGNED, NOT IMPLEMENTED
runtime implementation        NOT STARTED
release/0.2-prealpha          UNCHANGED
```

Draft design: https://github.com/MysterioCrypto/domain_generator/pull/98

Meaning: gross annual atmospheric precipitation volume routed over accepted MFD contributing catchments. **Not runoff, actual discharge, storage, groundwater or channel permanence.** Its design branch is separate and not part of the accepted architecture until formal acceptance.

Full dependency rationale lives in the **current context map at the start of `docs/CONTEXT.md`**.
