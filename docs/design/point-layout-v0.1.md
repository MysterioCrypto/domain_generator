---
id: DESIGN-POINT-LAYOUT-0.1
kind: design
status: accepted
target: core-0.1
---

# Point layout v0.1

This document fixes the first executable `GenerationPlan -> LayoutCandidate` path. It is deliberately limited to generic `layout.mode=geometry`, `shape=point` features. Illustrative content names are non-normative.

## Generation

For each resolved point geometry feature, derive one independent RNG stream:

```text
attempt_index = current attempt
stage = layout
scope = ["feature", feature_id, "geometry", "point"]
purpose = "position"
```

Consume exactly two `uniform01()` values from that stream:

```text
u_x = stream.uniform01()
u_y = stream.uniform01()
x_km = domain.width_km * u_x
y_km = domain.height_km * u_y
```

The resulting `PointGeometry` is therefore inside the half-open physical domain `[0,width) x [0,height)`. Feature iteration order does not affect a feature's stream.

Point layout v0.1 has no layout parameters and performs no hidden retries or constraint-aware steering.

## LayoutCandidate

The stage emits one concrete point in `geometry_realizations` for every supported geometry point feature and uses the semantic `plan_fingerprint` as `source_plan.fingerprint`.

This slice does not materialize reservation features. A plan containing `layout.mode=reservation` is unsupported by this stage until reservation construction is implemented.

Likewise, geometry shapes other than `point` are unsupported rather than silently approximated.

## Layout validation

Generation and validation are separate operations. Validation observes the candidate and never mutates or repairs it.

Engine invariants for this slice:

- candidate `source_plan.fingerprint` equals the semantic fingerprint of the supplied plan;
- candidate `attempt_index` equals the active attempt;
- every point geometry feature appears exactly once;
- no unknown geometry realization IDs exist;
- every realized point is inside or on the domain boundary.

Supported hard constraint measurements in this slice are intentionally narrow:

- `distance`: point-to-point Euclidean distance;
- `distance`: point-to-axis-aligned-rectangle minimum Euclidean distance (zero inside/on boundary);
- `contained_fraction`: point in rectangle -> `1.0`, otherwise `0.0`;
- `overlap_fraction`: point in rectangle -> `1.0`, otherwise `0.0`.

A feature selector resolves only when that feature has point geometry. For a point, `whole` and `center` both resolve to the point itself.

Unsupported evaluator/geometry combinations are engine/pipeline capability errors, not failed user constraints.

## Attempt semantics

A generated point is not regenerated because a hard constraint fails. The validator reports the failed hard constraint and the existing attempt orchestrator rejects the whole attempt immediately.

Therefore this first implementation establishes the complete deterministic path without introducing hidden local search:

```text
GenerationPlan
-> semantic RNG streams
-> point geometry realization
-> LayoutCandidate
-> layout ValidationResult
-> attempt early-pass/reject
```

## Explicitly out of scope

- corridor, band and area generation;
- RegionSet boolean operations;
- placement reservation materialization;
- constraint-aware proposal generation;
- soft-constraint scoring;
- terrain, hydrology, surface and dependent placement.
