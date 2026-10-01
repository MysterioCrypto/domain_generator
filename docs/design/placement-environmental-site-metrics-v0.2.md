# Placement Environmental Site Metrics v0.2

Status: **ACCEPTED / implemented / merged**
Target branch: `dev/0.2`
Checkpoint: P08-A
Depends on: accepted Terrain 0.2 + Hydrology 0.2/H11-A + C1 + C2 + C3

## 1. Purpose

Core 0.1 dependent placement already has a deterministic, setting-agnostic mechanism:

```text
reservation
→ world-space candidate lattice
→ site metrics
→ hard requirements
→ preference scoring
→ near-best
→ deterministic weighted selection
```

The candidate/selection mechanics remain valid in Core 0.2.

What changed is the available environment.

Core 0.2 now has:
- accepted annual temperature;
- accepted annual precipitation;
- accepted effective moisture;
- accepted climate-aware vegetation;
- accepted canonical water;
- accepted public/runtime potential drainage scaffold.

P08-A extends only the site-metric registry so Placement can observe the accepted Core 0.2 environment.

It does not redesign the placement algorithm.

## 2. Readiness audit

### KEEP unchanged

The following Core 0.1 semantics remain valid for Core 0.2:
- world-space rotated square candidate lattice;
- explicit `candidate_spacing_km`;
- reservation `covers` containment;
- canonical candidate ordering;
- circular raster footprint support;
- hard requirements with `less_or_equal` / `greater_or_equal`;
- preference evaluators `maximize`, `minimize`, `preferred_range`;
- near-best filtering;
- deterministic weighted selection;
- attempt-local RNG namespace separation;
- no hidden requirement relaxation;
- no candidate snapping to raster centers.

### KEEP existing metric IDs

These existing metrics remain valid:
- `slope_mean`;
- `water_fraction`;
- `elevation_mean`;
- `local_relief`;
- `relative_elevation`;
- `distance_to_water`.

### KEEP IDs, updated upstream meaning in Core 0.2

`moisture_mean`:
- Core 0.1: legacy moisture;
- Core 0.2: accepted C2 effective surface moisture.

`vegetation_density_mean`:
- Core 0.1: legacy vegetation;
- Core 0.2: accepted C3 climate-aware vegetation index.

The metric aggregation formula itself does not change.

## 3. Versioned metric registry

### Core 0.1

Exactly the existing registry:

```text
slope_mean
water_fraction
elevation_mean
local_relief
relative_elevation
moisture_mean
vegetation_density_mean
distance_to_water
```

No additional metric ID is valid for a Core 0.1 plan.

### Core 0.2

Core 0.1 registry plus:

```text
temperature_mean
annual_precipitation_mean
distance_to_potential_drainage
```

Unknown or version-incompatible metric IDs remain explicit placement capability errors.

## 4. temperature_mean

Input:
`SurfaceState.annual_mean_temperature_c`.

Definition:

```text
temperature_mean =
    arithmetic mean of annual_mean_temperature_c
    over the existing candidate footprint cells
```

Unit: °C.

Aggregation is float64.

For Core 0.2 the field is required. Missing/non-finite climate state is an explicit capability error.

P08-A does not recompute lapse rate or climate forcing inside Placement.

## 5. annual_precipitation_mean

Input:
`SurfaceState.annual_precipitation_mm`.

Definition:

```text
annual_precipitation_mean =
    arithmetic mean of annual_precipitation_mm
    over the existing candidate footprint cells
```

Unit: mm/year.

Aggregation is float64.

This metric is intentionally distinct from `moisture_mean`:
- precipitation describes atmospheric annual forcing;
- moisture describes accepted C2 effective surface moisture after climatic demand, local hydrology and slope retention.

Placement recipes may therefore express either climate preference or effective-water-state preference without Core conflating them.

## 6. distance_to_potential_drainage

Input:
`HydrologyState.potential_river_network`.

Meaning:

> geometric proximity to the accepted H09-E terrain-consistent potential drainage scaffold.

It does **not** mean:
- distance to permanent water;
- distance to a perennial stream;
- potable-water access;
- distance to canonical river water depth.

Those semantics remain with `distance_to_water` or future setting/process layers.

### Exact geometry

Let `D(point, network)` be the minimum Euclidean world-space distance from a point to any polyline segment of any centerline in `potential_river_network`.

The site metric uses the circular site footprint itself:

```text
distance_to_potential_drainage =
    max(
        0,
        D(candidate_point, potential_river_network)
        - footprint_radius_km
    )
```

Unit: km.

This gives the exact minimum distance from the circular candidate footprint to the potential drainage centerline geometry.

Why this differs from raster `distance_to_water`:
- canonical water is currently represented by a raster water mask;
- potential drainage already exists as accepted continuous world-space centerline geometry;
- rasterizing the network again would unnecessarily lose accepted geometric precision.

If the potential network has no segments:

```text
distance_to_potential_drainage = +inf
```

The same normal comparison semantics used by `distance_to_water` apply.

## 7. SiteMetricContext

For Core 0.1, runtime context remains semantically equivalent to the existing context.

