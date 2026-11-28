# P3.3 — Osvera region A first original-A8/A12 atlas (NOT CANON)

**Date:** 2026-11-21
**PR:** #103 — DRAFT / UNMERGED
**Operator status:** no author visual acceptance yet.
**Input confidentiality:** original private A8/A12 archives have NOT been pushed to GitHub.

## What was actually executed

- A8 and A12 original ZIPs were read from the owner's connected Google Drive into an ephemeral execution environment; both SHA-256 matched the previous source inventory:
  - A8: 6824ccf2a4aea7b2514a4e694e84ad13fd3ff4e18dba6c3be6b4b7753dc019ec
  - A12: db9f0f91fca845058c658dfdd639c882b9cf0514736b3677184a4c84ff20b3a4
- P1 load_archives checked global A8/A12 elevations, land and axis orientation: 600 × 1200 stations. P1 region_crop used a one-station halo around region A center (-47.25°, -98.25°); planet radius 7008.1 km, year 202.755 Earth days.
- Macro crop: 9 × 11 stations. P2-A generate_child produced 231 × 231 pixels over 230 × 230 km with 1-km spacing. 63 original DEM anchors retained; maximum parent anchor deviation **0.0 meters**.
- P3 classify_cover used ORIGINAL A12 scenarios and the working editable cover profile. Atlas audit_atlas + render_sheet used the current first-arc author ledger; no landmarks, rivers or routes were invented.
- Four exact-checkout computational modules were executed by a temporary local orchestration script. The current build_author_atlas_v02.py *CLI wrapper itself was not executed* against private ZIPs. Do not describe this as a CLI acceptance.
- At run time the exact Git blobs on HEAD d768808a17f3fda838280c8d27ab6e6f82eef023 were verified: P1 d4ba7a11f6a04d786a4971cb969b61f36e5a8900; P2 945f9105879dd52a7fe5e5fcca2b7ea0937444dd; P3 edbb8267fe97a7b2c44f97c96616c84c5e8c682f; atlas f404c2a1d1e5894c0d708987460886808c8ea332.
- After visual inspection, atlas legend/footer layout was corrected in #103 and the same underlying child DEM/cover were rendered again. This renderer change does not alter model arrays.

## Actual measured model fractions (noncanonical)

| Hypothetical class | Fraction |
| --- | ---: |
| POSSIBLE_WOODLAND | 0.64058 |
| POSSIBLE_OPEN_GROUND | 0.16731 |
| POSSIBLE_ROCKY_SLOPE | 0.00000 |
| POSSIBLE_WET_LOWLAND | 0.19211 |
| POSSIBLE_SPARSE_COVER | 0.00000 |

All 5 first-arc landmarks remain UNPLACED; the 2 routes remain without distances. Historical A8 D8 is not accepted Core MFD. No validated child river network, waterfall, wetland, road or travel cost. The pronounced oblique ridges and broad forest-like cover are **only a proposed appearance**.

## Private permanent artifacts

Private folder, nested under the owner's planetary-model folder:
https://drive.google.com/drive/folders/1gP6GiYaIrPPyciJutHzw1IVvuod9ugXI

Rendered atlas PNG after footer fix:
https://drive.google.com/file/d/1p4Ccrp2Q-lVuYTEk92BmjqApLzoxJaW5/view

Private review ZIP containing derived crop, child DEM, cover, PNG and build audit, **NOT the original ZIP archives**:
https://drive.google.com/file/d/1Cf4kY19FQku9eG67NhEHj1RQ0n9fa7yn/view

The temporary execution directory must not be regarded as a stable archive.

## Why this result matters and next gate

Actual original archives were in connected Google Drive; the prior assumption that they were unavailable was incorrect. Full original world-source validation and a meaningful private region A image are now possible. Initial visual inspection found a **legend/footer collision**, fixed in PR #103 with a synthetic rendering bbox regression.

**Next:** operator evaluates the new private single-sheet image for legibility, relief credibility and usefulness for first-arc geography. If rejected, localize the issue in source/terrain/P3 cover policy/renderer before adding extra modules. Child hydrology (P2-B2.7) is relevant when author feedback requires rivers, waterfalls, lakes or travel routes. PR #103 stays draft until an explicit decision; none of this is author canon or accepted Core 0.2.
