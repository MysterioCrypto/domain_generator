# Terrain-Aware Channel Initiation v0.2

Status: **accepted experimental design gate**  
Target branch: `dev/0.2`  
Operator decision: H09-C thin skeleton concept is useful, but the resulting network is too sparse; improve source initiation without reopening MFD transport or reverting to broad support channelization.

## 1. Problem

H09-C solved the H09-B over-fragmentation failure:

```text
H09-B direct MFD support:
  353 sources
  42 confluences
  408 segments
  ~3320 km rivers

H09-C thin dominant skeleton:
  14 sources
  3 confluences
  30 segments
  ~533 km rivers
```

The new network is coherent and far less redundant, but it may have over-corrected into an overly sparse drainage network.

Current source initiation uses one fixed contributing-area threshold on the unique dominant channel graph:

```text
channel_area >= stream_threshold_km2
```

This treats steep convergent headwater terrain and gentle planar terrain the same.

## 2. Geomorphic basis

Field studies of channel heads support an inverse relationship between contributing drainage area and local slope: steeper channel heads can occur at smaller source areas.

References used for this bounded experiment:

- Montgomery & Dietrich (1988), *Where do channels begin?*, Nature 336:232–234.
- Montgomery & Dietrich (1989), *Source areas, drainage density, and channel initiation*, Water Resources Research 25(8):1907–1918.
- Montgomery & Dietrich (1992), *Channel initiation and the problem of landscape scale*, Science 255:826–830.
- Later reviews summarize a common threshold form `A S^α >= C` and note that channel heads typically occur in topographic concavities/convergent flow zones.

This Core experiment does not claim a universal calibrated physical law. It uses the area–slope relation as a deterministic, setting-agnostic topographic heuristic for deciding where the thin semantic channel network begins.

## 3. Scope

Keep unchanged:

- Terrain 0.2;
- Priority-Flood conditioning;
- MFD p=1.1 transport and canonical `flow_accumulation_km2`;
- raw MFD threshold support as diagnostic;
- dominant one-downstream channel projection;
- one-cell-wide merge-only skeleton topology;
- lake supernodes and one canonical spill outlet;
- continuous world-space river tracing.

Replace only normal source initiation.

Do not add pruning, random source jitter, decorative smoothing, or a new public request parameter in this batch.

## 4. Unique channel area remains authoritative for source counting

For initiation, use the unique contributing area already computed on the dominant channel graph:

```text
A = channel_area_km2
```

Do not use raw MFD contributing area for source eligibility because neighbouring MFD cells may contain overlapping fractional catchment.

Final RiverSegment catchment magnitude remains canonical MFD contributing area.

## 5. Local slope

Compute local terrain gradient from the conditioned routing surface using deterministic central differences in world units.

For interior cells:

```text
dz/dx = (z_east - z_west) / (2 * cell_size_m)
dz/dy = (z_north - z_south) / (2 * cell_size_m)

S = hypot(dz/dx, dz/dy)
```

One-sided differences are used at domain edges.

`S` is dimensionless rise/run.

The routing surface is used rather than artistic/presentation terrain because hydrology must base initiation on the same conditioned topography used for downstream routing.

## 6. Flow convergence

Use the MFD field itself to measure local convergence without adding a second smoothed raster model.

For a cell `c`:

```text
incoming_fraction(c)
  = Σ fraction(neighbour → c)
```

Interpretation:

- approximately 1 on uniform planar transport;
- >1 where neighbouring flow vectors converge;
- <1 on divergent ridges.

Define:

```text
convergent(c) ⇔ incoming_fraction(c) > 1 + ε
```

with a small numerical epsilon only for floating-point stability.

This is an eligibility gate, not another tunable multiplier.

## 7. Area–slope initiation score

Use a fixed Core 0.2 experimental relation:

```text
score_km2 = A * (S / S_ref)^α

S_ref = 0.05
α = 1.0
```

Normal source initiation criterion:

```text
score_km2 >= stream_threshold_km2
AND
convergent(cell)
```

