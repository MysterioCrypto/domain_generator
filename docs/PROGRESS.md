# Project Progress Tree

Purpose: **current** DONE / IN PROGRESS / NEXT tree for chat recovery. For the dependency/context map and rejected hypotheses read `docs/CONTEXT.md`; for normative semantics read accepted `docs/design/*`.

**Active line:** `dev/0.2` · **current product checkpoint:** non-Earth source fixtures and [single navigation page](../START_HERE.md). **Parallel technical line:** H13 DESIGN accepted/merged #98, runtime #99 draft/unmerged; #100 C2 experiment and #101 atlas composer also draft/unmerged. **H12-A:** accepted/merged #97.
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
├─ H12-A optional marine/coastal boundary — ACCEPTED / MERGED #97
   ├─ O01–O13 + schema sync — GREEN
   ├─ full push/PR pytest — 502 passed
   ├─ coastal/archipelago operator checkpoint — GREEN
   └─ merge 3d275466ec5bfdb74f5dcb88bea6c8b641347f70
└─ H13-A gross catchment precipitation DESIGN — ACCEPTED / MERGED #98
   └─ merge 0000a208183a2ff3b1d7dc8eee8f93d54f72ef35
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
└─ H13-A gross catchment precipitation implementation — IN PROGRESS
   ├─ INV-006 design document — ACCEPTED / MERGED #98
   ├─ no-loss gross atmospheric allocation, NOT delivered runoff/discharge
   ├─ existing SURFACE stage boundary defined; no new ValidationStage
   ├─ runtime implementation — AUTHORIZED IN SEPARATE BRANCH / IN PROGRESS
   └─ formal design ACCEPT — DONE; implementation ACCEPT / REJECT — PENDING
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

## NEXT — active product track

```text
P0  navigation + provenance of non-Earth source materials   DOCS BRANCH
P1  A8/A12 SHA+NPZ+axis alignment QA                 VERIFIED; NOT IMPORTED
    External geogrid source adapter + region downscaling  NEXT
    or select explicitly NEW generated regional geography    NOT YET SELECTED
P2  3 genuinely distinct topographic/hydrologic regions      NEXT VISIBLE PNG GATE
P3  opt-in world-defined land cover categories               NOT IMPLEMENTED
P4  satellite-like overhead geographic substrate            NOT IMPLEMENTED
P5  optional ImageGen illustration + restore geo overlays  NOT IMPLEMENTED
P6  clean new repository after consolidation               USER-LED / NOT NOW

Parallel #99 H13 runtime                                DRAFT / UNMERGED
Parallel #100 C2 visual sensitivity                      DRAFT / UNMERGED
Parallel #101 map compositor / art palettes             DRAFT / UNMERGED
Frozen release/0.2-prealpha                            UNCHANGED
```

Historical H13 design PR #98 is **ACCEPTED/MERGED**. On separate PR #99, G01–G15 and wet/dry/coastal checkpoint have already been implemented and validated, but none of that runtime is on dev/0.2. Do not confuse green CI with merge acceptance. See [roadmap](PRODUCT_ROADMAP.md).

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


## Historical design gate — H13-A (closed by DESIGN ACCEPT)

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


## Parallel H13-A technical gate (not sole active product track, 2026-11-15)

```text
H13 design #98       OPERATOR ACCEPTED / MERGED
merge SHA            0000a208183a2ff3b1d7dc8eee8f93d54f72ef35
implementation       SEPARATE BRANCH / NOT ACCEPTED
G01–G15             PASSED ON DRAFT #99
full pytest          517 passed ON DRAFT #99
operator checkpoint  WET/DRY + COASTAL; GREEN ON DRAFT #99
implementation merge FORBIDDEN until separate explicit ACCEPT
frozen release       c69c1af010a085fb80d248af703a77471fc6c9d7
```

Why H13: C1 gross precipitation is already known and the MFD weighted DAG supports strictly mathematical accumulation without inventing runoff or permanence. Keep lake supernode identity, marine absorption, exact upstream field stability, and no delta/biome shortcut. See `docs/CONTEXT.md` and accepted design.


