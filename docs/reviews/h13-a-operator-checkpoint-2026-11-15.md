# H13-A implementation — operator checkpoint (NOT ACCEPTED)

**Date:** 2026-11-15  
**Repository:** `MysterioCrypto/domain_generator`  
**Base:** `dev/0.2`  
**Design:** [PR #98 — ACCEPTED / MERGED](https://github.com/MysterioCrypto/domain_generator/pull/98), merge `0000a208183a2ff3b1d7dc8eee8f93d54f72ef35`  
**Implementation:** [PR #99 — DRAFT / OPEN / UNMERGED](https://github.com/MysterioCrypto/domain_generator/pull/99)  
**Verified semantic HEAD:** `26292d3774867a33de6c3b33ee184a903b626363`  
**Runtime acceptance:** **PENDING OPERATOR**  
**Immutable release:** `release/0.2-prealpha` at `c69c1af010a085fb80d248af703a77471fc6c9d7`.

## Evidence

- [H13 operator checkpoint: G01–G15 + 8 diagnostic PNGs + JSON report](https://github.com/MysterioCrypto/domain_generator/actions/runs/43722355111) — GREEN, 15 PASS.
- [Full PR pytest](https://github.com/MysterioCrypto/domain_generator/actions/runs/43722354997) — GREEN, **517 passed**.
- [Full push pytest](https://github.com/MysterioCrypto/domain_generator/actions/runs/43722348833) — verify completion when inspecting latest HEAD.
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

## Review questions and confidence

1. Does the read-only diagnostic remain distinctly separate from MFD *area*, river topology and physical discharge? **YES** for tested contract and fixtures.
2. Are C1 precipitation, C2/C3, C4/C5, lakes/networks and old fingerprints unchanged when only H13 changes? **YES** by exact equality and historical fingerprints.
3. Are marine sources omitted and non-marine contributions accounted at the first marine entry? **YES** on synthetic cases and coastal A08.
4. Does the numerical source ledger conserve under MFD splits and lake supernodes? **YES** within float64 tolerance on tested fixtures.
5. Has H13 established real runoff, perennial rivers, deltas, wetlands, groundwater or validated global atmospheric circulation? **NO**. These are still scientifically and architecturally unmodeled.
6. Has the implementation been accepted for merge? **NO**. Separate explicit operator **IMPLEMENTATION ACCEPT / REJECT** required.

**Technical assessment:** ready for operator consideration based on tests, invariants and representative render; scientific limitations are explicit. This document records evidence, not operator acceptance.
