# D’Акхар: A8 ↔ A12 source integrity and geographic alignment audit

**Date:** 2026-11-15. **Scope:** source data read-only, not a new simulation; all planet geography remains WORKING MODEL / NOT CANON.

## Sources directly inspected (private Google Drive, do not upload raws into public GitHub)

- [A8 prototype.zip](https://drive.google.com/file/d/1WvMG9A2kmwBKBvaSTOY0XERElmka6r1s/view): 15,903,858 bytes; SHA-256 = **6824ccf2a4aea7b2514a4e694e84ad13fd3ff4e18dba6c3be6b4b7753dc019ec**, exactly matches archive README.
- [A12 full.zip](https://drive.google.com/file/d/1uPTSaGcynBnsWKF0Mfn-Ykw_0ko3a1mF/view): 48,280,825 bytes; SHA-256 = **db9f0f91fca845058c658dfdd639c882b9cf0514736b3677184a4c84ff20b3a4**, matches README.
- A12 embedded **A12_inputs.npz** SHA-256 = **f2d6c4463f969938c89290d8004f9e9b21570c01d664b3862f2bc2765b62fe7c**, equals A12_report.json.
- A10, A11 ZIPs exist, but were **not separately unpacked/verified** in this audit. A12_inputs.npz is the snapshot included by A12, not the same as having independently checked A10 and A11.

## Binary field inventories

A8 ZIP includes A8_hydrology.npz and A5_geodata_input.npz. A8_hydrology arrays include lat/lon, elevation, land, virtual-filled DEM and depression, downstream_index, catchment_area_km2, coastal_root_index, river_mask/major river mask, major outlet basins. Grid: **600 rows × 1200 columns**. A8 has no climate-derived discharge field in this NPZ.

A12 ZIP includes A12_biome_fields.npz, A12_inputs.npz and readable report/code. A12 fields: elevation/land, temperature_annual_C, warmest month, precipitation **mm/planetary year**, potential evapotranspiration, four scenario biome codes/stability/wetland candidates. Inputs include 12 monthly temperature/precipitation snapshots and **annual_Q_m3s** from an earlier A10 model. Grid also 600×1200; longitudes identical.

## CRITICAL integration constraint: opposite lat axis order

| Quantity | A8 | A12 |
| --- | --- | --- |
| lat[0] / lat[-1] | +89.85° / −89.85° (north first) | −89.85° / +89.85° (south first) |
| lon order | −179.85 → +179.85 | same exact |
| elevation grid orientation | north-first rows | south-first rows |
| exact equality | elevation_A8[::-1,:] == elevation_A12 | **true** |
| exact equality | land_A8[::-1,:] == land_A12 | **true** |

**Do NOT join A8 catchment/downstream river fields to A12 climate/cover fields row-for-row.** Reorient A8 by latitude before any overlay. For a graph with flattened A8 downstream indices, remap both source row and receiver row indices, not just the 2-D river mask. A bare raster flip does **not** rewrite graph-node identifiers. Domain coordinates and projected km grid differ from the 0.3° global lat/lon grid.

## Reproduced source candidate-A cells (NOT approved geography)

| Model landmark | Lat, lon | Elev. m | T°C | P mm / planetary year | A12 input Q m³/s |
| --- | --- | ---: | ---: | ---: | ---: |
| Proposed mansion | −46.95°, −97.95° | 363.40 | 15.20 | 848.16 | 61.76 |
| Overnight shelter | −47.25°, −98.25° | 311.16 | 15.39 | 851.92 | 75.01 |
| Fortified town | −47.55°, −98.55° | 285.30 | 15.42 | 809.02 | 1115.02 |
| Old crossing | −46.65°, −97.65° | 464.68 | 14.72 | 837.71 | 48.61 |

Those fields match the rounded values in the 08-Nov working atlas. This is **source consistency**, not validation of the empirical A10 hydrological physics or exact local settlement coordinates.

## Scaling / physically meaningful caveats

The global A8/A12 0.3° cell at candidate-A latitude has roughly 25–37 km spacing. A straight-line chain of several source cells cannot locate a local waterfall, cliff, bridge, road or building. Subregional detail must be generated or derived as a **child region constrained by macro geometry**, not by upscaling pixels and calling it measured local terrain.

The A8 global drainage is D8 Priority-Flood **working research**, distinct from the accepted Core 0.2 MFD river network. Neither one automatically outranks the other. A12 land-cover codes are a climate/PET-dependent **working classifier**, not universal non-Earth biomes. A12 rainfall uses **planetary year ~202.755 Earth days**, explicit external conversion needed for current Core C1.

## What has actually been done

- Verified raw ZIP SHA-256; opened NumPy members without pickle.
- Verified lat/lon and original DEM/land-mask exact alignment after row reversal.
- Read A12 climate/cover/annual Q fields and compared candidate route cells against the working atlas.
- Created a local diagnostic four-panel preview and JSON report for the user **outside the GitHub repository** because source Drive archives are private. These outputs have not been committed to public GitHub.
- **NOT YET**: source-specific reusable importer/CLI in Core, A8 downstream graph index remap, regional 1-km world generation/conditioning, A10/A11 ZIP verification, or authoritative author acceptance of candidate A.

## Next technical segment

A bounded **external world-geogrid adapter** that accepts A8/A12 ZIPs as user-supplied files, validates SHA/grid/orientation, maps lat/lon to region km coordinates preserving radius 7008.1 km and planet-year time basis, and emits local geographic anchor fields and metadata without mutating Core stages. Test graph-index remap with small synthetic fixtures and compare actual macro river connectivity. Then generate a truly regional sub-km or 1-km child landscape that remains linked to the source. No new Earth-only ecology or unsourced canonical town placement.
