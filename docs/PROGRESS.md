# Project Progress Tree

Purpose: a compact, human-readable project state for handoff between chats.

This file answers only:

```text
what is DONE?
what is IN PROGRESS?
what is NEXT?
```

For reasoning and rejected-path constraints read `docs/CONTEXT.md`. For normative semantics read the accepted design docs.

## DONE

```text
Core 0.1 infrastructure
├─ contracts / compiler
├─ deterministic semantic RNG
├─ attempts / ranking / validation
├─ DomainData / DomainBundle
├─ CLI / application boundary
├─ Codex + GitHub remote generation
└─ exact replay

Core 0.2
├─ Terrain 0.2 — ACCEPTED
├─ Hydrology foundations kept
│  ├─ Priority Flood
│  ├─ MFD p=1.1 contributing area
│  ├─ continuous MFD vector field
│  ├─ lake supernodes
│  └─ one canonical lake outlet
├─ H09-D2 regional river network — KEEP
├─ H09-E potential hierarchy — ACCEPTED
   ├─ 0.40 × regional extraction scale
   ├─ potential drainage scaffold
   ├─ Strahler hierarchy
   ├─ continuous vector geometry
   └─ false-confluence normalization
```

Rejected paths that must not silently return:

```text
D8 canonical routing
two-receiver D∞ accumulation
direct broad MFD support as semantic river network
H09-C as sole sparse network
multiplicative H09-D rule that deletes fixed-area baseline
renderer/smoothing as an upstream-fix substitute
```

## IN PROGRESS

```text
Surface / climate / biome 0.2
├─ C1 annual climate forcing — ACCEPTED
└─ C2 effective surface moisture — IMPLEMENTATION
   ├─ C1 climate frozen / ACCEPTED
   ├─ PR #82 ACCEPTED / merged
   ├─ effective moisture core — IMPLEMENTED
   ├─ PR #83 opened
   ├─ M01–M10 guardrails — IMPLEMENTED
   └─ CI stabilization / C2-A diagnostics — IN PROGRESS
   ├─ Hydrology 0.2 merged / frozen
   ├─ Surface 0.1 baseline inspected
   ├─ PR #80 ACCEPTED / merged
   ├─ climate contracts / compiler boundary — IMPLEMENTED
   ├─ temperature + precipitation fields — IMPLEMENTED
   ├─ climate DomainData export — IMPLEMENTED
   ├─ C01–C09 climate guardrails — IMPLEMENTED
   ├─ v0.2 fixture compatibility — IMPLEMENTED
   ├─ schema snapshots — UPDATED
   ├─ C1-A renderer/workflow — IMPLEMENTED
   ├─ push + PR pytest — GREEN
   ├─ C1-A workflow — GREEN
   └─ PR #81 ACCEPTED / merged

Hydrology 0.2 — ACCEPTED
├─ H10-A shoreline refinement — KEEP
└─ H10-B nested depression hierarchy — COMPLETE
   ├─ river hierarchy frozen
   ├─ diagnostics complete
   │  ├─ 13 routing lakes
   │  ├─ 890 km² total raster lake area
   │  └─ catchment/lake ratios ~5.6...136
   ├─ PR #78 ACCEPTED / merged
   ├─ refined sub-cell shoreline reconstruction — IMPLEMENTED
   ├─ exact lake inflow/outlet shoreline alignment — IMPLEMENTED
   ├─ L01/L03/L05/L06/L08 guards — IMPLEMENTED
   ├─ H10-A visual diagnostics — IMPLEMENTED
   ├─ CI + same-world checkpoint — GREEN
   └─ not final lake solution

H10-B
   ├─ design PR #79 ACCEPTED / merged
   ├─ hierarchy core + diagnostics — GREEN
   ├─ all 13 lakes: single-basin hierarchy
   ├─ nested-split hypothesis — REJECTED by evidence
   └─ production nested/partial-fill semantics — DO NOT IMPLEMENT
```

PR #72 is approved for merge into dev/0.2 after formal Hydrology ACCEPT.

## NEXT

```text
1. Implement C2 effective moisture
2. Add M01–M10 guardrails
3. Generate C2-A diagnostics / operator checkpoint
4. Only then design C3 vegetation / biome readiness
4. Later hydro-surface finishing
   ├─ low-order headwater-root visibility
   ├─ perennial / seasonal / dry classification
   ├─ estuary / delta / fan only when receiver semantics justify it
   └─ cartographic endpoint treatment
6. Placement continuation
```

River hierarchy is frozen. Reopen it only for a new concrete defect, not while tuning lakes.

## Acceptance boundary

```text
automated green
+
operator-visible checkpoint
+
explicit operator ACCEPT
=
accepted spatial semantic layer
```


## CURRENT DECISION GATE

```text
Terrain 0.2                   ACCEPTED
Hydrology 0.2                 ACCEPTED
C1 annual climate forcing     ACCEPTED
next                          C2 effective moisture design
```

Deferred to climate/surface/biomes:
- perennial vs seasonal low-order drainage;
- standing lake vs wetland/playa/dry basin classification;
- headwater visual roots;
- delta/estuary/fan endpoint morphology.
