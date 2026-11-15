# Tabletop atlas art-direction proof — visual operator checkpoint

**Date:** 2026-11-15. **Status:** visual proof GREEN; draft implementation, not merge-accepted.

**Visual artifact:** [GitHub Actions — three art directions for the same map](https://github.com/MysterioCrypto/domain_generator/actions/runs/43735383533). Download `tabletop-art-direction-v02` and open `07-three-style-comparison.png`. Full styles: `01-watercolour-map.png`, `02-engraving-map.png`, `03-illuminated-map.png`; matching framed previews `04-watercolour-framed.png`, `05-engraving-framed.png`, `06-illuminated-framed.png`. The same run also contains the canonical `tabletop-atlas-v02` with unstyled source layers.

## Hypothesis and boundaries

The author wants an expressive, roughly plausible, user-controllable fantasy map for tabletop or fiction and may later pass it to ImageGen. Before doing so, verify that alternate artistic styles can be produced without losing **accepted coast/lake, river, settlement or label geometries**. This test is a deterministic composition exercise rather than a test of a generative art model.

- Source of truth: `examples/tabletop-map/domain-request.json` plus already generated Core 0.2 `DomainData`. The existing atlas compositor exports 1536×1152 source/transparent overlays with a manifest.
- Styles intentionally edit the **terrain RGB** only; original `10-relief-contours.png`, `02-water.png`, `03-rivers.png`, `04-poi-markers.png` and `05-labels.png` are composited unchanged and checked against SHA-256 digests.
- Any rendered restyling is visually distinct from actual physical world generation. No new terrain elevations, rivers, roads, lakes, vegetation ecology, inhabitants or political boundaries were inferred.
- Deterministic paper textures are seeded from the source request hash, so image variants are reproducible for an identical request and script version.
- An overly dense initial engraving hatch was corrected to affect areas of strong existing relief-gradient contrast rather than all uniformly dark lowlands. This is an aesthetics-only fix.

## QA evidence and outcome

[Run https://github.com/MysterioCrypto/domain_generator/actions/runs/43735383533](https://github.com/MysterioCrypto/domain_generator/actions/runs/43735383533) is **GREEN** on implementation/test SHA `21a9375a7523d85bd4b27bcb731a1fffd62cc661`. Checkpoint successfully generated and uploaded both artifacts, passed 54 existing placement/DomainSpec tests, verified all three original named settlement coordinates and accepted label placement, verified six aligned map layers and intact PNG alpha, and passed art-overlay SHA checks plus output size/source-manifest comparisons. The unmodified overlays guarantee the source geographic layer coordinates are unchanged by this script.

These checks do **not** prove that an independent image generator would respect exact topological/label constraints. A later ImageGen stylization should operate preferably on a clean unlabeled map or terrain-only art layer and restore accepted `02-water.png`, `03-rivers.png`, `04-poi-markers.png`, `05-labels.png` afterward, comparing any shifted mountain/coast silhouettes with the originals.

## Decision / stop rule

No global science recalibration or C2 parameter sweep is warranted by this successful artistic test. Stop at three styles; the product-facing next step, if desired, is a controlled **actual image-illustration experiment** with layer re-composition and visual comparison, or usability improvements for authoring/previewing DomainSpec. Do not merge draft PR #101, unrelated #99 or #100 solely for CI GREEN. Frozen `release/0.2-prealpha` unchanged.
