# Nested Depression Hierarchy Diagnostic v0.2

Status: **accepted experimental design gate**
Target branch: dev/0.2
Checkpoint: H10-B
Depends on: H10-A refined shoreline semantics (KEEP) and accepted H09-E river hierarchy

## 1. Why H10-B is diagnostic first

H10-A proved that the old 1 km cell-union shoreline was a real geometry defect, but refinement reduced visible lake area by only about 6% and the largest full-spill silhouettes remain broad.

Simply lowering visible water level while keeping the same downstream outlet would be inconsistent: a continuously outflowing surface lake with no additional loss model must reach its spill elevation.

So before changing lake topology H10-B asks one structural question:

> Are the large full-spill lakes compound depressions containing multiple significant nested basins, or are they single broad basins implied by Terrain 0.2?

H10-B changes diagnostics only. It does not split, delete, shrink or partially fill lakes.

## 2. External basis

Wu et al. (2019) describe nested depression hierarchies by tracing topological splitting/merging within compound DEM depressions. Fill-Spill-Merge work by Barnes, Callaghan and Wickert likewise models leaf depressions, spill connections and higher-level meta-depressions.

References:
- Wu et al. 2019, JAWRA 55(2):354–368, DOI 10.1111/1752-1688.12689.
- Barnes, Callaghan & Wickert, depression hierarchy / Fill-Spill-Merge work.

## 3. Frozen semantics

H10-B must not change:
- Terrain 0.2;
- Priority-Flood routing/fill surfaces;
- MFD accumulation;
- H09-D2 regional rivers;
- H09-E potential hierarchy / Strahler order;
- accepted routing lake ids;
- canonical lake outlet receiver cells;
- H10-A refined shoreline;
- raster water-depth ownership;
- public request or DomainData contracts.

## 4. Internal hierarchy

For each accepted routing lake, construct an internal merge tree from original Terrain 0.2 elevations inside that lake's routing basin, bounded by its current spill/surface elevation.

Conceptual node fields:
- id / parent / children;
- minimum cell and elevation;
- merge elevation;
- relief to merge;
- cells and area at merge;
- storage-to-merge proxy.

The existing full-spill lake is the root/meta-depression. Leaf nodes are local minima that exist as separate flooded components before an internal saddle merges them.

## 5. Deterministic level sweep

Within one routing basin:
1. process cells in non-decreasing terrain-elevation batches;
2. activate all cells at the same elevation before resolving merges;
3. use the same 8-neighbor connectivity as current depression components;
4. a new isolated active component begins a leaf depression;
5. when distinct active components connect, record a merge/meta-depression at that saddle elevation;
6. continue until the accepted full-spill root is reached.

Stable tie-breaking may use cell coordinates and node ids only after same-elevation batch activation.

## 6. Node metrics

For every leaf/merge node report:
- minimum elevation;
- merge/spill elevation;
- relief = merge - minimum;
- area at merge;
- storage proxy = sum(max(merge elevation - terrain, 0)) * cell area;
- fraction of parent full-spill area;
- fraction of parent storage proxy.

## 7. Significant child definition

No new tuning sweep.

A child is threshold-significant only if at its own merge/spill level it satisfies the existing lake resolution thresholds:
- area_at_merge >= lake_min_area_km2;
- relief_to_merge >= lake_min_depth_m.

This is diagnostic classification only; it does not create a new lake.

For each current lake report leaf count, significant leaf count, merge count, largest/second child area fractions, largest/second storage fractions and internal saddle reliefs.

## 8. H10-B checkpoint

Same representative world: 180 × 120 km, seed 2026091402, same 13 routing lakes, same H10-A shorelines and H09-E rivers.

Required outputs:
1. unchanged H10-A regional refined-lake view;
2. contact sheet of all 13 lakes with minima, merge saddles and significant child basin outlines;
3. dedicated close-ups of the four largest lakes;
4. compact hierarchy tree for each large lake;
5. JSON/table with node metrics and child area/storage fractions.

## 9. Decision after H10-B

Case A — large lakes strongly compound:
- KEEP H10-A;
- next design may replace one full-spill visible lake with a nested/cascade semantic model;
- that later design must explicitly restore river connectivity between child lakes.

Case B — large lakes mostly single broad basins:
- nested splitting will not solve the visual issue;
- do not implement it merely to shrink lakes;
- remaining broadness comes from terrain basin geometry or from treating every accepted depression as standing water;
- defer water-availability classification to climate/surface or revisit terrain only with concrete evidence.

Case C — mixed:
- later splitting must be per-basin and structure-driven.

## 10. Automated guardrails

N01 deterministic hierarchy.
N02 one root per accepted routing lake.
N03 acyclic tree; every non-root has one parent.
N04 child->parent merge elevation and area are monotonic.
N05 every node is contained in its routing lake.
N06 generating diagnostics changes none of lake ids/outlets, river graphs, accumulation, Strahler, H10-A geometry or water-depth raster.

## 11. Stop rules

- No partial water levels in H10-B.
- No lake split/delete in H10-B.
- No global lake-size fitting.
- Do not reopen river routing.
- Do not increase shoreline subdivision as a substitute for hierarchy analysis.
- Ambiguous equal-elevation topology must fail explicitly rather than depend on iteration order.

## 12. Acceptance

H10-B succeeds if it explains whether the suspicious large lakes are broad because of compound nested structure or because the terrain itself contains a single broad depression. Only then choose a production semantic change.