# Lake Shoreline Morphology v0.2

Status: **proposed design gate**  
Target branch: `dev/0.2`  
Depends on: accepted H09-E river-hierarchy slice

## 1. Why this is the next bounded pass

H09-E river hierarchy is accepted and frozen. The remaining artificial look is now dominated more by standing water than by river centerlines.

Current lake semantics are simple:

```text
Priority-Flood fill residual
→ connected depression component
→ area/depth threshold
→ union of 1 km raster-cell squares
→ materialized lake polygon
```

This is topologically useful, but it conflates two different things:

1. a **routing depression / maximum spill basin** used to condition drainage;
2. an **exact visible shoreline**.

A filled depression is valid computational evidence for a basin, but a cell-union footprint is too coarse to be treated as the final shoreline geometry.

## 2. Measured H09-E lake state

Representative world:

```text
domain:       180 × 120 km = 21,600 km²
cell size:    1 km
accepted:     13 lakes
lake areas:   8, 13, 21, 25, 32, 36, 38, 52, 70, 103, 114, 156, 222 km²
total area:   890 km²
limnicity:    ~4.12%
median area:  38 km²
>100 km²:     4 lakes
```

Measured catchment / lake-area ratios span roughly:

```text
5.6 … 136
```

The four largest lakes are not obviously unsupported by catchment:

```text
222 km² lake → catchment ratio ~7.6
156 km² lake → ~8.9
114 km² lake → ~13.5
103 km² lake → ~27.8
```

This does **not** justify arbitrary shrinking or deleting lakes.

Global HydroLAKES data show a strongly skewed lake-size distribution and about 1.8% natural-lake cover globally, but regional lake density varies enormously with geomorphic history. Core 0.2 currently has no glaciation / tectonic geology model, so a global limnicity target would be false precision.

Therefore this bounded pass improves **shoreline morphology and lake/river geometric consistency first**, while preserving lake-basin selection semantics.

## 3. External reference principles

Relevant observations:

- HydroLAKES represents lakes as shoreline polygons co-registered to river pour points, not as raster cell unions.
- DEM hydrologic filling is primarily a routing-conditioning operation; filled sinks are not automatically exact observed shorelines.
- Hypsographic methods relate lake area to water level by intersecting terrain with a water-surface elevation.
- Nested-depression / fill-merge-spill methods are a legitimate later option if full-spill basin selection itself remains visually wrong.

These principles motivate a separation between the raster routing basin and a refined vector shoreline.

## 4. Scope

Keep unchanged in this pass:

- accepted H09-E river algorithms and thresholds;
- MFD accumulation;
- regional and potential drainage hierarchy;
- Strahler ordering;
- current depression-component acceptance by raster area/depth;
- one canonical spill outlet per accepted lake;
- lake routing supernode semantics;
- public request schema.

Change only:

```text
accepted raster lake basin
→ deterministic sub-cell shoreline reconstruction
→ exact vector lake geometry
→ lake inflow/outlet positions on that geometry
→ lake morphology diagnostics
```

No climate water balance, partial drying, nested-basin splitting, reservoir logic, delta generation, or global lake-count fitting in this slice.

## 5. Two representations, one lake identity

For each accepted lake:

### 5.1 Routing basin

Existing `LakeCandidate.cells` remains authoritative for:

- routing supernode membership;
- accumulation aggregation;
- one canonical outlet;
- raster water-depth support;
- exact replay.

### 5.2 Shoreline geometry

Add an internal refined vector geometry derived from:

- original Terrain 0.2 elevation;
- accepted candidate cells;
- candidate spill/surface elevation;
- deterministic local interpolation.

The vector shoreline is authoritative for:

- materialized `HydroFeature.geometry`;
- `LakeProperties.area_km2`;
- river `lake_inflow` endpoint positions;
- river `lake_outlet` endpoint position;
- operator-visible lake shape.

This is not renderer smoothing. It changes semantic vector geometry.

## 6. Deterministic sub-cell shoreline reconstruction

For the bounded experiment use a fixed **4× linear subdivision per 1 km cell**:

```text
1 km routing cell
→ 4 × 4 local samples
→ 250 m shoreline reconstruction scale
```

No new user-facing parameter.

### 6.1 Sampling

Within the bounding box of the accepted raster component:

1. bilinearly interpolate original terrain elevation from cell-center elevation samples;
2. consider only sub-cells belonging to the accepted raster-basin footprint;
3. classify sub-cell sample support relative to the candidate water surface;
4. polygonize the connected wet region associated with the accepted basin;
5. preserve deterministic islands/holes if terrain rises above the surface inside the basin.

The refined geometry **may shrink inside boundary raster cells**, but must not expand into an unrelated neighboring drainage basin.

### 6.2 Topology requirements

Refined shoreline must be:

- non-empty;
- finite;
- valid canonical `RegionSet`;
- contained inside the raster basin footprint within numeric tolerance;
- deterministic;
- free of self-intersections;
- topologically associated with the same lake id.

If 4× sampling fragments a basin into disconnected puddles because of interpolation artifacts, the pass must fail rather than silently choose an arbitrary component.

## 7. Area semantics

After refinement:

```text
LakeProperties.area_km2 = refined vector geometry area
```

The request `lake_min_area_km2` remains the **raster-resolved acceptance threshold** for Core 0.2 in this bounded slice.

Reason: changing acceptance after sub-cell reconstruction would change which routing supernodes exist and would mix shoreline refinement with lake-count redesign.

The checkpoint must report both:

```text
routing_basin_area_km2
refined_shoreline_area_km2
area_ratio = refined / routing
```

If this distinction proves too confusing or produces large differences, stop and redesign rather than silently changing lake acceptance semantics.

## 8. River/lake endpoint consistency

Current river tracing detects lake entry using raster membership and puts outlet nodes on a cell-edge midpoint.

After refinement:

### Lake inflow

- raster lake membership still detects which lake the trace is entering;
- the final serialized inflow endpoint is the first intersection of the continuous river segment with the refined lake shoreline;
- the river must not continue across visible open water.

### Lake outlet

- the canonical `LakeOutlet.lake_cell → receiver_cell` remains the topological spill transition;
- the serialized lake-outlet position is projected to / intersected with the refined shoreline nearest that spill transition;
- downstream vector tracing begins from that exact shoreline point and continues in the existing receiver cell.

Thus river topology does not change, but visible shoreline and river endpoints agree.

## 9. Size/count/catchment policy for this pass

Do **not** fit the representative world to a global lake-count or lake-area percentage.

Instead report:

- lake count;
- total refined area / domain area;
- area histogram;
- max / median area;
- catchment-to-lake-area ratio;
- storage proxy;
- shoreline development index;
- raster-area vs refined-area ratio.

A lake is not deleted merely because it is large.

### Stop rule for apparent oversized lakes

If refined shorelines still leave one or more lakes obviously oversized or compound-looking against terrain, the next design question is:

```text
nested depression hierarchy / fill-merge-spill
or
partial water-level semantics
```

—not arbitrary global size clipping.

## 10. Automated guardrails

### L01 — deterministic refinement

Same terrain + candidate produces bit-identical refined shoreline coordinates.

### L02 — containment

Refined shoreline area lies inside the accepted raster-basin footprint within tolerance.

### L03 — meaningful area

```text
0 < refined_area <= routing_basin_area
```

and all geometry is finite/canonical.

### L04 — lake identity

Exactly one refined geometry is associated with each accepted routing lake.

### L05 — inflow endpoint

Every `lake_inflow` endpoint lies on the referenced refined shoreline within geometric tolerance.

### L06 — outlet endpoint

Every `lake_outlet` node lies on its referenced refined shoreline near the canonical spill transition.

### L07 — topology preservation

Compared with pre-refinement H09-E:

- same accepted lake ids;
- same canonical outlet receiver cells;
- same regional/potential river graph connectivity ignoring endpoint-coordinate changes;
- same accumulation field;
- same Strahler hierarchy.

### L08 — water raster compatibility

Every raster lake cell with positive canonical lake water depth still references the same routing lake. Refined vector geometry must not cause raster water-depth ownership overlap.

## 11. Operator checkpoint H10-A

Same representative world:

```text
180 × 120 km
seed 2026091402
cell 1 km
same Terrain
same H09-E rivers
same 13 routing lakes
```

Required views:

1. old raster-cell lake footprint vs refined shoreline, side-by-side;
2. terrain + refined lakes + regional rivers;
3. terrain + refined lakes + potential hierarchy;
4. close-up contact sheet for all 13 lakes;
5. shoreline + canonical outlet + all river inflow points;
6. table / JSON of:
   - raster area;
   - refined area;
   - max/mean depth;
   - catchment area;
   - catchment/lake ratio;
   - shoreline development index.

Operator questions:

- do lakes stop reading as raster blobs?
- do shorelines follow local terrain better?
- do large lakes still look implausibly broad/compound?
- do inflows/outlets visually meet water exactly?
- does one lake still look like several basins artificially merged?
- after lake refinement, is the river hierarchy still visually stable?

## 12. Stop rules

If the main defect is fixed by shoreline refinement:
- keep current lake count/selection for Core 0.2;
- proceed to Hydrology final review.

If large/compound lakes remain the dominant defect:
- do not hand-shrink them;
- open a new bounded design for nested depression hierarchy / partial fill semantics.

If river topology changes materially:
- reject implementation; shoreline refinement must not reopen accepted river semantics.

If refinement only makes prettier polygons while hydrologically inconsistent endpoints remain:
- reject; geometry and topology must agree.

## 13. Deferred after climate/biomes

Still deferred:

- perennial vs seasonal low-order channels;
- dry gullies;
- headwater visual fading;
- estuary/delta/alluvial-fan semantics;
- arid closed-lake level variability.

Those require environmental context unavailable in this hydrology-only slice.

## 14. References

- Messager et al. (2016), HydroLAKES / global lake abundance and morphometry, Nature Communications 7:13603.
- HydroLAKES technical documentation: shoreline polygons and pour-point co-registration.
- USGS hydrologically conditioned DEM guidance: sink filling is routing conditioning; real sinks require separate treatment.
- Wu et al. (2018), nested depression hierarchy and fill-merge-spill hydrologic connectivity.
