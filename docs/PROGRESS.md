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
Hydrology 0.2
└─ H10-A lake shoreline morphology — IMPLEMENTATION
   ├─ river hierarchy frozen
   ├─ diagnostics complete
   │  ├─ 13 routing lakes
   │  ├─ 890 km² total raster lake area
   │  └─ catchment/lake ratios ~5.6...136
   ├─ PR #78 ACCEPTED / merged
   └─ implement refined shorelines + exact lake endpoints
```

PR #72 remains draft/open until the Hydrology lake slice and final review are complete.

## NEXT

```text
1. Implement H10-A shoreline refinement
2. Run automated guards and same-world checkpoint
   ├─ lake count
   ├─ size distribution
   ├─ terrain-following shape
   ├─ catchment ↔ lake size relation
   └─ placement inside drainage hierarchy
3. Hydrology 0.2 final operator review
4. Surface / climate / biome work
5. Later hydro-surface finishing
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
