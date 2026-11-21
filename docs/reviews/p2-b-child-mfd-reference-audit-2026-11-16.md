# P2-B1: child MFD vs historical A8 D8 — visual and numerical QA

**2026-11-16** · Implementation: [PR #103, DRAFT / UNMERGED](https://github.com/MysterioCrypto/domain_generator/pull/103) · Parent to child accepted **terrain** from P2-A; this is explicitly **diagnostics-only**, not accepted macro-constrained river generation.

## User-visible map checkpoints

1. [GREEN GitHub Actions, safe SYNTHETIC source](https://github.com/MysterioCrypto/domain_generator/actions/runs/43805052775) → artifact \`non-earth-geogrid-synthetic-demo\` → \`child-mfd/child-mfd-comparison.png\`. It shows source-pinned child topography, new Core-style MFD accumulation, and **old** D8 river guide, with unresolved filled depressions flagged. Full NPZ and JSON ledger included; no private literary world source was uploaded.
2. **Private real-source diagnosis** of regions A/B/C: generated locally in the ChatGPT session from user-provided original A8/A12 ZIPs, not committed. Each region 230×230 km with 231×231 samples (model 1 km). Images displayed in chat only. Local research script implemented the published Core 0.2 Priority-Flood/MFD weights and used a **SciPy C2 cubic** DEM interpolant; it is **not the exact repository P2-A C1 Hermite code**, therefore numeric results below are independent screening observations, not strict accepted-Core integration regression.

## Exact accepted routing authority (code path)

- \`scripts/diagnose_planetary_child_mfd_v02.py\` imports unmodified **accepted Core** \`priority_flood_surfaces\` and \`continuous_routing_field\`, creating new strictly draining P2-B child fractions. Its fast descending-elevation accumulation is regression-checked to the canonical Core \`distributed_flow_accumulation_km2\` on synthetic small grids (same fractions, no lakes/marine).
- All positive cell area starts at **1 km² per cell** (or configured spacing²), no incoming flow from outside the domain. Every ordinary cell distributes fractions to downslope receivers, every edge cell is a terminal. The terminal-area ledger requires \`sum(boundary accumulated area) ≈ sum(local source area)\`. This is a CONSERVATION TEST, **not a test of real-world discharge**.
- The separate A8 macro source includes its old **D8** river mask and 1-step receiver links; shown in orange for spatial contrast only. Macro D8 is never used as accepted fine-grid routing, and the new child has NOT been conditioned to it.
- The tool explicitly rejects non-land child masks. No H12 marine, no accepted lakes/lake supernodes, no C1 runoff or source external boundary inflow. It outputs only a **diagnostic** MFD channel-support raster and JSON metadata, not an accepted river network.

## Real A/B/C source evaluation (LOCAL SCREENING ONLY)

| Region | Old A8 river guide links in view | NEW 1-km MFD max local contributing area (km²) | Filled child cells deeper than 2m | Maximum virtual fill (m) | Boundary source-area error (km²) |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 12 | ≈10,265 | 1,220 | ≈12.41 | +4.37×10⁻¹¹ |
| B | 5 | ≈22,429 | 4,781 | ≈88.50 | −7.28×10⁻¹¹ |
| C | 1 | ≈32,593 | 2,738 | ≈60.02 | −1.31×10⁻¹⁰ |

Each local screenshot covers 53,361 model 1-km raster cells. Old A8 source river links are **too sparse and too coarse** to pretend they specify exact fine river centerlines. Much larger B/C filled depressions create fan-like areas of artificial routing under Priority-Flood. This is a **visible substantive fault** for the target satellite-like map. The subsequent fix is not more artistic filters, but correct lake candidates/outlet supernodes and macro-boundary continuity.

The tiny numerical ledger errors (relative ~10⁻¹⁵) validate internal local-source conservation only: a real trunk river may have a large catchment outside this 230-km crop, so **local accumulated areas are not comparable to old A10 global Q or global A8 catchment area**.

## Automated evidence and stop rule

[Dedicated P2-B1 Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/43805052775): **19 focused tests passed**, including exact synthetic replay, accepted-Core fractions and standard full-graph accumulated area equivalence, source-axis remapping, conservation at raster edges, no silent marine handling, and explicit failure to call filled sinks valid lakes. Current full pytest must be verified on the final documentation SHA independently.

**Next P2-B2 (not done):** connect source macro boundary inflow/outflow guidance to child MFD and use accepted lake supernode / spill semantics where warranted; distinguish external basin inflows from locally generated catchment. Validate on source-derived A/B/C; for the first-arc narrative region, only then attempt to position a waterfall and ford as locally plausible geography. No forced roads, city coordinates, biomes or ImageGen in this step.

**Product constraints:** primarily non-Earth, configurable world profile; never silently convert mm/planetary-year to earth mm/year. Private original world arrays and derived PNGs stay out of public GitHub.
