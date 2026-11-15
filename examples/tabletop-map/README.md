# Tabletop atlas from an editable DomainSpec

This example is an end-to-end, parameter-driven map for tabletop RPGs and literary worlds. **It does not change the generator.** It uses existing versioned spec contracts, terrain and hydrology, and the already-implemented dependent POI placement workflow.

## Editing the world, not post-processing the render

Edit `domain-request.json`:

- `domain_spec.surface.water_moisture_decay_km` is a **real positive floating-point DomainSpec field**. This example chooses `4.0` km for a wider, smoother transition from lakes and rivers; other worlds can keep `2.0` or select any validated value. `water_moisture_boost` remains `0.55`. No universal default was modified.
- `domain_spec.features` declares a fixed list of desired features, each with stable `id`, optional `label`, optional `tags`, and a `preset` reference. Here the author explicitly requests one terrain ridge and three named settlements.
- `domain_spec.constraints` specifies hard geographic placement envelopes for the settlements (west, east, south). Existing `a08_settlement` preset then chooses a suitable point using accepted dependent-placement mechanics, including suitability requirements and preferences. This is **semi-procedural**: the settlement identity and broad placement rules are authored, the precise position is generated.
- `presets.json` is separately versioned content; this example reuses the A08 preset catalog. A preset's fixed or ranged parameter recipes, effect operator and SiteProfile remain separate from user feature metadata.
- **Exact manual pinning:** the existing selectors include literal points/regions and the `near` relation, but this example does *not* claim a general exact-coordinate lock for dependent POIs. Reproducible generated placement under constraints is implemented; unconstrained manual dragging/pinning in a map editor is not part of this renderer.

Input semantics are preserved: changing `label` should change printed presentation text, not the placement RNG; changing `id`, preset, parameters, hard constraints or root seed may change realization.

## Generate the atlas

From the repository root, after installing the project with rendering dependencies:

```bash
python -m pip install -e ".[dev,render]"
python scripts/render_tabletop_domain_map_v02.py \
  --request examples/tabletop-map/domain-request.json \
  --presets tests/acceptance/cases/a08-core-v02-integrated/presets.json \
  --pixels-per-km 24 \
  --output output/tabletop-atlas
```

You can pass any compatible existing Core 0.2 generation request with `--request` and its matching preset catalog with `--presets`. The renderer does not invent a new user input contract or silently replace the water-moisture setting.

## What the map compositor writes

All six transparent/opaque layers use **identical dimensions and world alignment** and can be imported as layers in an image editor or later into an illustration pipeline:

| File | Purpose |
| --- | --- |
| `01-terrain.png` | Opaque continuous relief + vegetation/moisture palette, no categorical biomes |
| `10-relief-contours.png` | Transparent height contours from accepted elevation; display-only interval |
| `02-water.png` | Transparent water, **marine mask and real lake polygon geometry only** |
| `03-rivers.png` | Transparent accepted vector river centerlines, not blue 1-km raster stripes |
| `04-poi-markers.png` | Transparent POI symbols at accepted coordinates |
| `05-labels.png` | Transparent authored POI names, collision-adjusted **labels only** |
| `06-map-full.png` | Combined full-color map |
| `07-map-no-labels.png` | Clean map for subsequent artist-directed layout |
| `08-atlas-preview.png` | Framed titled map with scale bar and north marker |
| `09-parchment-palette.png` | Alternative color treatment, unchanged geometry |
| `11-parchment-no-labels.png` | Art-ready parchment map without text; overlay canonical labels afterward |
| `12-stylization-brief.txt` | Optional art-direction brief fixing coastlines, rivers, lakes and POI coordinates |
| `manifest.json` | Pixel/km mapping, source SHA-256, settlements/coordinates, source parameter values, layer order and limitations |

In the current sample the output raster is 1536×1152 px, representing 64×48 km. The renderer uses the accepted DomainData fields and vector geometries: it never changes any authoritative elevation, waterways, settlements or climate values. The colors are *continuous artistic greenness*, not a biome classification.

## CI and operator visual checkpoint

- Draft implementation: [PR #101](https://github.com/MysterioCrypto/domain_generator/pull/101).
- [GitHub Actions — tabletop atlas, settlement labels and aligned layers](https://github.com/MysterioCrypto/domain_generator/actions/runs/43732653717).
- Download artifact `tabletop-atlas-v02` and open `08-atlas-preview.png`, then `06-map-full.png`, `07-map-no-labels.png` and individual layers.

Regression checks assert all three named settlements are present and each layer is aligned, correctly typed and non-empty. The script itself can be reused with a different DomainSpec; this example is not a special hardcoded universe.

### Product boundary

The goal is an expressive, approximately plausible and parameter-controllable **map**, not a scientific climate model. More physically detailed rainfall, hydrology or ecology belongs in a new separately justified stage only if it materially improves maps. Exact manual settlement pinning, roads, political boundaries, automated settlement naming and artist-quality forest/mountain symbols are not yet implemented. They should be product-facing additions rather than disguised assumptions inside the renderer.


### Improved atlas readability and optional image stylization (2026-11-15)

The latest draft renderer strengthens accepted terrain relief, draws subdued height contours, enlarges readable label plaques, gives a `fort`-tagged POI a square fort symbol and a `village`-tagged POI a circular village symbol, and shows a matching legend. These symbols encode **only explicit input tags**; no settlement classification or new world simulation is implied.

For an illustrated version, use `11-parchment-no-labels.png` as a **visual reference** and `12-stylization-brief.txt` as instructions. Give any image generator the author's intention to preserve geography, but assume it may distort rivers, lakes, labels or settlements. Use aligned `02-water.png`, `03-rivers.png`, `04-poi-markers.png` and `05-labels.png` as authoritative overlays in the final composite. This avoids asking generative illustration to act as a precise GIS editor.

The current visual version remains in [draft PR #101](https://github.com/MysterioCrypto/domain_generator/pull/101). It is not a new accepted default. The DomainSpec still controls moisture decay, object identity, hard regions and suitability presets; presentation does not affect generated coordinates or hydraulic fields.