## Actual world-source QA (2026-11-15)

A8/A12 ZIPs found in the connected Drive folder and locally opened. Exact SHA-256 matches archived README; exact 600×1200 DEM/land match after A8 north-south axis reversal; A12 global climate/biome arrays and A12 annual Q snapshot read, not used as accepted DomainData. See [A8/A12 audit](reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md). **Next work:** implement explicit non-Earth geogrid import/adapter and work from source candidate A instead of unrelated random terrain. No author canon or Core runtime contract was modified.


## P1 planetary macro-geogrid adapter — 2026-11-15, DRAFT #103

- User's non-Earth source A8/A10/A11/A12 archives are verified (SHA/CRC, A8 north-first vs A10/A11/A12 south-first) and kept PRIVATE. Source A8 global D8 is an older research hydrology, not Core 0.2 accepted MFD.
- On an isolated DRAFT [PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103), external-only script scripts/export_planetary_macro_region_v02.py reads paths of original ZIPs, validates exact A8/A12 shared land/DEM, accepts user-specified planetary radius/year and local km source crop, remaps BOTH endpoints of A8 global flattened D8 downstream indices, and flags rivers exiting crop. It emits source NPZ+manifest+PNG, deliberately NOT DomainData and NOT fake local 1-km elevation.
- Synthetic workflow [GREEN](https://github.com/MysterioCrypto/domain_generator/actions/runs/43742308913) passes 4 targeted tests and writes a demo artifact. No private source ZIP/PNG was committed or uploaded to Actions.
- [CLI instructions and explicit boundaries](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-geogrid-adapter.md). Next meaningful work is source-constrained finer regional terrain and new MFD river generation, followed by non-Earth profile-based land cover; not further parchment filters or full planetary climate science.
- This is a parallel draft branch. PR #99 H13, #100 C2 tests, #101 atlas composer remain DRAFT/UNMERGED. Frozen release c69c1af010a085fb80d248af703a77471fc6c9d7 remains unchanged.


### External source-geogrid P1 checkpoint (DRAFT, no merge)

- [PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103): external A8/A12/A10 model crop, exact lat axis reconciliation, D8 flat source→receiver remap, explicit planetary-year/radius, output macro-source NPZ/manifest/PNG. No Core runtime change.
- [GREEN synthetic Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/43742308913), 4 tests and end-to-end toy archive; no private user's world data in repository.
- Next P2: source-constrained child-region elevation and hydrology from macro source. Do not mistake D8 macro or 0.3-degree data for 1-km accepted MFD.


### P2-A child terrain (DRAFT #103, not merged)

- Real private 230×230 km A/B/C working-model previews with new 1-km terrain; exact macro elevations at 63/49/49 original parent nodes, zero measured difference. C1 Hermite removes grid artifacts; deterministic world-coordinate fine relief. No private binaries/images committed.
- [Source-aware child script and limitations](world-fixtures/planetary-child-terrain.md). [Synthetic dedicated Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/43746102251); full CI at latest PR head must be checked.
- **NEXT P2-B:** build/verify a fine-grid MFD river network conditioned on macro outlet/major-basin constraints; do not claim old D8 is accepted MFD. Then P3 configurable non-Earth land cover.
- Keep draft PRs #99/#100/#101/#103 unmerged and release branch frozen.


### P2-B1 — actual child MFD diagnostics (2026-11-16; draft PR #103)

- [19 GREEN targeted tests, Actions and synthetic comparison PNG](https://github.com/MysterioCrypto/domain_generator/actions/runs/43805052775); accepted Core fractions, ledger and fast vs canonical area equivalence, old D8 overlay separately. Existing full pytest on prior algorithm SHA GREEN; verify current doc SHA separately.
- Real private A/B/C diagnostic in chat: three geographically distinct 230km regions. External inflows missing. Real B/C source-derived deep terrain depressions up to ~88.5/60m virtual filling; pre-lake MFD fans are not valid materialized river networks. [Audit and stop rule](reviews/p2-b-child-mfd-reference-audit-2026-11-16.md).
- Next P2-B2: external boundary contributions + *accepted* lake outlet supernodes, then cross-scale MFD ↔ old A8 source topology comparison; only later waterfall/road and non-Earth land cover. No runtime modification, no merge of #99/#100/#101/#103, frozen release unchanged.


### P2-B2.1 — geometric lake basin review (2026-11-20, PR #103 DRAFT)

- [Visual synthetic QA](https://github.com/MysterioCrypto/domain_generator/actions/runs/44748762996) and [operator review](reviews/p2-b2-1-child-lake-basin-operator-checkpoint-2026-11-20.md): external read-only `scripts/audit_planetary_child_lakes_v02.py`, Core Priority Flood/extract_lake_candidates/choose_lake_outlets, bounded nested hierarchy, Core lake-supernode conservation on SMALL bowl only. Proposed basin ≠ actual water occupancy; no universal Earth-specific thresholds, no external inflow, no source-D8 substitution.
- 27 focused tests GREEN; full algorithmic SHA pytest 532 GREEN; final docs SHA must have new CI. Private A/B/C sensitivity screening performed locally using independently interpolated DEM, not an exact PR P2-A regression; resulting numerical/visual data stay in conversation only.
- P2-B2.2 next: source-macro boundary inflows/outflows and constrained MFD+lake supernode routing, before asserting credible river/ford/waterfall geometry. Keep PR #103, #99–101 draft/unmerged. Frozen `release/0.2-prealpha` unchanged.


### P2-B2.2 — explicit cross-scale river boundary area (2026-11-20, draft PR #103)

- External scripts/condition_planetary_child_boundary_mfd_v02.py: identify directionally INCOMING original A8 D8 macro-river links at a 230km child box; preserve source catchment as UNSAFE_HINT only. With NO explicit scenario, inject **zero** external km2. With a keyed, operator-annotated, positive EXTERNAL_ONLY scenario, run new Core-compatible O((N+E)logN) MFD + geometric lake-supernode area propagation and enforce area-conservation ledger. It is **NOT discharge Q**, a world water balance, actual lake occupancy, an accepted child vector river network or an automatic A8-to-MFD merger. Does not mutate normative Core.
- [Operator audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md) · [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-boundary-inflow.md). [Synthetic GREEN preview and ledger](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925): 35 focused tests, two contrasting maps, no private source uploaded. [Full pytest GREEN 540](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA 35163cd7b6f8c3c9c8c74ea3a5ec24c2aa603dc3; check final documentation SHA again.
- Original PRIVATE A8/A12 data were screened locally for 230×230km A/B/C: OLD D8 crossing counts A **1 IN / 1 OUT**, B **0 IN / 2 OUT**, C **0/0**. A source D8 entry has upstream catchment proxy **86,106.66 km²**, but this is **NOT** verified external-only area and MUST NOT be injected unexamined. No old-source data/real-derived maps in public GitHub.
- **NEXT P2-B2.3:** compute true external-only provenance using original global D8 with re-entry detection, then compare macro basin exits to new actual connected MFD channels and qualify real lake occupancy per world-specific water profile. PR #103 DRAFT/UNMERGED, #99–101 DRAFT/UNMERGED; dev/0.2 and frozen release unchanged.


### Latest P2-B2.2 boundary-source and MFD supernode scenario (DRAFT #103)

- 35 GREEN focused tests; 540 GREEN full on algorithm SHA; visual Actions demo produces **NO external** vs **+250 km2 explicitly synthetic** comparison. The sum of edge terminal contributing area changes exactly by declared external area (numerical error ~1e-11 km2). No Core change.
- Genuine private A8/A12 original candidate regions A/B/C 230km squares have OLD D8 boundary crossings 1/1, 0/2, 0/0. A inbound macro catchment hint 86,106.66 km2 is NOT external-only and is not injected.
- [Review](reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md) and [public-data-safe CLI](world-fixtures/planetary-child-boundary-inflow.md). **NEXT P2-B2.3**: macro-graph provenance of outside-only area including possible re-entry, then fine-grid MFD river skeleton/outlet matching; not a planetwide geology dissertation.
- PR #103 remains DRAFT/UNMERGED; #99–101 drafts not merged; dev/0.2 and frozen release remain unchanged.


### P2-B2.3 · 2026-11-20: global A8 FIRST-ENTRY source partition (DRAFT #103)

- The original PRIVATE global A8 600×1200 D8 graph (not a crop) was inspected. New external script scripts/trace_a8_external_first_entry_v02.py computes the partition of **each original EXTERIOR LAND SOURCE cell** by the FIRST directed downstream entry into each 230km child rectangle. This prevents source-area duplication on exit/re-entry: only own new exterior source area is allocated to later entries. Full graph must be acyclic; macro/crop links must match exact global A8 lat/lon/receiver indices; A8 source cell area uses world radius and cos(latitude), NOT Earth constants.
- Original privately checked working model A/B/C: all directed A8 entry LINKS **23 / 12 / 5**; subset tagged old major river mask **1 / 0 / 0**. All-source EXTERIOR first-entry areas A ≈297,336.828km² / B ≈87,705.114km² / C ≈11,515.098km². A's ONE major river has A8 external first-entry area ≈**86,106.657km²**, matching old total source catchment ≈86,106.65625km² within rounding. No inside-upstream reentry in these specific scenes; a synthetic exit→reentry case is tested explicitly.
- A8 first-entry provenance is NOT physically verified 1km CHILD MFD drainage, river discharge Q or author canon. **No auto injection into child MFD.** Old D8 river_mask ignores numerous smaller old macro incoming links; B/C "zero major" DOES NOT mean no rivers. Private source ZIPs and actual region imagery are NOT committed to public GitHub.
- [P2-B2.3 audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-a8-first-entry-provenance.md). Synthetic tests cover reentry, unequal latitude row areas, cycle and source mismatch; current CI status must be confirmed at latest final SHA.
- **NEXT P2-B2.4:** match source A8 MACRO outlets with actual CHILD MFD edge-terminal geography and connected river lines, then explicit world-specific hydrologic semantics; neither A8 D8 nor newly rendered detail is authoritative. PR #103 remains DRAFT/UNMERGED; #99–101 drafts and dev/0.2/frozen release unchanged.


### Latest P2-B2.3 in draft #103

External global original A8 first-entry partition, no source cell double counted across regional reentries. Actual private A/B/C first-entry results 23/12/5 all D8 links, 1/0/0 old major river links, with A major outside-only area 86,106.657km² (matches old source catchment within rounding). Global A8 original SHA/axes not replaced, no private assets pushed. [Operator audit](reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md) and [CLI](world-fixtures/planetary-a8-first-entry-provenance.md); synthetic re-entry/cycle/geometry regression included. **NEXT:** P2-B2.4, source A8 exits vs actual MFD terminal map and connected fine river lines; do not copy macro A8 first-entry values into new MFD without topology reconciliation. PR #103 remains draft and no Core change.


### P2-B2.4 (2026-11-20): old A8 macro river exits vs CONNECTED CHILD Core MFD dominant channels — DRAFT #103

- New read-only external script scripts/compare_planetary_child_mfd_outlets_v02.py: directionally **INSIDE→OUTSIDE** old major A8 D8 links (distinct from earlier inlet provenance), accepted Core Priority Flood+MFD, Core dominant-channel area+terrain-aware initiation, positive-fraction adjoining channel edges traced to actual region boundary, and explicitly NONPHYSICAL jumps across geometrical lake proxy supernodes. Generates georeferenced-local-km masks/edge pairs + three-panel diagnostic PNG and manifest. This is NOT accepted Core RiverNetwork, physical water Q or proof of perennial lakes.
- Thresholds `stream_threshold_km2=30` and `matching_tolerance_km=30` are editable **demo** parameters, not immutable Earth/world rules. Matches only same boundary side within spatial tolerance, unique one-to-one, always tagged GEOMETRICALLY_NEAR_ONLY_NOT_SAME_WATERSHED; unmatched stays UNMATCHED, no terrain correction or A8→MFD forced merge.
- [Operator evidence](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-mfd-outlet-review.md). [GREEN synthetic map](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499) with 49 focused tests: toy A8 has **1 major macro exit**, new connected MFD cartoon has **19 terminal edge cells**, **1 same-side within-30km purely spatial match**. The discrepancy is exposed, not patched. Old source A/B/C major EXITS known A=1, B=2, C=0, but **actual real private A/B/C CHILD MFD outlet matching was NOT yet run**, do not invent distances.
- The CI demonstration is SYNTHETIC ONLY; original private literary planet A8/A12 and derived real maps have not been committed to public GitHub. Full pytest is to be confirmed at FINAL branch SHA; earlier source version had 554 tests passed. PR #103 DRAFT/UNMERGED. PR #99–101 remain drafts. dev/0.2 and frozen release untouched.
- **NEXT P2-B2.5**: run real private A/B/C matching, then specifically condition coarse river corridors and watershed boundaries on real source at 1km without changing original macro-station heights; recompute MFD and compare before/after. Land cover P3 and ImageGen only after credible river continuity.


### P2-B2.4 current observable output (draft #103; 2026-11-20)

- External old A8 OUT→child edge comparisons vs Core-dominant MFD channel topology, no forced river joins. Synthetic 1 macro A8 exit vs 19 new MFD edge terminals, 1 geometric same-side near match within 30km; 49 focus tests GREEN. [Checkpoint](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499), [audit](reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md), [CLI](world-fixtures/planetary-child-mfd-outlet-review.md).
- New child river mask is the dominant Core MFD projection with terrain-aware area/slope eligibility, NOT the accepted vector RiverNetwork or a valid world-specific annual Q. Geometrical lake proxy jumps are NOT physical river segments. Real private A/B/C still need the same exact test.
- NEXT P2-B2.5: source-conditioned major local river corridor/parent macro elevation and watershed reconciliation with a rerun of Core MFD. Do not paint old D8 or ImageGen rivers before this. #103 draft/unmerged; dev/0.2 and frozen release unchanged.



### P2-B2.5, 2026-11-20 — REAL PRIVATE A/B/C preliminary MFD check and NEGATIVE river-carving result

- Local PRIVATE original A8/A12 ZIPs used for independent 231×231 child DEM and Core-like Freeman MFD dominant-channel reconstruction **WITHOUT full current PR lake-supernode routing** (not byte-exact PR #103). Old major A8 exits vs same-side near new modeled terminals (30km): A=1 old exit / 1 near (0.028km), B=2 old / 2 near (1.078 and 3.682km), C=0 old / no verifiable exit matches. New independent channel-edge terminal counts 36/40/63. Source elevation anchors are mathematically fixed; PNG/JSON kept PRIVATELY in ChatGPT, never published to GitHub. This is *preliminary evidence only*, not a production PR reproducibility claim.
- New opt-in external `scripts/propose_planetary_river_corridor_v02.py` performs bounded negative excavation beside old A8 coarse river segments, preserving every original macro DEM station analytically, child boundary cells, land/sea sign; reevaluates after with actual connected Core MFD. It **NEVER automatically updates Core/child terrain**, and is marked NONCANONICAL and NOT_SEAMLESS across changing crop origins. A separate private independent A/B/C trial at -15m cap: A exit worsened from 0.028km to ~11.972km; B did not improve; C no old major exit to judge. **DO NOT APPLY THIS TRIAL** to real planet as-is; counterexample to global source-carving assumption.
- [Operator negative result](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) · [optional CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-river-corridor-trial.md) · [synthetic GREEN 57 focused tests](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Need check full pytest on final documentation SHA.
- **NEXT P2-B2.6:** compare true current Core lake-supernode routing on real B/C vs independent no-lake channels; diagnose 80m/55m virtual Priority Flood fill, verify basin shape/spills and decide whether topography needs targeted changes or world-defined lake/water rules. No false Earthlike norms; do not overbuild physics. PR #103 DRAFT/UNMERGED, #99–101 drafts, dev/0.2 and release/0.2-prealpha unchanged.


### P2-B2.5 conclusion: do NOT force old D8 macro rivers into already near-aligned MFD exits

Real private source independent check old macro exit distance A~0.028km, B~1.078/3.682km, C none to test. Experimental bounded corridor excavation A worsened to ~11.972km, B no benefit, C no macro exit. Exact Core-with-lakes replay on real private A/B/C remains outstanding; prior independent test did not use full Core lake supernodes. [Review](reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) / [CLI](world-fixtures/planetary-river-corridor-trial.md). New synthetic Actions 57 focus tests GREEN. **NEXT P2-B2.6** real B/C candidate lake/priority-flood and topology review; do not conflate geometric fill with water. #103 draft/unmerged; canonical branch frozen.



### P2-B2.6 — 2026-11-21: Core geometric lake proxies versus baseline MFD (DRAFT #103)

- Read-only experimental `scripts/diagnose_planetary_child_lake_topology_v02.py`: accepted Core priority_flood_surfaces, extract_lake_candidates, continuous_routing_field, choose_lake_outlets, bounded nested hierarchy, plus P2-B2.2 fast MFD/lake supernode accumulator **parity-checked against full accepted Core on SMALL synthetic lakes**. Same unchanged DEM with vs without routing proxy. Reports BOTH internal redistribution and terminal-edge balance (km², NOT Q); fail-closed unresolved/comparison-not-available mask if >12 basins, >12k candidate cells, or Core spill topology fails. No real lake occupancy inferred.
- [Operator review](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-6-core-lake-topology-vs-private-bc-2026-11-21.md) · [private checkout CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-lake-topology-compare.md). Synthetic Actions has three paths: unresolved many-basin region, forced unresolved, and 21x21 POSITIVE one-bowl exact Core-parity + PNG. Current SHA CI status must be read after docs update, not inferred.
- Original PRIVATE B/C real source tested in a **separate independent reconstruction of published P2-A/priority flood/MFD/spill algorithms, NOT an imported full PR #103 Core**. 1km candidate sizes: B 3 basins / 4185 cells, C 1 / 2135 cells at demo 16km²/10m; virtual fill maxima ~67.45m /55.18m. Candidate lake routing substantially changes INTERNAL contributing area (peak absolute ~19,256/32,124km²) but edge area remains fixed to ~1e-10km² numerical error. Earlier independent baseline obtained different counts; DO NOT treat these as author-canon or exact Core/regression. Private PNG and JSON are only in conversation, NOT GitHub.
- No original planet terrain changed. No macro A8 external water injected. Next **P2-B2.7** reproducible exact real B/C run in a checked-out PR #103 with source privacy, then basin-specific water occupancy/seasonality and onward P3 natural cover/P4 map/satellite-like art. PR #103 DRAFT/UNMERGED, PR #99–101 drafts separate, dev/0.2 and frozen release unchanged.


### Current P2-B2.6 implementation (DRAFT #103)

External Core-based geometry comparison script and 9 new focused tests, explicit full-size no-lake vs Core lake supernodes fast-conservative area graph and a positive old-Core-parity 21x21 synthetic bowl. Example large synthetic region yields >12 candidates and should be UNRESOLVED rather than claiming a zero lake effect. [Review](reviews/p2-b2-6-core-lake-topology-vs-private-bc-2026-11-21.md) / [CLI](world-fixtures/planetary-child-lake-topology-compare.md). Independent private B/C comparison from source has B=3 basin proxies / 4185 cells, C=1 / 2135, with internal area redistribution but negligible terminal edge changes; NOT exact Core checkout, NO permanent lake claim. Next P2-B2.7 exact private same-code replay and author-specific water profile, then P3.
