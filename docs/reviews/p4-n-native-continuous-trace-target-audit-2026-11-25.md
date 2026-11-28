# P4-N — native Core continuous trace target compatibility (2026-11-25)

**NONCANONICAL diagnostic; PR #103 draft/open/unmerged.** P4-M HEAD 2be880deee61e1f7a1eee7d2f3ffe3c009cf4b80 all three CI GREEN. Accepted dev/0.2, frozen release, original terrain and source A8/A12 unchanged.

## Question and experiment

Can the existing Core _trace_continuous supply a drop-in, flow-informed representation of the frozen P4-M 500 m ordinary graph while preserving its semantic endpoints? Verify the P4-M source macro and three fine files against SHA-256, independently replay all original projected fields exactly, partition the 11,402 ordinary directed edges using the existing P4-K reach splitter. Exclude reaches containing endpoints of any archived lake proxy link; use the full recomputed geometric lake-candidate cell support for trace termination. No lake proxy jump is drawn as a channel. Run the actual accepted Core _trace_continuous on the recomputed conditioned MFD direction field from each eligible reach's source cell center, with ordinary confluences as possible stopping cells. Do not force the expected destination, snap, normalize false confluences, or combine traces into a replacement network. Use Core's full-cell SW metric frame (230.5 km square, offset 0.25 km outside P4-M outer node span). For boundary endpoints compare the cell containing the actual terminal position, not simply the last traversed cell. A boundary-cell match does not imply the old center coordinate equals the new outer-face position.

## Measured results, PRIVATE Region A

| Metric | Result |
|---|---:|
| Ordinary edges | 11,402 |
| Partitioned ordinary reaches | 934 |
| Excluded proxy-contact reaches | 4 |
| Tested reaches | 930 |
| Same expected target cell and terminal kind | 801 (86.13%) |
| Wrong target cell, same kind | 123 |
| Wrong kind (confluence vs boundary) | 5 |
| Other terminal (lake inflow) | 1 |
| Core trace errors | 0 |
| Confluence target match | 787 / 905 |
| Boundary target match | 14 / 25 reaches |
| Matched exact terminal coordinates | 787 |
| Matched discrete Hausdorff median / maximum | 0.285747 / 1.777702 km |
| Matched non-simple individual polylines | 0 |
| Archived proxy links not drawn | 6 |
| Full candidate lake support cells | 727 |

Boundary targets are counted per reach, not unique outlets (P4-M has 22 unique outlets). Original archive arrays replayed exactly. The right diagnostic panel shows native flow-informed traces, blue for matched terminal cells and orange for differing terminals; omitted proxy-contact reaches are not repaired. Native curves visually improve regional angularity substantially more than P4-J/K cosmetic geometry. However 129 tested reaches do not preserve the expected terminal, and boundary coordinates cannot be equated with centers. Even matched individual lines do not establish a globally valid noncrossing network. This experiment is neither a complete Core network extraction nor a defect in the accepted tracer; Core explicitly normalizes unrealized skeleton confluences during assembly. **Reject a drop-in geometry-only replacement on the frozen graph.** No approval of water, Q, permanence, topology, or geography.

## Reproduction and evidence

Three local synthetic tests pass: actual Core plane confluence and boundary semantics, lake termination classification, full synthetic independent replay/partition/immutability and tamper rejection. Geographic CI includes tests; remote status tracked independently. Script blob a7dc6e75d7e521ab374c113ce7fb018735256436; test blob 0af4bc586bb6d6846a7612f3c2d55183bcc092ee. [Private derived ZIP](https://drive.google.com/file/d/14w3V_hEw64_jiUnetXhlyAbV33__Fzql/view) SHA-256 80e5d360bbb6a4ee4274d50912f8e3ede89fc6fa7631927d17735b5e9d2358e4 contains diagnostic PNG, per-reach JSON, trace coordinates/source-node paths NPZ and provenance audit. No private source arrays committed to GitHub.

## Next P4-O

Do not force native curves to fit the provisional one-receiver raster graph, and do not start another cosmetic smoothing or resolution sweep. Evaluate one **complete native Core network extraction and normalization** on the same P4-M 500 m terrain as an independent experimental topology candidate, if the existing Core contract allows imported terrain without modifying accepted algorithms. Compare semantic nodes, connected segments, geographic terminal positions and lake semantics against P4-M; render the complete candidate at the same region scale. Do not silently claim old graph identity or accept new geography. Fail closed and document blockers if Core's assembly or lake validation cannot support this input. Product-oriented visual gate remains necessary.
