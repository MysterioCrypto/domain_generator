# Project Progress Tree

Purpose: **current** DONE / IN PROGRESS / NEXT tree for chat recovery. For the dependency/context map and rejected hypotheses read `docs/CONTEXT.md`; for normative semantics read accepted `docs/design/*`.

**Active accepted Core:** `dev/0.2` (unchanged). **Current external product checkpoint:** PR #103, P4-R geometry-only candidate eliminates exact same-target crossings; native property integration pending; geography not accepted. Historical navigation checkpoint: [START_HERE](../START_HERE.md). **Parallel technical line:** H13 DESIGN accepted/merged #98, runtime #99 draft/unmerged; #100 C2 experiment and #101 atlas composer also draft/unmerged. **H12-A:** accepted/merged #97.
Historical checkpoint notes below are not current gates.

## Author correction — geographic design freedom (2026-11-25)

**Binding author clarification; supersedes any earlier project note treating draft source geography as immutable.** The only hard geographic canon constraint is consistency with the geography established in Chapter 1; Chapter 1 will not be rewritten to accommodate a new map. The general atmosphere/character of the planet must remain recognizable. The remaining geography is a draft, not fixed canon.

- A8/A12 source geography, macro relief and height anchors, land/coast masks, river/lake locations, catchments, outlets, terrain parameters, seed and grid spacing may be revised or regenerated if useful, subject to Chapter 1 compatibility and planetary atmosphere. No obligation to preserve a provisional raster graph, macro DEM, or prior outlet coordinates.
- Archived input/output versions remain reproducible controls, not mandatory inputs for later candidates. Equality, SHA checks, fixed anchors and graph preservation in P1–P4 are experiment-specific controls, not author requirements. A failed identity comparison alone is not grounds to reject a better map. Keep historical reports as historical evidence.
- Extract the actual hard geographic facts from the private Chapter 1 source before claiming narrative compatibility. The exact constraint inventory is not established by this clarification; do not invent additional canon or publish private story material in this repository.
- Prefer a usable, expressive, internally coherent regional map over numerical identity to a draft. Existing Core algorithms can be improved through the normal development process if needed; frozen software releases remain archival reproducibility points, not a ban on future development. No implicit merge or canon acceptance.
- Next P4-O: build a complete native Core network candidate, initially using P4-M 500 m terrain as a convenient comparison control, not a binding geography. Allow normalization and a new topology. If needed, revise/regenerate the terrain or source geography rather than force compatibility with the old sketch. Compare actual map quality and internal consistency; identify Chapter 1 constraints before approving a revised author map.

## CURRENT: P4-R same-target early confluence geometry (2026-11-28)

