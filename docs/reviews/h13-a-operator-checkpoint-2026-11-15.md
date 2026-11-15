# H13-A implementation — operator checkpoint (NOT ACCEPTED)

**Date:** 2026-11-15  
**Repository:** `MysterioCrypto/domain_generator`  
**Base:** `dev/0.2`  
**Design:** [PR #98 — ACCEPTED / MERGED](https://github.com/MysterioCrypto/domain_generator/pull/98), merge `0000a208183a2ff3b1d7dc8eee8f93d54f72ef35`  
**Implementation:** [PR #99 — DRAFT / OPEN / UNMERGED](https://github.com/MysterioCrypto/domain_generator/pull/99)  
**Verified implementation/test HEAD:** `d6b76c312a251100695abd48a11fe28877b7e17e`  
**Runtime acceptance:** **PENDING OPERATOR**  
**Immutable release:** `release/0.2-prealpha` at `c69c1af010a085fb80d248af703a77471fc6c9d7`.

## Evidence

- [H13 operator checkpoint (PR): G01–G15 + 8 diagnostic PNGs + JSON report](https://github.com/MysterioCrypto/domain_generator/actions/runs/43723094447) — GREEN, 15 PASS; [push checkpoint](https://github.com/MysterioCrypto/domain_generator/actions/runs/43723089353) — GREEN.
- [Full PR pytest](https://github.com/MysterioCrypto/domain_generator/actions/runs/43723094387) — GREEN, **517 passed**.
- [Full push pytest](https://github.com/MysterioCrypto/domain_generator/actions/runs/43723089326) — GREEN, **517 passed**.
- Artifact within checkpoint workflow: `hydrology-v02-h13`; workflow stores 8 PNGs and `report.json`. No large artifact is attached here.
- All prior world field payloads, features and networks remain **exact-equal** when toggling H13 at otherwise identical input.
- C1 source: annual precipitation `float32` (mm/year); H13 mathematical accumulation/output: `float64` (`m3/year`), marked **derived**.
- Uniform 1000 mm/year, no marine: H13 matches existing `flow_accumulation_km2 × 1,000,000` with **maximum absolute difference 1.1920928955078125e-7 m³/year**.
- Input/terminal conservation checked independently for land outlets, lake supernodes, MFD forks and first-entry H12 marine receivers.

## Representative fixtures and ledgers

| Fixture | Configured C1 mean (mm/year) | Gross source (m³/year) | Terminal error (m³/year) | Notes |
| --- | ---: | ---: | ---: | --- |
| Dry inland A08 | 100 | 306,403,590.042114 | −0.0000000596 | 4 inland lakes, no marine |
| Wet inland A08 | 1800 | 5,515,264,620.483398 | −0.0000019073 | Same terrain; 18× median gross input |
| Inland reference A08 | 900 | 2,757,632,310.241699 | −0.0000009537 | Non-marine uniform-identity baseline |
| Coastal A08 | 900 | 2,632,837,588.684082 | +0.0000004768 | 154 marine cells, 4 inland lakes, 2 marine components |

Coastal receiver accounting (m³/year):
- land-domain edges: `1,944,176,811.9092715`
- `marine-0001`: `420,032,709.0809797`
- `marine-0002`: `268,628,067.69383055`
- total terminals: `2,632,837,588.6840816`

**Do not sum the whole raster to estimate catchment mass:** every upstream source is intentionally represented at successive downstream nodes. Conservation is defined over unique local sources and terminal receipts.

## Operator-visible panels (artifact)

1. `01-dry-c1-precipitation.png` — accepted C1 annual rain input
2. `02-dry-gross-input.png` — no-loss accumulated source allocation in dry inland fixture
3. `03-wet-c1-precipitation.png` — accepted C1 wetter rain input
4. `04-wet-gross-input.png` — wet gross upstream allocation
5. `05-accepted-mfd-area.png` — existing area field, **not** actual discharge
6. `06-coastal-gross-input.png` — coastline, marine source exclusion and unchanged river networks
7. `07-uniform-identity-error.png` — residual of H13 vs frozen MFD area × 1e6
8. `08-local-and-upstream-traces.png` — three illustrative directed MFD paths, local source vs accumulated source at selected cells

Logarithmic display is a **renderer-only transform**; numerical raster is unmodified. Each map auto-scales its colors, so dry/wet comparisons must be made using numeric fields/report, not an assumed shared colorbar.

## Strengthened exact oracles before final gate

- **G04:** the uniform precipitation identity with the frozen MFD area kernel is now explicitly tested both with and without a lake supernode. This catches lake source double-counting and outlet discrepancies that a no-lake grid cannot reveal.
- **G08:** an intentionally adversarial marine receiver has a seabed-to-land outgoing fraction; the H13 ledger must stop at first marine entry and not contaminate terrestrial accumulations.
- **G09:** an enclosed below-sea inland depression is represented as an ordinary inland lake supernode with local and upstream precipitation. A disconnected marine boundary cell is excluded from land sources, but the below-sea inland basin remains included. The previous trivial one-cell-only accounting check was strengthened.
- No runtime, accepted routing, rain, stage or public contract changed in this strengthening commit; only test evidence changed. All G01–G15 and 517 full tests remained GREEN on `d6b76c312a251100695abd48a11fe28877b7e17e`.

## Review questions and confidence

1. Does the read-only diagnostic remain distinctly separate from MFD *area*, river topology and physical discharge? **YES** for tested contract and fixtures.
2. Are C1 precipitation, C2/C3, C4/C5, lakes/networks and old fingerprints unchanged when only H13 changes? **YES** by exact equality and historical fingerprints.
3. Are marine sources omitted and non-marine contributions accounted at the first marine entry? **YES** on synthetic cases and coastal A08.
4. Does the numerical source ledger conserve under MFD splits and lake supernodes? **YES** within float64 tolerance on tested fixtures.
5. Has H13 established real runoff, perennial rivers, deltas, wetlands, groundwater or validated global atmospheric circulation? **NO**. These are still scientifically and architecturally unmodeled.
6. Has the implementation been accepted for merge? **NO**. Separate explicit operator **IMPLEMENTATION ACCEPT / REJECT** required.

**Technical assessment:** ready for operator consideration based on tests, invariants and representative render; scientific limitations are explicit. This document records evidence, not operator acceptance.

## Operator-visible visual comparability upgrade — 2026-11-15

This bounded **renderer/checkpoint-only** change does not modify H13 runtime, accepted drainage, source accounting, schema or world output. The original dry/wet panels independently auto-scaled colors: both could look virtually identical despite the 18-fold source-volume difference. An unshared colorbar is unsuitable for direct visual judgement.

The revised GitHub Actions artifact now also includes:

- `09-dry-wet-shared-absolute-scale.png` — dry and wet gross-input maps rendered on the **same absolute log color scale**. The 18-fold input contrast is visible without reading separate legends.
- `10-opposite-winds-c1-shared-scale.png` — the accepted C1 spatial rain raster for moisture-transport bearing 90° vs 270°, with identical terrain, seed, annual-mean precipitation and scale.
- `11-opposite-winds-h13-shared-scale.png` — the H13 gross-upstream-input raster with the **same color scale** under opposite moisture transport. This tests a spatial change, not merely uniform wet/dry multiplication.
- `12-opposite-winds-h13-signed-delta.png` — signed difference **westward minus eastward** H13 gross input, centered at zero. Positive/negative values show changed *atmospheric source allocation*, not changes to river flow.

The checkpoint enforces exact invariance of terrain, water, MFD fractions/area and network topology under reversal of the moisture-transport bearing. It also verifies C1 rainfall and H13 gross input genuinely differ (no cosmetic-only map change). These are scientific/visual diagnostics of accepted C1+H13 coupling, **not** claims about actual runoff or discharge. Numeric differences and common color bounds are stored in `report.json`.

**Updated gate:** request visual feedback only after a GREEN Actions run generates these 12 PNGs. Do not ask the operator to audit code or formally approve internal technical checks; maintain PR #99 draft/unmerged pending an unambiguous release/merge decision.
