# Marine / Coastal Boundary Semantics v0.2

Status: **ACCEPTED design gate; runtime implementation authorized but not yet accepted**
Target development line: dev/0.2
Checkpoint: H12-A
Depends on: accepted Terrain 0.2 + Hydrology 0.2 + H10 refined shoreline geometry

## 1. Why H12 exists

The current Core can represent continuous terrain, rivers, accepted depression lakes and boundary drainage outlets.

It cannot currently represent:
- sea/ocean water;
- a coastline;
- an archipelago as land surrounded by marine water;
- a known marine receiving environment for a river mouth.

Negative elevation is currently only terrain elevation. It does not mean ocean.

Likewise, a river that reaches the domain edge is currently a domain_outlet, not an estuary or marine mouth.

This is a fundamental universality gap. H12-A adds only the missing marine boundary condition and coastline semantics.

It does not add tides, waves, salinity, estuaries or deltas.

## 2. Opt-in contract

Extend Core 0.2 hydrology with optional:

~~~text
hydrology:
  marine:
    sea_level_m: <finite float>
~~~

Rules:
- marine is optional;
- there is no hidden sea level;
- negative terrain elevation alone never creates marine water;
- when marine is absent, all accepted pre-H12 behavior remains bit-identical;
- Core 0.1 cannot contain the marine recipe.

This keeps the generator universal:
- inland map → omit marine;
- island/archipelago/coast → provide explicit sea level;
- unusual/fantasy datum → any finite sea-level value may be supplied.

H12-A does not infer 0 m = sea level.

## 3. Marine raster semantics

Let:

~~~text
below_sea = terrain_elevation_m < sea_level_m
~~~

A cell is marine only if it belongs to a below-sea component connected to the domain boundary.

Connectivity is fixed **4-neighbour edge connectivity**.

Reason:
- two cells touching only at one corner do not provide finite-width water connectivity;
- diagonal connectivity could flood an otherwise enclosed basin through a one-point raster contact.

~~~text
marine_mask = boundary_connected_4_neighbour_components(below_sea)
~~~

Consequences:
- edge-connected below-sea terrain becomes marine;
- an enclosed below-sea depression remains inland terrain;
- such an enclosed depression may still become an ordinary lake;
- several marine components may exist if land separates them inside the domain.

## 4. Marine components and identity

Each 4-connected marine component receives a deterministic generated id:

~~~text
marine-0001
marine-0002
...
~~~

Ordering:
1. minimum raster row;
2. minimum raster column;
3. component cell count;
4. deterministic lexical fallback if needed.

A runtime MarineCandidate conceptually contains:

~~~text
cells
sea_level_m
raster_area_km2
max_depth_m
~~~

Marine candidates are deterministic terrain + sea-level products and consume no RNG.

## 5. Relationship to lake classification

Marine cells are not lakes.

For marine-enabled worlds:

~~~text
lake depression support
= accepted depression support
  minus marine_mask
~~~

Requirements:
- no cell may simultaneously belong to a marine component and accepted lake candidate;
- an enclosed below-sea depression not boundary-connected remains eligible for ordinary lake semantics;
- existing inland lake thresholds and H10 shoreline rules remain unchanged outside marine support.

## 6. Canonical water depth

For a marine cell:

~~~text
marine_depth_m = sea_level_m - terrain_elevation_m
~~~

which is strictly positive because marine support uses terrain < sea_level.

Final canonical water depth:

~~~text
water_depth_m =
    marine_depth_m       on marine cells
    accepted lake depth  on lake cells
    accepted river depth on visible river cells
    0                    otherwise
~~~

Marine support has precedence over river/lake depth on the same raster cell, although marine/lake overlap must be impossible by guardrail.

## 7. Public marine mask

When marine is enabled add one derived 2D field:

~~~text
marine_mask

role  = derived
dtype = uint8
unit  = binary
0 = non-marine
1 = marine
~~~

The mask is explicit input to rendering, Placement and later coastal/environmental logic.

When marine is absent, the field is absent.

## 8. Refined coastline geometry

A one-kilometre cell union is not an acceptable final coastline.

Reuse the accepted H10 separation between raster semantic support and refined visible shoreline.

For H12-A use fixed 4× linear subdivision per base cell.

For each marine component:

