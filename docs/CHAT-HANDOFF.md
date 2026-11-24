# Chat Handoff Snapshot

Generated for chat transfer. If this snapshot conflicts with `PROJECT.md`, `docs/CONTEXT.md` or `docs/PROGRESS.md`, those canonical files win.

**NEWEST P4-K SEMANTIC REACH DISPLAY AND MACRO DIRECTION DIAGNOSTIC (2026-11-24; PR #103 DRAFT):** P4-J HEAD 607521f6 all 3 CI GREEN. PRIVATE region A original P4B 2.0/30 km² 231×231 source + P4-E background SHA verified via P4-J. 5,868 exact source edges partitioned into 927 reaches with 952 fixed source/confluence/terminal/boundary nodes; 4,941 other nodes need not be display vertices. RDP 0.35 km + two Chaikin passes, bidirectional 0.75 km corridor, land coverage, sampled nearest-original height difference guard 15m at ≤0.125km, no unsupported lake proxies, no new intersections. 581 reaches shifted >20m, max measured Hausdorff 0.708572km, sampled elevation difference max 1.873517m, 2 corridor/land fallbacks. Display length −3.0%, absolute internal turning −7.4%, unchanged source graph. Long same-heading runs ≥8 **within reaches**: 295/544 (54.2%) oriented within 22.5° of parent downhill vs 1897/5324 (35.6%) other edges; association only. More visible smoothing than P4-J, still synthetic regional pattern. Optional display-only result, not approved rivers/geography. 15 local tests pass; CI integrated, NumPy-only height sampling, PNG/NPZ exact vs initial run. [Private final v2 archive](https://drive.google.com/file/d/1HarTQ1wcjLzqVvoYonORlQnZGHIrQwxu/view), [review](reviews/p4-k-semantic-reach-display-corridor-review-2026-11-24.md). **NEXT P4-L:** stop cosmetic smoothing; controlled source/child terrain detail morphology hypothesis for valley coherence, anchored heights and coastline/boundaries, independent reroute under unchanged Core; no automatic acceptance or blanket old A8 D8 carving. Core dev/0.2 and frozen release untouched.

**PREVIOUS P4-J DISPLAY-ONLY TOPOLOGY-PRESERVING CHANNEL CURVES (2026-11-22; PR #103 DRAFT):** PRIVATE Region A baseline **original P4B strength=2.0**, 231×231 at threshold 30 km². Source network verified via prior P4-I SHA. New script `scripts/generalize_region_model_channel_geometry_v02.py` and 18 full synthetic graph+SHA+deterministic-CLI tests. Geometric display only: 5,868 ordinary model edges, 5,893 original graph nodes with **every endpoint/node coordinate and source→receiver ID exactly unchanged**. G1 per-edge sampled Hermite display (9 points/edge), strict ≤0.20 km Hausdorff source-segment displacement; observed maximum **0.13916 km**, P95 **0.07742 km**, mean **0.03203 km**, 2,902 edges shifted >20m, 2,966 essentially unchanged. STRtree proves **0 original and 0 new independent segment crossings**, no graph reroute, lake proxy, Q, approved river or terrain edit. **CRITICAL NEGATIVE PRODUCT FINDING:** real full-region map looks almost identical; 1-km cell-node-preserving smoothing cannot cure long grid-aligned chains. Cropped 65×65km shows only modest bend reduction, so save code as optional display adapter NOT approved regional map; do not tune blindly. [Full-map side-by-side](https://drive.google.com/file/d/19Hkx6ZQ3YZ9fOs1nBbEjURqhL-MWKXDt/view), [zoom side-by-side](https://drive.google.com/file/d/1i63mXqB56je2TW8fMMKOBPyKtzlvhLUB/view), [derived vector NPZ/PNG/JSON SHA ZIP](https://drive.google.com/file/d/1TMOAs6wfzYfqqhN7M0y4Vfeq6nylGBo2/view), [full review](reviews/p4-j-region-a-display-only-topology-preserving-channel-curves-2026-11-22.md). **NEXT bounded P4-K:** evaluate actual product-readability blocker at semantic network-scale (headwater/confluence/terminal fixed), with optional larger-scale corridor-constrained display geometry, but do not alter accepted MFD or invent natural rivers; if long directional macro-landform remains, diagnose source morphology rather than cosmetically draw fake flow. PR #103 Draft, accepted Core dev/0.2 and frozen release unchanged.

**PREVIOUS P4-I SOURCE-ANCHORED INTERPOLATION COUNTERFACTUAL (2026-11-22; PR #103 DRAFT/UNMERGED):** PRIVATE Region A 231×231, unchanged original macro A8 heights, coastline, coordinate grid, planet projection and each P4-E frozen child local detail; compare original C1 Hermite parent vs bilinear parent with **all 63 source height stations exact (0 m error)**. Parent height bilinear−Hermite ∆ ranges **−49.00 to +52.68 m**, RMS **9.335 m**. All three original P4-F model projections replay **BIT EXACT**, source SHA verified through P4-H; 0 km² external A8 area injected and MFD conservation verified. Independent bilinear re-routing produces different boundary outlet sets: strength 0.5 **22→20**, 1.25 **20→17**, 2.0 **25→22**; channel mask IoU Hermite/bilinear **43.37%/60.10%/65.71%**; straight single-heading runs ≥8 edges: **47.67→51.78% / 17.95→18.86% / 15.78→14.80%**. Parent-only control: 98.49→99.06%, 7→2 model outlets, and is NOT viable terrain. **CONCLUSION:** bilinear does NOT solve grid-aligned river skeleton, and would silently change model outlets. Preserve existing Hermite; do not select DEM/approve river or physically infer discharge. Added scripts/compare_region_parent_interpolants_v02.py (full SHA source and derived NPZ replay), **15 toy tests**, optional synthetic CI. [2×3 comparison](https://drive.google.com/file/d/1V46y7uZIhz35XcO75aSdubdlm78riVq1/view), [Δ-parent heatmap](https://drive.google.com/file/d/1JOGnRG1J94IskN29mCDXBk7lzF0LaAkk/view), [PRIVATE derived ZIP, 4 NPZ+JSON+CSV](https://drive.google.com/file/d/1Fa8OiUgD_yJaK3NZ7hXWJiSxxuLZMp16/view), [full review](reviews/p4-i-region-a-parent-interpolator-counterfactual-2026-11-22.md). **NEXT P4-J:** display-only topology-preserving vector/channel geometry generalization; assert node IDs/outlets/edges unchanged, bounded displacement and non-crossing, compare genuinely more readable author map. Accepted Core dev/0.2 and frozen release untouched.

**PREVIOUS P4-H PARENT-ONLY DIRECTIONAL NEGATIVE CONTROL (2026-11-22; PR #103 DRAFT/UNMERGED):** Recovered SHA-verified real PRIVATE P4-B/E/F/G 231×231 1-km source; unchanged accepted Core priority flood/MFD + dominant channel projection at threshold 30 km² independently rerun for parent-only interpolated height (**strength 0**) and 3 P4-E DEM strengths 0.5/1.25/2.0. All archived P4-F raster fields for 3 real DEMs reproduced **BIT EXACT**, 63 P4-E parent anchors unchanged, 0 km² external A8 catchment injected. Uniquely partitioned model edges into maximal same-heading 8-neighbor runs ≥8 cells: parent-only **98.49%** (35,728 ordinary edges; max 203 steps); strength 0.5 **47.67%** (9,095; max 42); strength 1.25 **17.95%** (6,374; max 24); strength 2.0 **15.78%** (5,868; max 29). Parent-only vastly overtraces 35,735 model channel cells: **NEGATIVE CONTROL not candidate rivers/terrain**. On identical fixed original-2.0 channel cells, continuous RAW downhill nearest 45° ±7.5° fraction 41.5% parent vs 36.4/31.9/31.0% for added detail, while continuous Core MFD fractions 43.7%/41.3%/39.8%/47.3%; mean model 1-receiver vs continuous MFD turn 10.6/12.4/11.9/10.9°. Direction *consistency over space* rather than exact diagonal fraction separates long straight-branch artifact. **CAUSE:** broad macro+interpolated parent terrain already supports strong straight chains, local detail interrupts them; discrete 8-neighbor projection quantizes all physical drawn edges. **UNRESOLVED:** distinguish intrinsic macro A8 source from interpolation algorithm itself with identical anchors. Added scripts/diagnose_region_directional_bias_v02.py, 19 toy+CLI guards and conditional synthetic CI. [4-panel region comparison](https://drive.google.com/file/d/1rmqJYcFyWysT42y9UPoyRfFGQdAO4iRO/view), [run-length chart](https://drive.google.com/file/d/1rLXr28VxInG-xLSoEGV7bQR5G7gFOnp6/view), [PRIVATE derived ZIP/CSV/JSON/SHA](https://drive.google.com/file/d/1fklqctRGDxl46P_OZDJzbH-66cP9LT1K/view), [full review](reviews/p4-h-parent-only-negative-control-directional-bias-2026-11-22.md). **NEXT bounded P4-I:** isolate macro A8 vs interpolation with an alternate anchored interpolant and/or model-preserving cartographic trace that does not alter nodes/outlets; no auto-accepted natural rivers/map, POIs or merged Core. PR #103 DRAFT, accepted dev/0.2 frozen untouched.

**PREVIOUS P4-G MODEL CHANNEL MAP THRESHOLD SENSITIVITY (2026-11-21, PR #103 DRAFT/UNMERGED):** Real private Region A, 3 fixed anchor-preserving P4-E terrains strength 0.5/1.25/2.0 × channel source thresholds 15/30/60 km². Nine independent calls to existing Core-compatible MFD projection, **all 3 threshold=30 outputs BIT-EXACT P4-F**, input SHA-256 validated, 63 P4-E parent anchors preserved; 0 km² A8 area injected and all mass ledgers conservative. Channel cells across thresholds: 0.5 **15083/9117/6004**, 1.25 **9354/6394/4538**, 2.0 **8513/5893/4248**; confluence counts 0.5 **1123/528/239**, 1.25 **968/449/211**, 2.0 **927/442/218**. Important: threshold change affects dominant receiver preference, model channel masks ARE NOT nested: at 60 vs 30, 0.5 has **466 NEW mask cells**, 1.25 **131**, 2.0 **101**. Visual defect remains: 0.5 produces conspicuously parallel diagonal/horizontal branches; 1.25 and 2.0 retain stepped grid look. Varying extraction threshold alone does NOT yield author-ready regional geography. New scripts/compare_region_channel_scale_v02.py, 18 toy tests, workflow geogrid 3×3 CI. [3 variant map](https://drive.google.com/file/d/1yV5X_xHlUuSc9sEVp-JEocMCSu3iH08P/view), [9 threshold maps](https://drive.google.com/file/d/1En27QXP-ELeIC4VElqgoBgfJ07wGZ8yf/view), [derived audit ZIP + CSV/JSON](https://drive.google.com/file/d/1EHR2vxFQTYv2Hh2QooObips-lVP6iwwD/view), [full P4-G review](reviews/p4-g-region-a-three-threshold-channel-map-sensitivity-2026-11-21.md). Still NO rivers, Q, canonical map/settlements, imported A8 area, accepted Core changes. **NEXT P4-H:** diagnose where model directional/grid bias originates (parent terrain vs child interpolation/relief vs dominant-receiver topology) and test topology-preserving map generalization; avoid blind threshold tuning. Accepted dev/0.2/frozen release untouched.

**PREVIOUS P4-F REAL independent Core-MFD topology for three P4-E DEMs (2026-11-21; PR #103 DRAFT/UNMERGED):** Source-hash-verified P4-B/P4-C1/P4-E private data; re-ran unchanged accepted Core priority flood + Freeman MFD + P2-B2.4 dominant channel projection separately for 0.5/1.25/2.0 relief strengths, preserving 63 parent anchors and full 231×231 child grid. Old strength 2.0 **BIT-EXACT** vs archived P2-B2.4 fields AND exact JSON report. Real candidate channel terminal counts **22/20/25**; model channel cells **9,117/6,394/5,893**. IoU channel mask vs 2.0 **18.47%/40.44%/100%**; all-cell dominant MODEL root same exact boundary pixel **52.72%/85.96%/100%**; same boundary side **94.88%/95.67%/100%**. Historic P4-C1 selected east-near reference cell [220,224] now terminates WEST [177,0] at strength 0.5 (32 km N shift), WEST [209,0] for 1.25 and 2.0. Fractional MFD transported *local* area exactly conserves 53,361 km² (float64 ledger ~1e-10 km² residual); **0 km²** A8 external-only area auto-injected; not Q, not water, no new physical basin identity. Dominant 1-receiver model root comparison ≠ fractional MFD catchment. New scripts/compare_region_mfd_variant_basins_v02.py, **24 synthetic tests**, SHA guards incl direct synthetic/wrapped private C1, geogrid synthetic end-to-end. [Private 3-column map](https://drive.google.com/file/d/1FDp5FX1Rg_n5VsbCzfVe1Wmxx_SFbI9T/view), [final v2 derived ZIP+NPZ reports and SHA](https://drive.google.com/file/d/1nRuXLKjx6sKxHnuBqOXuQGCbLg_m-XLy/view), [full rationale](reviews/p4-f-region-a-independent-mfd-variant-topology-2026-11-21.md). **NEXT bounded P4-G:** visibility/morphology of newly recomputed skeletons and source/threshold sensitivity, author-visible region-map quality. No terrain choice accepted, no POI placed, no approved river created. Accepted dev/0.2/frozen release untouched.

**PREVIOUS P4-E THREE ANCHOR-PRESERVING 1km CHILD RELIEF VARIANTS (2026-11-21, PR #103 DRAFT/UNMERGED):** Re-generated real PRIVATE A8-conditioned region-A 231x231 DEM using unchanged spherical_xyz_v1, seed 1406, parent interpolation and 63 continuous source height stations. **Original strength 2.0 regenerated BIT EXACT** against archived child NPZ. Two noncanonical alternatives strength **1.25** and **0.5** preserve all **63 original source anchors at 0m maximum error**, same parent baseline and land mask. On the **FIXED OLD P4-D 253-edge reference graph only**, raw-non-downhill counts: baseline 2.0 **58**, 1.25 **32**, 0.5 **15**. At 0.5, 50 original blockers become downhill but 7 previously downhill edges become non-downhill; interior DEM raw local minima **476→307→35** across strengths 2.0→1.25→0.5 (mathematical pits, NEVER lakes). Fine residual std **7.478→4.674→1.869m**. New `scripts/compare_region_relief_strength_v02.py` + 18 toy regression tests + geogrid synthetic CI; exact P4-D/P4-A source SHA provenance checked. Top row comparison uses FROZEN baseline P3 cover coloration (NOT recalculated ecosystem); bottom row fixed ±35m parent residual tint. **No alternative MFD routing / real watershed continuity / external catchment Q computed and NO Core or authored POIs changed.** [Drive comparison sheet](https://drive.google.com/file/d/1FGOm44nzbvTwSA5SyKMum6Mtyb9O5fux/view), [private ZIP with 0.5 and 1.25 derived NPZ, 3 maps and audit](https://drive.google.com/file/d/1NlJgASNvupeQ3E4Ykcr0k8gSRylGLQtg/view), [full review](reviews/p4-e-region-a-three-source-anchored-relief-variants-2026-11-21.md). **NEXT bounded P4-F:** recompute isolated candidate MFD graphs for both new DEMs and test changes to terminal/catchment identity/river morphology before any map acceptance; no premature overlay of old 253-edge graph as new river. Accepted dev/0.2 and frozen release untouched; PR #103 DRAFT/UNMERGED.

**PREVIOUS P4-D ANCHORED GRADIENT / RAW-SINK NEGATIVE CONTROL (2026-11-21; PR #103 DRAFT/UNMERGED):** Source-hashed, read-only new `scripts/audit_region_anchor_alternative_drains_v02.py`, 17 dedicated toy tests, geogrid synthetic CLI. Real region A, 253 candidate model edges and 63 original continuous parent height stations: 58 raw DEM uphill/flat; **56** have descending parent interpolated gradient reversed by effective fine residual; **2** already lack parent descent. **46** bad sources have >=1 immediate raw-downhill neighbor but **12** have none. All **58/58** greedy raw-steepest negative-control walks end at local DEM minima, **0** reach crop boundary: not lakes, not physical flow or new D8 routing. Median nearest parent-station distance 13.923 km for bad edges vs 12.585 km for 181 strict, no apparent concentration at anchors; bad links form 31 consecutive groups, longest 5. Input P4-C2 CSV independently recomputed from hash-verified P4-B child, macro, child metadata, P4-A PNG. **No parent/micro DEM, Core MFD, old A8 area, rivers, settlement POI or canonical geography changed.** Source supports `spherical_xyz_v1` and `legacy_lat_scaled_easting_v1` at the common parent anchor chart (actual real data uses sphere). [Private map](https://drive.google.com/file/d/173WacgMXJyC99yWBTANNCRS9lgxvsehG/view), [final v2 ZIP with CSV and SHA](https://drive.google.com/file/d/1d-5K2MFumj1aSQCcINSAUatDafp-UQsM/view), [full review](reviews/p4-d-region-a-parent-anchor-and-alternative-descent-2026-11-21.md). On code HEAD b4430503 geography+atlas CI GREEN, full pytest running at report preparation. **NEXT P4-E:** opt-in *noncanonical* controlled alternative fine relief recipes preserving 63 source stations, compare visually and quantitatively against P4-D; no direct carve/injected river.

**PREVIOUS P4-C2 CHECKPOINT (2026-11-21):** Work in draft PR #103 only; dev/0.2/frozen release untouched. scripts/audit_region_corridor_sensitivity_v02.py read-only diagnostic + 18 toy tests + synthetic geogrid CLI. Reuses exact SHA-verified private P4-B bundle and rederives P4-C1 route against its recorded audit, original A8/A12 ZIP not recopied. One 253-edge candidate east→west dominant path: at baseline 2m virtual fill 181 strict and 72 withheld; withheld reasons **49 raw uphill/flat only, 14 virtual fill only, 9 BOTH**, so 58 persistent uphill blockers. Fill-threshold 0/1/2/3/5/10m yields 128/161/181/185/189/195 strictly acceptable *model edges*, never actual real rivers; max uninterrupted strict chain only 30 edges at 2m. No external-only catchment area inferred or auto injected (0 km²); A8 D8 historical area cannot be added. No actual lake depth, flow Q, real river, catchment identity, author map accepted. All 253 edge deltas, virtual fills, scenario counts in [private ZIP](https://drive.google.com/file/d/1Ba9eisALnpJxxkwwXhfm82N63jnqGuc-/view); [private map](https://drive.google.com/file/d/1jfdGEdJzNptZXPn24WdZaCXQlqrnwHg1/view); full [review](reviews/p4-c2-region-a-corridor-fill-sensitivity-2026-11-21.md). New P4-C2 code commit 63fc6e0d synthetic geography CI GREEN; verify full pytest after doc commits. NEXT P4-D analyze 58 raw DEM climb sites vs 63 pinned source heights and alternative routing; no unapproved terrain excavation or ImageGen-for-hydrology. Respect PR #103 DRAFT/UNMERGED and five unplaced author POIs.

**PREVIOUS P4-C1 CHECKPOINT (2026-11-21):** PR #103 remains DRAFT/UNMERGED. New scripts/reconcile_region_boundary_corridors_v02.py (toy tests, live synthetic geogrid workflow) compares A8 *coarse inlet* hints with P4-B screened child Core MFD graph, checks A8 exit identity and exact P4-B hashes. Region A real PRIVATE derived P4-B bundle NOT original A8/A12 run this turn: ONE historic EAST input (+115,-110.083km), ONE WEST exit (-115,-96.028km). 20 inward positive/downhill P4-B edges near entry converge to ONE WEST child terminal [209,0], old exit 2.028km away; nearest child start 7.864km from macro entrance. 253-edge DOMINANT GRAPH route =181 strict and **72 withheld uncertain**, so NOT accepted river/basin identity. A8 old cumulative area hints 86,107/315,647km² NOT external-only and **0 km² injected**. P4-C1 image https://drive.google.com/file/d/1n8MMN4eGzR0LtPvgmB-l7-9rr3_9Xx_R/view, ZIP https://drive.google.com/file/d/1tBviEHXytjBTCgyGQ2S35lwQBPK4nyWf/view, docs/reviews/p4-c1-region-a-macro-inlet-to-child-mfd-route-evidence-2026-11-21.md. Code CI e34e783b: full pytest **641 passed**, geogrid and author atlas GREEN. NEXT P4-C2 explicit outside-boundary area vs raw-DEM uncertainties and lake-spill sensitivity; preserve 5 unplaced story locations, no author map acceptance and no auto merge or change to Core dev/0.2/freeze. Do not ask again for sphere-vs-legacy choice.

**PREVIOUS P4-B CHECKPOINT (2026-11-21):** Actual original PRIVATE A8/A12 were SHA verified again and same `spherical_xyz_v1` P1/P2/P3/P4-A run, now plus existing P2-B2.4 Core dominant-MFD candidate channel projection + NEW conservative render `scripts/render_region_drainage_evidence_v02.py`. P4-B checks every ordinary candidate edge against accepted Core MFD positive fractional receiver and ORIGINAL unfilled DEM downhill, refuses projected lake jumps, hides virtual fill >2m, never invents macro A8 external inflow. Real region A: 231x231 / 63 pinned heights / 0m anchor error, 5868 ordinary candidates, 4517 strict safe, 1351 withheld (not river), max virtual fill ~9.813m (NOT lake), 1374 uncertain fill cells, 0 proxy jumps under candidate threshold (does NOT mean no physical lake). At explicit DISPLAY area proxy >=100 km²: 2515 edges shown; 2002 strict minor edges hidden from image but preserved NPZ. Synthetic full pytest 627 passed and geo/author CI GREEN at code HEAD 8427f391. Private [P4-B PNG](https://drive.google.com/file/d/1FHsVVlPY4UVa6dZK-41NERLnd6g0E5Fn/view), [P4-B derived ZIP](https://drive.google.com/file/d/1G6hxsqMNBIk_ZovBZ4nrepf7fLOxrHtX/view), [review](reviews/p4-b-region-a-drainage-evidence-2026-11-21.md). No accepted permanent river, Q, lakes, external catchment, 5 story POIs or 2 routes. NEXT P4-C: bridge global macro watershed boundary inflow/lake outlets/child MFD integrity and validate real map topology before cosmetic blue water. PR #103 stays DRAFT/UNMERGED, dev/0.2 and freeze unchanged. This latest checkpoint supersedes older repeated prompts for P4-A/P3.6 selection; author already approved continuation.

**PREVIOUS P4-A CHECKPOINT (2026-11-21):** Draft PR #103 now includes tested P4-A map-first renderer scripts/render_region_cartographic_base_v02.py, dedicated tests and synthetic author-map workflow; last functional HEAD checks 612 passed, geo/author workflow GREEN. Private ORIGINAL A8/A12 verified, same exact Git modules P1/P2/P3 plus P4 renderer, generated one 230x230 km cartographic base with spherical_xyz_v1, real scale, north-up, 50-m model height isolines; same DEM and cover counts, 63 source anchors exact. Private Drive [map sheet](https://drive.google.com/file/d/1mZUlYpafZyF3wDWXKyANfgvcCGkOuSYH/view), [clean base](https://drive.google.com/file/d/1NfnBSXDdCXnHMb_X6xZFnCT7dkq-zjFO/view). Read docs/reviews/p4-a-region-a-map-first-renderer-2026-11-21.md for exact original ZIP SHA, Git blobs and limitations. User has NOT reviewed or accepted this P4 map. It is STILL NOT a complete geographic map: river topology, lakes, settlements, roads, 5 POI and 2 routes unknown. NEXT P4-B is evidence-driven child drainage candidate, NOT invented blue rivers or blind ImageGen. Do not change Core/freeze or merge #103 without gate; legacy global terrain default unchanged.

**NEWEST P3.6 AUTHOR DECISION (2026-11-21):** User formally chose RIGHT `spherical_xyz_v1` as OSVERA REGION-A WORKING detail for further experiments. User EXPLICITLY DID NOT accept either P3.5 atlas as a plausible/readable regional map; do NOT call current map finished or canon. No author-imposed repeat of spherical-vs-legacy selection is required. Keep generic legacy default, #103 DRAFT/UNMERGED, no POI positions/accepted river network, original ZIPs private. Product next task P4-A: one cartographically convincing top-down base from actual terrain and model-cover layers (no fabricated rivers/roads), separate map from technical panel, record exact inputs and geography; ImageGen mentioned only as uncertain future option, not a request to run. Read docs/reviews/p3-6-operator-selection-and-map-product-gap-2026-11-21.md, then current PROJECT/CONTEXT/PROGRESS and live PR SHA/CI.

**NEWEST P3.5 CHECKPOINT (2026-11-21):** Real PRIVATE original A8/A12 were downloaded and SHA-verified; exact GitHub P1/P2-A/P3/author-atlas MODULES + author ledger/profile (blob SHA-1 verified) were executed for BOTH legacy and opt-in spherical detail. Both full 230×230 km sheets stored as ONE side-by-side private Drive PNG (https://drive.google.com/file/d/12T79Z9GcKD41LyDGOaKli-WJlNK3emNQ/view); published review docs/reviews/p3-5-region-a-full-private-spherical-vs-legacy-2026-11-21.md. 63 parent anchors preserved with 0m error and same land; model cover changes in 13,510/53,361 pixels; forest/open/wet candidate legacy 64.058/16.731/19.211%, sphere 66.663/17.275/16.062%. Smaller diagonal artifacts in sphere; macro bands persist. **One-shot orchestration called exact implementations; private CLI wrapper itself NOT run.** NO operator acceptance, NO POI/route coordinates, NO accepted MFD or water balance. Keep PR #103 open/draft/unmerged and LEGACY default until explicit choice. Current PR head may differ due to documentation updates; verify GitHub. Next: author inspects real two-atlas comparison and chooses next spatial acceptance/repair.

**NEWEST P3.4 CHECKPOINT (2026-11-21):** PR #103 now has opt-in `spherical_xyz_v1` P2-A procedural detail option in both P2 standalone and one-command P3 atlas, legacy default unchanged. Real PRIVATE derived region-A NPZ comparison showed old P2 detail diagonal shear from latitude-scaled absolute-longitude easting; sphere-xyz removes most artificial anisotropy. See docs/reviews/p3-4-region-a-spherical-detail-projection-2026-11-21.md and private Drive screenshot, NOT a final P3 cover map. Synthetic CI must be checked on live head; no user visual acceptance, no merge, no Core change. Next if preferred: re-run complete private ZIP→child→cover→atlas with spherical mode and review one sheet.

**NEWEST P3.3 CHECKPOINT (2026-11-21):** Original A8/A12 ZIPs were FOUND in the user's connected Google Drive, validated against documented SHA and P1 full-world parity, and a first REAL region-A 230×230-km author sheet was computed through the exact P1/P2/P3/atlas function blobs. Child 231×231, 63 original anchors, 0m error. P3 candidate woodland/open/wet-lowland ~64.06/16.73/19.21%, NOT real ecology. Legend/footer overlap FIXED in PR #103 with a bbox regression, and final private PNG plus derived-only bundle STORED in private Drive. Read docs/reviews/p3-3-osvera-region-a-private-source-atlas-2026-11-21.md for evidence/links. **Operator visual acceptance NOT done. New P3.2 CLI wrapper itself not run privately**, only its exact underlying modules via temporary orchestration. Keep #103 draft/unmerged and don't publish ZIP originals or assume rivers/routes. Next step is visual author review of one map.

**NEWER P3.2 UPDATE (2026-11-21):** Draft PR #103 accepts ORIGINAL private A8/A12 ZIPs in one CLI call; see docs/world-fixtures/osvera-author-natural-cover.md P3.2. Uses existing P1 whole-source grid equality and one-station crop halo. Synthetic archive tests. No actual private region-A result / author acceptance, do not upload originals or merge #103 without decision. Reverify HEAD and CI.

**LATEST WORKING-BRANCH CHECKPOINT (2026-11-21):** Draft PR #103 now contains a source-verified P2-A -> P3 -> author-atlas CLI and synthetic CI. Read docs/PROGRESS.md and docs/world-fixtures/osvera-author-natural-cover.md for current next steps. NO exact private A8/A12 build or visual acceptance yet; keep PR #103 unmerged. dev/0.2 is accepted base; frozen release unchanged. Older "current" paragraphs below are historical.

## Copy into a new chat

Repository: `MysterioCrypto/domain_generator`.

Active development line: `dev/0.2`. Do **not** reconstruct current state from `main`.

First read, in order:

```text
PROJECT.md
docs/CONTEXT.md
docs/PROGRESS.md
docs/design/gross-catchment-precipitation-input-v0.2.md
docs/design/marine-coastal-boundary-v0.2.md
```

Current **product/recovery** checkpoint: [START_HERE.md](../START_HERE.md) → [docs/PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) → [D’Акхар source fixture](world-fixtures/dakhar-first-arc.md). Parallel technical H13-A: design #98 accepted/merged, implementation #99 draft/unmerged; #100 and #101 likewise draft/unmerged.

Post-H12 dependency audit is DONE. H13-A accepted design was merged as PR #98:
https://github.com/MysterioCrypto/domain_generator/pull/98

Design branch: `design/v0.2-gross-catchment-precipitation`.
Normative accepted document: `docs/design/gross-catchment-precipitation-input-v0.2.md` (now on dev/0.2).
Proposal: opt-in gross upstream atmospheric precipitation input (m³/year) from accepted C1 annual precipitation + accepted weighted MFD/lakes + optional H12 marine absorption. This is **not runoff/discharge/permanence**.
G01–G15 are the implementation acceptance plan. Design formally accepted by operator on 2026-11-15 and PR #98 merged at `0000a208183a2ff3b1d7dc8eee8f93d54f72ef35`. Implementation remains unaccepted. Do not merge implementation without separate ACCEPT.

- PR #97: https://github.com/MysterioCrypto/domain_generator/pull/97
- Merge: `3d275466ec5bfdb74f5dcb88bea6c8b641347f70`
- Accepted tests: O01–O13 GREEN, schema sync GREEN, 502 full tests passing, coastal workflow GREEN.
- Marine is opt-in; negative elevation alone does not imply sea. Boundary-connected 4-neighbour marine, refined shoreline and `marine_outlet` are accepted.
- Canonical dependency map: **see the beginning of `docs/CONTEXT.md`**. This handoff is not authoritative if they disagree.
- Next: implement H13-A in separate branch, G01–G15 and checkpoint; request separate IMPLEMENTATION ACCEPT / REJECT.

Accepted and frozen:
- Terrain 0.2;
- Hydrology 0.2 routing/network;
- C1 Annual Climate Forcing;
- C2 Effective Surface Moisture;
- C3 Climate-Aware Vegetation.

C3:
- design PR #84 merged;
- implementation PR #85 merged;
- merge commit: `37e213ebf5f82ebfae149d21088c07e08d836549`;
- V01–V11 GREEN;
- C3-A workflow GREEN and formally ACCEPTED:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36842261493`.

C3 semantics:
```text
accepted C2 moisture
× normalized annual thermal suitability
+ vegetation_bias
-> vegetation_density

canonical water = 0
```

`vegetation_density` is an abstract normalized ecological potential index, not percent canopy cover or literal NPP.

Mountain influence:
- C1 elevation/lapse-rate temperature;
- C1 windward/lee precipitation;
- C2 slope retention;
- terrain-shaped hydrology feeding C2;
- no second direct C3 slope penalty.

Hydro-surface readiness audit:
- perennial / seasonal / dry remains blocked by absent seasonality/baseflow/groundwater;
- lake vs wetland/playa/dry basin remains blocked by absent water-balance/permanence;
- delta/estuary/fan remains blocked by absent receiving-environment/process context;
- headwater visibility can use the accepted potential scaffold, but that scaffold is currently internal only.

H11-A design PR #86 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/86`

Merge commit:
`712dae3179605b894558a9e399cd6929ffcda459`

Accepted design:
```text
Core 0.2 networks["rivers"] = accepted regional H09-D2
Core 0.2 networks["potential_drainage"] = accepted H09-E potential network
```

No flow-permanence labels, no Strahler public metadata, no hydrology geometry changes.

H11-A implementation:
- PR #87 ACCEPTED / merged;
- merge commit: `cef91e81c86c64555ae1e1363d7ffaf2934ff6ce`;
- checkpoint: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`;
- Core 0.2 public networks: `rivers`, `potential_drainage`;
- Core 0.1 remains `rivers` only;
- potential network is a drainage scaffold, not a permanence class.

Physical hydro classifications still deferred:
- perennial / seasonal / dry;
- lake vs wetland/playa/dry basin;
- delta / estuary / fan.

Immediate next step:
- Placement readiness audit against accepted Core 0.2 environment;
- choose one bounded Placement slice;
- design before implementation if semantics materially change.

Do not reopen the accepted hydrology routing/network body without concrete evidence.

Process rule:
after every meaningful implementation/decision slice, update external context so a chat failure loses at most the current unfinished step.


## Placement readiness result

Existing Core 0.1 placement mechanics are retained:
- lattice/reservation/footprint;
- requirements;
- preferences;
- near-best;
- deterministic weighted selection.

Core 0.2 automatically gives new meaning to:
- `moisture_mean` via C2;
- `vegetation_density_mean` via C3.

P08-A design PR #88 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/88`

Merge commit:
`66003288e528fc340663d92f84ed14cbee88744b`

Accepted Core 0.2-only metrics:
```text
temperature_mean
annual_precipitation_mean
distance_to_potential_drainage
```

P08-A implementation:
- PR #89 ACCEPTED / merged;
- merge commit: `57e77c8de6ac8668ddd09e25167e30aa773cf645`;
- P01–P11 GREEN;
- checkpoint: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`;
- Core 0.1 registry remains 8 metrics;
- Core 0.2 adds temperature_mean, annual_precipitation_mean, distance_to_potential_drainage;
- existing Placement mechanics remain unchanged.

Immediate next step:
- audit remaining Placement boundaries;
- choose one bounded Core 0.2 follow-up slice;
- design before implementation if semantics change.


## Placement closure / A08 hardening

Post-P08-A audit found no additional base Placement contract gap. New Core 0.2 metrics already pass through normal preset/compiler SiteProfile strings.

Placement current scope is complete.

Hardening PR #90:
`https://github.com/MysterioCrypto/domain_generator/pull/90`

A08 is a full Core 0.2 acceptance fixture using P08-A metrics through a real preset. Initial baseline is intentionally PENDING so CI can emit the exact deterministic snapshot before pinning.

No new world semantics are introduced by PR #90.


## A08 integrated acceptance

PR #90 merged:
`568eeff9676ee387d5837cfb1fca1a8ff087e99b`

A08 is frozen and GREEN:
- full Core 0.2 pipeline;
- P08-A metrics through preset/compiler;
- exact replay;
- canonical bundle;
- regional + potential networks.

Release-readiness audit now focuses on stale package/docs version metadata. Independent contract versions remain independent unless a concrete shape break requires a bump.


## Core 0.2 release-candidate readiness

PR #91 merged:
`5cafb8119050f19765447d65dcef022ebebe052b`

Generator identity:
`0.2.0.dev0`

Merge-head pytest GREEN:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36853774759`

A01–A08 are GREEN. Version re-sign changed only DomainData provenance hashes; world fields/geometry/networks/placement remained identical.

No known blocker remains inside accepted Core 0.2 scope.

Operator formally ACCEPTED the release candidate.

Frozen release:
- branch: `release/0.2-prealpha`;
- exact freeze commit: `c69c1af010a085fb80d248af703a77471fc6c9d7`;
- generator identity: `0.2.0.dev0`.

The release branch is frozen. New semantic work continues only on `dev/0.2`.

Immediate next step:
- choose the next post-release semantic layer;
- open a new INV-006 design gate before material implementation;
- do not reopen accepted Core 0.2 semantics without concrete evidence.


## Post-release C4-A seasonality

Dependency audit rejected immediate biome classification because current climate is annual-only.

Design PR #92:
`https://github.com/MysterioCrypto/domain_generator/pull/92`

Proposal:
- optional explicit 12-month climatological envelope;
- monthly temperature preserves annual mean;
- monthly precipitation preserves annual total;
- explicit peak months and amplitudes;
- no hemisphere/latitude inference;
- no new monthly noise or seasonal wind changes;
- C2/C3 unchanged during C4-A;
- no biome or stream-permanence labels yet;
- no seasonality recipe means frozen prealpha-compatible annual behavior.

C4-A design PR #92 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/92`

Merge commit:
`e729d836d29df790fa1c0056e7b686d6189703f9`

C4-A implementation:
- PR #93 ACCEPTED / merged: `https://github.com/MysterioCrypto/domain_generator/pull/93`;
- accepted semantic head: `5b9b4e7341bfb3c8b496f25b3e9f741128f31b2a`;
- merge commit: `570a5c4730419d17bce69f9e804b805125343fa5`;
- S01–S13 GREEN;
- schema snapshots GREEN;
- push/PR full pytest GREEN;
- representative checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36959449118`;
- exactly 24 monthly derived fields;
- annual C1/C2/C3 canonical outputs exact-unchanged;
- features/networks unchanged.

Important compatibility fix:
- absent seasonality initially altered frozen A08 fingerprints because the new optional field serialized as null;
- this was fixed by omitting only absent seasonality from fingerprint payloads;
- frozen A08 fingerprints are explicitly pinned by S10;
- explicit seasonality still changes semantic fingerprint.

Representative conservation after float32 persistence:
- temperature max error ~4.77e-7 C;
- precipitation max error ~1.91e-4 mm.

Operator formally ACCEPTED C4-A implementation.

Immediate next step:
- perform a fresh post-C4 dependency audit;
- choose exactly one next bounded semantic layer;
- open a new INV-006 design gate before implementation;
- do not assume biome or flow-permanence is ready without checking its remaining dependencies.

`release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Post-C4 audit / C5-A

After C4:
- channel permanence is still blocked by groundwater/baseflow/storage;
- lake/wetland/playa/dry-basin semantics are still blocked by basin permanence/water balance;
- delta/estuary/fan remains blocked by receiving-environment context;
- direct biome labels remain deferred.

Selected next bounded layer:
**C5-A Köppen–Geiger climate regionalization**.

Design PR #94:
`https://github.com/MysterioCrypto/domain_generator/pull/94`

Proposal:
- opt-in scheme `koppen_geiger_local_season_v1`;
- derived `uint8` field `climate_regime_koppen_geiger`;
- fixed 30-class codebook;
- local warm/cold half-year anchored on explicit C4 temperature peak month;
- climate classification only, not biome classification.

No runtime implementation before explicit C5-A design ACCEPT.


C5-A design PR #94 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/94`

Merge commit:
`d75b2f6f55b53a14b048a38bb2a69d339c8cf44e`

Important:
- Köppen remains opt-in Earth-derived interpretation only;
- C4 climate parameters are explicit inputs, not hard-coded geography;
- fantasy/non-Earthlike worlds may omit classification entirely;
- exact Beck/Peel 10 C boundary retained.

C5-A implementation:
- PR #95 ACCEPTED / merged: `https://github.com/MysterioCrypto/domain_generator/pull/95`;
- accepted semantic head: `43519587fac92e94cb8bbbb64222c876d7579882`;
- merge commit: `8af34da0c66c48b62172b8654edc5876d9414085`;
- K01–K15 GREEN;
- schema snapshots GREEN;
- push/PR full pytest GREEN;
- representative checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36968143576`;
- all pre-existing C4 fields/features/networks exact-unchanged;
- output is one optional derived uint8 climate-regime field.

Representative map uses 7 of the 30 possible classes and is dominated by Csb because the diagnostic input is intentionally winter-wet / warm-season-dry. This is test input behavior, not a hidden default.

Operator formally ACCEPTED C5-A implementation.

Immediate next step:
- perform a fresh post-C5 dependency audit;
- select exactly one next bounded semantic layer;
- open a new design gate before implementation;
- keep `release/0.2-prealpha` frozen.


## Post-C5 audit / H12-A

Post-C5 audit found:
- direct biome labels still deferred;
- channel permanence still blocked by groundwater/baseflow/storage;
- basin permanence/type still blocked by water balance/infiltration;
- delta/estuary/fan still blocked by receiving-environment/process context.

Universality audit exposed a more fundamental missing capability: no sea/ocean/coastline semantics exist.

Design PR #96:
`https://github.com/MysterioCrypto/domain_generator/pull/96`

Proposal:
- optional explicit `hydrology.marine.sea_level_m`;
- no hidden sea level;
- marine = boundary-connected below-sea terrain using 4-neighbour connectivity;
- enclosed below-sea basins remain inland;
- derived `marine_mask`;
- refined 4× coastline;
- distinct `MarineFeature`;
- `marine_outlet` river nodes;
- regional/potential rivers stop at first coastline intersection;
- no tides/waves/salinity/delta/estuary semantics yet.

H12-A design PR #96 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/96`

Merge commit:
`f8efae6e24cdda68fb10960f13ca69d342a61a7b`

Immediate next step:
- separate H12-A implementation branch;
- O01–O13 + dedicated coastal/archipelago checkpoint;
- no implementation merge before explicit ACCEPT.


H12 implementation clarification:
- marine enters canonical water_depth;
- no C2/C3 algorithm changes;
- new marine cells therefore inherit accepted canonical-water semantics: moisture=1, vegetation=0;
- outside marine support C2/C3 stay exact-unchanged;
- C1/C4/C5 climate remains unchanged.


Further H12 clarification:
- C2 distance-to-water means marine water can affect nearby coastal land moisture;
- C3 may then change via accepted C2 moisture;
- algorithms/parameters stay unchanged; only deterministic dependency propagation is allowed;
- C1/C4/C5 climate remains exact-unchanged;
- no marine-specific ecological formula is part of H12.


H12 implementation is now active:
- draft PR #97: `https://github.com/MysterioCrypto/domain_generator/pull/97`;
- branch `impl/v0.2-marine-coastal-boundary`;
- contract/classification/coastline/marine-depth/marine-outlet/public-mask integration is implemented;
- first regression exposed and fixed an accidental attempt to pass marine exclusion into MFD accumulation; routing/accumulation remains frozen;
- O01–O13 tests are added and currently under CI;
- schema sync and dedicated coastal checkpoint remain pending;
- PR remains unmerged.


H12-A implementation recovery is complete.

Current implementation:
- draft PR #97: `https://github.com/MysterioCrypto/domain_generator/pull/97`;
- semantic head: `4dc897906d2e67ae7c3bccb2c9ef49934339f4a6`;
- O01-O13 GREEN;
- schema snapshots GREEN;
- PR and push full pytest: 502 passed;
- dedicated coastal/archipelago checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161098`.

Checkpoint observations:
- marine fraction ≈42.64%;
- one marine component with one island hole;
- two inland lakes;
- enclosed below-sea basin remains non-marine;
- regional/potential drainage terminates at refined coastline;
- no visible channels continue through marine interior;
- fixed 4× refinement is visibly stepped at ~250 m, as accepted by design.

Historical operator-review gate was closed by formal ACCEPT on 2026-10-09.

Current gate: **POST-H12 DEPENDENCY AUDIT**. PR #97 is merged, not draft or pending.
Read the top-level dependency map in `docs/CONTEXT.md` before choosing the next slice.


## Historical checkpoint: H13-A design review (now accepted)

- PR #98: https://github.com/MysterioCrypto/domain_generator/pull/98
- Branch: `design/v0.2-gross-catchment-precipitation`
- Runtime: NOT STARTED.
- Status: awaiting explicit design ACCEPT / REJECT.
- Accepted upstream: C1 annual precipitation; Hydrology 0.2 MFD weighted DAG and lake supernodes; H12 marine is optional.
- Proposed output: one derived float64 `gross_upstream_precipitation_m3_per_year` field.
- Key semantic limit: **mathematically allocated gross upstream rainfall input**, NOT water physically delivered to a channel; no runoff, discharge, water-balance closure or stream permanence.
- Design clarification (2026-11-15), PR #98 head `5fbd6b5904071feefc38a0ab66f093e68845e81e`: compute in the existing SURFACE stage after C1 is available; no new ValidationStage and no assembly-side physics. Keep accepted MFD area outputs unchanged.
- Explicitly still blocked: perennial/seasonal/dry flow (baseflow/storage/infiltration), delta/estuary (sediment/discharge/coastal processes), lake/wetland/playa permanence, direct biome labels.
- Context-map source of truth: top of `docs/CONTEXT.md`, which now shows H13 as PROPOSED, not part of accepted DAG.
- Next: operator design decision; ACCEPT allows design merge and a **separate** implementation branch, not implementation merge.

Frozen `release/0.2-prealpha`: `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Current checkpoint: H13-A DESIGN ACCEPTED / implementation development

- User formally accepted design on 2026-11-15; PR #98 merged `0000a208183a2ff3b1d7dc8eee8f93d54f72ef35` with successful push and PR CI on design HEAD `5fbd6b5904071feefc38a0ab66f093e68845e81e`.
- Normative spec on dev: `docs/design/gross-catchment-precipitation-input-v0.2.md`.
- Active branch: `dev/0.2`, new independent implementation branch forthcoming. No implementation ACCEPT and no implementation merge.
- Physical interpretation: **annual gross upstream source allocation under MFD**, not actual delivered water/discharge/runoff. C4/C5 not dependencies; H12 optional.
- Implementation must protect baseline MFD/lake supernode behavior, coastline terminal ledger, exact opt-out fingerprint, float64 derived field, deterministic replay, and stable canonical stages; G01–G15 + wet/dry/coastal evidence.
- After each meaningful milestone, update `PROJECT.md`, `docs/CONTEXT.md`, `docs/PROGRESS.md` and this handoff; keep historical release unchanged.


## New active product route — 2026-11-15

- One-click repo navigation at START_HERE.md; P0–P6 roadmap in docs/PRODUCT_ROADMAP.md; non-Earth D’Акхар source at docs/world-fixtures/dakhar-first-arc.md with JSON source-only fixture and stdlib tests.
- Original A1–A11 and A12 Drive archives plus georeferenced PNG atlas ARE PRESENT: direct Google_Drive.fetch folder lists them even when search returned empty. A8/A12 NumPy arrays are now parsed, SHA-256 verified, A8 north→south versus A12 south→north orientation reconciled (reverse A8 raster rows exact). A10/A11 ZIPs and NPZ content independently SHA/CRC-verified; A10 annual_Q exactly equals its copy in A12_inputs; no Core import. Do not claim import; working Atlas A/B/C proposed not canon, short planetary year 202.755 Earth days; mm/planetary year not automatically Earth mm/year.
- Next bounded visible step: three actually different regional terrain/hydrology scenes. Follow with opt-in world-defined land cover; no more unneeded parchment physics. Preserve dev/0.2 accepted contracts, three unmerged PRs #99/100/101 and frozen release.


- **Live source QA evidence:** A8 ZIP SHA `6824ccf2...`, A12 ZIP SHA `db9f0f91...`, A12_inputs NPZ SHA `f2d6c446...` (complete in docs/reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md). Original 600×1200 arrays identical for elevation+land after A8 row reversal. User-visible source-derived diagnostic map created outside repo from private Drive archives; do not commit private ZIP or rendered crops to public repo without explicit consent.


## P1 planetary macro-geogrid adapter — 2026-11-15, DRAFT #103

- User's non-Earth source A8/A10/A11/A12 archives are verified (SHA/CRC, A8 north-first vs A10/A11/A12 south-first) and kept PRIVATE. Source A8 global D8 is an older research hydrology, not Core 0.2 accepted MFD.
- On an isolated DRAFT [PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103), external-only script scripts/export_planetary_macro_region_v02.py reads paths of original ZIPs, validates exact A8/A12 shared land/DEM, accepts user-specified planetary radius/year and local km source crop, remaps BOTH endpoints of A8 global flattened D8 downstream indices, and flags rivers exiting crop. It emits source NPZ+manifest+PNG, deliberately NOT DomainData and NOT fake local 1-km elevation.
- Synthetic workflow [GREEN](https://github.com/MysterioCrypto/domain_generator/actions/runs/43742308913) passes 4 targeted tests and writes a demo artifact. No private source ZIP/PNG was committed or uploaded to Actions.
- [CLI instructions and explicit boundaries](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-geogrid-adapter.md). Next meaningful work is source-constrained finer regional terrain and new MFD river generation, followed by non-Earth profile-based land cover; not further parchment filters or full planetary climate science.
- This is a parallel draft branch. PR #99 H13, #100 C2 tests, #101 atlas composer remain DRAFT/UNMERGED. Frozen release c69c1af010a085fb80d248af703a77471fc6c9d7 remains unchanged.


### P2-A 1-km non-Earth child terrain preview (2026-11-15)

- In isolated draft #103, scripts/condition_planetary_child_terrain_v02.py uses the source macro NPZ/manifest and explicit planet-year/radius to synthesize WORLD-LOCKED multiscale local DEM texture, with exact A8 parent elevations and C1 cubic parent interpolation. Outputs new child NPZ/manifest/PNG, NOT Core DomainData or accepted MFD.
- Original A/B/C private-source regions, 230×230 km each, 231×231 child samples and source elevation anchors 63/49/49 exact. Source assets and real derived images are not in public repo or Actions; only synthetic illustration is in dedicated GitHub Actions [run](https://github.com/MysterioCrypto/domain_generator/actions/runs/43746102251).
- [Design/bounds](world-fixtures/planetary-child-terrain.md). **Next P2-B:** parent-conditioned MFD, river continuity and outlets, then land cover; never paint old D8 over child and pretend new hydrology validated. No implicit merge of #103/#99/#100/#101.


### Current P2-B1 handoff (2026-11-16)

- Branch `feature/v0.2-planetary-geogrid-source-adapter` draft PR #103 gained `scripts/diagnose_planetary_child_mfd_v02.py` and six targeted tests plus deep-depression regression. Accepted Core Priority-Flood and MFD fractions used **without changes**; local-source accumulation matches accepted distributed flow at small grids, 1km² sources conserved to edge, A8 old D8 river segments only guide. [GREEN 19-test synthetic Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/43805052775) with child-MFD PNG, no private user-world data publicly uploaded.
- Real private A/B/C diagnostic maps generated from old source ZIP using independent local SciPy C2 cubic DEM approximation (different from GitHub C1 Hermite) and equivalent published Core MFD weights: deep virtual fill depressions B=88.5m, C=60.0m, A=12.4m. This is a real map-design blocker; must **NOT** call the filled MFD fan a validated physical river. Repro screenshots/results attached in chat, not GitHub. [User and technical review](reviews/p2-b-child-mfd-reference-audit-2026-11-16.md).
- Next P2-B2: accepted lake candidates/spill supernodes and external inflow/basin boundary coupling to historic source A8 D8 (not same algorithm), plus continuity QA, NOT more aesthetic filters. Still no accepted world-cover classes or production ImageGen. Frozen release unchanged; previous PRs stay draft.


### P2-B2.1 — geometric lake basin review (2026-11-20, PR #103 DRAFT)

- [Visual synthetic QA](https://github.com/MysterioCrypto/domain_generator/actions/runs/44748762996) and [operator review](reviews/p2-b2-1-child-lake-basin-operator-checkpoint-2026-11-20.md): external read-only `scripts/audit_planetary_child_lakes_v02.py`, Core Priority Flood/extract_lake_candidates/choose_lake_outlets, bounded nested hierarchy, Core lake-supernode conservation on SMALL bowl only. Proposed basin ≠ actual water occupancy; no universal Earth-specific thresholds, no external inflow, no source-D8 substitution.
- 27 focused tests GREEN; full algorithmic SHA pytest 532 GREEN; final docs SHA must have new CI. Private A/B/C sensitivity screening performed locally using independently interpolated DEM, not an exact PR P2-A regression; resulting numerical/visual data stay in conversation only.
- P2-B2.2 next: source-macro boundary inflows/outflows and constrained MFD+lake supernode routing, before asserting credible river/ford/waterfall geometry. Keep PR #103, #99–101 draft/unmerged. Frozen `release/0.2-prealpha` unchanged.


### P2-B2.2 — explicit cross-scale river boundary area (2026-11-20, draft PR #103)

- External scripts/condition_planetary_child_boundary_mfd_v02.py: identify directionally INCOMING original A8 D8 macro-river links at a 230km child box; preserve source catchment as UNSAFE_HINT only. With NO explicit scenario, inject **zero** external km2. With a keyed, operator-annotated, positive EXTERNAL_ONLY scenario, run new Core-compatible O((N+E)logN) MFD + geometric lake-supernode area propagation and enforce area-conservation ledger. It is **NOT discharge Q**, a world water balance, actual lake occupancy, an accepted child vector river network or an automatic A8-to-MFD merger. Does not mutate normative Core.
- [Operator audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md) · [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-boundary-inflow.md). [Synthetic GREEN preview and ledger](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925): 35 focused tests, two contrasting maps, no private source uploaded. [Full pytest GREEN 540](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA 35163cd7b6f8c3c9c8c74ea3a5ec24c2aa603dc3; check final documentation SHA again.
- Original PRIVATE A8/A12 data were screened locally for 230×230km A/B/C: OLD D8 crossing counts A **1 IN / 1 OUT**, B **0 IN / 2 OUT**, C **0/0**. A source D8 entry has upstream catchment proxy **86,106.66 km²**, but this is **NOT** verified external-only area and MUST NOT be injected unexamined. No old-source data/real-derived maps in public GitHub.
- **NEXT P2-B2.3:** compute true external-only provenance using original global D8 with re-entry detection, then compare macro basin exits to new actual connected MFD channels and qualify real lake occupancy per world-specific water profile. PR #103 DRAFT/UNMERGED, #99–101 DRAFT/UNMERGED; dev/0.2 and frozen release unchanged.


### P2-B2.2 next-chat recovery: A8 boundary inflows are NOT A8 catchment totals

External script scripts/condition_planetary_child_boundary_mfd_v02.py + tests/test_planetary_boundary_inflow_mfd_v02.py landed in **draft/unmerged PR #103** on 2026-11-20. Exact Core Priority Flood/MFD weights with fast lake supernodes area graph. No automatic A8 D8 catchment injections; only keyed operator EXTERNAL_ONLY assumptions (not independently validated) may add km². GREEN 35 targeted tests [Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925), full 540 [pytest](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA. Real private original A/B/C old macro crossings A=1 incoming/1 outgoing, B=0/2, C=0/0, and A source catchment ≈86,106.66 km² UNSAFE_HINT; original real PNG/JSON only in chat, never public repo. New child river network **not yet validated** and lake occupancy **not inferred**. [Review](reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md). NEXT P2-B2.3 implement provenance of truly outside-only upstream graph area with D8 re-entry detection; compare macro outlets to accepted fine MFD vectors, no false Q/water claims.


### P2-B2.3 · 2026-11-20: global A8 FIRST-ENTRY source partition (DRAFT #103)

- The original PRIVATE global A8 600×1200 D8 graph (not a crop) was inspected. New external script scripts/trace_a8_external_first_entry_v02.py computes the partition of **each original EXTERIOR LAND SOURCE cell** by the FIRST directed downstream entry into each 230km child rectangle. This prevents source-area duplication on exit/re-entry: only own new exterior source area is allocated to later entries. Full graph must be acyclic; macro/crop links must match exact global A8 lat/lon/receiver indices; A8 source cell area uses world radius and cos(latitude), NOT Earth constants.
- Original privately checked working model A/B/C: all directed A8 entry LINKS **23 / 12 / 5**; subset tagged old major river mask **1 / 0 / 0**. All-source EXTERIOR first-entry areas A ≈297,336.828km² / B ≈87,705.114km² / C ≈11,515.098km². A's ONE major river has A8 external first-entry area ≈**86,106.657km²**, matching old total source catchment ≈86,106.65625km² within rounding. No inside-upstream reentry in these specific scenes; a synthetic exit→reentry case is tested explicitly.
- A8 first-entry provenance is NOT physically verified 1km CHILD MFD drainage, river discharge Q or author canon. **No auto injection into child MFD.** Old D8 river_mask ignores numerous smaller old macro incoming links; B/C "zero major" DOES NOT mean no rivers. Private source ZIPs and actual region imagery are NOT committed to public GitHub.
- [P2-B2.3 audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-a8-first-entry-provenance.md). Synthetic tests cover reentry, unequal latitude row areas, cycle and source mismatch; current CI status must be confirmed at latest final SHA.
- **NEXT P2-B2.4:** match source A8 MACRO outlets with actual CHILD MFD edge-terminal geography and connected river lines, then explicit world-specific hydrologic semantics; neither A8 D8 nor newly rendered detail is authoritative. PR #103 remains DRAFT/UNMERGED; #99–101 drafts and dev/0.2/frozen release unchanged.


### P2-B2.3 recover global A8 provenance, do NOT auto-inject

Branch feature/v0.2-planetary-geogrid-source-adapter (draft PR #103) now has scripts/trace_a8_external_first_entry_v02.py, tests/test_a8_external_first_entry_v02.py and workflow synthetic global A8 audit. It classifies each OUTSIDE original A8 land source by FIRST downstream entry to child; this avoids double-counting when river passes inside→outside→inside. A8 source-only provenance: A/B/C 230km boxes all macro inbound links =23/12/5; old MAJOR river links=1/0/0. A old major inbound outside-only area=86,106.657km² vs original unsafe full catchment=86,106.65625km²; B/C also contain many smaller links. Reentry zero in 3 real windows but explicitly synthetic tested. [Audit](reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md), [CLI](world-fixtures/planetary-a8-first-entry-provenance.md). Real ZIPs, real PNGs and full original planet arrays are private and NOT pushed. No new MFD river vector, no actual lake occupancy or physical Q; **auto-inject=0** until outlet matching and child topology P2-B2.4. Keep PR #103 DRAFT/UNMERGED and #99–101 separate; dev/frozen release unmodified.


### P2-B2.4 (2026-11-20): old A8 macro river exits vs CONNECTED CHILD Core MFD dominant channels — DRAFT #103

- New read-only external script scripts/compare_planetary_child_mfd_outlets_v02.py: directionally **INSIDE→OUTSIDE** old major A8 D8 links (distinct from earlier inlet provenance), accepted Core Priority Flood+MFD, Core dominant-channel area+terrain-aware initiation, positive-fraction adjoining channel edges traced to actual region boundary, and explicitly NONPHYSICAL jumps across geometrical lake proxy supernodes. Generates georeferenced-local-km masks/edge pairs + three-panel diagnostic PNG and manifest. This is NOT accepted Core RiverNetwork, physical water Q or proof of perennial lakes.
- Thresholds `stream_threshold_km2=30` and `matching_tolerance_km=30` are editable **demo** parameters, not immutable Earth/world rules. Matches only same boundary side within spatial tolerance, unique one-to-one, always tagged GEOMETRICALLY_NEAR_ONLY_NOT_SAME_WATERSHED; unmatched stays UNMATCHED, no terrain correction or A8→MFD forced merge.
- [Operator evidence](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-mfd-outlet-review.md). [GREEN synthetic map](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499) with 49 focused tests: toy A8 has **1 major macro exit**, new connected MFD cartoon has **19 terminal edge cells**, **1 same-side within-30km purely spatial match**. The discrepancy is exposed, not patched. Old source A/B/C major EXITS known A=1, B=2, C=0, but **actual real private A/B/C CHILD MFD outlet matching was NOT yet run**, do not invent distances.
- The CI demonstration is SYNTHETIC ONLY; original private literary planet A8/A12 and derived real maps have not been committed to public GitHub. Full pytest is to be confirmed at FINAL branch SHA; earlier source version had 554 tests passed. PR #103 DRAFT/UNMERGED. PR #99–101 remain drafts. dev/0.2 and frozen release untouched.
- **NEXT P2-B2.5**: run real private A/B/C matching, then specifically condition coarse river corridors and watershed boundaries on real source at 1km without changing original macro-station heights; recompute MFD and compare before/after. Land cover P3 and ImageGen only after credible river continuity.


### Latest P2-B2.4: macro river EXITS versus child MFD DOMINANT CONNECTED CHANNELS

Scripts: scripts/compare_planetary_child_mfd_outlets_v02.py (new), tests/test_planetary_child_mfd_outlet_alignment_v02.py, synthetic workflow. Read [operator review](reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md). Uses unchanged accepted Core Priority Flood/MFD and Core _dominant_channel_receiver_index, _dominant_channel_area_km2, _terrain_aware_initiation for cartographic one-path-per-flow-cell projection; validates contiguous edges to real boundary. Flags lake proxy jumps as nonphysical. Same-side exit comparison is only geometric and does not assert common basin. Demo 30km² initiation/30km tolerance, toy A8 1 large exit vs 19 MFD terminals, 1 spatial pair (not physically validated). Synthetic CI 49 focused GREEN [Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499). Real private A/B/C Core MFD outlet comparison NOT YET RUN; only old A8 large exits A/B/C=1/2/0. Next P2-B2.5 run REAL child maps, use macro-coherent hydrological conditioning and tests without violating original height anchors; further P3 world landcover and P4 map/satellite-like design. No Core commits/merges; #103 draft and #99–101 draft.



### P2-B2.5, 2026-11-20 — REAL PRIVATE A/B/C preliminary MFD check and NEGATIVE river-carving result

- Local PRIVATE original A8/A12 ZIPs used for independent 231×231 child DEM and Core-like Freeman MFD dominant-channel reconstruction **WITHOUT full current PR lake-supernode routing** (not byte-exact PR #103). Old major A8 exits vs same-side near new modeled terminals (30km): A=1 old exit / 1 near (0.028km), B=2 old / 2 near (1.078 and 3.682km), C=0 old / no verifiable exit matches. New independent channel-edge terminal counts 36/40/63. Source elevation anchors are mathematically fixed; PNG/JSON kept PRIVATELY in ChatGPT, never published to GitHub. This is *preliminary evidence only*, not a production PR reproducibility claim.
- New opt-in external `scripts/propose_planetary_river_corridor_v02.py` performs bounded negative excavation beside old A8 coarse river segments, preserving every original macro DEM station analytically, child boundary cells, land/sea sign; reevaluates after with actual connected Core MFD. It **NEVER automatically updates Core/child terrain**, and is marked NONCANONICAL and NOT_SEAMLESS across changing crop origins. A separate private independent A/B/C trial at -15m cap: A exit worsened from 0.028km to ~11.972km; B did not improve; C no old major exit to judge. **DO NOT APPLY THIS TRIAL** to real planet as-is; counterexample to global source-carving assumption.
- [Operator negative result](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) · [optional CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-river-corridor-trial.md) · [synthetic GREEN 57 focused tests](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Need check full pytest on final documentation SHA.
- **NEXT P2-B2.6:** compare true current Core lake-supernode routing on real B/C vs independent no-lake channels; diagnose 80m/55m virtual Priority Flood fill, verify basin shape/spills and decide whether topography needs targeted changes or world-defined lake/water rules. No false Earthlike norms; do not overbuild physics. PR #103 DRAFT/UNMERGED, #99–101 drafts, dev/0.2 and release/0.2-prealpha unchanged.


### Latest P2-B2.5: real private preliminary TEST and rejected river corridor correction

External draft #103 new script scripts/propose_planetary_river_corridor_v02.py and tests/test_planetary_source_corridor_trial_v02.py. The script makes optional bounded -15m candidate along ORIGINAL A8 D8 river-mask segments; exact analytic macro source anchors, unchanged edge heights and sea signs; real Core MFD rerun before/after and explicit reject/needs-review gates, never autocommit candidate. [CLI](world-fixtures/planetary-river-corridor-trial.md), [operator negative checkpoint](reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md). Real PRIVATE A/B/C source checked in chat with a separate mathematical P2-A+Core-like MFD reimplementation **without lake supernodes**: 1/2/0 old major A8 exits, nearest local matches A~0.028km B~1.078/3.682km, C no old exit; trial A worsened to ~11.972km; B unchanged; C untestable. THIS IS NOT EXACT production Core lake routing. No private ZIP/PNG into GitHub. [Actions GREEN 57 focus](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Next P2-B2.6: actual current Core lake-supernode routing in private B/C, analyze large virtual depressions, avoid forced river valleys without evidence. PR #103 remains draft; dev/release unchanged.



### P2-B2.6 — 2026-11-21: Core geometric lake proxies versus baseline MFD (DRAFT #103)

- Read-only experimental `scripts/diagnose_planetary_child_lake_topology_v02.py`: accepted Core priority_flood_surfaces, extract_lake_candidates, continuous_routing_field, choose_lake_outlets, bounded nested hierarchy, plus P2-B2.2 fast MFD/lake supernode accumulator **parity-checked against full accepted Core on SMALL synthetic lakes**. Same unchanged DEM with vs without routing proxy. Reports BOTH internal redistribution and terminal-edge balance (km², NOT Q); fail-closed unresolved/comparison-not-available mask if >12 basins, >12k candidate cells, or Core spill topology fails. No real lake occupancy inferred.
- [Operator review](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-6-core-lake-topology-vs-private-bc-2026-11-21.md) · [private checkout CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-lake-topology-compare.md). Synthetic Actions has three paths: unresolved many-basin region, forced unresolved, and 21x21 POSITIVE one-bowl exact Core-parity + PNG. Current SHA CI status must be read after docs update, not inferred.
- Original PRIVATE B/C real source tested in a **separate independent reconstruction of published P2-A/priority flood/MFD/spill algorithms, NOT an imported full PR #103 Core**. 1km candidate sizes: B 3 basins / 4185 cells, C 1 / 2135 cells at demo 16km²/10m; virtual fill maxima ~67.45m /55.18m. Candidate lake routing substantially changes INTERNAL contributing area (peak absolute ~19,256/32,124km²) but edge area remains fixed to ~1e-10km² numerical error. Earlier independent baseline obtained different counts; DO NOT treat these as author-canon or exact Core/regression. Private PNG and JSON are only in conversation, NOT GitHub.
- No original planet terrain changed. No macro A8 external water injected. Next **P2-B2.7** reproducible exact real B/C run in a checked-out PR #103 with source privacy, then basin-specific water occupancy/seasonality and onward P3 natural cover/P4 map/satellite-like art. PR #103 DRAFT/UNMERGED, PR #99–101 drafts separate, dev/0.2 and frozen release unchanged.


### Latest P2-B2.6 — actual Core lake components in synthetic CI / independent real B/C

Script scripts/diagnose_planetary_child_lake_topology_v02.py imports unchanged accepted Core PriorityFlood, lake candidates, continuous MFD, choose_lake_outlets, nested hierarchy. Uses fast P2-B2.2 Kahn graph for 231² with small-fixture parity to Core's full lake-supernode accumulation. Compares no-lake and with-geometric-lakes contributing area, flags large/many/unresolved basins, never interprets virtual fill as physical water. Operator report docs/reviews/p2-b2-6-core-lake-topology-vs-private-bc-2026-11-21.md, CLI docs/world-fixtures/planetary-child-lake-topology-compare.md. Original PRIVATE A8/A12 real B/C independent Core-formula reproduction (NOT imported same live source checkout) B 3 candidate basins 4185km², C 1 2135km², interior area redistribution maxima ~19,256/32,124km², edge sums unchanged numerically. These are not finished real-lake GIS. CI positive known-bowl + synthetic region unresolved. NEXT P2-B2.7 actual PR #103 checkout replay on same private source and then world-specific water balance and P3. Keep draft, do not merge, dev and release unchanged.


## 2026-11-21 — исправленная терминология и принцип достаточности

**Осве́ра** — рабочее, НЕ окончательно канонизированное название **планеты**. **Д’Акхар** — главный герой (ксенолог), НЕ регион и НЕ планета. Сохранённые исторические названия файлов `dakhar-first-arc` означают исходную арку *о герое*, а не географическое имя. Первая арка проходит в пока не зафиксированном по координатам регионе; модель A/B/C — кандидаты, НЕ авторское утверждение.

**Цель продукта:** авторская согласованность мест, природных препятствий, расстояний и маршрутов между арками, а НЕ научная диссертация о планете и НЕ обязательная карта для читателя. Дальнейшие гидрологические вычисления — только по реальному препятствию для художественной географии. Новый [прототип листа авторского атласа](docs/world-fixtures/osvera-author-region-atlas.md) и [реестр мест](examples/world-fixtures/osvera-first-arc-author-ledger.json) не размещают неизвестные объекты произвольно; промежуточная DEM и вся модельная география остаются неканоническими. [Публичный синтетический visual QA (6 tests GREEN)](https://github.com/MysterioCrypto/domain_generator/actions/runs/44886151409) НЕ является картой настоящей Осве́ры. Следующее P3-MVP — природный покров и первая цельная авторская карта с корректной легендой.

**Важно при продолжении:** не использовать словосочетания «планета Д’Акхара» или «регион Д’Акхар». Исторические имена скриптов/фикстур оставить без массового переименования (совместимость). Первую редакцию author sheet демонстрирует только SYNTHETIC CI; приватную реальную основу пока нужно собрать локально. Не рисовать лес без world-defined land-cover, не назначать координаты дома/переправы/города. Принцип «необходимой достаточности» автора приоритетнее бесконечных B2.x диагностика. PR #103 всё ещё draft, без merge.


### AUTHOR-PRODUCT PIVOT 2026-11-21 — IMPORTANT FOR NEXT CHAT

User correction: **Осве́ра** = tentative WORKING planet name, **Д’Акхар** = protagonist, NOT planet or region. Historical fixture path dakhar-first-arc is a legacy story-centered ID; don't bulk rename old filenames/PRs. Goal is author continuity of physical locations/distances/travel routes between arcs, not research dissertation or mandatory reader handout. User said *необходимая достаточность*. New files: scripts/render_author_region_atlas_v02.py, tests/test_author_region_atlas_v02.py, examples/world-fixtures/osvera-first-arc-author-ledger.json and docs/world-fixtures/osvera-author-region-atlas.md. First REAL PRIVATE A8/A12 author sheet for candidate region A run in chat using exact public scripts: 231², 1km, 63 exact macro DEM anchors, 5 story places UNPLACED, 2 unknown-distance routes; full 1.4MB private derived-region ZIP supplied to user as sandbox in conversation. Neither private original ZIPs nor real image uploaded to public GitHub. [Review](reviews/osvera-first-private-author-atlas-2026-11-21.md). Green SYNTHETIC atlas tests [Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/44886151409). Next P3-MVP is *visually useful* optional land-cover on real A using A12 scenario and world-defined class profile; do not infer literal forest from C3 or elevation; local MFD channel overlay remains candidate. Avoid more P2-B2.x unless genuine worldbuilding obstruction. PR #103 remains draft/unmerged and dev/release frozen.



## P3-MVP 2026-11-21 — source-conditioned noncanonical author natural cover

**Problem:** A visually useful author continuity map requires actual forest/open/rock/wetland candidate patterns; C3 vegetation potential and A12 source-biome code alone do not supply observed local cover. Endless lake-correction P2-B2 tests without a location conflict do not increase author usefulness. **Decision:** stop automatic hydrology deepening after P2-B2.6 for A, keep P2-B2.7 exact-Core private B/C validation as a targeted debt, implement ONE opt-in external visual land-cover source adapter in DRAFT PR #103.

**Code:** scripts/derive_author_natural_cover_v02.py with explicit editable examples/world-fixtures/osvera-working-cover-profile.json + tests/test_author_natural_cover_v02.py, integrated optional --cover-npz/--cover-manifest to scripts/render_author_region_atlas_v02.py. Source A12 latitude south-first, child north-first. Four source scenario votes blended spatially without source-grid rectangular nearest neighbor blocks; deterministic world-coordinate patch geometry; steep slope rock candidates, forest/open mosaic, WET LOWLAND only with original A12 wetland candidate AND locally lower terrain AND gentle slope. **Rejected:** directly treating broad A12 wetland_candidate mask as real swamp/water (early private candidate miscolored 65% of A as wet). Result is not canonical biome, measured forest, groundwater, permanent water or terrain mutation; no chosen landmark coordinates or travel times inferred.

**PRIVATE source real Osvera A:** independent cubic source-interpolated 231² region 230×230 km from original private A12, original source stations exactly reproduced numerically; candidate artist map ~71.9% woodland, ~16.2% open, ~11.9% potential lowland, zero forced rock. This private preview is NOT an exact current PR #103 P2-A/Core DEM replay, nor a claim of actual Osvera ecosystems; original source ZIP and derived map kept in ChatGPT, not public GitHub. [Review](reviews/p3-mvp-osvera-natural-cover-2026-11-21.md), [offline private runbook](world-fixtures/osvera-author-natural-cover.md). [Synthetic author-map CI](https://github.com/MysterioCrypto/domain_generator/actions/runs/44887608102) **16 focused tests GREEN**; check final SHA full pytest after docs.

**NEXT:** run P3 on EXACT source-conditioned child-A from this same PR #103 checkout using original private A12, inspect ONE author-facing complete cover map, not technical heatmaps. Then optional river topology/author landmark/route placement with explicit approvals and distance semantics; ImageGen only after geographic stabilization. **Planet working name Осве́ра, protagonist Д’Акхар** (not a toponym). PR #103 DRAFT/UNMERGED, dev/0.2 and frozen release untouched.
 (2026-11-21):** Draft PR #103 now includes tested P4-A map-first renderer scripts/render_region_cartographic_base_v02.py, dedicated tests and synthetic author-map workflow; last functional HEAD checks 612 passed, geo/author workflow GREEN. Private ORIGINAL A8/A12 verified, same exact Git modules P1/P2/P3 plus P4 renderer, generated one 230x230 km cartographic base with spherical_xyz_v1, real scale, north-up, 50-m model height isolines; same DEM and cover counts, 63 source anchors exact. Private Drive [map sheet](https://drive.google.com/file/d/1mZUlYpafZyF3wDWXKyANfgvcCGkOuSYH/view), [clean base](https://drive.google.com/file/d/1NfnBSXDdCXnHMb_X6xZFnCT7dkq-zjFO/view). Read docs/reviews/p4-a-region-a-map-first-renderer-2026-11-21.md for exact original ZIP SHA, Git blobs and limitations. User has NOT reviewed or accepted this P4 map. It is STILL NOT a complete geographic map: river topology, lakes, settlements, roads, 5 POI and 2 routes unknown. NEXT P4-B is evidence-driven child drainage candidate, NOT invented blue rivers or blind ImageGen. Do not change Core/freeze or merge #103 without gate; legacy global terrain default unchanged.

**NEWEST P3.6 AUTHOR DECISION (2026-11-21):** User formally chose RIGHT `spherical_xyz_v1` as OSVERA REGION-A WORKING detail for further experiments. User EXPLICITLY DID NOT accept either P3.5 atlas as a plausible/readable regional map; do NOT call current map finished or canon. No author-imposed repeat of spherical-vs-legacy selection is required. Keep generic legacy default, #103 DRAFT/UNMERGED, no POI positions/accepted river network, original ZIPs private. Product next task P4-A: one cartographically convincing top-down base from actual terrain and model-cover layers (no fabricated rivers/roads), separate map from technical panel, record exact inputs and geography; ImageGen mentioned only as uncertain future option, not a request to run. Read docs/reviews/p3-6-operator-selection-and-map-product-gap-2026-11-21.md, then current PROJECT/CONTEXT/PROGRESS and live PR SHA/CI.

**NEWEST P3.5 CHECKPOINT (2026-11-21):** Real PRIVATE original A8/A12 were downloaded and SHA-verified; exact GitHub P1/P2-A/P3/author-atlas MODULES + author ledger/profile (blob SHA-1 verified) were executed for BOTH legacy and opt-in spherical detail. Both full 230×230 km sheets stored as ONE side-by-side private Drive PNG (https://drive.google.com/file/d/12T79Z9GcKD41LyDGOaKli-WJlNK3emNQ/view); published review docs/reviews/p3-5-region-a-full-private-spherical-vs-legacy-2026-11-21.md. 63 parent anchors preserved with 0m error and same land; model cover changes in 13,510/53,361 pixels; forest/open/wet candidate legacy 64.058/16.731/19.211%, sphere 66.663/17.275/16.062%. Smaller diagonal artifacts in sphere; macro bands persist. **One-shot orchestration called exact implementations; private CLI wrapper itself NOT run.** NO operator acceptance, NO POI/route coordinates, NO accepted MFD or water balance. Keep PR #103 open/draft/unmerged and LEGACY default until explicit choice. Current PR head may differ due to documentation updates; verify GitHub. Next: author inspects real two-atlas comparison and chooses next spatial acceptance/repair.

**NEWEST P3.4 CHECKPOINT (2026-11-21):** PR #103 now has opt-in `spherical_xyz_v1` P2-A procedural detail option in both P2 standalone and one-command P3 atlas, legacy default unchanged. Real PRIVATE derived region-A NPZ comparison showed old P2 detail diagonal shear from latitude-scaled absolute-longitude easting; sphere-xyz removes most artificial anisotropy. See docs/reviews/p3-4-region-a-spherical-detail-projection-2026-11-21.md and private Drive screenshot, NOT a final P3 cover map. Synthetic CI must be checked on live head; no user visual acceptance, no merge, no Core change. Next if preferred: re-run complete private ZIP→child→cover→atlas with spherical mode and review one sheet.

**NEWEST P3.3 CHECKPOINT (2026-11-21):** Original A8/A12 ZIPs were FOUND in the user's connected Google Drive, validated against documented SHA and P1 full-world parity, and a first REAL region-A 230×230-km author sheet was computed through the exact P1/P2/P3/atlas function blobs. Child 231×231, 63 original anchors, 0m error. P3 candidate woodland/open/wet-lowland ~64.06/16.73/19.21%, NOT real ecology. Legend/footer overlap FIXED in PR #103 with a bbox regression, and final private PNG plus derived-only bundle STORED in private Drive. Read docs/reviews/p3-3-osvera-region-a-private-source-atlas-2026-11-21.md for evidence/links. **Operator visual acceptance NOT done. New P3.2 CLI wrapper itself not run privately**, only its exact underlying modules via temporary orchestration. Keep #103 draft/unmerged and don't publish ZIP originals or assume rivers/routes. Next step is visual author review of one map.

**NEWER P3.2 UPDATE (2026-11-21):** Draft PR #103 accepts ORIGINAL private A8/A12 ZIPs in one CLI call; see docs/world-fixtures/osvera-author-natural-cover.md P3.2. Uses existing P1 whole-source grid equality and one-station crop halo. Synthetic archive tests. No actual private region-A result / author acceptance, do not upload originals or merge #103 without decision. Reverify HEAD and CI.

**LATEST WORKING-BRANCH CHECKPOINT (2026-11-21):** Draft PR #103 now contains a source-verified P2-A -> P3 -> author-atlas CLI and synthetic CI. Read docs/PROGRESS.md and docs/world-fixtures/osvera-author-natural-cover.md for current next steps. NO exact private A8/A12 build or visual acceptance yet; keep PR #103 unmerged. dev/0.2 is accepted base; frozen release unchanged. Older "current" paragraphs below are historical.

## Copy into a new chat

Repository: `MysterioCrypto/domain_generator`.

Active development line: `dev/0.2`. Do **not** reconstruct current state from `main`.

First read, in order:

```text
PROJECT.md
docs/CONTEXT.md
docs/PROGRESS.md
docs/design/gross-catchment-precipitation-input-v0.2.md
docs/design/marine-coastal-boundary-v0.2.md
```

Current **product/recovery** checkpoint: [START_HERE.md](../START_HERE.md) → [docs/PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) → [D’Акхар source fixture](world-fixtures/dakhar-first-arc.md). Parallel technical H13-A: design #98 accepted/merged, implementation #99 draft/unmerged; #100 and #101 likewise draft/unmerged.

Post-H12 dependency audit is DONE. H13-A accepted design was merged as PR #98:
https://github.com/MysterioCrypto/domain_generator/pull/98

Design branch: `design/v0.2-gross-catchment-precipitation`.
Normative accepted document: `docs/design/gross-catchment-precipitation-input-v0.2.md` (now on dev/0.2).
Proposal: opt-in gross upstream atmospheric precipitation input (m³/year) from accepted C1 annual precipitation + accepted weighted MFD/lakes + optional H12 marine absorption. This is **not runoff/discharge/permanence**.
G01–G15 are the implementation acceptance plan. Design formally accepted by operator on 2026-11-15 and PR #98 merged at `0000a208183a2ff3b1d7dc8eee8f93d54f72ef35`. Implementation remains unaccepted. Do not merge implementation without separate ACCEPT.

- PR #97: https://github.com/MysterioCrypto/domain_generator/pull/97
- Merge: `3d275466ec5bfdb74f5dcb88bea6c8b641347f70`
- Accepted tests: O01–O13 GREEN, schema sync GREEN, 502 full tests passing, coastal workflow GREEN.
- Marine is opt-in; negative elevation alone does not imply sea. Boundary-connected 4-neighbour marine, refined shoreline and `marine_outlet` are accepted.
- Canonical dependency map: **see the beginning of `docs/CONTEXT.md`**. This handoff is not authoritative if they disagree.
- Next: implement H13-A in separate branch, G01–G15 and checkpoint; request separate IMPLEMENTATION ACCEPT / REJECT.

Accepted and frozen:
- Terrain 0.2;
- Hydrology 0.2 routing/network;
- C1 Annual Climate Forcing;
- C2 Effective Surface Moisture;
- C3 Climate-Aware Vegetation.

C3:
- design PR #84 merged;
- implementation PR #85 merged;
- merge commit: `37e213ebf5f82ebfae149d21088c07e08d836549`;
- V01–V11 GREEN;
- C3-A workflow GREEN and formally ACCEPTED:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36842261493`.

C3 semantics:
```text
accepted C2 moisture
× normalized annual thermal suitability
+ vegetation_bias
-> vegetation_density

canonical water = 0
```

`vegetation_density` is an abstract normalized ecological potential index, not percent canopy cover or literal NPP.

Mountain influence:
- C1 elevation/lapse-rate temperature;
- C1 windward/lee precipitation;
- C2 slope retention;
- terrain-shaped hydrology feeding C2;
- no second direct C3 slope penalty.

Hydro-surface readiness audit:
- perennial / seasonal / dry remains blocked by absent seasonality/baseflow/groundwater;
- lake vs wetland/playa/dry basin remains blocked by absent water-balance/permanence;
- delta/estuary/fan remains blocked by absent receiving-environment/process context;
- headwater visibility can use the accepted potential scaffold, but that scaffold is currently internal only.

H11-A design PR #86 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/86`

Merge commit:
`712dae3179605b894558a9e399cd6929ffcda459`

Accepted design:
```text
Core 0.2 networks["rivers"] = accepted regional H09-D2
Core 0.2 networks["potential_drainage"] = accepted H09-E potential network
```

No flow-permanence labels, no Strahler public metadata, no hydrology geometry changes.

H11-A implementation:
- PR #87 ACCEPTED / merged;
- merge commit: `cef91e81c86c64555ae1e1363d7ffaf2934ff6ce`;
- checkpoint: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`;
- Core 0.2 public networks: `rivers`, `potential_drainage`;
- Core 0.1 remains `rivers` only;
- potential network is a drainage scaffold, not a permanence class.

Physical hydro classifications still deferred:
- perennial / seasonal / dry;
- lake vs wetland/playa/dry basin;
- delta / estuary / fan.

Immediate next step:
- Placement readiness audit against accepted Core 0.2 environment;
- choose one bounded Placement slice;
- design before implementation if semantics materially change.

Do not reopen the accepted hydrology routing/network body without concrete evidence.

Process rule:
after every meaningful implementation/decision slice, update external context so a chat failure loses at most the current unfinished step.


## Placement readiness result

Existing Core 0.1 placement mechanics are retained:
- lattice/reservation/footprint;
- requirements;
- preferences;
- near-best;
- deterministic weighted selection.

Core 0.2 automatically gives new meaning to:
- `moisture_mean` via C2;
- `vegetation_density_mean` via C3.

P08-A design PR #88 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/88`

Merge commit:
`66003288e528fc340663d92f84ed14cbee88744b`

Accepted Core 0.2-only metrics:
```text
temperature_mean
annual_precipitation_mean
distance_to_potential_drainage
```

P08-A implementation:
- PR #89 ACCEPTED / merged;
- merge commit: `57e77c8de6ac8668ddd09e25167e30aa773cf645`;
- P01–P11 GREEN;
- checkpoint: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`;
- Core 0.1 registry remains 8 metrics;
- Core 0.2 adds temperature_mean, annual_precipitation_mean, distance_to_potential_drainage;
- existing Placement mechanics remain unchanged.

Immediate next step:
- audit remaining Placement boundaries;
- choose one bounded Core 0.2 follow-up slice;
- design before implementation if semantics change.


## Placement closure / A08 hardening

Post-P08-A audit found no additional base Placement contract gap. New Core 0.2 metrics already pass through normal preset/compiler SiteProfile strings.

Placement current scope is complete.

Hardening PR #90:
`https://github.com/MysterioCrypto/domain_generator/pull/90`

A08 is a full Core 0.2 acceptance fixture using P08-A metrics through a real preset. Initial baseline is intentionally PENDING so CI can emit the exact deterministic snapshot before pinning.

No new world semantics are introduced by PR #90.


## A08 integrated acceptance

PR #90 merged:
`568eeff9676ee387d5837cfb1fca1a8ff087e99b`

A08 is frozen and GREEN:
- full Core 0.2 pipeline;
- P08-A metrics through preset/compiler;
- exact replay;
- canonical bundle;
- regional + potential networks.

Release-readiness audit now focuses on stale package/docs version metadata. Independent contract versions remain independent unless a concrete shape break requires a bump.


## Core 0.2 release-candidate readiness

PR #91 merged:
`5cafb8119050f19765447d65dcef022ebebe052b`

Generator identity:
`0.2.0.dev0`

Merge-head pytest GREEN:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36853774759`

A01–A08 are GREEN. Version re-sign changed only DomainData provenance hashes; world fields/geometry/networks/placement remained identical.

No known blocker remains inside accepted Core 0.2 scope.

Operator formally ACCEPTED the release candidate.

Frozen release:
- branch: `release/0.2-prealpha`;
- exact freeze commit: `c69c1af010a085fb80d248af703a77471fc6c9d7`;
- generator identity: `0.2.0.dev0`.

The release branch is frozen. New semantic work continues only on `dev/0.2`.

Immediate next step:
- choose the next post-release semantic layer;
- open a new INV-006 design gate before material implementation;
- do not reopen accepted Core 0.2 semantics without concrete evidence.


## Post-release C4-A seasonality

Dependency audit rejected immediate biome classification because current climate is annual-only.

Design PR #92:
`https://github.com/MysterioCrypto/domain_generator/pull/92`

Proposal:
- optional explicit 12-month climatological envelope;
- monthly temperature preserves annual mean;
- monthly precipitation preserves annual total;
- explicit peak months and amplitudes;
- no hemisphere/latitude inference;
- no new monthly noise or seasonal wind changes;
- C2/C3 unchanged during C4-A;
- no biome or stream-permanence labels yet;
- no seasonality recipe means frozen prealpha-compatible annual behavior.

C4-A design PR #92 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/92`

Merge commit:
`e729d836d29df790fa1c0056e7b686d6189703f9`

C4-A implementation:
- PR #93 ACCEPTED / merged: `https://github.com/MysterioCrypto/domain_generator/pull/93`;
- accepted semantic head: `5b9b4e7341bfb3c8b496f25b3e9f741128f31b2a`;
- merge commit: `570a5c4730419d17bce69f9e804b805125343fa5`;
- S01–S13 GREEN;
- schema snapshots GREEN;
- push/PR full pytest GREEN;
- representative checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36959449118`;
- exactly 24 monthly derived fields;
- annual C1/C2/C3 canonical outputs exact-unchanged;
- features/networks unchanged.

Important compatibility fix:
- absent seasonality initially altered frozen A08 fingerprints because the new optional field serialized as null;
- this was fixed by omitting only absent seasonality from fingerprint payloads;
- frozen A08 fingerprints are explicitly pinned by S10;
- explicit seasonality still changes semantic fingerprint.

Representative conservation after float32 persistence:
- temperature max error ~4.77e-7 C;
- precipitation max error ~1.91e-4 mm.

Operator formally ACCEPTED C4-A implementation.

Immediate next step:
- perform a fresh post-C4 dependency audit;
- choose exactly one next bounded semantic layer;
- open a new INV-006 design gate before implementation;
- do not assume biome or flow-permanence is ready without checking its remaining dependencies.

`release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Post-C4 audit / C5-A

After C4:
- channel permanence is still blocked by groundwater/baseflow/storage;
- lake/wetland/playa/dry-basin semantics are still blocked by basin permanence/water balance;
- delta/estuary/fan remains blocked by receiving-environment context;
- direct biome labels remain deferred.

Selected next bounded layer:
**C5-A Köppen–Geiger climate regionalization**.

Design PR #94:
`https://github.com/MysterioCrypto/domain_generator/pull/94`

Proposal:
- opt-in scheme `koppen_geiger_local_season_v1`;
- derived `uint8` field `climate_regime_koppen_geiger`;
- fixed 30-class codebook;
- local warm/cold half-year anchored on explicit C4 temperature peak month;
- climate classification only, not biome classification.

No runtime implementation before explicit C5-A design ACCEPT.


C5-A design PR #94 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/94`

Merge commit:
`d75b2f6f55b53a14b048a38bb2a69d339c8cf44e`

Important:
- Köppen remains opt-in Earth-derived interpretation only;
- C4 climate parameters are explicit inputs, not hard-coded geography;
- fantasy/non-Earthlike worlds may omit classification entirely;
- exact Beck/Peel 10 C boundary retained.

C5-A implementation:
- PR #95 ACCEPTED / merged: `https://github.com/MysterioCrypto/domain_generator/pull/95`;
- accepted semantic head: `43519587fac92e94cb8bbbb64222c876d7579882`;
- merge commit: `8af34da0c66c48b62172b8654edc5876d9414085`;
- K01–K15 GREEN;
- schema snapshots GREEN;
- push/PR full pytest GREEN;
- representative checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36968143576`;
- all pre-existing C4 fields/features/networks exact-unchanged;
- output is one optional derived uint8 climate-regime field.

Representative map uses 7 of the 30 possible classes and is dominated by Csb because the diagnostic input is intentionally winter-wet / warm-season-dry. This is test input behavior, not a hidden default.

Operator formally ACCEPTED C5-A implementation.

Immediate next step:
- perform a fresh post-C5 dependency audit;
- select exactly one next bounded semantic layer;
- open a new design gate before implementation;
- keep `release/0.2-prealpha` frozen.


## Post-C5 audit / H12-A

Post-C5 audit found:
- direct biome labels still deferred;
- channel permanence still blocked by groundwater/baseflow/storage;
- basin permanence/type still blocked by water balance/infiltration;
- delta/estuary/fan still blocked by receiving-environment/process context.

Universality audit exposed a more fundamental missing capability: no sea/ocean/coastline semantics exist.

Design PR #96:
`https://github.com/MysterioCrypto/domain_generator/pull/96`

Proposal:
- optional explicit `hydrology.marine.sea_level_m`;
- no hidden sea level;
- marine = boundary-connected below-sea terrain using 4-neighbour connectivity;
- enclosed below-sea basins remain inland;
- derived `marine_mask`;
- refined 4× coastline;
- distinct `MarineFeature`;
- `marine_outlet` river nodes;
- regional/potential rivers stop at first coastline intersection;
- no tides/waves/salinity/delta/estuary semantics yet.

H12-A design PR #96 ACCEPTED / merged:
`https://github.com/MysterioCrypto/domain_generator/pull/96`

Merge commit:
`f8efae6e24cdda68fb10960f13ca69d342a61a7b`

Immediate next step:
- separate H12-A implementation branch;
- O01–O13 + dedicated coastal/archipelago checkpoint;
- no implementation merge before explicit ACCEPT.


H12 implementation clarification:
- marine enters canonical water_depth;
- no C2/C3 algorithm changes;
- new marine cells therefore inherit accepted canonical-water semantics: moisture=1, vegetation=0;
- outside marine support C2/C3 stay exact-unchanged;
- C1/C4/C5 climate remains unchanged.


Further H12 clarification:
- C2 distance-to-water means marine water can affect nearby coastal land moisture;
- C3 may then change via accepted C2 moisture;
- algorithms/parameters stay unchanged; only deterministic dependency propagation is allowed;
- C1/C4/C5 climate remains exact-unchanged;
- no marine-specific ecological formula is part of H12.


H12 implementation is now active:
- draft PR #97: `https://github.com/MysterioCrypto/domain_generator/pull/97`;
- branch `impl/v0.2-marine-coastal-boundary`;
- contract/classification/coastline/marine-depth/marine-outlet/public-mask integration is implemented;
- first regression exposed and fixed an accidental attempt to pass marine exclusion into MFD accumulation; routing/accumulation remains frozen;
- O01–O13 tests are added and currently under CI;
- schema sync and dedicated coastal checkpoint remain pending;
- PR remains unmerged.


H12-A implementation recovery is complete.

Current implementation:
- draft PR #97: `https://github.com/MysterioCrypto/domain_generator/pull/97`;
- semantic head: `4dc897906d2e67ae7c3bccb2c9ef49934339f4a6`;
- O01-O13 GREEN;
- schema snapshots GREEN;
- PR and push full pytest: 502 passed;
- dedicated coastal/archipelago checkpoint GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161098`.

Checkpoint observations:
- marine fraction ≈42.64%;
- one marine component with one island hole;
- two inland lakes;
- enclosed below-sea basin remains non-marine;
- regional/potential drainage terminates at refined coastline;
- no visible channels continue through marine interior;
- fixed 4× refinement is visibly stepped at ~250 m, as accepted by design.

Historical operator-review gate was closed by formal ACCEPT on 2026-10-09.

Current gate: **POST-H12 DEPENDENCY AUDIT**. PR #97 is merged, not draft or pending.
Read the top-level dependency map in `docs/CONTEXT.md` before choosing the next slice.


## Historical checkpoint: H13-A design review (now accepted)

- PR #98: https://github.com/MysterioCrypto/domain_generator/pull/98
- Branch: `design/v0.2-gross-catchment-precipitation`
- Runtime: NOT STARTED.
- Status: awaiting explicit design ACCEPT / REJECT.
- Accepted upstream: C1 annual precipitation; Hydrology 0.2 MFD weighted DAG and lake supernodes; H12 marine is optional.
- Proposed output: one derived float64 `gross_upstream_precipitation_m3_per_year` field.
- Key semantic limit: **mathematically allocated gross upstream rainfall input**, NOT water physically delivered to a channel; no runoff, discharge, water-balance closure or stream permanence.
- Design clarification (2026-11-15), PR #98 head `5fbd6b5904071feefc38a0ab66f093e68845e81e`: compute in the existing SURFACE stage after C1 is available; no new ValidationStage and no assembly-side physics. Keep accepted MFD area outputs unchanged.
- Explicitly still blocked: perennial/seasonal/dry flow (baseflow/storage/infiltration), delta/estuary (sediment/discharge/coastal processes), lake/wetland/playa permanence, direct biome labels.
- Context-map source of truth: top of `docs/CONTEXT.md`, which now shows H13 as PROPOSED, not part of accepted DAG.
- Next: operator design decision; ACCEPT allows design merge and a **separate** implementation branch, not implementation merge.

Frozen `release/0.2-prealpha`: `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Current checkpoint: H13-A DESIGN ACCEPTED / implementation development

- User formally accepted design on 2026-11-15; PR #98 merged `0000a208183a2ff3b1d7dc8eee8f93d54f72ef35` with successful push and PR CI on design HEAD `5fbd6b5904071feefc38a0ab66f093e68845e81e`.
- Normative spec on dev: `docs/design/gross-catchment-precipitation-input-v0.2.md`.
- Active branch: `dev/0.2`, new independent implementation branch forthcoming. No implementation ACCEPT and no implementation merge.
- Physical interpretation: **annual gross upstream source allocation under MFD**, not actual delivered water/discharge/runoff. C4/C5 not dependencies; H12 optional.
- Implementation must protect baseline MFD/lake supernode behavior, coastline terminal ledger, exact opt-out fingerprint, float64 derived field, deterministic replay, and stable canonical stages; G01–G15 + wet/dry/coastal evidence.
- After each meaningful milestone, update `PROJECT.md`, `docs/CONTEXT.md`, `docs/PROGRESS.md` and this handoff; keep historical release unchanged.


## New active product route — 2026-11-15

- One-click repo navigation at START_HERE.md; P0–P6 roadmap in docs/PRODUCT_ROADMAP.md; non-Earth D’Акхар source at docs/world-fixtures/dakhar-first-arc.md with JSON source-only fixture and stdlib tests.
- Original A1–A11 and A12 Drive archives plus georeferenced PNG atlas ARE PRESENT: direct Google_Drive.fetch folder lists them even when search returned empty. A8/A12 NumPy arrays are now parsed, SHA-256 verified, A8 north→south versus A12 south→north orientation reconciled (reverse A8 raster rows exact). A10/A11 ZIPs and NPZ content independently SHA/CRC-verified; A10 annual_Q exactly equals its copy in A12_inputs; no Core import. Do not claim import; working Atlas A/B/C proposed not canon, short planetary year 202.755 Earth days; mm/planetary year not automatically Earth mm/year.
- Next bounded visible step: three actually different regional terrain/hydrology scenes. Follow with opt-in world-defined land cover; no more unneeded parchment physics. Preserve dev/0.2 accepted contracts, three unmerged PRs #99/100/101 and frozen release.


- **Live source QA evidence:** A8 ZIP SHA `6824ccf2...`, A12 ZIP SHA `db9f0f91...`, A12_inputs NPZ SHA `f2d6c446...` (complete in docs/reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md). Original 600×1200 arrays identical for elevation+land after A8 row reversal. User-visible source-derived diagnostic map created outside repo from private Drive archives; do not commit private ZIP or rendered crops to public repo without explicit consent.


## P1 planetary macro-geogrid adapter — 2026-11-15, DRAFT #103

- User's non-Earth source A8/A10/A11/A12 archives are verified (SHA/CRC, A8 north-first vs A10/A11/A12 south-first) and kept PRIVATE. Source A8 global D8 is an older research hydrology, not Core 0.2 accepted MFD.
- On an isolated DRAFT [PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103), external-only script scripts/export_planetary_macro_region_v02.py reads paths of original ZIPs, validates exact A8/A12 shared land/DEM, accepts user-specified planetary radius/year and local km source crop, remaps BOTH endpoints of A8 global flattened D8 downstream indices, and flags rivers exiting crop. It emits source NPZ+manifest+PNG, deliberately NOT DomainData and NOT fake local 1-km elevation.
- Synthetic workflow [GREEN](https://github.com/MysterioCrypto/domain_generator/actions/runs/43742308913) passes 4 targeted tests and writes a demo artifact. No private source ZIP/PNG was committed or uploaded to Actions.
- [CLI instructions and explicit boundaries](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-geogrid-adapter.md). Next meaningful work is source-constrained finer regional terrain and new MFD river generation, followed by non-Earth profile-based land cover; not further parchment filters or full planetary climate science.
- This is a parallel draft branch. PR #99 H13, #100 C2 tests, #101 atlas composer remain DRAFT/UNMERGED. Frozen release c69c1af010a085fb80d248af703a77471fc6c9d7 remains unchanged.


### P2-A 1-km non-Earth child terrain preview (2026-11-15)

- In isolated draft #103, scripts/condition_planetary_child_terrain_v02.py uses the source macro NPZ/manifest and explicit planet-year/radius to synthesize WORLD-LOCKED multiscale local DEM texture, with exact A8 parent elevations and C1 cubic parent interpolation. Outputs new child NPZ/manifest/PNG, NOT Core DomainData or accepted MFD.
- Original A/B/C private-source regions, 230×230 km each, 231×231 child samples and source elevation anchors 63/49/49 exact. Source assets and real derived images are not in public repo or Actions; only synthetic illustration is in dedicated GitHub Actions [run](https://github.com/MysterioCrypto/domain_generator/actions/runs/43746102251).
- [Design/bounds](world-fixtures/planetary-child-terrain.md). **Next P2-B:** parent-conditioned MFD, river continuity and outlets, then land cover; never paint old D8 over child and pretend new hydrology validated. No implicit merge of #103/#99/#100/#101.


### Current P2-B1 handoff (2026-11-16)

- Branch `feature/v0.2-planetary-geogrid-source-adapter` draft PR #103 gained `scripts/diagnose_planetary_child_mfd_v02.py` and six targeted tests plus deep-depression regression. Accepted Core Priority-Flood and MFD fractions used **without changes**; local-source accumulation matches accepted distributed flow at small grids, 1km² sources conserved to edge, A8 old D8 river segments only guide. [GREEN 19-test synthetic Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/43805052775) with child-MFD PNG, no private user-world data publicly uploaded.
- Real private A/B/C diagnostic maps generated from old source ZIP using independent local SciPy C2 cubic DEM approximation (different from GitHub C1 Hermite) and equivalent published Core MFD weights: deep virtual fill depressions B=88.5m, C=60.0m, A=12.4m. This is a real map-design blocker; must **NOT** call the filled MFD fan a validated physical river. Repro screenshots/results attached in chat, not GitHub. [User and technical review](reviews/p2-b-child-mfd-reference-audit-2026-11-16.md).
- Next P2-B2: accepted lake candidates/spill supernodes and external inflow/basin boundary coupling to historic source A8 D8 (not same algorithm), plus continuity QA, NOT more aesthetic filters. Still no accepted world-cover classes or production ImageGen. Frozen release unchanged; previous PRs stay draft.


### P2-B2.1 — geometric lake basin review (2026-11-20, PR #103 DRAFT)

- [Visual synthetic QA](https://github.com/MysterioCrypto/domain_generator/actions/runs/44748762996) and [operator review](reviews/p2-b2-1-child-lake-basin-operator-checkpoint-2026-11-20.md): external read-only `scripts/audit_planetary_child_lakes_v02.py`, Core Priority Flood/extract_lake_candidates/choose_lake_outlets, bounded nested hierarchy, Core lake-supernode conservation on SMALL bowl only. Proposed basin ≠ actual water occupancy; no universal Earth-specific thresholds, no external inflow, no source-D8 substitution.
- 27 focused tests GREEN; full algorithmic SHA pytest 532 GREEN; final docs SHA must have new CI. Private A/B/C sensitivity screening performed locally using independently interpolated DEM, not an exact PR P2-A regression; resulting numerical/visual data stay in conversation only.
- P2-B2.2 next: source-macro boundary inflows/outflows and constrained MFD+lake supernode routing, before asserting credible river/ford/waterfall geometry. Keep PR #103, #99–101 draft/unmerged. Frozen `release/0.2-prealpha` unchanged.


### P2-B2.2 — explicit cross-scale river boundary area (2026-11-20, draft PR #103)

- External scripts/condition_planetary_child_boundary_mfd_v02.py: identify directionally INCOMING original A8 D8 macro-river links at a 230km child box; preserve source catchment as UNSAFE_HINT only. With NO explicit scenario, inject **zero** external km2. With a keyed, operator-annotated, positive EXTERNAL_ONLY scenario, run new Core-compatible O((N+E)logN) MFD + geometric lake-supernode area propagation and enforce area-conservation ledger. It is **NOT discharge Q**, a world water balance, actual lake occupancy, an accepted child vector river network or an automatic A8-to-MFD merger. Does not mutate normative Core.
- [Operator audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md) · [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-boundary-inflow.md). [Synthetic GREEN preview and ledger](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925): 35 focused tests, two contrasting maps, no private source uploaded. [Full pytest GREEN 540](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA 35163cd7b6f8c3c9c8c74ea3a5ec24c2aa603dc3; check final documentation SHA again.
- Original PRIVATE A8/A12 data were screened locally for 230×230km A/B/C: OLD D8 crossing counts A **1 IN / 1 OUT**, B **0 IN / 2 OUT**, C **0/0**. A source D8 entry has upstream catchment proxy **86,106.66 km²**, but this is **NOT** verified external-only area and MUST NOT be injected unexamined. No old-source data/real-derived maps in public GitHub.
- **NEXT P2-B2.3:** compute true external-only provenance using original global D8 with re-entry detection, then compare macro basin exits to new actual connected MFD channels and qualify real lake occupancy per world-specific water profile. PR #103 DRAFT/UNMERGED, #99–101 DRAFT/UNMERGED; dev/0.2 and frozen release unchanged.


### P2-B2.2 next-chat recovery: A8 boundary inflows are NOT A8 catchment totals

External script scripts/condition_planetary_child_boundary_mfd_v02.py + tests/test_planetary_boundary_inflow_mfd_v02.py landed in **draft/unmerged PR #103** on 2026-11-20. Exact Core Priority Flood/MFD weights with fast lake supernodes area graph. No automatic A8 D8 catchment injections; only keyed operator EXTERNAL_ONLY assumptions (not independently validated) may add km². GREEN 35 targeted tests [Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925), full 540 [pytest](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA. Real private original A/B/C old macro crossings A=1 incoming/1 outgoing, B=0/2, C=0/0, and A source catchment ≈86,106.66 km² UNSAFE_HINT; original real PNG/JSON only in chat, never public repo. New child river network **not yet validated** and lake occupancy **not inferred**. [Review](reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md). NEXT P2-B2.3 implement provenance of truly outside-only upstream graph area with D8 re-entry detection; compare macro outlets to accepted fine MFD vectors, no false Q/water claims.


### P2-B2.3 · 2026-11-20: global A8 FIRST-ENTRY source partition (DRAFT #103)

- The original PRIVATE global A8 600×1200 D8 graph (not a crop) was inspected. New external script scripts/trace_a8_external_first_entry_v02.py computes the partition of **each original EXTERIOR LAND SOURCE cell** by the FIRST directed downstream entry into each 230km child rectangle. This prevents source-area duplication on exit/re-entry: only own new exterior source area is allocated to later entries. Full graph must be acyclic; macro/crop links must match exact global A8 lat/lon/receiver indices; A8 source cell area uses world radius and cos(latitude), NOT Earth constants.
- Original privately checked working model A/B/C: all directed A8 entry LINKS **23 / 12 / 5**; subset tagged old major river mask **1 / 0 / 0**. All-source EXTERIOR first-entry areas A ≈297,336.828km² / B ≈87,705.114km² / C ≈11,515.098km². A's ONE major river has A8 external first-entry area ≈**86,106.657km²**, matching old total source catchment ≈86,106.65625km² within rounding. No inside-upstream reentry in these specific scenes; a synthetic exit→reentry case is tested explicitly.
- A8 first-entry provenance is NOT physically verified 1km CHILD MFD drainage, river discharge Q or author canon. **No auto injection into child MFD.** Old D8 river_mask ignores numerous smaller old macro incoming links; B/C "zero major" DOES NOT mean no rivers. Private source ZIPs and actual region imagery are NOT committed to public GitHub.
- [P2-B2.3 audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-a8-first-entry-provenance.md). Synthetic tests cover reentry, unequal latitude row areas, cycle and source mismatch; current CI status must be confirmed at latest final SHA.
- **NEXT P2-B2.4:** match source A8 MACRO outlets with actual CHILD MFD edge-terminal geography and connected river lines, then explicit world-specific hydrologic semantics; neither A8 D8 nor newly rendered detail is authoritative. PR #103 remains DRAFT/UNMERGED; #99–101 drafts and dev/0.2/frozen release unchanged.


### P2-B2.3 recover global A8 provenance, do NOT auto-inject

Branch feature/v0.2-planetary-geogrid-source-adapter (draft PR #103) now has scripts/trace_a8_external_first_entry_v02.py, tests/test_a8_external_first_entry_v02.py and workflow synthetic global A8 audit. It classifies each OUTSIDE original A8 land source by FIRST downstream entry to child; this avoids double-counting when river passes inside→outside→inside. A8 source-only provenance: A/B/C 230km boxes all macro inbound links =23/12/5; old MAJOR river links=1/0/0. A old major inbound outside-only area=86,106.657km² vs original unsafe full catchment=86,106.65625km²; B/C also contain many smaller links. Reentry zero in 3 real windows but explicitly synthetic tested. [Audit](reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md), [CLI](world-fixtures/planetary-a8-first-entry-provenance.md). Real ZIPs, real PNGs and full original planet arrays are private and NOT pushed. No new MFD river vector, no actual lake occupancy or physical Q; **auto-inject=0** until outlet matching and child topology P2-B2.4. Keep PR #103 DRAFT/UNMERGED and #99–101 separate; dev/frozen release unmodified.


### P2-B2.4 (2026-11-20): old A8 macro river exits vs CONNECTED CHILD Core MFD dominant channels — DRAFT #103

- New read-only external script scripts/compare_planetary_child_mfd_outlets_v02.py: directionally **INSIDE→OUTSIDE** old major A8 D8 links (distinct from earlier inlet provenance), accepted Core Priority Flood+MFD, Core dominant-channel area+terrain-aware initiation, positive-fraction adjoining channel edges traced to actual region boundary, and explicitly NONPHYSICAL jumps across geometrical lake proxy supernodes. Generates georeferenced-local-km masks/edge pairs + three-panel diagnostic PNG and manifest. This is NOT accepted Core RiverNetwork, physical water Q or proof of perennial lakes.
- Thresholds `stream_threshold_km2=30` and `matching_tolerance_km=30` are editable **demo** parameters, not immutable Earth/world rules. Matches only same boundary side within spatial tolerance, unique one-to-one, always tagged GEOMETRICALLY_NEAR_ONLY_NOT_SAME_WATERSHED; unmatched stays UNMATCHED, no terrain correction or A8→MFD forced merge.
- [Operator evidence](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-mfd-outlet-review.md). [GREEN synthetic map](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499) with 49 focused tests: toy A8 has **1 major macro exit**, new connected MFD cartoon has **19 terminal edge cells**, **1 same-side within-30km purely spatial match**. The discrepancy is exposed, not patched. Old source A/B/C major EXITS known A=1, B=2, C=0, but **actual real private A/B/C CHILD MFD outlet matching was NOT yet run**, do not invent distances.
- The CI demonstration is SYNTHETIC ONLY; original private literary planet A8/A12 and derived real maps have not been committed to public GitHub. Full pytest is to be confirmed at FINAL branch SHA; earlier source version had 554 tests passed. PR #103 DRAFT/UNMERGED. PR #99–101 remain drafts. dev/0.2 and frozen release untouched.
- **NEXT P2-B2.5**: run real private A/B/C matching, then specifically condition coarse river corridors and watershed boundaries on real source at 1km without changing original macro-station heights; recompute MFD and compare before/after. Land cover P3 and ImageGen only after credible river continuity.


### Latest P2-B2.4: macro river EXITS versus child MFD DOMINANT CONNECTED CHANNELS

Scripts: scripts/compare_planetary_child_mfd_outlets_v02.py (new), tests/test_planetary_child_mfd_outlet_alignment_v02.py, synthetic workflow. Read [operator review](reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md). Uses unchanged accepted Core Priority Flood/MFD and Core _dominant_channel_receiver_index, _dominant_channel_area_km2, _terrain_aware_initiation for cartographic one-path-per-flow-cell projection; validates contiguous edges to real boundary. Flags lake proxy jumps as nonphysical. Same-side exit comparison is only geometric and does not assert common basin. Demo 30km² initiation/30km tolerance, toy A8 1 large exit vs 19 MFD terminals, 1 spatial pair (not physically validated). Synthetic CI 49 focused GREEN [Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499). Real private A/B/C Core MFD outlet comparison NOT YET RUN; only old A8 large exits A/B/C=1/2/0. Next P2-B2.5 run REAL child maps, use macro-coherent hydrological conditioning and tests without violating original height anchors; further P3 world landcover and P4 map/satellite-like design. No Core commits/merges; #103 draft and #99–101 draft.



### P2-B2.5, 2026-11-20 — REAL PRIVATE A/B/C preliminary MFD check and NEGATIVE river-carving result

- Local PRIVATE original A8/A12 ZIPs used for independent 231×231 child DEM and Core-like Freeman MFD dominant-channel reconstruction **WITHOUT full current PR lake-supernode routing** (not byte-exact PR #103). Old major A8 exits vs same-side near new modeled terminals (30km): A=1 old exit / 1 near (0.028km), B=2 old / 2 near (1.078 and 3.682km), C=0 old / no verifiable exit matches. New independent channel-edge terminal counts 36/40/63. Source elevation anchors are mathematically fixed; PNG/JSON kept PRIVATELY in ChatGPT, never published to GitHub. This is *preliminary evidence only*, not a production PR reproducibility claim.
- New opt-in external `scripts/propose_planetary_river_corridor_v02.py` performs bounded negative excavation beside old A8 coarse river segments, preserving every original macro DEM station analytically, child boundary cells, land/sea sign; reevaluates after with actual connected Core MFD. It **NEVER automatically updates Core/child terrain**, and is marked NONCANONICAL and NOT_SEAMLESS across changing crop origins. A separate private independent A/B/C trial at -15m cap: A exit worsened from 0.028km to ~11.972km; B did not improve; C no old major exit to judge. **DO NOT APPLY THIS TRIAL** to real planet as-is; counterexample to global source-carving assumption.
- [Operator negative result](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) · [optional CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-river-corridor-trial.md) · [synthetic GREEN 57 focused tests](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Need check full pytest on final documentation SHA.
- **NEXT P2-B2.6:** compare true current Core lake-supernode routing on real B/C vs independent no-lake channels; diagnose 80m/55m virtual Priority Flood fill, verify basin shape/spills and decide whether topography needs targeted changes or world-defined lake/water rules. No false Earthlike norms; do not overbuild physics. PR #103 DRAFT/UNMERGED, #99–101 drafts, dev/0.2 and release/0.2-prealpha unchanged.


### Latest P2-B2.5: real private preliminary TEST and rejected river corridor correction

External draft #103 new script scripts/propose_planetary_river_corridor_v02.py and tests/test_planetary_source_corridor_trial_v02.py. The script makes optional bounded -15m candidate along ORIGINAL A8 D8 river-mask segments; exact analytic macro source anchors, unchanged edge heights and sea signs; real Core MFD rerun before/after and explicit reject/needs-review gates, never autocommit candidate. [CLI](world-fixtures/planetary-river-corridor-trial.md), [operator negative checkpoint](reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md). Real PRIVATE A/B/C source checked in chat with a separate mathematical P2-A+Core-like MFD reimplementation **without lake supernodes**: 1/2/0 old major A8 exits, nearest local matches A~0.028km B~1.078/3.682km, C no old exit; trial A worsened to ~11.972km; B unchanged; C untestable. THIS IS NOT EXACT production Core lake routing. No private ZIP/PNG into GitHub. [Actions GREEN 57 focus](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Next P2-B2.6: actual current Core lake-supernode routing in private B/C, analyze large virtual depressions, avoid forced river valleys without evidence. PR #103 remains draft; dev/release unchanged.



### P2-B2.6 — 2026-11-21: Core geometric lake proxies versus baseline MFD (DRAFT #103)

- Read-only experimental `scripts/diagnose_planetary_child_lake_topology_v02.py`: accepted Core priority_flood_surfaces, extract_lake_candidates, continuous_routing_field, choose_lake_outlets, bounded nested hierarchy, plus P2-B2.2 fast MFD/lake supernode accumulator **parity-checked against full accepted Core on SMALL synthetic lakes**. Same unchanged DEM with vs without routing proxy. Reports BOTH internal redistribution and terminal-edge balance (km², NOT Q); fail-closed unresolved/comparison-not-available mask if >12 basins, >12k candidate cells, or Core spill topology fails. No real lake occupancy inferred.
- [Operator review](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-6-core-lake-topology-vs-private-bc-2026-11-21.md) · [private checkout CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-lake-topology-compare.md). Synthetic Actions has three paths: unresolved many-basin region, forced unresolved, and 21x21 POSITIVE one-bowl exact Core-parity + PNG. Current SHA CI status must be read after docs update, not inferred.
- Original PRIVATE B/C real source tested in a **separate independent reconstruction of published P2-A/priority flood/MFD/spill algorithms, NOT an imported full PR #103 Core**. 1km candidate sizes: B 3 basins / 4185 cells, C 1 / 2135 cells at demo 16km²/10m; virtual fill maxima ~67.45m /55.18m. Candidate lake routing substantially changes INTERNAL contributing area (peak absolute ~19,256/32,124km²) but edge area remains fixed to ~1e-10km² numerical error. Earlier independent baseline obtained different counts; DO NOT treat these as author-canon or exact Core/regression. Private PNG and JSON are only in conversation, NOT GitHub.
- No original planet terrain changed. No macro A8 external water injected. Next **P2-B2.7** reproducible exact real B/C run in a checked-out PR #103 with source privacy, then basin-specific water occupancy/seasonality and onward P3 natural cover/P4 map/satellite-like art. PR #103 DRAFT/UNMERGED, PR #99–101 drafts separate, dev/0.2 and frozen release unchanged.


### Latest P2-B2.6 — actual Core lake components in synthetic CI / independent real B/C

Script scripts/diagnose_planetary_child_lake_topology_v02.py imports unchanged accepted Core PriorityFlood, lake candidates, continuous MFD, choose_lake_outlets, nested hierarchy. Uses fast P2-B2.2 Kahn graph for 231² with small-fixture parity to Core's full lake-supernode accumulation. Compares no-lake and with-geometric-lakes contributing area, flags large/many/unresolved basins, never interprets virtual fill as physical water. Operator report docs/reviews/p2-b2-6-core-lake-topology-vs-private-bc-2026-11-21.md, CLI docs/world-fixtures/planetary-child-lake-topology-compare.md. Original PRIVATE A8/A12 real B/C independent Core-formula reproduction (NOT imported same live source checkout) B 3 candidate basins 4185km², C 1 2135km², interior area redistribution maxima ~19,256/32,124km², edge sums unchanged numerically. These are not finished real-lake GIS. CI positive known-bowl + synthetic region unresolved. NEXT P2-B2.7 actual PR #103 checkout replay on same private source and then world-specific water balance and P3. Keep draft, do not merge, dev and release unchanged.


## 2026-11-21 — исправленная терминология и принцип достаточности

**Осве́ра** — рабочее, НЕ окончательно канонизированное название **планеты**. **Д’Акхар** — главный герой (ксенолог), НЕ регион и НЕ планета. Сохранённые исторические названия файлов `dakhar-first-arc` означают исходную арку *о герое*, а не географическое имя. Первая арка проходит в пока не зафиксированном по координатам регионе; модель A/B/C — кандидаты, НЕ авторское утверждение.

**Цель продукта:** авторская согласованность мест, природных препятствий, расстояний и маршрутов между арками, а НЕ научная диссертация о планете и НЕ обязательная карта для читателя. Дальнейшие гидрологические вычисления — только по реальному препятствию для художественной географии. Новый [прототип листа авторского атласа](docs/world-fixtures/osvera-author-region-atlas.md) и [реестр мест](examples/world-fixtures/osvera-first-arc-author-ledger.json) не размещают неизвестные объекты произвольно; промежуточная DEM и вся модельная география остаются неканоническими. [Публичный синтетический visual QA (6 tests GREEN)](https://github.com/MysterioCrypto/domain_generator/actions/runs/44886151409) НЕ является картой настоящей Осве́ры. Следующее P3-MVP — природный покров и первая цельная авторская карта с корректной легендой.

**Важно при продолжении:** не использовать словосочетания «планета Д’Акхара» или «регион Д’Акхар». Исторические имена скриптов/фикстур оставить без массового переименования (совместимость). Первую редакцию author sheet демонстрирует только SYNTHETIC CI; приватную реальную основу пока нужно собрать локально. Не рисовать лес без world-defined land-cover, не назначать координаты дома/переправы/города. Принцип «необходимой достаточности» автора приоритетнее бесконечных B2.x диагностика. PR #103 всё ещё draft, без merge.


### AUTHOR-PRODUCT PIVOT 2026-11-21 — IMPORTANT FOR NEXT CHAT

User correction: **Осве́ра** = tentative WORKING planet name, **Д’Акхар** = protagonist, NOT planet or region. Historical fixture path dakhar-first-arc is a legacy story-centered ID; don't bulk rename old filenames/PRs. Goal is author continuity of physical locations/distances/travel routes between arcs, not research dissertation or mandatory reader handout. User said *необходимая достаточность*. New files: scripts/render_author_region_atlas_v02.py, tests/test_author_region_atlas_v02.py, examples/world-fixtures/osvera-first-arc-author-ledger.json and docs/world-fixtures/osvera-author-region-atlas.md. First REAL PRIVATE A8/A12 author sheet for candidate region A run in chat using exact public scripts: 231², 1km, 63 exact macro DEM anchors, 5 story places UNPLACED, 2 unknown-distance routes; full 1.4MB private derived-region ZIP supplied to user as sandbox in conversation. Neither private original ZIPs nor real image uploaded to public GitHub. [Review](reviews/osvera-first-private-author-atlas-2026-11-21.md). Green SYNTHETIC atlas tests [Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/44886151409). Next P3-MVP is *visually useful* optional land-cover on real A using A12 scenario and world-defined class profile; do not infer literal forest from C3 or elevation; local MFD channel overlay remains candidate. Avoid more P2-B2.x unless genuine worldbuilding obstruction. PR #103 remains draft/unmerged and dev/release frozen.



## P3-MVP 2026-11-21 — source-conditioned noncanonical author natural cover

**Problem:** A visually useful author continuity map requires actual forest/open/rock/wetland candidate patterns; C3 vegetation potential and A12 source-biome code alone do not supply observed local cover. Endless lake-correction P2-B2 tests without a location conflict do not increase author usefulness. **Decision:** stop automatic hydrology deepening after P2-B2.6 for A, keep P2-B2.7 exact-Core private B/C validation as a targeted debt, implement ONE opt-in external visual land-cover source adapter in DRAFT PR #103.

**Code:** scripts/derive_author_natural_cover_v02.py with explicit editable examples/world-fixtures/osvera-working-cover-profile.json + tests/test_author_natural_cover_v02.py, integrated optional --cover-npz/--cover-manifest to scripts/render_author_region_atlas_v02.py. Source A12 latitude south-first, child north-first. Four source scenario votes blended spatially without source-grid rectangular nearest neighbor blocks; deterministic world-coordinate patch geometry; steep slope rock candidates, forest/open mosaic, WET LOWLAND only with original A12 wetland candidate AND locally lower terrain AND gentle slope. **Rejected:** directly treating broad A12 wetland_candidate mask as real swamp/water (early private candidate miscolored 65% of A as wet). Result is not canonical biome, measured forest, groundwater, permanent water or terrain mutation; no chosen landmark coordinates or travel times inferred.

**PRIVATE source real Osvera A:** independent cubic source-interpolated 231² region 230×230 km from original private A12, original source stations exactly reproduced numerically; candidate artist map ~71.9% woodland, ~16.2% open, ~11.9% potential lowland, zero forced rock. This private preview is NOT an exact current PR #103 P2-A/Core DEM replay, nor a claim of actual Osvera ecosystems; original source ZIP and derived map kept in ChatGPT, not public GitHub. [Review](reviews/p3-mvp-osvera-natural-cover-2026-11-21.md), [offline private runbook](world-fixtures/osvera-author-natural-cover.md). [Synthetic author-map CI](https://github.com/MysterioCrypto/domain_generator/actions/runs/44887608102) **16 focused tests GREEN**; check final SHA full pytest after docs.

**NEXT:** run P3 on EXACT source-conditioned child-A from this same PR #103 checkout using original private A12, inspect ONE author-facing complete cover map, not technical heatmaps. Then optional river topology/author landmark/route placement with explicit approvals and distance semantics; ImageGen only after geographic stabilization. **Planet working name Осве́ра, protagonist Д’Акхар** (not a toponym). PR #103 DRAFT/UNMERGED, dev/0.2 and frozen release untouched.
