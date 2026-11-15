# Planetary macro-geogrid source adapter (non-Earth)

**Status:** experimental external adapter, [draft PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103). It does NOT modify the accepted Core 0.2 runtime or automatically turn old D8 rivers into Core MFD.

## Why this exists

The original user-supplied planet archives are available privately in Google Drive: [A8](https://drive.google.com/file/d/1WvMG9A2kmwBKBvaSTOY0XERElmka6r1s/view), [A10](https://drive.google.com/file/d/1C0bklcAIRmlWSHoYIVONuyse_63xBMkH/view), and [A12](https://drive.google.com/file/d/1uPTSaGcynBnsWKF0Mfn-Ykw_0ko3a1mF/view).

A8 rows are north-to-south; A10/A12 rows are south-to-north. Elevations and land match EXACTLY only after reversing A8 latitude. A8 downstream targets are GLOBAL flattened D8 indices and must be remapped on cropping. Out-of-crop links remain recorded; they are not newly declared physical river sinks.

## Command (locally; user downloads the ZIPs)

Install the repository dependencies with pip install -e ".[dev,render]".

    python scripts/export_planetary_macro_region_v02.py \
      --a8 /private/planet_A8_prototype.zip \
      --a10 /private/planet_A10_prototype.zip \
      --a12 /private/planet_A12_prototype.zip \
      --lat -46.95 --lon -97.95 \
      --half-width-km 480 --half-height-km 390 \
      --planet-radius-km 7008.1 \
      --planet-year-earth-days 202.755 \
      --output /private/output-dakhar-A

These radius/year and geographic values come from an unaccepted WORKING literary planet MODEL. They are not Earth defaults and not author-approved city or waterfall locations. Optional expected SHA-256 arguments are supported.

Outputs: macro-region-source.npz (north-first source rasters and both global/local D8 targets), manifest.json (provenance, grid and exits), macro-region-preview.png (terrain, A8 D8 catchments, A12 MODEL ecological classes).

**This is still original 0.3-degree source resolution.** Cropping or interpolating pixels does not produce physically resolved 1km terrain, small valleys, a waterfall, roads or a bridge.

## CI and provenance

[Dedicated GREEN Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/43742308913): four source-remapping/axis/calendar tests and a complete synthetic ZIP export with diagnostic PNG. The Action uploads only a synthetic toy planet, not private Drive ZIPs or derived maps.

All A8/A10/A11/A12 real ZIPs independently passed SHA-256/ZIP CRC checks; A10 annual Q equals A12-input copied Q exactly (NOT independent hydrologic validation). [Source report](../reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md).

## Next physical boundary (NOT implemented yet)

Develop a controlled parent/child **regional terrain conditioning** adapter. Preserve source macro coast/height/watershed relationships while letting accepted Core MFD generate a finer drainage network. Record origin, local map projection, finite source 0.3-degree resolution and uncertain local detail. Never auto-import A12 ecology as universal Earth biomes; use an explicit per-world profile. Keep DataSpec and old model canon statuses distinct. Original ZIPs and derived crops remain private unless the user explicitly approves publication.


## Downstream P2-A: modeled 1-km child terrain

[External conditioning method and CLI](planetary-child-terrain.md) produces finer 1-km generated DEM from the macro source, preserving exact parent station elevations, planet time/radius and coastal mask. It is a separate output from the old macro NPZ; do not confuse its new detail with sourced global geology or a validated child MFD river network.
