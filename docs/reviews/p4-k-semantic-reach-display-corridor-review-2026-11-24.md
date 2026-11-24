# P4-K — semantic reach display and macro-direction diagnostic (2026-11-24)

**NONCANONICAL / PR #103 DRAFT.** P4-J final HEAD 607521f681ccc17ca7eebfc6a71f9ba63f65df79: all three CI runs GREEN. This iteration is display only on the SHA-verified original PRIVATE P4-B region A (231×231, 1 km, relief 2.0, threshold 30 km²) and original P4-E background. No Core, source graph, terrain, frozen release, physical water, POIs or routes modified.

## Method and boundaries
Partition every ordinary directed edge exactly once into maximal paths between headwaters, confluences, terminals and boundary nodes. Internal sampling points need not be passed through by the display line. Original edge IDs are retained in the export, not replaced by inferred links. RDP tolerance 0.35 km followed by two endpoint-fixed Chaikin passes. Bidirectional polyline buffer coverage within 0.75 km (not a new universal constant), source land-cell coverage, simple polylines and final STRtree intersections restricted to shared graph endpoints. Revert invalid candidate reaches, repeat intersection check. No lake proxy support. Nearest-original-line raw elevation difference checked at <=0.125 km sample spacing against 15 m limit using NumPy bilinear sampling; this is a sampled diagnostic, NOT continuous proof of channel descent or valley occupancy. Final noncrossing is not proof of a crossing-free continuous deformation. No invented meanders. Render both alternatives on same background with identical per-reach width based on start-area class (NOT Q).

## Measured actual region A
- 5,868 original edges, 5,893 original nodes; 927 reaches, 952 fixed semantic/boundary nodes, 4,941 intermediate nodes not required as display vertices.
- 581 reaches changed by >20 m; maximum Shapely discrete Hausdorff 0.708572 km, sampled max elevation difference 1.873517 m, 2 corridor/land fallbacks, 0 terrain-height or intersection fallbacks, final unrelated crossings 0.
- Display length 6788.383 → 6584.605 km (-3.00%); total absolute internal turning 85860 → 79514.49 degrees (-7.39%). Display distances NOT authoritative; original graph unchanged.
- 544 edges in runs >=8 same-heading steps **within semantic reaches** (different partition from P4-H). Parent interpolated DEM downhill gradient within 22.5°: 295/544 =54.2%, vs 1897/5324 =35.6% for other edges; mean angular gaps 22.56° vs 38.85°. Association, not isolated causal proof.
- Visible bends improved relative to original; large-scale synthetic orientation persists. Keep optional geometry only; **do not increase cosmetic offsets blindly or claim acceptable natural regional map**.

## Reproducibility
15 local synthetic tests passed, including exact edge partition, immutability, malformed graph, cycles, boundary fixed nodes, crossing rejection, unsupported lakes, land/axis/receiver checks, straight-line no-meander case and deterministic CLI SHA guard. Removed SciPy dependency in favor of existing NumPy; PNG and NPZ identical before/after, sampled height scalar difference <1e-12 m. Code blob c12d31618c428d2a7e21ddcc6ae3fe5dc0996def, tests d9eac77b693c1a96eb06c9bbc47d9fc62e1345bd. CI explicitly includes 15 tests; remote status tracked separately.

[Private final v2 ZIP (PNG, source-node lists, display polylines NPZ, JSON+SHA)](https://drive.google.com/file/d/1HarTQ1wcjLzqVvoYonORlQnZGHIrQwxu/view). No private arrays/maps committed to GitHub. Original private A8/A12 not included.

## Next P4-L
Stop successive cosmetic smoothing experiments. Inspect source/child relief morphology at regional scale; one controlled terrain-detail hypothesis should address valley coherence rather than inventing meanders. Preserve macro height anchors, land/boundary constraints and accepted routing algorithm; independently reroute only a candidate and compare with frozen baseline. No automatic topology acceptance; avoid repeating rejected blanket A8 D8 carving. Product gate remains visually useful regional geography, not an increase in diagnostic complexity.
