# C2 pragmatic three-scene tabletop map checkpoint — 2026-11-15

Status: **VISUAL SANITY CHECK / RENDERER EXPERIMENT ONLY**. Existing C1/C2/C3/H12 algorithms and defaults unchanged.

Branch: `experiment/v0.2-moisture-gradient-checkpoint`, [draft PR #100](https://github.com/MysterioCrypto/domain_generator/pull/100) (not merged). [H13 runtime PR #99](https://github.com/MysterioCrypto/domain_generator/pull/99) separately remains draft/unmerged.

**Operator-facing artifact:** [GitHub Actions — dry, wet, coastal cartographic checkpoint](https://github.com/MysterioCrypto/domain_generator/actions/runs/43730764902) → `tabletop-c2-maps-v02` (10 PNGs + JSON report; inspect workflow result before reusing as proof). Earlier successful numeric+render proof for the *prior* coastal palette version: [run 43730254158](https://github.com/MysterioCrypto/domain_generator/actions/runs/43730254158).

## Question

Does changing existing C2 recipe `water_moisture_decay_km` from 2.0 to 4.0 km (boost unchanged at 0.55) produce a visually beneficial smoother moisture transition across three contrasting climate/marine conditions without inventing soil physics or corrupting rivers?

## Fixture and strict invariants

Every scenario uses the existing A08 64×48 km, 1 km/cell terrain and deterministic seed 8008. **These are three climate/marine conditions on one terrain, not independent geographic examples.**

| Scene | Configured annual mean precipitation | Marine support | Changes baseline→candidate |
| --- | ---: | --- | --- |
| Dry inland | 180 mm/year | no | only C2 decay 2→4 km |
| Wet inland | 1500 mm/year | no | only C2 decay 2→4 km |
| Coastal | 800 mm/year | H12 sea level 0 m | only C2 decay 2→4 km |

Within each pair, elevation, water depth, C1 temperature/precipitation, all accepted river networks, generated feature geometry, and exported field IDs must be exact-equal. Water cells retain exact C2 moisture 1.0.

## Measured results

95th percentile absolute moisture difference between adjacent 1-km cells (unitless C2 score, not physical water content):

| Scenario | Land-land p95 2→4 km | Change | All-edges p95 2→4 km | Change | Mean land C2 moisture 2→4 km |
| --- | --- | ---: | --- | ---: | --- |
| Dry inland | 0.071806→0.058055 | −19.2% | 0.513056→0.440132 | −14.2% | 0.32928→0.41135 |
| Wet inland | 0.034156→0.024943 | −27.0% | 0.184363→0.161900 | −12.2% | 0.75675→0.78222 |
| Coastal | 0.047993→0.037101 | −22.7% | 0.284415→0.244929 | −13.9% | 0.63277→0.67493 |

C3 average vegetation also shifts because its accepted recipe uses C2: dry `0.17065→0.21339`, wet `0.39339→0.40667`, coastal `0.32926→0.35127`. The dry-world change is substantial: broadening water influence may make supposed arid worlds too green, so prefer a **selectable art-direction input recipe**, not a universal new constant.

## Visual assets and product direction

The `tabletop-c2-maps-v02` artifact contains:

- `01-dry_inland-moisture-before-after.png`, `01-wet_inland-moisture-before-after.png`, `01-coastal-moisture-before-after.png` — paired absolute-scale C2 comparison;
- matching `02-<scene>-vegetation-before-after.png` — downstream C3 consequences;
- `03-<scene>-cartographic-preview.png` — first actual map-like composite with hillshade, continuous greenness proxy, rivers, accepted inland lake polygons, H12 sea support when enabled, subtle contours;
- `04-three-scene-p95-summary.png` — compact numerical sanity summary, plus `report.json`.

**Rendering caution:** Do not paint every 1-km water-depth/channel raster pixel as a lake or 1-km-wide river. Instead, blue-fill only real marine support and accepted lake polygons; draw rivers from accepted vector centrelines. This is a visual distinction, not a hydrology patch. A first fix mistakenly escaped newline characters within a Python comment and hid marine fill; corrected on SHA `68df29d7f60f85ed3d59839e8fcb3763838dbf3c` with an explicit sea RGB assertion in cartographic output.

The composite is intentionally a **technical-art direction preview**, not a final atlas. Colors are continuous greenness/terrain proxies and must never be described as newly modelled biomes or as vegetation ecology. The next product-facing improvement should focus on readable water, coastline, relief, settlements, labels, legends and exportable layers for an eventual art pass, rather than more climate parameter sweeps.

## Decision and stopping rule

**Technical judgement:** 4 km decay clearly reduces local numerical abruptness in all three tested conditions; 2 km remains useful for arid tonal intent. No global model/default change, no merge of draft PR #100 or #99, and no separate operator approval request for numerical internals. Map aesthetics are the legitimate next operator-checkable gate. Frozen release `release/0.2-prealpha` remains at `c69c1af010a085fb80d248af703a77471fc6c9d7`.
