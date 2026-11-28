# P4-R — same-target early confluence geometry experiment (2026-11-28)

**Draft PR #103; geometry-only, NOT canon or RiverNetwork/DomainData.** Prior P4-Q HEAD 3bbbcb0d passed geographic, atlas and full pytest CI (full run 46126535311). Accepted dev/0.2 and frozen release unchanged. Author constraints remain Chapter 1 geography and planetary atmosphere; other geography revisable.

## Diagnosis
SHA-verified private P4-Q network archives. All 46 regional and 66 potential defective pairs have the SAME existing downstream confluence; 39/52 pairs have identical archived catchment descriptors. 34/55 affected existing confluence groups. Thus the observed defect is independently traced branches meeting prematurely before their common planned merge. Exact GEOS crossing components (2547/2067) are not independent hydrological events.

## Bounded algorithm
Process affected same-target groups jointly. Retain first trace by descending archived catchment descriptor, descending length, then stable ID. Insert subsequent trace up to its first exact contact with retained tree. Split accepting edge at contact and discard donor suffix; reuse existing confluence when applicable. Collapse unary nodes after group assembly. No new meanders or global rerouting. Fail closed on cross-target intersections, positive-length overlaps, unsupported contact at source, invalid graph or remaining spatial defects. Preserve all source/lake-outlet first terminal identities and all original non-confluence descriptors; validate directed merge-only graph and virtual lake feature continuation. Report exact source fragment arclength spans and length ledger. Existing isolated boundary descriptors (1 regional, 3 potential) are preserved, not claimed connected. Explicit experiment hypothesis: first contact with the existing same-target tree represents a merge in a planar drainage network. Not hydraulic proof; no near-miss repair, no inter-layer spatial audit, no universal claim.

## Private Region A
| Metric | Regional | Potential |
|---|---:|---:|
| Defective exact intersecting pairs before → after | 46 → 0 | 66 → 0 |
| Unauthorized point components | 2547 → 0 | 2067 → 0 |
| Early joins | 40 | 61 |
| Unary nodes collapsed | 3 | 2 |
| Nodes | 871 → 908 | 2147 → 2206 |
| Segments | 842 → 879 | 2089 → 2148 |
| Original length km | 7061.471331 | 11009.852330 |
| Candidate length km | 6821.715666 | 10808.118791 |
| Discarded suffix length km | 239.755665 | 201.733539 |
| Source and lake outlet first-terminal identities preserved | 484/484 | 1222/1222 |
| Non-simple or degenerate segments after | 0 | 0 |
| Positive length overlap pairs after | 0 | 0 |

All exact remaining intersections at shared nodes. No same-lake return reintroduced. Two independent CLI runs generated all three JSON outputs byte-identically. Six targeted public synthetic tests pass: early contact/unary collapse, multi-branch group/determinism, unaffected graph/isolated boundary, cross-target failure, positive overlap failure and lake-terminal/feature-cycle semantics. Existing spatial audit contract used; local equivalent audit implementation checked on archived inputs; actual repository audit exercised by CI. Private archive [ZIP](https://drive.google.com/file/d/1xgvQ1M4oYDXKFIjs6hi984vCJS3GmQBD/view) SHA256 acc350bbddfa7048317997e7e1bcbeeb08eaf24378940aafbc2d5321a237c923 includes comparison PNG, both geometry-only candidate graphs and audit; original private inputs not committed. Script blob 7324b02d822ea9bc0940d5df989f9b993347378c, test blob eaccf4f632b6341f75083c9dfbe27dd88a62a1c6. CI integrated.

## Boundary and next P4-S
Geometry-only candidate deliberately drops segment properties: no recomputed contributing area, Strahler, raster stream/water masks, hydrological validation or inter-layer consistency. Cannot be substituted into DomainData or declared production fix. Core unchanged. Next: integrate the bounded joining into explicit experimental native assembly BEFORE deriving segment properties and masks, using original trace-cell provenance or correctly recomputed fields (never sum overlapping archived descriptors). Recompute topology-dependent metadata, ensure regional/potential consistency and lake semantics, and run existing validations/compatibility. If contracts prevent sound integration, report it rather than fabricate properties. Then shift to expressive terrain and full regional maps; extract actual Chapter 1 constraints before author geography acceptance. No merge or auto-acceptance.
