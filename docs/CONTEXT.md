# Rolling Context / Backlog

Этот файл — сжатая рабочая память проекта, а не журнал событий.

## Текущая опорная точка

```text
active:
  dev/0.2
  Terrain 0.2: ACCEPTED
  Hydrology 0.2: redesign in progress

kept river base:
  Priority-Flood
  MFD p=1.1 contributing area
  continuous MFD vector field
  dominant one-downstream skeleton
  H09-D2 additive source promotion
  lake supernodes / one canonical outlet

latest accepted direction:
  H09-D2 regional network = KEEP, not final Hydrology ACCEPT
  next = H09-E multiscale potential drainage hierarchy
```

`main` не является active development truth.

## Rejected / constrained history

- D8 canonical routing: rejected for lattice imprint.
- Two-receiver D∞ accumulation: rejected; grid bias remained in accumulation.
- Direct broad MFD threshold-mask channelization: rejected; 353 sources / 408 segments.
- H09-C thin skeleton: coherent but too sparse as sole drainage view.
- First H09-D multiplicative area-slope replacement: rejected; removed all normal headwaters.

These failures constrain the next work: do not reopen MFD, do not return to broad support as semantic channels, and do not replace the fixed-area baseline with a slope multiplier.

## H09-D2 regional base

Accepted design:
`docs/design/additive-terrain-aware-source-promotion-v0.2.md`

Same-world checkpoint:

```text
sources / semantic confluences: 16 / 4
segments:                        33
skeleton cells:                  610
river length:                    ~648.75 km
final grid-lock within 1°:       9.08%
baseline eligible cells:         283
terrain-promoted cells:          37
```

Automated state was green. Operator did not freeze Hydrology because the cumulative layout still looked somewhat procedural / under-branched, and exact sufficiency is better judged against real DEM + hydrography than fantasy map conventions.

Interpretation: H09-D2 is a good **regional river baseline**, but Hydrology should expose a denser potential drainage scaffold before climate/biomes decide what is perennial, seasonal, dry, or cartographically omitted.

## Accepted H09-E design

`docs/design/multiscale-drainage-hierarchy-v0.2.md`

Two nested scales:

```text
regional:
  current H09-D2 semantics, threshold T

potential:
  T_potential = 0.40 * T
  potential eligibility =
      unique_area >= T_potential
      OR regional eligibility
```

Potential channels use the same dominant one-downstream graph and continuous tracing. No new broad MFD semantic mask.

Compute Strahler order on the potential skeleton:

```text
headwater = order 1
equal-order merge m+m -> m+1
unequal merge -> max order
```

Lakes are transparent hierarchy supernodes: inflow orders aggregate through the accepted lake and continue at its one canonical outlet; no channel cells are drawn through lake interiors.

## Runtime boundary for H09-E

No public DomainData contract change yet.

Internal HydrologyState should gain:

```text
potential_channel_skeleton_mask
channel_strahler_order
potential_river_network
potential_segment_strahler_order
```

Current `river_network`, `stream_mask`, and water-depth semantics remain H09-D2 regional semantics. Potential hierarchy is a scaffold for later climate/biome classification and operator diagnostics.

## H09-E operator checkpoint

Exact same world:

```text
180 × 120 km
seed 2026091402
cell 1 km
regional threshold 250 km²
potential threshold 100 km²
same Terrain 0.2
same MFD
same accepted lakes
```

Need show:
1. regional H09-D2 rivers;
2. full potential drainage hierarchy;
3. regional over potential;
4. Strahler-order skeleton diagnostic;
5. accumulation + potential hierarchy;
6. regional/potential counts, lengths, order histogram, max order, grid-lock and regional coverage.

Primary acceptance question: does the potential network read as a plausible dendritic hierarchy without returning to H09-B parallel noise?

## Next

```text
1. Implement H09-E internal potential skeleton + Strahler hierarchy.
2. Preserve regional network/water depth unchanged.
3. Add M01–M06 guards.
4. Render same-world H09-E.
5. Operator ACCEPT / REJECT.
6. If hierarchy is acceptable, freeze river hierarchy and do the separate bounded lake pass.
7. Surface / Placement remain blocked until Hydrology ACCEPT.
```
