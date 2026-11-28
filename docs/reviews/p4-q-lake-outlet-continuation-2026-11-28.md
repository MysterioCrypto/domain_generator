# P4-Q — experimental lake outlet continuation and assembly compatibility (2026-11-28)

**PR #103 draft, not merged; no author geography approved.** P4-P HEAD c6e1347d: geographic and atlas CI passed, full pytest 831 passed / 1 failed (A08 exact baseline). See [failed CI](https://github.com/MysterioCrypto/domain_generator/actions/runs/45679995803). Author constraints: Chapter 1 geography and planetary atmosphere; other geography revisable.

## Diagnosis and compatibility decision
P4-P changed the raw regional builder to pre-serialization normalization, but public hydrology already calls channelization.normalize_semantic_confluences after raw assembly. The policies differ: raw removes zero-input confluence traces; public normalization promotes their starts to sources and preserves original IDs. Local A08 controlled reproduction shows differing serialized regional networks (same field byte hashes and counts 49 nodes/31 segments), despite passing semantic validation. Do not re-sign the accepted A08 snapshot or pretend P4-P is backward compatible. Restore default raw legacy behavior and expose the P4-P/P4-Q assembly as explicit internal keyword experimental_network_assembly=True for imported DEM evaluation. This is NOT a new public DomainSpec option; a formal policy/version migration remains a separate decision. Existing public pipeline and frozen release are not silently switched. Local default A08 reproduces the pre-P4-P raw toggle exactly on the same environment; local DomainData hash differs from archived expected hash in both paths, so CI must establish exact A08 acceptance. A08 also contains a historical same-lake return; default compatibility deliberately retains legacy behavior pending migration.

## Outlet correction
The P4-M region spill selection and MFD transport are valid at the discrete receiver. Near the refined shoreline, interpolated flow vector returned to the originating lake immediately, producing a zero-length segment. In experimental assembly, only on a same-lake direct return from a lake outlet, retry once from the already chosen downstream receiver center (not a new outlet, no terrain/routing mutation), retain original shoreline endpoint, and fail closed if retry still returns to the same lake. Validate downstream lake-feature paths including virtual lake-inflow→outlet links, rejecting cyclic or missing continuations. No global crossing repair. The short shoreline-to-center connector is a local geometric fallback, not a solved continuous hydraulic streamline; no universal polygon clearance claim.

## Private Region A evidence
SHA-verified original P4-M 461×461 at 500 m, same 30 km² threshold. Experimental native generation passes 19/19 existing hydrology checks. Compared with P4-P:
| Metric | Regional P4-P → P4-Q | Potential P4-P → P4-Q |
|---|---:|---:|
| Segments | 841 → 842 | 2088 → 2089 |
| Same-lake direct returns | 1 → 0 | 1 → 0 |
| Zero-length segments | 1 → 0 | 1 → 0 |
| Defective spatial pairs | 46 → 46 | 66 → 66 |
| Unauthorized intersection point components | 2547 → 2547 | 2067 → 2067 |
| Positive-length overlaps | 0 → 0 | 0 → 0 |
| Downstream segments to domain edge from lake | self-return → 8 | self-return → 13 |

Regional outlet SW coordinates (44.625,39.625) km; first receiver center (44.25,39.25) km. First downstream segment length 3.2323 km; intersection length with refined source lake polygon 0 in this fixture. Full regional downstream path reaches west edge at (0,21.476847) km. Geometry is diagnostic, not physical water or geography acceptance.

Three targeted local tests pass: actual synthetic DEM with historical return, legitimate existing outlet, feature-level cycle vs marine terminal. Both DEM fixtures preserve accepted spill, routing/fill surfaces, accumulation and skeletons exactly. Marine terminal semantics tested at graph level, not a new full coastal DEM fixture. Existing P4-P regressions now explicitly opt into the experimental path; geographic workflow includes P4-Q tests. Core blob 824253d4d85a1c87b86c705e8ff0e854a049e0b4, script 9f4e7feacf9e82497335615c687e7102aca90b20, test 1958ea580c1609338bff7206b209f0c228a360b8. [Private evidence ZIP](https://drive.google.com/file/d/18RSSlwCacUFzSrrLqVhAxwtJhpAwfe5I/view) SHA-256 1c740d47b00c68b9ce88a5b506f0cdb846d98c8fb3b3b6ff67b84ef2126c5be7; network JSON, lakes, exact spatial audit and diagnostic map. No private DEM committed to GitHub.

## Next P4-R
Resolve the remaining semantic joining/crossing defect by a bounded algorithmic experiment on actual traces; distinguish distinct tributary intersections from near-coincident downstream traces. Do not blindly split thousands of GEOS point components or add ornamental smoothing. Keep the experimental assembly explicit until the public normalization policies and A08 migration are resolved. Then return to expressive geographic terrain and complete regional cartography; extract actual Chapter 1 facts before author map acceptance. No forced old map topology, no merge.
