# P2-B1: fine MFD drainage compared with macro D8 (diagnostics ONLY)

[Product navigation](../../START_HERE.md) · [P2-A child terrain](planetary-child-terrain.md) · [operator evidence](../reviews/p2-b-child-mfd-reference-audit-2026-11-16.md).

The script \`scripts/diagnose_planetary_child_mfd_v02.py\` runs **the accepted Core 0.2** Priority-Flood + Freeman-style MFD fraction solver over P2-A NEW child relief, then uses a source-independent fast accumulation order with tests against the accepted canonical Core accumulator on small grids. It overlays historical A8 D8 macro links in a separate color as a **guide**. It does **not** promise matching global basins, exact hydrologic reality, lake/marine handling or watershed-conditioned rivers. A contour of possible filled depressions >2m is marked **unresolved**, not accepted water.

## How to run against private original sources

Prerequisites: generate the private macro-region with \`export_planetary_macro_region_v02.py\`, then child terrain with \`condition_planetary_child_terrain_v02.py\`. Do not commit the user's ZIP/NPZ or derived maps to public GitHub.

    python scripts/diagnose_planetary_child_mfd_v02.py \
      --child-npz /private/child-A/child-terrain-generated.npz \
      --child-manifest /private/child-A/manifest.json \
      --macro-npz /private/source-A/macro-region-source.npz \
      --threshold-km2 45 \
      --output /private/child-A/mfd-diagnostic

The input must describe an all-land **inland-only** regular square-km raster. A coastal region or H12 lake treatment cannot be silently approximated. Data outputs: \`child-mfd-diagnostic.npz\` with MFD accumulated area, routing elevation, flow angles, preliminary channel threshold mask, virtual fill-depth and unresolved-depression mask; \`manifest.json\` with conservation ledger, major edge outlets by side, old-D8 source link counts, explicit unsupported functionality; and \`child-mfd-comparison.png\`.

[Safe synthetic Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/43805052775) → download \`non-earth-geogrid-synthetic-demo\`, open \`child-mfd/child-mfd-comparison.png\`. The real A/B/C images were generated locally from private source and shown in ChatGPT instead of uploaded.

## What these maps actually prove

- Nonzero source-generated hill-valley textures produce new Core-compatible MFD fractions and internal routing, not simply painted lines from A8.
- Local area sum is conserved at boundary exits. No outside-domain contributing area is supplied, therefore a genuine trunk river is artificially small if its basin enters the crop.
- Source A8 D8 links and new fine MFD may disagree: the diagnostic measures that visual mismatch but does not yet fix it.
- **Filled interior depressions are unresolved:** correct solution needs accepted lake candidates / spill outlets / lake supernodes before declaring permanent rivers or a viable waterfall.
- The \`stream_threshold_km2\` parameter marks **potential channel support**, not a permanent or physically measured river, and no literal forest/biome has been generated.

**Next P2-B2:** implement macro-to-child boundary flow and accepted H12-compatible lake routing, with separately validated forced/soft river corridors only when justified by the source. Retain both original D8 and Core MFD as distinct layers and label their sources.