For Core 0.2 it additionally holds/references:
- annual mean temperature array;
- annual precipitation array;
- accepted potential drainage network.

Attempt-global derived state remains computed once and reused across candidate sites.

No RNG is used by site-metric evaluation.

## 8. Existing recipe compatibility

Existing placement recipes that use only Core 0.1 metrics must produce the same candidate lattice and selection mechanics.

For Core 0.2, their numerical result may legitimately differ from historical Core 0.1 because:
- `moisture_mean` now observes C2;
- `vegetation_density_mean` now observes C3.

That is an upstream semantic change, not a P08-A placement-algorithm change.

P08-A must not silently rewrite recipe metric IDs.

## 9. What P08-A does not add

No:
- biome metric;
- biome labels;
- seasonal temperature/precipitation;
- perennial/seasonal/dry channel metric;
- soil/substrate metric;
- groundwater metric;
- road/accessibility metric;
- coast/ocean metric;
- population/human-geography metric;
- settlement-specific heuristic;
- deferred-to-deferred placement graph;
- interaction between separately placed POIs;
- adaptive candidate lattice.

These remain later or external semantics.

## 10. Automated guardrails

### P01 — Core 0.1 registry identity

Core 0.1 supports exactly the historical eight metric IDs.

### P02 — Core 0.2 registry extension

Core 0.2 supports exactly the historical eight plus:
- `temperature_mean`;
- `annual_precipitation_mean`;
- `distance_to_potential_drainage`.

### P03 — temperature footprint mean

`temperature_mean` equals the float64 arithmetic mean of accepted C1 annual temperature over canonical footprint cells.

### P04 — precipitation footprint mean

`annual_precipitation_mean` equals the float64 arithmetic mean of accepted C1 annual precipitation over canonical footprint cells.

### P05 — potential drainage exact distance

Synthetic world-space fixtures verify point-to-polyline distance and footprint-radius subtraction exactly.

### P06 — empty potential drainage

No potential segments gives `+inf`, with existing requirement/preference non-finite rules preserved.

### P07 — semantic distinction from canonical water

Changing potential drainage geometry while canonical water stays fixed may change only `distance_to_potential_drainage`, not `distance_to_water`.

Conversely, changing canonical water while potential drainage stays fixed may change `distance_to_water` without redefining potential-drainage distance.

### P08 — upstream immutability

Metric evaluation does not mutate Terrain, Hydrology or Surface state.

### P09 — no RNG

Metric evaluation consumes no RNG and is exactly replayable.

### P10 — old placement mechanics unchanged

Candidate lattice, hard filtering, scoring, near-best and weighted selection remain behaviorally identical when supplied the same metric values and recipe.

### P11 — version-incompatible metric rejection

A Core 0.1 recipe requesting any P08-A-only metric fails explicitly; it is not silently ignored or replaced.

## 11. Operator-visible checkpoint P08-A

P08-A changes available spatial observations but does not change default placement behavior by itself.

Representative checkpoint should therefore show:
1. accepted C1 temperature map;
2. accepted C1 precipitation map;
3. accepted potential drainage overlay;
4. a deterministic sample/lattice of candidate points;
5. candidate values for all three new metrics;
6. one diagnostic placement recipe using the new metrics, clearly labeled as a test fixture rather than a production settlement policy;
7. selected diagnostic point and near-best set.

The diagnostic recipe must be simple enough that the selection is interpretable from the maps.

Its thresholds/preferences are test evidence only and do not become hidden Core defaults.

## 12. Acceptance criteria

Implementation may be accepted only if:
- P01–P11 are green;
- full pytest is green;
- Core 0.1 acceptance behavior remains green;
- no upstream arrays/networks change;
- operator-visible P08-A checkpoint is available;
- the new metrics visually/numerically correspond to the accepted upstream fields and potential geometry;
- explicit implementation ACCEPT / REJECT is recorded.

## 13. Stop rules

- Do not modify C1/C2/C3 to make a placement fixture look better.
- Do not reinterpret potential drainage as permanent water.
- Do not add a hidden settlement suitability formula.
- Do not add biome or human-geography semantics in P08-A.
- Do not change candidate lattice or site-selection RNG.
- Do not add adaptive retries or requirement relaxation.
- Do not mutate Hydrology/Surface from Placement.
- If a future setting needs a semantic concept not represented by these physical metrics, add a new explicit layer/metric rather than overloading an existing ID.


## 14. Design acceptance

Operator decision: **ACCEPTED**.

PR #88 merged into `dev/0.2` at:
`66003288e528fc340663d92f84ed14cbee88744b`.

Implementation is authorized only for the bounded metric-registry extension above. Existing candidate generation and site-selection semantics remain frozen for P08-A.


## 15. Implementation acceptance

P08-A implementation was formally ACCEPTED and merged through PR #89.

Merge commit:
`57e77c8de6ac8668ddd09e25167e30aa773cf645`

Accepted checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`

P01–P11 and full pytest were green.

The diagnostic placement recipe remains test-only evidence and is not a production settlement policy.

P08-A is frozen unless later evidence identifies a concrete metric or contract defect.