~~~text
component raster support
+ original Terrain 0.2 elevation
+ explicit sea_level_m
→ bilinear sub-cell sampling
→ wet sub-cells where elevation < sea_level_m
→ deterministic polygonization
→ MarineFeature geometry
~~~

The refined geometry:
- may shrink within marine boundary cells;
- must not expand into a base cell belonging to another inland hydrologic class;
- must be finite and canonical;
- may contain holes representing islands;
- must touch the domain boundary;
- must not overlap another marine feature.

If refinement produces a disconnected interior polygon that does not touch the domain boundary, H12-A fails rather than silently treating it as the same sea.

## 9. Public marine feature

Add a distinct public semantic feature type rather than overloading lake properties.

Conceptually:

~~~text
MarineFeature
  family = hydro
  kind   = marine
  source = generated / hydrology
  geometry = RegionSet
  properties:
    area_km2
    sea_level_m
    max_depth_m
~~~

Existing serialized lake HydroFeature shape remains unchanged.

SemanticFeature adds MarineFeature as an additional union member.

## 10. River-mouth semantics

Add:

~~~text
RiverNodeKind.MARINE_OUTLET = marine_outlet
~~~

A marine outlet:
- has outdegree 0;
- has no boundary_side;
- has feature_id referencing a MarineFeature;
- lies on the refined marine shoreline.

A river entering marine water terminates at the **first intersection with the refined coastline**.

~~~text
land river → coastline intersection → marine_outlet
~~~

It must not continue across marine cells toward the domain boundary.

A river leaving the domain through ordinary land without entering marine water remains a domain_outlet.

## 11. Regional and potential drainage networks

Both accepted public networks must respect marine support:

~~~text
rivers
potential_drainage
~~~

Rules:
- marine cells are excluded from visible/potential channel support;
- traces terminate at first marine entry;
- no serialized river/potential segment continues through open marine water;
- marine outlet topology is deterministic;
- upstream catchment values remain land-drainage values and are not reset at the mouth.

H12-A does not generate submarine channels.

## 12. Routing boundary

H12-A does not replace accepted Terrain/Hydrology routing algorithms.

The existing conditioned drainage field may continue to be computed from terrain as before.

Marine semantics intervene at classification/materialization boundaries:
- marine support is known before lake acceptance;
- marine cells are excluded from lake/channel support;
- semantic traces terminate on first marine entry;
- canonical water depth uses explicit sea level in marine support.

If evidence shows accepted routing itself produces incorrect land drainage once marine support exists, stop and open a separate routing-boundary design. Do not silently rewrite Priority Flood / MFD inside H12-A.

## 13. Relationship to climate and surface

C1/C2/C3/C4/C5 are unchanged in H12-A.

In particular:
- marine water does not automatically change C1 precipitation;
- no ocean moderation of temperature is added;
- no sea-breeze or monsoon model is added;
- C2 continues its already accepted canonical-water semantics unless a later bounded design distinguishes marine influence;
- C3 vegetation on marine cells is reported as an integration issue if present; H12-A must not silently redesign C3.

First establish correct marine topology/geometry; only then decide which environmental layers should consume it.

## 14. Relationship to delta / estuary semantics

H12-A creates a known marine receiving environment.

That removes one blocker for later estuary/delta/coastal-fan work.

H12-A itself does not decide whether a marine river mouth is an estuary, delta or simple open-coast mouth. Those require discharge/sediment/coastal-process semantics.

## 15. Automated guardrails

### O01 — opt-in compatibility

Without hydrology.marine:
- no marine runtime state;
- no marine_mask;
- no MarineFeature;
- no marine_outlet;
- exact accepted pre-H12 Core 0.2 fingerprints and world output remain unchanged.

### O02 — explicit sea-level semantics

Changing only sea_level_m changes semantic fingerprints.

Negative terrain does not create marine support when the recipe is absent.

### O03 — boundary-connected classification

Synthetic fixtures prove:
- edge-connected below-sea cells become marine;
- enclosed below-sea cells do not;
- 4-neighbour connectivity does not leak across diagonal point contacts.

### O04 — deterministic component identity

Same terrain + sea level yields bit-identical marine masks, component ordering and feature ids.

### O05 — marine/lake exclusivity

No accepted lake cell overlaps marine_mask.

An enclosed below-sea depression remains eligible for lake classification.

### O06 — canonical marine depth

For every marine cell:

