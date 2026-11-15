# Project Progress Tree

Purpose: **current** DONE / IN PROGRESS / NEXT tree for chat recovery. For the dependency/context map and rejected hypotheses read `docs/CONTEXT.md`; for normative semantics read accepted `docs/design/*`.

**Active line:** `dev/0.2` · **checkpoint:** H13-A IMPLEMENTATION — DESIGN ACCEPTED, IMPLEMENTATION NOT ACCEPTED · **H12-A:** ACCEPTED / MERGED PR #97 (`3d275466ec5bfdb74f5dcb88bea6c8b641347f70`).
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

## NEXT

```text
1. H13 design PR #98 — ACCEPTED / MERGED 0000a208183a2ff3b1d7dc8eee8f93d54f72ef35
2. separate H13 implementation branch — develop opt-in source-weighted MFD diagnostic and G01–G15
3. full pytest and wet/dry + coastal operator-visible checkpoint, then separate implementation ACCEPT / REJECT
4. do not merge implementation before explicit operator decision
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


## Current active gate — H13-A implementation (2026-11-15)

```text
H13 design #98       OPERATOR ACCEPTED / MERGED
merge SHA            0000a208183a2ff3b1d7dc8eee8f93d54f72ef35
implementation       SEPARATE BRANCH / NOT ACCEPTED
G01–G15             NEXT TECHNICAL GATE
full pytest          PENDING IMPLEMENTATION
operator checkpoint  WET/DRY + COASTAL; PENDING
implementation merge FORBIDDEN until separate explicit ACCEPT
frozen release       c69c1af010a085fb80d248af703a77471fc6c9d7
```

Why H13: C1 gross precipitation is already known and the MFD weighted DAG supports strictly mathematical accumulation without inventing runoff or permanence. Keep lake supernode identity, marine absorption, exact upstream field stability, and no delta/biome shortcut. See `docs/CONTEXT.md` and accepted design.


## Product-facing map compositor checkpoint — 2026-11-15 (DRAFT / NOT MERGED)

- Parallel branch `feature/v0.2-tabletop-map-compositor`, [PR #101](https://github.com/MysterioCrypto/domain_generator/pull/101) DRAFT, branched from accepted `dev/0.2`; H13 runtime #99 and experimental C1/C2 #100 also remain DRAFT. No default, world runtime, hydrology or frozen-release change.
- User asks for **expressive, plausibly consistent tabletop/literary maps from pre-specified DomainSpec**, not dissertation-grade climate calibration. Prior accepted preset/dependent-placement pipeline is still present: authored `FeatureSpec` IDs/labels/presets/tags; fixed/ranged parameter overrides; hard/soft `ConstraintSpec` with literal point/region and named domain selectors; deterministic `suitability_placement` with SiteProfile preferences and requirements. Exact manual coordinate locking via graphical drag-and-drop is **not** claimed as implemented.
- Existing `DomainSpec.surface.water_moisture_decay_km` is an editable strict-positive float; user can choose 4 km in JSON instead of changing defaults. Example `examples/tabletop-map/domain-request.json` declares one ridge and three named settlements with hard west/east/south region constraints. The accepted A08 settlement preset supplies temperature/precipitation requirements and drainage proximity preference. Successful Actions proof generated 3 POIs with their labels unchanged, point positions 14.92×23.42, 44.42×24.21, 23.17×3.71 km, and 5 pixel-aligned 1536×1152 RGBA layers.
- `scripts/render_tabletop_domain_map_v02.py` consumes an explicit user request and catalog, draws generated terrain palette, H12 sea if opted, **lake polygons (not 1km river raster pixels)**, accepted river centerlines, POI markers and collision-aware labels; writes a composite map, clean map, parchment alternative, framed preview and provenance/position manifest. This is post-generation presentation only. Fully preserved raster/POI world coordinates; markers never move, only label candidates do.
- [GREEN operator-facing visual Actions workflow](https://github.com/MysterioCrypto/domain_generator/actions/runs/43732653717): downloadable `tabletop-atlas-v02`, first inspect `08-atlas-preview.png`. Placement/DomainSpec targeted regression **54 passed**; full pytest runs separately. Usage and hard limits: `examples/tabletop-map/README.md`.
- Next decision should be visual: map readability (water, settlement symbols, labels, scale), not operator approval of internals. Explicit merge instruction required for draft PR #101; no automatic acceptance of #99/#100. Release `release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Tabletop atlas readability and optional art-direction slice — 2026-11-15

- Product-facing priority: **readable, expressive TTRPG/literary maps**, not increasingly elaborate climate physics. The first atlas was geographically coherent but low-contrast, with tiny labels and identical symbols for all settlements. Improve presentation only: stronger relief shading, subtle elevation contours, clearer label plaques, larger type, north/scale/legend framing, and icons selected by *explicit authored tags* `village` vs `fort` (never inferred settlement populations).
- Renderer `scripts/render_tabletop_domain_map_v02.py` now exports a sixth aligned transparency layer `10-relief-contours.png` in addition to the five original terrain/water/river/POI/text layers, and preserves the original named filenames. Contour interval is a **cartographic display choice** based on accepted elevation, not an extra geomorphological model. Confirm source POI coordinates and accepted rivers are byte-stable under renderer-only changes; the dedicated Actions job checks all three POI coordinates, symbols, aligned layers, visible contours and label placement. 
- Add `11-parchment-no-labels.png` and `12-stylization-brief.txt`: optional image-illustration source and a constraints-first art handoff. Keep coastlines, lake polygons, river paths, POI coordinates and text as separate authoritative overlays; ImageGen is NOT assumed to preserve precise topology by itself. Always recompose original RGBA water/rivers/markers/labels after stylization if needed. 
- All map visuals remain derived **only** from the already accepted `DomainData` and user `DomainSpec`. No hidden roads/biomes, no physically modelled river discharge, and no change to Core 0.2 generation or frozen prealpha. Example still uses editable `surface.water_moisture_decay_km=4.0`, while preserving other allowed positive values; three fixed-named, constrained semi-procedural settlements are unchanged. This is a display renderer checkpoint, not a new placement feature.
- Work remains in draft [PR #101](https://github.com/MysterioCrypto/domain_generator/pull/101), **OPEN / UNMERGED**. Independent H13 runtime PR #99 and gradient experiment PR #100 likewise remain draft/unmerged. Targeted map CI previously GREEN at [Actions run 43733960567](https://github.com/MysterioCrypto/domain_generator/actions/runs/43733960567); extended art handoff must be revalidated on its latest head before operator sees final checkpoint.
- Stop rule: do not expand scientific tuning on the strength of a nicer palette. Next valid operator feedback is on actual updated `08-atlas-preview.png` and `09-parchment-palette.png` in the latest GREEN GitHub Actions artifact `tabletop-atlas-v02`. Do not ask for acceptance of internal test design, and do not infer approval to merge drafts.