Interpretation at the existing `stream_threshold_km2 = 250`:

- at 5% slope, the old 250 km² scale is unchanged;
- at 10% slope, about 125 km² unique area can initiate;
- at 20% slope, about 62.5 km² can initiate;
- at 2% slope, about 625 km² is required.

`S_ref` and `α` are fixed internal semantics for this experiment, not user-facing tuning knobs.

A very small slope floor is used only to avoid numerical division/zero score; it must not make flat terrain easier to channelize.

## 8. Source propagation on the dominant graph

Because the area–slope score is not monotonic downstream, a naive threshold-crossing mask could create repeated source restarts.

Instead, source activation propagates downstream on the dominant graph.

Process cells in topological order:

1. if any dominant upstream channel is already active, this cell is active and is **not** a new source;
2. otherwise, if the local initiation criterion passes, activate the channel and mark this cell as a source;
3. otherwise remain inactive.

Once active, a channel remains active downstream until it enters an accepted lake or exits the domain.

At confluences, multiple active upstream branches merge normally.

Lake outlets are active starts independent of the normal headwater criterion.

This preserves one-dimensional merge-only topology while allowing more steep/convergent headwaters.

## 9. Skeleton semantics

The final skeleton is the union of downstream paths from:

- terrain-aware normal sources;
- accepted lake outlets.

Required:

- one-cell wide by construction;
- no ordinary downstream bifurcation;
- confluences require at least two active upstream branches;
- no ordinary interior dead end;
- no skeleton inside accepted lakes;
- deterministic replay.

## 10. Diagnostics H09-D

Use the exact same representative world:

```text
180 × 120 km
seed 2026091402
cell size 1 km
stream_threshold_km2 = 250
same Terrain 0.2
same MFD p=1.1
```

Add operator diagnostics:

1. terrain + final rivers;
2. MFD accumulation + final rivers;
3. raw support vs thin skeleton;
4. local slope field;
5. MFD convergence field;
6. channel-initiation score with selected source points.

The operator must be able to inspect **why** each source exists.

## 11. Automated guards

Guardrails only; not acceptance.

### I01 — slope sensitivity

Two otherwise comparable synthetic source areas with equal unique area but different slope:
- steep convergent branch may initiate;
- gentle branch below its effective threshold may not.

### I02 — convergence eligibility

A planar/divergent location cannot become a normal source solely because area–slope score is high.

### I03 — no repeated restart

Along one dominant branch, once an upstream source activates the channel, downstream score fluctuations cannot create additional sources.

### I04 — merge-only topology

Active branches may merge but ordinary downstream bifurcation remains impossible.

### I05 — lake outlet continuity

Lake outlets remain active starts and preserve one canonical spill route.

## 12. Operator acceptance

Compare:

```text
H09-B — too many parallel/redundant rivers
H09-C — coherent but probably too sparse
H09-D — terrain-aware source initiation
```

Primary questions:

- Are steep/convergent headwaters restored where terrain suggests tributaries?
- Does the network remain much less fragmented than H09-B?
- Do new sources visually sit in plausible valleys rather than planar slopes/ridges?
- Are parallel duplicate rivers still suppressed?
- Are short tributaries plausible rather than computational fragments?
- Does final geometry still follow the MFD accumulation corridors?

Only explicit operator `ACCEPT` advances Hydrology 0.2.

## 13. Stop rules

If H09-D returns toward H09-B over-density:
- do not hide it with branch pruning in the same iteration;
- first inspect slope/convergence initiation logic.

If H09-D remains too sparse:
- next bounded question is source threshold calibration or branch-scale valley detection.

If sources appear on wrong terrain:
- fix slope/convergence semantics before touching stream threshold.

If final river geometry disagrees with the thin skeleton or accumulation corridor:
- fix trace/skeleton consistency separately.

## 14. Compatibility

- no public schema change;
- no DomainData / DomainBundle contract change;
- no Surface / Placement work;
- MFD accumulation remains canonical diagnostic;
- exact replay remains required within exact generator version.
