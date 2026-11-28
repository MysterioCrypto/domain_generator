# P4-P — native regional normalization and spatial audit (2026-11-25)

**Experimental Core change in PR #103 draft, not merged.** P4-O HEAD 21123fd0 all three CI GREEN. Author draft geography is freely revisable; Chapter 1 geography and planetary atmosphere remain binding. No requirement to reproduce an obsolete draft map.

## Fix and compatibility
Verified original Core blob 32bf846d5804ae050663246c349d8946386ce100 against live P4-O. In generate_hydrology_v02, enable the existing normalize_false_confluences=True for the regional channel skeleton, matching the already accepted potential-network assembly behavior. No change to routing, accumulation, skeleton extraction, trace algorithm or public contracts. No new parameter. Valid legacy graph is unchanged on synthetic control seed 0; seed 3 demonstrates native false confluence before and successful validation after fix (13→12 segments). Both preserve routing/filled DEM, accumulation, both skeleton masks and potential network exactly. Valid control also preserves water depth, stream mask and regional network. Five local targeted tests passed. This is bounded evidence, not global backward compatibility; full CI is required. The historical P4-O script will now observe the corrected native path when run on new Core; use its historical commit for the old failing baseline.

Using SHA-verified private P4-M 500m DEM, native corrected generate_hydrology_v02 reproduces the archived P4-O normalized regional and potential network JSON structures exactly (841 and 2088 segments), all 19 Core hydrology invariants pass. No manual rebuild. No acceptance of author geography or physical water.

## Spatial audit
Use Shapely 2.1.2 STRtree intersecting-pair query, exact piecewise-linear intersection components, allowed points only at shared semantic node coordinates (1e-8 km tolerance); report positive length overlaps separately. Zero-length segments are reported and excluded from pair tests. No repair.

| Metric | Original regional | Normalized regional | Potential |
|---|---:|---:|---:|
| Segments | 936 | 841 | 2088 |
| Intersecting nondegenerate pairs | 1528 | 1396 | 3567 |
| Shared-node-only pairs | 1477 | 1350 | 3501 |
| Defective pairs | 51 | 46 | 66 |
| Unauthorized point components | 2719 | 2547 | 2067 |
| Positive-length overlaps | 0 | 0 | 0 |
| Zero-length segments | 1 | 1 | 1 |

All defective pairs in this fixture satisfy the GEOS crosses predicate. Point components are not independent hydrologic events; exact intersections do not measure near-coincident geometry. One zero-length segment per network links a lake outlet to an inflow of the SAME lake (normalized regional river-segment-0358, potential river-segment-0867). Existing graph validator passes despite this lake self-return in the feature-level semantics. This is a real independent defect, not a reason to force the old graph. Do not claim physical validity. Normalizer leaves the existing source/confluence stream-mask behavior untouched.

## Artifacts and tests
Core blob b4d88960aa5c02c2a7512a70c20c878e831e5876; spatial audit script c4dda8f7c50d2c40e93a68d1405007c728479f2e; regression tests eba83f7981d21f800d38594a36950beb9be92f91. Five targeted local tests passed including true legacy failure/repair, valid control, shared nodes, crossing and overlap, coincident different IDs and degenerate lake segment. Integrated in geographic workflow. [Private evidence ZIP](https://drive.google.com/file/d/1B1sNWeiuQsRqeyc_1QRabp1tn0PNhLKN/view) SHA-256 142ad2d3c896afce6564b10bd47258bec065138e71b06d34700331b029b2555c contains exact audit JSON, private replay result and diagnostic PNG; no original DEM or private geometry in GitHub.

## Next P4-Q
Fix the concrete same-lake outlet/inflow return mechanism and test a legitimate lake outlet on public synthetic terrain, including marine receiving environment if relevant. Verify actual candidate with independent spatial audit. Address crossing/near-coincident traces via semantic joining rather than ornamental smoothing, as a separate bounded slice if needed. Prioritize usable representative maps and expressive terrain, not a long chain of diagnostics. Chapter 1 geographic facts still need extraction before accepting any author map. No merge without explicit acceptance.
