# Additive Terrain-Aware Source Promotion v0.2

Status: **accepted experimental design gate**  
Target branch: `dev/0.2`  
Operator decision: keep H09-C fixed-area initiation as the baseline and let terrain awareness only promote additional steep/convergent headwaters. The first H09-D multiplicative replacement is rejected.

## 1. Why this amendment exists

The first H09-D criterion replaced the H09-C source rule with:

```text
score = unique_area * (slope / 0.05)
source ⇔ score >= stream_threshold
         AND convergence > 1
```

On the representative 1 km raster this suppressed every ordinary source:

```text
max score:        146.93 km²
threshold:        250 km²
ordinary sources: 0
```

The failure was calibration/scale mismatch, not a reason to discard MFD, the dominant skeleton, or terrain-aware promotion.

## 2. Accepted semantic correction

Terrain awareness becomes **additive**, never subtractive.

Normal source eligibility is:

```text
base =
    unique_area >= stream_threshold_km2

promotion =
    unique_area < stream_threshold_km2
    AND convergence > 1 + epsilon
    AND local_slope > S_ref
    AND unique_area * (local_slope / S_ref)^alpha >= stream_threshold_km2

eligible = base OR promotion
```

Consequences:

- every H09-C fixed-area branch remains eligible;
- terrain-aware logic can only start a branch farther upstream / add a headwater branch;
- convergence and slope gates apply only to promoted sub-threshold sources;
- large low-gradient basins are not deleted.

## 3. Fixed experimental calibration

For one bounded same-world experiment:

```text
S_ref = 0.020
alpha = 1.65
```

These are internal experimental constants, not request parameters.

This calibration was selected from the diagnostic sweep because it produced a moderate expansion rather than H09-B-style over-density:

```text
diagnostic prediction:
  ~16 sources
  ~6 confluences
  ~610 skeleton cells
```

Those counts are not acceptance targets. They only establish that the chosen point is bounded enough to justify a visual checkpoint.

## 4. What remains unchanged

Keep:

- Terrain 0.2;
- Priority-Flood conditioning;
- MFD p=1.1 contributing area;
- MFD continuous vector field;
- raw MFD support diagnostic;
- dominant one-downstream channel projection;
- unique dominant-graph area;
- one-cell-wide merge-only skeleton;
- accepted lake supernodes and one outlet each;
- continuous world-space river tracing;
- no post-smoothing.

## 5. Activation semantics

Use the existing topological activation propagation.

For each dominant-graph cell in stable topological order:

1. if an upstream active channel already reaches the cell, continue the channel and do not create another source;
2. otherwise, if `base OR promotion` is true, create one source and activate downstream propagation;
3. lake outlets remain independent active starts.

Thus a score fluctuation downstream cannot restart an already active branch.

## 6. Diagnostics H09-D2

Use the same representative world:

```text
180 × 120 km
seed 2026091402
cell size 1 km
stream threshold 250 km²
same Terrain 0.2
same MFD p=1.1
```

Required views:

1. terrain + final rivers;
2. MFD accumulation + final rivers;
3. raw support vs thin skeleton;
4. local slope + selected sources;
5. MFD convergence + selected sources;
6. source eligibility diagnostic distinguishing:
   - baseline fixed-area eligible cells;
   - terrain-promoted cells;
   - selected semantic source nodes.

Compare directly against H09-C and the rejected first H09-D.

## 7. Automated guardrails

### P01 — baseline preservation

A cell with `unique_area >= threshold` remains eligible even on gentle or non-convergent terrain.

### P02 — promotion requires all gates

A sub-threshold cell is promoted only if:
- convergence passes;
- slope is above `S_ref`;
- area–slope score reaches threshold.

### P03 — steep convergent promotion

A synthetic steep/convergent sub-threshold headwater can become eligible under the fixed H09-D2 constants.

### P04 — no downstream restart

Existing topological activation still prevents additional sources downstream of an active source.

### P05 — merge-only topology / lake continuity

Existing skeleton and lake invariants remain green.

Automated guards are necessary but not operator acceptance.

## 8. Stop rules

If H09-D2 becomes over-dense or returns parallel duplicate rivers:
- do not add pruning in the same iteration;
- reject the calibration/promotion rule and inspect initiation semantics.

If H09-D2 is still too sparse:
- next question is branch-scale valley detection or another explicitly designed calibration gate.

If source locations look topographically wrong:
- inspect slope/convergence diagnostics before changing threshold.

If topology looks acceptable but final vector traces diverge from skeleton/accumulation:
- treat tracing consistency as a separate defect.

## 9. Acceptance

Only explicit operator review of H09-D2 can accept or reject this hydrology slice.

Surface and Placement remain blocked.