**CURRENT P4-R SAME-TARGET EARLY CONFLUENCE GEOMETRY (2026-11-28; PR #103 DRAFT):** P4-Q HEAD 3bbbcb0d all 3 CI GREEN, including full pytest (A08 compatibility restored). All 46/66 defective regional/potential pairs share same existing downstream confluence, 39/52 identical archived catchment descriptors; 34/55 affected groups. SHA-verified private P4-Q graphs. Joint same-target group first-contact planar merge hypothesis: prioritize archived catchment descriptor/length/stable ID, insert each donor to first exact intersection, split accepting edge, discard donor suffix, collapse unary nodes. Fail closed on cross-target crossings, positive-length overlap, invalid source contacts or remaining defects. Geometry-only candidate: 40/61 joins, 3/2 unary collapses, segments 842→879 / 2089→2148; removed 239.756/201.734km, lengths 6821.716/10808.119km. **46→0 / 66→0** exact defective pairs; point components 2547→0/2067→0; no degenerate/non-simple or positive-length overlaps; all 484/1222 source/lake-outlet first-terminal identities and non-confluence descriptors preserved, including 1/3 isolated boundary descriptors. Six local synthetic tests GREEN; two CLI runs byte-exact three JSON; CI integrated. No recomputed area/Strahler/masks, no inter-layer audit, no hydraulic/canon claim; not RiverNetwork/DomainData. Core unchanged. [Private archive](https://drive.google.com/file/d/1xgvQ1M4oYDXKFIjs6hi984vCJS3GmQBD/view), [review](reviews/p4-r-same-target-early-confluence-geometry-2026-11-28.md). **NEXT P4-S:** integrate bounded joining in explicit experimental assembly before deriving segment properties and masks, use trace-cell provenance/recomputed fields, never sum overlapping descriptors; check topology-dependent metadata, regional/potential consistency, lake semantics and native validation/compatibility. Then expressive terrain and complete map, Chapter 1 constraint extraction before geography approval. Draft geography freely revisable; no merge.

## PREVIOUS: P4-Q experimental lake outlet continuation (2026-11-28)

**PREVIOUS P4-Q EXPERIMENTAL LAKE OUTLET CONTINUATION (2026-11-28; PR #103 DRAFT):** P4-P full CI RED 831 passed/1 failed A08 baseline; geographic/atlas GREEN. Two inequivalent normalizers discovered: raw pre-serialization deletes zero-input confluence traces; public post-serialization promotes them to sources/preserves IDs. Restore legacy public default without changing A08 expected snapshot; P4-P/P4-Q improved assembly explicit internal `experimental_network_assembly=True` (not public DomainSpec). Local A08 default equals legacy-toggle result exactly within local environment; archived expected hash not reproduced locally in either path, remote CI required. Legacy A08 also contains same-lake return; migration separate. On SHA-verified P4-M 500m region, retry only same-lake outlet return from chosen receiver center, preserve shoreline endpoint and MFD/routing, fail closed on repeat; validate downstream feature graph including virtual lake links. Native experimental 19/19 checks, regional/potential segments 841→842 / 2088→2089, same-lake returns and zero-length segments 1→0 each, downstream chain 8/13 segments reaches domain edge. First regional segment 3.232km, source lake polygon intersection length 0 on this fixture. Exact spatial defective pairs remain 46/66, no positive-length overlaps. Three targeted tests GREEN, historical P4-P regression explicitly opts in; CI integrated. [Private archive](https://drive.google.com/file/d/18RSSlwCacUFzSrrLqVhAxwtJhpAwfe5I/view), [review](reviews/p4-q-lake-outlet-continuation-2026-11-28.md). **NEXT P4-R:** bounded semantic joining/crossing solution, distinguish genuine tributaries and near-coincident traces, no blind intersection splitting or smoothing; keep experimental mode until public policy/version migration. Then expressive regional geography, Chapter 1 constraint extraction before author acceptance. Draft geography revisable; no merge.

## PREVIOUS: P4-P native regional normalization and spatial audit (2026-11-25)

**PREVIOUS P4-P NATIVE REGIONAL NORMALIZATION AND SPATIAL AUDIT (2026-11-25; PR #103 DRAFT):** P4-O HEAD 21123fd0 all 3 CI GREEN. Author correction applies: draft geography freely revisable, Chapter 1 geography and planetary atmosphere binding. Regional generate_hydrology_v02 now invokes existing normalize_false_confluences=True, as potential assembly already does; experimental Core edit on feature branch only. Five local regression tests pass. Synthetic seed 3 legacy graph invalid→valid (13→12 segments), seed 0 valid graph, stream mask and water depth unchanged; routing/accumulation/skeletons/potential unchanged on both. SHA-verified private P4-M 500m DEM native corrected run exactly reproduces P4-O normalized regional and potential network JSON (841/2088 segments), passes 19/19 Core hydrology invariants without manual rebuild. Indexed exact Shapely intersegment audit: original regional 1528 intersecting nondegenerate pairs, 51 defective; normalized 1396/46; potential 3567/66. All defective pairs satisfy crosses predicate; zero positive-length overlaps; 2719/2547/2067 unauthorized point components respectively, NOT independent events. Each network contains one degenerate zero-length same-lake outlet→inflow segment, excluded from pair checks and separately reported. Core graph validation not spatial or lake-feature-level validity. No repairs to crossing or lake return yet, no near-overlap audit, no Chapter 1 compatibility claim. [Private evidence ZIP](https://drive.google.com/file/d/1B1sNWeiuQsRqeyc_1QRabp1tn0PNhLKN/view), [review](reviews/p4-p-native-regional-normalization-spatial-audit-2026-11-25.md). **NEXT P4-Q:** fix concrete same-lake outlet/inflow return, test legitimate downstream continuation and audit real candidate. Treat crossing/near-coincident traces via semantic joins separately if needed. Move toward expressive usable regional geography rather than preserving provisional map. No merge or canon acceptance.

## PREVIOUS: P4-O full native imported DEM hydrology (2026-11-25)

**PREVIOUS P4-O FULL NATIVE IMPORTED DEM HYDROLOGY (2026-11-25; PR #103 DRAFT):** Author correction: draft geography freely revisable; only Chapter 1 geography and planetary atmosphere binding. HEAD 947956ee all 3 CI GREEN. SHA-verified PRIVATE P4-M 461×461 500m DEM imported as TerrainState into actual compiled 0.2 hydrology plan; same 30 km² stream threshold, 16 km²/10m lake thresholds, 230.5km full-cell extent. Actual generate_hydrology_v02 yields native regional 966 nodes/936 segments, 94 false confluences, 18/19 invariants (only regional graph fails); potential 2147 nodes/2088 segments passes hierarchy invariant. Explicit experimental call to existing regional builder with normalize_false_confluences=True, rebuild stream mask/water depth, revalidate: **19/19**, 871 nodes/841 segments, 483 sources, 357 confluences, zero false confluences, 25 boundary outlets, 5 lake inflows/1 outflow, 7058.239km, 0 individually non-simple segments. One modeled lake 181.75km²/10.2036m max depth. Native curves visually substantially less angular; terrain still lacks expressive geography. Spatial intersegment intersection/overlap audit timed out and omitted (null, not zero). P4-M archive MFD float32 vs native float64 not exactly equal; reason not fully isolated. No full DomainData, physical water, Chapter 1 compliance or geography acceptance. No accepted Core code edits in this experiment. Four local tests pass, CI integrated. [Private archive](https://drive.google.com/file/d/1vIsm_2-toDzA1d3ZhXl150tHgSrQSL61/view), [review](reviews/p4-o-native-imported-dem-network-2026-11-25.md). **NEXT P4-P:** bounded native regional assembly regression + spatial overlap/crossing audit; evaluate enabling existing normalization in regional assembly with compatibility testing. No forced old graph identity. Then representative expressive map/terrain improvements, with private Chapter 1 facts extracted before author map acceptance.

## PREVIOUS: P4-N native Core continuous trace target audit (2026-11-25)

**PREVIOUS P4-N NATIVE CORE CONTINUOUS TRACE TARGET AUDIT (2026-11-25; PR #103 DRAFT):** P4-M HEAD 2be880de all 3 CI GREEN. PRIVATE original P4-M 500m candidate, SHA-verified macro/terrain/manifest/projection and exact replay of all projected fields. 11,402 ordinary edges partitioned into 934 semantic reaches; 4 proxy-contact reaches excluded (6 nonlocal proxy links not drawn; full recomputed candidate lake support 727 cells). Actual unchanged Core _trace_continuous from frozen source centers with ordinary confluence stop set; no snapping/normalization/assembly. 801/930 (86.13%) same target cell and kind, 123 wrong target cell, 5 wrong terminal kind, 1 lake inflow, 0 trace errors. Confluence matches 787/905, boundary 14/25 reach targets (not unique outlets); 787 exact end coordinates. Matched discrete Hausdorff median 0.286km/max 1.778km, 0 non-simple individual traces. Full-cell Core extent 230.5km vs outer node span 230km; actual boundary face not archived center. Flow-informed lines markedly less angular than P4-J/K, but 129 mismatches mean NOT a topology-preserving replacement; no assembled valid network or geography approved. Core intentionally normalizes unrealized confluences, so not necessarily a defect. 3 local tests pass, CI integrated. [Private derived ZIP](https://drive.google.com/file/d/14w3V_hEw64_jiUnetXhlyAbV33__Fzql/view), [review](reviews/p4-n-native-continuous-trace-target-audit-2026-11-25.md). **NEXT P4-O:** evaluate complete native Core network extraction/normalization on the same frozen 500m terrain as independent topology candidate, if existing contracts permit imported terrain; compare nodes, terminals, connected segments and lake semantics, render full candidate; no forced fit, silent acceptance, Core mutation or merge.

## PREVIOUS: P4-M nested resolution counterfactual (2026-11-25)

**PREVIOUS P4-M NESTED SAME-ANALYTIC-TERRAIN RESOLUTION COUNTERFACTUAL (2026-11-25; PR #103 DRAFT):** P4-L HEAD eff61976 all 3 CI GREEN. PRIVATE original P4B Region A, NOT rejected P4-L variant. Source macro/child/manifest/projection SHA via P4-L, exact original terrain and MFD projection replay. Only spacing 1→0.5 km, 231²→461², all six terrain/axis arrays bit-exact at common samples; 63 source anchors exact, same 230×230 km outer node span and 30 km² threshold. Existing full boundary-cell accounting area 53361→53130.25 km² (-0.4324%), mass ledger ~1e-10 km², external area 0. Same-heading **physical length** fraction in runs ≥8 km **18.436→10.145%** (~45% reduction), ≥16 km 2.429→1.456%, longest 29→28 km; ordinary length 6788.383→6595.080 km, edges 5868→11402. Outlets 25→22, 9 exact common; old→fine nearest median 0.5 km, max 22.677 km, 22/25 within 1 km; reverse max 3 km, 21/22 within 1 km. One new geometric lake supernode (3 traversed proxy cells), NOT confirmed water; nonlocal jumps not drawn. Finer grid improves metric but long straight lines remain, changed topology not accepted. One region/two grids do not prove convergence or isolate MFD from extraction/conditioning. 10 local tests pass, CI integrated. [Private derived ZIP](https://drive.google.com/file/d/13lIHSG1LHs22PjN-rkb3jkTE-MKfWFcX/view), [review](reviews/p4-m-nested-resolution-counterfactual-2026-11-25.md). **NEXT P4-N:** bounded comparison on same 500 m candidate using existing accepted Core continuous flow-informed subcell tracing contract versus one-receiver centerlines, if fixed semantic topology/outlets can be preserved; isolate lake-proxy geometry. No cosmetic invented meanders, Core change, automatic acceptance, or merge.

## PREVIOUS: P4-L slope-aligned detail counterfactual — rejected (2026-11-25)

**PREVIOUS P4-L SLOPE-ALIGNED DETAIL COUNTERFACTUAL — REJECTED AS TERRAIN GENERATOR (2026-11-25; PR #103 DRAFT):** P4-K HEAD 9be57779 all 3 CI GREEN. PRIVATE Region A original P4B 231×231/1 km/strength 2.0; original child and channel projection SHA via P4-K and bit-exact independent replay. Tested five-tap ±4 km along-parent-slope detail filtering with source-station detrending, 8 km boundary blend and matched land-detail RMS 7.492951m (gain 1.06937). 63 continuous source anchors exact (0 m error), raster boundary heights and detail bit-exact, land mask unchanged (region all land; not coastal validation), max height change 9.159m. At same 30 km² threshold under unchanged Core, strict raw pits **476→182**, nondescending raw edges **1076→737**, but edges in same-heading runs ≥8 (P4-H partition) **15.78→27.62%**, ordinary edges 5868→5992, outlets 25→27 (21 common), channel mask IoU 32.05%. Reduced directional roughness along slope 2.670→1.886m at equal detail RMS, but worsened regional straightness; reject this specific variant, not all anisotropic/erosion methods. No external A8 area injected; MFD ledger balances ~1e-10 km². Crop-dependent filter/taper not a globally seamless terrain generator. 8 local synthetic tests passed, CI integrated; [private derived ZIP](https://drive.google.com/file/d/1YlngHFHwaYiZnF9IRgBU_R6N5Bfl7A84/view), [review](reviews/p4-l-slope-aligned-detail-counterfactual-2026-11-25.md). **NEXT P4-M:** one controlled resolution counterfactual: same original analytic terrain and extent at 1 and 0.5 km, verify nested samples, fixed source anchors, unchanged Core and physical extraction threshold; compare straight chains by physical length, outlet shifts and same-scale appearance. No further blind noise sweeps, approved rivers, Core mutation or merge.

## PREVIOUS: P4-K semantic reach display and macro direction diagnostic (2026-11-24)

**PREVIOUS P4-K SEMANTIC REACH DISPLAY AND MACRO DIRECTION DIAGNOSTIC (2026-11-24; PR #103 DRAFT):** P4-J HEAD 607521f6 all 3 CI GREEN. PRIVATE region A original P4B 2.0/30 km² 231×231 source + P4-E background SHA verified via P4-J. 5,868 exact source edges partitioned into 927 reaches with 952 fixed source/confluence/terminal/boundary nodes; 4,941 other nodes need not be display vertices. RDP 0.35 km + two Chaikin passes, bidirectional 0.75 km corridor, land coverage, sampled nearest-original height difference guard 15m at ≤0.125km, no unsupported lake proxies, no new intersections. 581 reaches shifted >20m, max measured Hausdorff 0.708572km, sampled elevation difference max 1.873517m, 2 corridor/land fallbacks. Display length −3.0%, absolute internal turning −7.4%, unchanged source graph. Long same-heading runs ≥8 **within reaches**: 295/544 (54.2%) oriented within 22.5° of parent downhill vs 1897/5324 (35.6%) other edges; association only. More visible smoothing than P4-J, still synthetic regional pattern. Optional display-only result, not approved rivers/geography. 15 local tests pass; CI integrated, NumPy-only height sampling, PNG/NPZ exact vs initial run. [Private final v2 archive](https://drive.google.com/file/d/1HarTQ1wcjLzqVvoYonORlQnZGHIrQwxu/view), [review](reviews/p4-k-semantic-reach-display-corridor-review-2026-11-24.md). **NEXT P4-L:** stop cosmetic smoothing; controlled source/child terrain detail morphology hypothesis for valley coherence, anchored heights and coastline/boundaries, independent reroute under unchanged Core; no automatic acceptance or blanket old A8 D8 carving. Core dev/0.2 and frozen release untouched.

## PREVIOUS: P4-J immutable graph display geometry (2026-11-22)

**CURRENT P4-J DISPLAY-ONLY TOPOLOGY-PRESERVING CHANNEL CURVES (2026-11-22; PR #103 DRAFT):** PRIVATE Region A baseline **original P4B strength=2.0**, 231×231 at threshold 30 km². Source network verified via prior P4-I SHA. New script `scripts/generalize_region_model_channel_geometry_v02.py` and 18 full synthetic graph+SHA+deterministic-CLI tests. Geometric display only: 5,868 ordinary model edges, 5,893 original graph nodes with **every endpoint/node coordinate and source→receiver ID exactly unchanged**. G1 per-edge sampled Hermite display (9 points/edge), strict ≤0.20 km Hausdorff source-segment displacement; observed maximum **0.13916 km**, P95 **0.07742 km**, mean **0.03203 km**, 2,902 edges shifted >20m, 2,966 essentially unchanged. STRtree proves **0 original and 0 new independent segment crossings**, no graph reroute, lake proxy, Q, approved river or terrain edit. **CRITICAL NEGATIVE PRODUCT FINDING:** real full-region map looks almost identical; 1-km cell-node-preserving smoothing cannot cure long grid-aligned chains. Cropped 65×65km shows only modest bend reduction, so save code as optional display adapter NOT approved regional map; do not tune blindly. [Full-map side-by-side](https://drive.google.com/file/d/19Hkx6ZQ3YZ9fOs1nBbEjURqhL-MWKXDt/view), [zoom side-by-side](https://drive.google.com/file/d/1i63mXqB56je2TW8fMMKOBPyKtzlvhLUB/view), [derived vector NPZ/PNG/JSON SHA ZIP](https://drive.google.com/file/d/1TMOAs6wfzYfqqhN7M0y4Vfeq6nylGBo2/view), [full review](reviews/p4-j-region-a-display-only-topology-preserving-channel-curves-2026-11-22.md). **NEXT bounded P4-K:** evaluate actual product-readability blocker at semantic network-scale (headwater/confluence/terminal fixed), with optional larger-scale corridor-constrained display geometry, but do not alter accepted MFD or invent natural rivers; if long directional macro-landform remains, diagnose source morphology rather than cosmetically draw fake flow. PR #103 Draft, accepted Core dev/0.2 and frozen release unchanged.

## PREVIOUS: P4-I source-anchored interpolation counterfactual, PRIVATE region A (2026-11-22)

**CURRENT P4-I SOURCE-ANCHORED INTERPOLATION COUNTERFACTUAL (2026-11-22; PR #103 DRAFT/UNMERGED):** PRIVATE Region A 231×231, unchanged original macro A8 heights, coastline, coordinate grid, planet projection and each P4-E frozen child local detail; compare original C1 Hermite parent vs bilinear parent with **all 63 source height stations exact (0 m error)**. Parent height bilinear−Hermite ∆ ranges **−49.00 to +52.68 m**, RMS **9.335 m**. All three original P4-F model projections replay **BIT EXACT**, source SHA verified through P4-H; 0 km² external A8 area injected and MFD conservation verified. Independent bilinear re-routing produces different boundary outlet sets: strength 0.5 **22→20**, 1.25 **20→17**, 2.0 **25→22**; channel mask IoU Hermite/bilinear **43.37%/60.10%/65.71%**; straight single-heading runs ≥8 edges: **47.67→51.78% / 17.95→18.86% / 15.78→14.80%**. Parent-only control: 98.49→99.06%, 7→2 model outlets, and is NOT viable terrain. **CONCLUSION:** bilinear does NOT solve grid-aligned river skeleton, and would silently change model outlets. Preserve existing Hermite; do not select DEM/approve river or physically infer discharge. Added scripts/compare_region_parent_interpolants_v02.py (full SHA source and derived NPZ replay), **15 toy tests**, optional synthetic CI. [2×3 comparison](https://drive.google.com/file/d/1V46y7uZIhz35XcO75aSdubdlm78riVq1/view), [Δ-parent heatmap](https://drive.google.com/file/d/1JOGnRG1J94IskN29mCDXBk7lzF0LaAkk/view), [PRIVATE derived ZIP, 4 NPZ+JSON+CSV](https://drive.google.com/file/d/1Fa8OiUgD_yJaK3NZ7hXWJiSxxuLZMp16/view), [full review](reviews/p4-i-region-a-parent-interpolator-counterfactual-2026-11-22.md). **NEXT P4-J:** display-only topology-preserving vector/channel geometry generalization; assert node IDs/outlets/edges unchanged, bounded displacement and non-crossing, compare genuinely more readable author map. Accepted Core dev/0.2 and frozen release untouched.

## PREVIOUS: P4-H directional-bias attribution using parent-only negative control, PRIVATE region A (2026-11-22)

**CURRENT P4-H PARENT-ONLY DIRECTIONAL NEGATIVE CONTROL (2026-11-22; PR #103 DRAFT/UNMERGED):** Recovered SHA-verified real PRIVATE P4-B/E/F/G 231×231 1-km source; unchanged accepted Core priority flood/MFD + dominant channel projection at threshold 30 km² independently rerun for parent-only interpolated height (**strength 0**) and 3 P4-E DEM strengths 0.5/1.25/2.0. All archived P4-F raster fields for 3 real DEMs reproduced **BIT EXACT**, 63 P4-E parent anchors unchanged, 0 km² external A8 catchment injected. Uniquely partitioned model edges into maximal same-heading 8-neighbor runs ≥8 cells: parent-only **98.49%** (35,728 ordinary edges; max 203 steps); strength 0.5 **47.67%** (9,095; max 42); strength 1.25 **17.95%** (6,374; max 24); strength 2.0 **15.78%** (5,868; max 29). Parent-only vastly overtraces 35,735 model channel cells: **NEGATIVE CONTROL not candidate rivers/terrain**. On identical fixed original-2.0 channel cells, continuous RAW downhill nearest 45° ±7.5° fraction 41.5% parent vs 36.4/31.9/31.0% for added detail, while continuous Core MFD fractions 43.7%/41.3%/39.8%/47.3%; mean model 1-receiver vs continuous MFD turn 10.6/12.4/11.9/10.9°. Direction *consistency over space* rather than exact diagonal fraction separates long straight-branch artifact. **CAUSE:** broad macro+interpolated parent terrain already supports strong straight chains, local detail interrupts them; discrete 8-neighbor projection quantizes all physical drawn edges. **UNRESOLVED:** distinguish intrinsic macro A8 source from interpolation algorithm itself with identical anchors. Added scripts/diagnose_region_directional_bias_v02.py, 19 toy+CLI guards and conditional synthetic CI. [4-panel region comparison](https://drive.google.com/file/d/1rmqJYcFyWysT42y9UPoyRfFGQdAO4iRO/view), [run-length chart](https://drive.google.com/file/d/1rLXr28VxInG-xLSoEGV7bQR5G7gFOnp6/view), [PRIVATE derived ZIP/CSV/JSON/SHA](https://drive.google.com/file/d/1fklqctRGDxl46P_OZDJzbH-66cP9LT1K/view), [full review](reviews/p4-h-parent-only-negative-control-directional-bias-2026-11-22.md). **NEXT bounded P4-I:** isolate macro A8 vs interpolation with an alternate anchored interpolant and/or model-preserving cartographic trace that does not alter nodes/outlets; no auto-accepted natural rivers/map, POIs or merged Core. PR #103 DRAFT, accepted dev/0.2 frozen untouched.

## PREVIOUS: P4-G channel source threshold map morphology, PRIVATE region A (2026-11-21)

**CURRENT P4-G MODEL CHANNEL MAP THRESHOLD SENSITIVITY (2026-11-21, PR #103 DRAFT/UNMERGED):** Real private Region A, 3 fixed anchor-preserving P4-E terrains strength 0.5/1.25/2.0 × channel source thresholds 15/30/60 km². Nine independent calls to existing Core-compatible MFD projection, **all 3 threshold=30 outputs BIT-EXACT P4-F**, input SHA-256 validated, 63 P4-E parent anchors preserved; 0 km² A8 area injected and all mass ledgers conservative. Channel cells across thresholds: 0.5 **15083/9117/6004**, 1.25 **9354/6394/4538**, 2.0 **8513/5893/4248**; confluence counts 0.5 **1123/528/239**, 1.25 **968/449/211**, 2.0 **927/442/218**. Important: threshold change affects dominant receiver preference, model channel masks ARE NOT nested: at 60 vs 30, 0.5 has **466 NEW mask cells**, 1.25 **131**, 2.0 **101**. Visual defect remains: 0.5 produces conspicuously parallel diagonal/horizontal branches; 1.25 and 2.0 retain stepped grid look. Varying extraction threshold alone does NOT yield author-ready regional geography. New scripts/compare_region_channel_scale_v02.py, 18 toy tests, workflow geogrid 3×3 CI. [3 variant map](https://drive.google.com/file/d/1yV5X_xHlUuSc9sEVp-JEocMCSu3iH08P/view), [9 threshold maps](https://drive.google.com/file/d/1En27QXP-ELeIC4VElqgoBgfJ07wGZ8yf/view), [derived audit ZIP + CSV/JSON](https://drive.google.com/file/d/1EHR2vxFQTYv2Hh2QooObips-lVP6iwwD/view), [full P4-G review](reviews/p4-g-region-a-three-threshold-channel-map-sensitivity-2026-11-21.md). Still NO rivers, Q, canonical map/settlements, imported A8 area, accepted Core changes. **NEXT P4-H:** diagnose where model directional/grid bias originates (parent terrain vs child interpolation/relief vs dominant-receiver topology) and test topology-preserving map generalization; avoid blind threshold tuning. Accepted dev/0.2/frozen release untouched.

## PREVIOUS: P4-F independent three-MFD variant terminal topology, PRIVATE region A (2026-11-21)

**CURRENT P4-F REAL independent Core-MFD topology for three P4-E DEMs (2026-11-21; PR #103 DRAFT/UNMERGED):** Source-hash-verified P4-B/P4-C1/P4-E private data; re-ran unchanged accepted Core priority flood + Freeman MFD + P2-B2.4 dominant channel projection separately for 0.5/1.25/2.0 relief strengths, preserving 63 parent anchors and full 231×231 child grid. Old strength 2.0 **BIT-EXACT** vs archived P2-B2.4 fields AND exact JSON report. Real candidate channel terminal counts **22/20/25**; model channel cells **9,117/6,394/5,893**. IoU channel mask vs 2.0 **18.47%/40.44%/100%**; all-cell dominant MODEL root same exact boundary pixel **52.72%/85.96%/100%**; same boundary side **94.88%/95.67%/100%**. Historic P4-C1 selected east-near reference cell [220,224] now terminates WEST [177,0] at strength 0.5 (32 km N shift), WEST [209,0] for 1.25 and 2.0. Fractional MFD transported *local* area exactly conserves 53,361 km² (float64 ledger ~1e-10 km² residual); **0 km²** A8 external-only area auto-injected; not Q, not water, no new physical basin identity. Dominant 1-receiver model root comparison ≠ fractional MFD catchment. New scripts/compare_region_mfd_variant_basins_v02.py, **24 synthetic tests**, SHA guards incl direct synthetic/wrapped private C1, geogrid synthetic end-to-end. [Private 3-column map](https://drive.google.com/file/d/1FDp5FX1Rg_n5VsbCzfVe1Wmxx_SFbI9T/view), [final v2 derived ZIP+NPZ reports and SHA](https://drive.google.com/file/d/1nRuXLKjx6sKxHnuBqOXuQGCbLg_m-XLy/view), [full rationale](reviews/p4-f-region-a-independent-mfd-variant-topology-2026-11-21.md). **NEXT bounded P4-G:** visibility/morphology of newly recomputed skeletons and source/threshold sensitivity, author-visible region-map quality. No terrain choice accepted, no POI placed, no approved river created. Accepted dev/0.2/frozen release untouched.

## PREVIOUS: P4-E three source-anchored relief-strength variants, PRIVATE region A (2026-11-21)

**CURRENT P4-E THREE ANCHOR-PRESERVING 1km CHILD RELIEF VARIANTS (2026-11-21, PR #103 DRAFT/UNMERGED):** Re-generated real PRIVATE A8-conditioned region-A 231x231 DEM using unchanged spherical_xyz_v1, seed 1406, parent interpolation and 63 continuous source height stations. **Original strength 2.0 regenerated BIT EXACT** against archived child NPZ. Two noncanonical alternatives strength **1.25** and **0.5** preserve all **63 original source anchors at 0m maximum error**, same parent baseline and land mask. On the **FIXED OLD P4-D 253-edge reference graph only**, raw-non-downhill counts: baseline 2.0 **58**, 1.25 **32**, 0.5 **15**. At 0.5, 50 original blockers become downhill but 7 previously downhill edges become non-downhill; interior DEM raw local minima **476→307→35** across strengths 2.0→1.25→0.5 (mathematical pits, NEVER lakes). Fine residual std **7.478→4.674→1.869m**. New `scripts/compare_region_relief_strength_v02.py` + 18 toy regression tests + geogrid synthetic CI; exact P4-D/P4-A source SHA provenance checked. Top row comparison uses FROZEN baseline P3 cover coloration (NOT recalculated ecosystem); bottom row fixed ±35m parent residual tint. **No alternative MFD routing / real watershed continuity / external catchment Q computed and NO Core or authored POIs changed.** [Drive comparison sheet](https://drive.google.com/file/d/1FGOm44nzbvTwSA5SyKMum6Mtyb9O5fux/view), [private ZIP with 0.5 and 1.25 derived NPZ, 3 maps and audit](https://drive.google.com/file/d/1NlJgASNvupeQ3E4Ykcr0k8gSRylGLQtg/view), [full review](reviews/p4-e-region-a-three-source-anchored-relief-variants-2026-11-21.md). **NEXT bounded P4-F:** recompute isolated candidate MFD graphs for both new DEMs and test changes to terminal/catchment identity/river morphology before any map acceptance; no premature overlay of old 253-edge graph as new river. Accepted dev/0.2 and frozen release untouched; PR #103 DRAFT/UNMERGED.

## PREVIOUS: P4-D real parent stations vs fine relief gradient reversal (2026-11-21)

Source-hashed, read-only new `scripts/audit_region_anchor_alternative_drains_v02.py`, 17 dedicated toy tests, geogrid synthetic CLI. Real region A, 253 candidate model edges and 63 original continuous parent height stations: 58 raw DEM uphill/flat; **56** have descending parent interpolated gradient reversed by effective fine residual; **2** already lack parent descent. **46** bad sources have >=1 immediate raw-downhill neighbor but **12** have none. All **58/58** greedy raw-steepest negative-control walks end at local DEM minima, **0** reach crop boundary: not lakes, not physical flow or new D8 routing. Median nearest parent-station distance 13.923 km for bad edges vs 12.585 km for 181 strict, no apparent concentration at anchors; bad links form 31 consecutive groups, longest 5. Input P4-C2 CSV independently recomputed from hash-verified P4-B child, macro, child metadata, P4-A PNG. **No parent/micro DEM, Core MFD, old A8 area, rivers, settlement POI or canonical geography changed.** Source supports `spherical_xyz_v1` and `legacy_lat_scaled_easting_v1` at the common parent anchor chart (actual real data uses sphere). [Private map](https://drive.google.com/file/d/173WacgMXJyC99yWBTANNCRS9lgxvsehG/view), [final v2 ZIP with CSV and SHA](https://drive.google.com/file/d/1d-5K2MFumj1aSQCcINSAUatDafp-UQsM/view), [full review](reviews/p4-d-region-a-parent-anchor-and-alternative-descent-2026-11-21.md). On code HEAD b4430503 geography+atlas CI GREEN, full pytest running at report preparation. **NEXT P4-E:** opt-in *noncanonical* controlled alternative fine relief recipes preserving 63 source stations, compare visually and quantitatively against P4-D; no direct carve/injected river.

## PREVIOUS: P4-C2 raw-DEM slope vs virtual-fill sensitivity on real region A (2026-11-21)

Read-only `scripts/audit_region_corridor_sensitivity_v02.py`, 17 synthetic local unit tests and synthetic geogrid end-to-end proof. Exact P4-C1 SHA-256 lineage and independently recomputed P4-C1 route, baseline partition matched to P4-B original. On private P4-B derived Osvera A 253-edge P4-C1 route: **181 strict**, **49 raw uphill/flat only**, **14 virtual-fill >2m only**, **9 both**. Thus 58 original-DEM-uphill links cannot become raw-downhill by simply relaxing fill threshold. Threshold (metres) 0/1/2/3/5/10 gives strict-edge counts 128/161/181/185/189/195; maximum consecutive strict chain 28/29/30/31/32/33 edges. **No river length or water occupancy inferred**; external-only inflow remains unknown and **0 km²** imported from old A8 D8 cumulative area. P4-A/B/C1/accepted Core untouched, 5 POI and 2 story paths still UNPLACED. [Detailed review](reviews/p4-c2-region-a-corridor-fill-sensitivity-2026-11-21.md), [private map](https://drive.google.com/file/d/1jfdGEdJzNptZXPn24WdZaCXQlqrnwHg1/view), [ZIP with per-edge CSV, scenario audit and SHA](https://drive.google.com/file/d/1Ba9eisALnpJxxkwwXhfm82N63jnqGuc-/view). New P4-C2 synthetic CI on functional code commit 63fc6e0d: geography and author-map green; full pytest status should be verified on current HEAD before quoting count. PR #103 stays DRAFT/UNMERGED, dev/0.2 unchanged.

**NEXT P4-D bounded diagnostic:** find *why* 58 raw-gradient failures cluster near anchored terrain and whether alternative local drainage basins exist. No automatically lowered DEM, imposed river, lake water or inherited A8 area.

## PREVIOUS: P4-C1 PRIVATE macro-inlet ↔ child dominant channel geometry (2026-11-21)

On private region A from prior P4-B SHA-verified derived ZIP (NOT fresh original A8/A12 execution), historical A8 has ONE EAST inbound D8 hint and ONE WEST old exit. 20 strictly inward P4-B channel edges within 30 km of the input all lead to ONE child MFD terminal [209,0] on WEST; selected nearest at [220,224] is 7.864 km from old crossing; terminal 2.028 km from old WEST macro exit. Candidate projected path 253 edges = **181 strict downhill +72 withheld uncertain**, 0 proxy lake jumps under current threshold. Geometry is promising but NOT physical basin equality, real river, discharge or full continuous raw-DEM channel; no A8 source catchment automatically injected (0 km²; historic inlet/outlet area hints NOT external-only). P4-C1 code script/reconcile_region_boundary_corridors_v02.py, 14 synthetic tests + end-to-end synthetic CLI, input SHA exact P4-B lineage, A8 stored exit rechecked. Last functional code head e34e783b full pytest **641 passed**, geogrid/P4-C1 and author atlas workflows GREEN. Private [map](https://drive.google.com/file/d/1n8MMN4eGzR0LtPvgmB-l7-9rr3_9Xx_R/view), [ZIP](https://drive.google.com/file/d/1tBviEHXytjBTCgyGQ2S35lwQBPK4nyWf/view), [review](reviews/p4-c1-region-a-macro-inlet-to-child-mfd-route-evidence-2026-11-21.md). PR #103 DRAFT/UNMERGED, accepted Core/dev/0.2 unchanged.

**NEXT P4-C2:** evidence-based external area / uncertain 72-link / lake-spill sensitivity, no invented river, no premature geo canon.

## PREVIOUS: P4-B conservative real child Core-MFD candidate drainage evidence (2026-11-21)

Added `scripts/render_region_drainage_evidence_v02.py`: nonmutating overlay of EXISTING P2-B2.4 dominant Core MFD channel graph onto P4-A, with strict checks against current Core positive MFD fractions, adjacent receivers, original raw DEM downhill, virtual Priority Flood fill, and hidden lake proxy jumps. Zero lake jumps does **NOT** mean no lakes: input status NO_LAKES_QUALIFIED under the chosen candidate threshold. The display-only `--min-display-dominant-area-km2` setting suppresses noisy small tributaries but preserves ALL validated channel edges in NPZ. P4-A/child input SHA-256 cross-check refuses wrong map; projection child exact archive lineage remains unproven (reanalyzed Core fractions guard).

REAL ORIGINAL A8/A12 (same verified hashes) region A, selected sphere child 231×231, **63 parent height anchors / max 0m error**: 5868 Core candidate ordinary edges, 4517 raw-downhill/low-fill strict geometry, 1351 withheld, 1374 virtual-fill cells >2m, 9.813m max virtual fill (NOT lake depth). At explicit preview area threshold 100km² **NOT discharge**: 2515 edges visible, 2002 strict eligible minor edges hidden ONLY FROM IMAGE. Equations: 5868=4517+1351=2515+2002+1351. No external upstream area injected, no verified perennial rivers, water balance, lake occupancy, road/POI/route geometry. Private [PNG](https://drive.google.com/file/d/1FHsVVlPY4UVa6dZK-41NERLnd6g0E5Fn/view), [derived ZIP+NPZ+audit](https://drive.google.com/file/d/1G6hxsqMNBIk_ZovBZ4nrepf7fLOxrHtX/view); [P4-B report](reviews/p4-b-region-a-drainage-evidence-2026-11-21.md).

On last functional code HEAD (8427f391), **627 pytest passed** and [geogrid/P4-B synthetic CI](https://github.com/MysterioCrypto/domain_generator/actions/runs/44911808269) plus author-atlas CI GREEN. The operator approved continued work after P4-A; do not infer canonical geography or present map accepted. **NEXT P4-C**: reconcile *external* macro catchment entry, outlets and unresolved basin / lake-geometry topology before water blue-lines or ImageGen. PR #103 DRAFT/UNMERGED, Core/freeze unchanged.

## PREVIOUS: P4-A real region-A map-first cartographic output (2026-11-21)

New independent scripts/render_region_cartographic_base_v02.py combines **existing** P2-A sphere DEM and P3 source-conditioned cover WITHOUT mutating numeric fields or inventing rivers/roads/POI. Outputs clean PNG, mapped sheet (north up, correct 50-km scalebar, color legend separated from bar, 50-m DEM isolines) and input-hashed JSON audit. Real ORIGINAL private A8/A12 SHA verified, exact GH P1/P2/P3/P4 module blobs verified; 230×230 km, 231×231, 63 preserved original heights, zero anchor error. Hypothetical woodland/open/wet counts 35572/9218/8571, consistent with P3.5. **Still not an accepted usable complete regional map.** Image only is cartographic visualization; no reliable 1-km river topology, lakes, roads, settlements, five POI or two route geometries. Synthetic all-test CI on last P4 code commit **612 passed**, geogrid and author-map CI GREEN. Private map outputs: [sheet](https://drive.google.com/file/d/1mZUlYpafZyF3wDWXKyANfgvcCGkOuSYH/view), [clean base](https://drive.google.com/file/d/1NfnBSXDdCXnHMb_X6xZFnCT7dkq-zjFO/view), detailed [review](reviews/p4-a-region-a-map-first-renderer-2026-11-21.md). Next bounded feature candidate **P4-B: properly evidenced local drainage connectivity**, not arbitrary blue river drawing or another palette tweak. PR #103 DRAFT/UNMERGED, Core unchanged.

## PREVIOUS: P3.6 bounded author acceptance, P4-A requested (2026-11-21)

**Decision received:** RIGHT spherical_xyz_v1 is formally SELECTED as the working model for Osvera region A, no further choice/approval ceremony required on that narrow point. **Explicit negative product feedback:** NEITHER atlas resembles the expected regional map. Therefore not accepted: P3.5 map presentation, canonical terrain, forests/wetlands, water/roads, POI positions, routes, or merge PR #103. Legacy remains universal CLI default for deterministic compatibility, while Osvera P4-A uses explicit spherical setting. Green tests prove software paths, not a map that serves the author.

**NEXT single feature:** P4-A readable 230×230-km overhead cartographic base from already calculated DEM and candidate natural cover, with separate technical diagnostics; do not invent rivers, lakes, roads or landmarks. ImageGen can be separately evaluated for styling only after geometry control. [Decision/evidence](reviews/p3-6-operator-selection-and-map-product-gap-2026-11-21.md). PR #103 DRAFT/UNMERGED; no changes to Core accepted dev/0.2 or freeze.

### Historical P3 checkpoints (no longer current approval gates)

## CURRENT: P3.5 full legacy-vs-spherical real A8/A12 region-A atlases (2026-11-21)

The full original-source P1→P2-A→P3→author-atlas **function** chain was executed twice with EXACT SHA-verified GitHub modules (HEAD initially 8248e97f) and identical private inputs/ledger/profile; code not modified. Legacy candidate fractions (woodland/open/wet) 64.058/16.731/19.211%; spherical 66.663/17.275/16.062%; 13,510 of 53,361 cover pixels changed. Parent interpolation identical, 63 parent DEM nodes pinned with 0.0m maximum error, same land mask; spherical changes terrain RMSE 11.927m. The oblique small ridges largely disappear, but macro bands remain. **No operator visual decision, no real 1km hydrology, no named-site placement.** Source archives and derived rasters remain private, only comparison PNG [in Drive](https://drive.google.com/file/d/12T79Z9GcKD41LyDGOaKli-WJlNK3emNQ/view); audit and full details [P3.5 review](reviews/p3-5-region-a-full-private-spherical-vs-legacy-2026-11-21.md). Unlike P3.4 probe, both *full* atlases were rendered; private `build_author_atlas_v02.py` CLI wrapper itself still not invoked, only its exact functions. PR #103 remains DRAFT/UNMERGED; next gate is user author comparison/selection before tuning anything else.

## CURRENT: P3.4 spherical child-detail alternative (2026-11-21)

A real P3.3 bundle separated source-interpolated DEM from procedural local detail. Original A8 macro P1 is a mostly smooth broad ramp; *procedural P2-A detail* exhibits unnatural repeated oblique streaks because legacy easting = R·lon_rad·cos(lat) shears value noise with absolute longitude (local meridional coupling about −1.26 near region A). New `spherical_xyz_v1` opt-in 3D anchored noise, exposed in the P2 CLI and P3 one-command atlas. **Legacy remains default and P3.3 remains exactly replayable; no Core or author canon change.** Private diagnostic (not new full P3 cover map): 1-km centered gradient anisotropy 0.869 legacy vs 0.022 spherical; 8-km 0.522 vs 0.120. Compare screenshots at [private Drive](https://drive.google.com/file/d/1RBUPKmqR5ICBX-pZ6KjNQRvf6_3qMGCc/view). Rationale and measurements in [P3.4 review](reviews/p3-4-region-a-spherical-detail-projection-2026-11-21.md). Synthetic replay, source anchors, dateline continuity and full-chain option tests added; final CI must be checked on actual HEAD. Next: author selection, then rebuild private source→child→cover→atlas with that selection, no river invention. PR #103 DRAFT/UNMERGED.

## CURRENT: P3.3 first REAL private region-A author sheet (2026-11-21)

Original user Drive A8/A12 ZIP hashes verified, P1 whole-source equality passed (600×1200), source crop 9×11, P2-A child 231×231 at 1 km with 63 preserved anchors and 0.0 m maximum anchor error. P3 hypothetical forest/open/wet-lowland fractions 0.64058/0.16731/0.19211. Atlas rendered using EXACT code-blob P1/P2/P3/atlas functions; full new CLI wrapper itself NOT run on private ZIPs. First real sheet exposed overlap of model legend with status footer, fixed in PR #103 and regression-test added. Private PNG/bundle stored in access-controlled Drive; full run details and exact links in docs/reviews/p3-3-osvera-region-a-private-source-atlas-2026-11-21.md.

**STATUS:** operator visual review pending; five POI unplaced, two routes unknown, no 1-km accepted Core MFD rivers. PR #103 DRAFT/UNMERGED, Core dev/0.2 and frozen releases unchanged. NEXT: author evaluates ONE map; tune guilty layer or targeted hydrology only with evidence.

## CURRENT: P3.2 direct private archive intake (2026-11-21)

Draft PR #103 now also accepts ORIGINAL A8/A12 ZIPs directly in the SAME source-verified P2-A -> P3 -> author atlas CLI. It reuses P1 whole-world checks, enlarges the SOURCE CROP (not the author map) by one source station for valid interpolation, and records original input hashes and derived region provenance. Former NPZ mode remains supported. New synthetic archive-to-map + mismatch/digest regression checks. Next product gate is still real private region-A build, one reviewable PNG and audit; no merge/canon assumed.

## CURRENT (working PR #103, 2026-11-21)

Source-verified exact-checkout P2-A -> P3 natural cover -> author atlas builder added, together with synthetic regression tests and full-chain CI. Core dev/0.2 and frozen release unchanged. **No exact PRIVATE Osvera run or user visual acceptance yet.** Next: run builder on private A/A12 in a temporary checkout, inspect build-audit.json and one complete map. P2-B2.7 remains targeted hydrology debt only if it blocks real geographic continuity. PR #103 stays DRAFT / UNMERGED.

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


## 2026-11-21 — исправленная терминология и принцип достаточности

**Осве́ра** — рабочее, НЕ окончательно канонизированное название **планеты**. **Д’Акхар** — главный герой (ксенолог), НЕ регион и НЕ планета. Сохранённые исторические названия файлов `dakhar-first-arc` означают исходную арку *о герое*, а не географическое имя. Первая арка проходит в пока не зафиксированном по координатам регионе; модель A/B/C — кандидаты, НЕ авторское утверждение.

**Цель продукта:** авторская согласованность мест, природных препятствий, расстояний и маршрутов между арками, а НЕ научная диссертация о планете и НЕ обязательная карта для читателя. Дальнейшие гидрологические вычисления — только по реальному препятствию для художественной географии. Новый [прототип листа авторского атласа](docs/world-fixtures/osvera-author-region-atlas.md) и [реестр мест](examples/world-fixtures/osvera-first-arc-author-ledger.json) не размещают неизвестные объекты произвольно; промежуточная DEM и вся модельная география остаются неканоническими. [Публичный синтетический visual QA (6 tests GREEN)](https://github.com/MysterioCrypto/domain_generator/actions/runs/44886151409) НЕ является картой настоящей Осве́ры. Следующее P3-MVP — природный покров и первая цельная авторская карта с корректной легендой.

**Готово:** внешний скрипт scripts/render_author_region_atlas_v02.py, шесть новых тестов, JSON реестра и CI; ещё НЕ выполнен запуск этого инструмента на приватной A8/A12 DEM с Core MFD. P2-B2.7 точный пересчёт реального B/C остаётся открытым, но не обязан блокировать авторский атлас A при отсутствии выявленной сюжетной проблемы.


### Product checkpoint: PRIVATE real Osvera A author map, 2026-11-21

Full archived original A8/A12 privately mounted, SHA-256 verified and processed using EXACT external #103 Python scripts for macro crop and child terrain, 230×230km 1km grid 231², 63 source DEM elevation anchors with max error exactly 0.0m; elevation ~232.85–834.25m. The author ledger (Osvera working planet, D’Akhar protagonist) generates one coherent map, preserves five WRITTEN/BRIEF landmarks UNPLACED, and does not invent two route lengths. Real private image, compact 1.4MB model workspace ZIP and numeric audit were delivered **in the conversation only**, not public GitHub. [Product review](reviews/osvera-first-private-author-atlas-2026-11-21.md) and [how-to](world-fixtures/osvera-author-region-atlas.md). New 6 targeted tests GREEN on synthetic [Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/44886151409) before aesthetic styling update; check final full CI at final head. NEXT P3-MVP: noncanonical world-defined vegetation/open/rock/wetland visual modeling from A12 eco-climate source and CHILD slope with clear uncertainty, connect MFD before any authored route placement. P2-B2.7 exact real B/C lake Core parity remains outstanding, not universally blocking.



## P3-MVP 2026-11-21 — source-conditioned noncanonical author natural cover

**Problem:** A visually useful author continuity map requires actual forest/open/rock/wetland candidate patterns; C3 vegetation potential and A12 source-biome code alone do not supply observed local cover. Endless lake-correction P2-B2 tests without a location conflict do not increase author usefulness. **Decision:** stop automatic hydrology deepening after P2-B2.6 for A, keep P2-B2.7 exact-Core private B/C validation as a targeted debt, implement ONE opt-in external visual land-cover source adapter in DRAFT PR #103.

**Code:** scripts/derive_author_natural_cover_v02.py with explicit editable examples/world-fixtures/osvera-working-cover-profile.json + tests/test_author_natural_cover_v02.py, integrated optional --cover-npz/--cover-manifest to scripts/render_author_region_atlas_v02.py. Source A12 latitude south-first, child north-first. Four source scenario votes blended spatially without source-grid rectangular nearest neighbor blocks; deterministic world-coordinate patch geometry; steep slope rock candidates, forest/open mosaic, WET LOWLAND only with original A12 wetland candidate AND locally lower terrain AND gentle slope. **Rejected:** directly treating broad A12 wetland_candidate mask as real swamp/water (early private candidate miscolored 65% of A as wet). Result is not canonical biome, measured forest, groundwater, permanent water or terrain mutation; no chosen landmark coordinates or travel times inferred.

**PRIVATE source real Osvera A:** independent cubic source-interpolated 231² region 230×230 km from original private A12, original source stations exactly reproduced numerically; candidate artist map ~71.9% woodland, ~16.2% open, ~11.9% potential lowland, zero forced rock. This private preview is NOT an exact current PR #103 P2-A/Core DEM replay, nor a claim of actual Osvera ecosystems; original source ZIP and derived map kept in ChatGPT, not public GitHub. [Review](reviews/p3-mvp-osvera-natural-cover-2026-11-21.md), [offline private runbook](world-fixtures/osvera-author-natural-cover.md). [Synthetic author-map CI](https://github.com/MysterioCrypto/domain_generator/actions/runs/44887608102) **16 focused tests GREEN**; check final SHA full pytest after docs.

**NEXT:** run P3 on EXACT source-conditioned child-A from this same PR #103 checkout using original private A12, inspect ONE author-facing complete cover map, not technical heatmaps. Then optional river topology/author landmark/route placement with explicit approvals and distance semantics; ImageGen only after geographic stabilization. **Planet working name Осве́ра, protagonist Д’Акхар** (not a toponym). PR #103 DRAFT/UNMERGED, dev/0.2 and frozen release untouched.


### Current product gate P3-MVP — FIRST candidate natural-cover author map (DRAFT #103)

Implemented editable noncanonical A12-like scenario-to-woodland/open/rock/wet-lowland source adapter + optional author-atlas overlay + tests + synthetic visual CI. Real PRIVATE A source-independent candidate image completed in current chat; caveat: reconstructed DEM not exact GH P2-A. [Review](reviews/p3-mvp-osvera-natural-cover-2026-11-21.md), [private CLI](world-fixtures/osvera-author-natural-cover.md). Explicit local depression evidence prevents blanket swamps. Next verify on exact child-A same-code private source and show map; do not merge PR #103 or change frozen release.
