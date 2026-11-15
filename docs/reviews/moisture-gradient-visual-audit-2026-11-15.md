# C1/C2 moisture-gradient visual audit — 2026-11-15

Status: **EXPERIMENT / VISUAL CHECKPOINT ONLY — NO MODEL CHANGE OR OPERATOR ACCEPT**.

- Branch: `experiment/v0.2-moisture-gradient-checkpoint`, draft [PR #100](https://github.com/MysterioCrypto/domain_generator/pull/100), based on `dev/0.2`.
- [View completed GitHub Actions and download `moisture-gradient-comparison-v02`](https://github.com/MysterioCrypto/domain_generator/actions/runs/43727764619).
- Artifact folder `moisture-gradient-audit-v02` has **12 PNG panels + `report.json`**; `c2-water-proximity-audit-v02` has **5 PNG panels + `report.json`**.
- H13 implementation remains separately proposed in draft PR #99; no merge occurred.

## Why

User asked whether the moisture gradient actually became softer. Prior H13 changes only made maps visually comparable through shared-scale colorbars; **they did not change C1/C2 world fields**. A plot with softened colors alone does not constitute a softer numerical gradient.

This audit holds A08's terrain/seed, climate annual mean, MFD routing, river networks and lakes fixed. It varies **accepted explicit input parameters** in temporary generation requests (not global defaults) and plots C1 rain, C2 moisture, C3 vegetation with identical scales. For numeric comparisons, define a local gradient as the absolute difference of neighboring 1-km grid-cell values; the primary p95 excludes pairs touching water (to distinguish gradual land transitions from the exact hard-water `moisture=1.0` rule). Secondary p95 includes all pairs.

## C1 atmospheric sensitivity — one input family at a time

| Scenario | Orographic scale (km) | Orographic strength | C1 rain neighbor p95 (mm/year) | C2 moisture land-neighbor p95 |
| --- | ---: | ---: | ---: | ---: |
| Accepted fixture baseline | 18 | 1.20 | 28.0714 | 0.0461003 |
| Reduced relief contrast | 18 | 0.75 | 19.2642 (−31.4%) | 0.0440654 (−4.4%) |
| Longer upwind reference | 27 | 1.20 | 29.7834 (+6.1%) | 0.0453395 (−1.7%) |
| Both | 27 | 0.75 | 19.8356 (−29.3%) | 0.0441415 (−4.2%) |

Land precipitation mean remained 850 mm/year (floating-point tolerance) in every case. C1-only reduction therefore redistributes spatial contrast rather than changing total requested mean.

Read-only C2 component reconstruction on the baseline gives p95 adjacent-land-cell differences: `climatic_wetness=0.01085`, `water_proximity_signal=0.09138`, `climate_gated_catchment=0.10108`, `slope_retention=0.00107`. The terms are combined nonlinearly, so their p95 values cannot be added as independent contributions. **Interpretation:** near-water and contributing-area signals explain why C2's river-adjacent visual bands barely respond to C1 softening.

## C2 water-proximity recipe sensitivity — C1 entirely unchanged

| C2 configuration | Boost | Distance decay (km) | Land-to-land neighbor p95 | All-edge neighbor p95 | Mean land moisture |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.55 | 2 | 0.04610 | 0.27288 | 0.64462 |
| Lower boost | 0.40 | 2 | 0.03776 (−18.1%) | 0.30059 (+10.2%) | 0.63387 |
| Longer decay | 0.55 | 4 | 0.03517 (−23.7%) | 0.23709 (−13.1%) | 0.68413 |
| Combined | 0.40 | 4 | 0.02759 (−40.2%) | 0.28087 (+2.9%) | 0.65936 |

Read-only analysis identifies **longer decay at the same boost** as a candidate that softens both land gradients and bank transitions, at the cost of raising broad-area wetness. This is not necessarily more plausible in all climates or terrain.

The following invariants were exact: existing accepted elevation, water depth, C1 precipitation/temperature (in C2-only run), river networks, feature geometry. Water cells remain exactly `moisture=1.0`. C2 and C3 formulas are unchanged.

## How to inspect

Start with `c2-water-proximity-audit-v02/01-c2-moisture-4ways.png` and `04-c2-adjacent-cell-gradient-statistics.png`. Contrast them with `moisture-gradient-audit-v02/01-precipitation-4ways-shared-scale.png`, `02-moisture-4ways-shared-scale.png`, and `12-c2-component-decomposition.png`.

The purpose is to decide whether **visual and numerical changes are desirable**, not to approve a hidden algorithm. There is no post-hoc Gaussian blur or any unapproved physical hydrology model.

## Next step and stop rule

If visual feedback favours a softened wetness transition, design a bounded opt-in or explicit recipe change with reproducible contrasting arid/humid/coastal fixtures, same shared-scale maps, land/water boundary metrics and downstream C3 consequences. Do not globally change accepted C2 semantics on a single A08 fixture; do not merge draft PR #100 or #99 without a clear applicable decision.
