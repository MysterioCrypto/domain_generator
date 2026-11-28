# P4-M — nested same-analytic-terrain resolution counterfactual (2026-11-25)

**NONCANONICAL / PR #103 DRAFT.** P4-L HEAD eff6197686e27aa6b49672e4764450a9eadd346e all three CI GREEN. Rejected P4-L surface not used. Accepted Core dev/0.2, frozen release, original A8/A12 and author geography unchanged.

## Controlled experiment

Use archived original PRIVATE P4-B Region A at 231×231, 1 km. Verify macro, child, manifest and projection SHA-256 through P4-L audit. Replay all six original terrain arrays and all original MFD projection arrays exactly. Generate 461×461 terrain by changing only ChildTerrainSettings.spacing_km to 0.5, keeping analytic Hermite + spherical detail function, source, seed, strength, extent and planet parameters. Every original axis/sample of all six arrays equals the corresponding fine subsample bit-for-bit; 63 continuous macro anchors remain exact (0 m error). All-land region; not coastal evidence.

Run independently through existing connected_mfd_channel_projection with stream threshold 30 km² and unchanged lake criteria (16 km², 10 m, max 12). No external A8 area injected. Fixed outer node coordinates span 230×230 km; **not exactly identical cell footprint**: unchanged Core uses full cell area even at boundary. Source accounting area 53361 → 53130.25 km² (-0.4324%). No hidden boundary compensation. Both ledgers close within 1e-6 km² (actual ~1e-10). This is a resolution counterfactual of the combined conditioning/routing/extraction, not an isolated MFD exponent or a convergence proof.

Partition ordinary directed edges into maximal same-heading runs using existing P4-H cycle/adjacency guard. Use actual length of axial and diagonal edges (spacing and sqrt(2)*spacing), not equal edge counts. Report length-weighted fractions with fixed physical thresholds 8 and 16 km. These percentages are not directly the older P4-H ≥8 edges statistic. Map panels same world node extent, color/illumination, physical threshold and display width classes. Exclude proxy jumps from drawn ordinary channels.

## Results

| Metric | 1 km | 0.5 km |
|---|---:|---:|
| Nodes | 53,361 | 212,521 |
| Ordinary edges | 5,868 | 11,402 |
| Ordinary length, km | 6788.383 | 6595.080 |
| Maximal same-heading runs | 2326 | 3206 |
| Length fraction in runs ≥8 km | 18.4362% | 10.1455% |
| Runs ≥8 km | 119 | 64 |
| Length fraction in runs ≥16 km | 2.4287% | 1.4556% |
| Runs ≥16 km | 8 | 5 |
| Maximum same-heading run, km | 29 | 28 |
| Boundary endpoints | 25 | 22 |
| Routing lake supernodes | 0 | 1 |
| Traversed lake proxy cells | 0 | 3 |

Nearest spatial outlet comparison (not basin matching): 9 exact shared coordinates; old→fine median 0.5 km, max 22.677 km, 22/25 within 1 km and 23/25 within 5 km; fine→old median 0.5 km, max 3 km, 21/22 within 1 km and 22/22 within 5 km. The one fine geometric lake proxy is not confirmed water; no nonlocal links drawn. New fine boundary topology not accepted.

**Conclusion:** finer sampling reduces long straight length share by ~45% relative, preserving the analytic surface. This establishes a substantial resolution-sensitive component of the grid-aligned skeleton. It does not remove long straight segments or make the regional map automatically acceptable; dominant 8-neighbor topology and source morphology remain plausible contributors. Fine resolution is a useful experimental candidate, not replacement of the original network or a new universal default. No further blind detail tuning. No physical discharge, water permanence, POI or road inference.

## Reproducibility

10 local synthetic tests GREEN (nested invariants, source tamper, axial/diagonal length equivalence, cycles, nearest outlet semantics, independent routing/conservation, CLI exact replay and SHA). Code blob e451451da73373eeaac082aca88a8fb9151267fd; tests a21e18bad9fe42e9bb015274b172430b42e1ae3b; workflow explicitly includes tests. [Private derived ZIP](https://drive.google.com/file/d/13lIHSG1LHs22PjN-rkb3jkTE-MKfWFcX/view) SHA-256 b68d63cf4e3a0ce05623f0eeb2028a7d2b542a8fafe5f4df47f239ea7bffa5f5. Includes comparison PNG, fine terrain/projection NPZ, manifest and SHA audit, no original A8/A12 archive or private arrays in GitHub.

## Next P4-N

Use the 500 m candidate as read-only experimental input; inspect the existing accepted Core continuous channel tracing contract and compare the same candidate's ordinary one-receiver centerlines with actual flow-informed subcell vectors, if the existing API supports fixed topology/outlet semantics. This is distinct from P4-J/K decorative smoothing. Explicitly isolate lake-proxy geometry and do not draw nonlocal links as rivers. A bounded adapter/proof, not a new routing algorithm or accepted Core change. If the contract cannot preserve the candidate network semantics, report the blocker instead of fabricating geometry. Product objective remains a geographically readable map, not indefinite resolution/noise sweeps.