~~~text
water_depth_m == sea_level_m - elevation_m
~~~

within float persistence tolerance.

No non-marine water-depth value changes solely because marine exists elsewhere.

### O07 — coastline geometry

Every MarineFeature:
- has valid canonical RegionSet geometry;
- positive refined area;
- touches the domain boundary;
- has no overlap with another marine feature;
- is deterministic;
- has area <= its raster-component support area within refinement tolerance.

### O08 — marine outlet references

Every marine_outlet:
- references an existing MarineFeature;
- lies on that feature shoreline within geometric tolerance;
- has outdegree 0;
- has no boundary side.

### O09 — river termination

No regional river segment continues into marine interior beyond its shoreline endpoint.

Ordinary non-marine domain outlets remain valid.

### O10 — potential drainage termination

No potential-drainage segment continues into marine interior beyond its shoreline endpoint.

### O11 — public contract

When marine is enabled:
- exactly one derived marine_mask field exists;
- dtype = uint8;
- values are only 0/1;
- every marine feature uses the distinct marine feature shape;
- every marine outlet feature reference is valid.

### O12 — upstream immutability outside bounded marine effects

For cells/features not affected by marine support:
- terrain exact-unchanged;
- accepted climate exact-unchanged;
- C2/C3/C4/C5 exact-unchanged;
- Placement logic unchanged.

Hydrology differences are limited to the explicitly marine-affected boundary:
- marine/lake classification;
- channel termination;
- water depth;
- marine features/outlets.

### O13 — replay

Identical plan/attempt reproduces marine mask, component ids, refined coastline geometry, canonical water depth, mouth topology and bundle payloads bit-exactly within exact generator version.

## 16. Representative operator checkpoint H12-A

Use a dedicated coastal/archipelago fixture, not the frozen inland C5 diagnostic as the only evidence.

Fixture requirements:
- substantial marine area but substantial land remains;
- at least two islands or an island + mainland;
- at least one enclosed below-sea inland depression;
- at least one river reaching marine water;
- at least one ordinary inland lake if terrain supports it;
- at least one non-marine domain outlet if practical.

The diagnostic sea_level_m is fixture data only and is not a Core default.

Required views:
1. raw terrain with sea-level contour;
2. base marine_mask;
3. refined marine geometry / coastline;
4. canonical water_depth;
5. regional rivers + lakes + marine;
6. potential drainage + marine;
7. close-ups of every marine river mouth;
8. enclosed below-sea depression proving it was not flooded by boundary connectivity;
9. report with marine component count, marine raster/refined area, land area, marine fraction, shoreline length, river mouth count and lake count.

Operator questions:
- does the coastline follow terrain rather than 1 km raster blocks?
- are islands preserved cleanly?
- does sea water avoid flooding enclosed below-sea inland basins?
- do rivers terminate exactly at the coast?
- do any rivers continue visibly through the sea?
- are lakes and marine water visually/semantically distinct?
- does the result look usable for both mainland-coast and archipelago domains?

## 17. Acceptance boundary

H12-A implementation may be accepted only if:
- O01–O13 are green;
- full pytest is green;
- pre-H12 inland acceptance remains exact;
- dedicated coastal/archipelago checkpoint is reviewed;
- marine/lake distinction is visually and contractually clear;
- explicit implementation ACCEPT / REJECT is recorded.

## 18. Stop rules

- Do not infer a hidden sea level.
- Do not treat every negative-elevation cell as ocean.
- Do not flood enclosed below-sea basins unless boundary-connected.
- Do not classify marine cells as lakes.
- Do not trace rivers across open sea.
- Do not generate submarine rivers.
- Do not add tides, waves, salinity or coastal erosion in H12-A.
- Do not generate deltas or estuaries merely because a marine outlet exists.
- Do not change C1 climate or C2/C3 ecology to make coastlines look familiar.
- Do not reopen accepted inland Hydrology globally if the defect is confined to marine-enabled routing.
- If sea-level boundary conditions require a different routing algorithm, stop and design that separately.


## 19. Design acceptance

Operator decision: **ACCEPTED**.

PR #96 merged into `dev/0.2` at:
`f8efae6e24cdda68fb10960f13ca69d342a61a7b`.

Implementation is authorized only for the bounded marine/coastline semantics above. Inland compatibility and the absence of hidden sea-level assumptions remain mandatory.
