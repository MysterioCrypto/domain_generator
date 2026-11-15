# Tabletop atlas composer — operator-visible checkpoint

**2026-11-15** · Status **DRAFT / not accepted for merge** · [PR #101](https://github.com/MysterioCrypto/domain_generator/pull/101).

## Executive product goal

Build an expressive, roughly plausible and controllable map from `DomainSpec` for tabletop RPGs and literary worlds. A map should preserve a user's authored ridge/settlement identities, optional location constraints, accepted generated terrain and hydrography, and be exportable for **optional future artistic stylization**. Do not silently add physical runoff, geology, biome or settlement logic.

## Working authoring contract

- `surface.water_moisture_decay_km` is already exposed as a strictly positive `DomainSpec` floating-point value. Demo = `4.0` km, preserving `water_moisture_boost=0.55` and untouched global defaults.
- `features` declares one named ridge and three named settlements, all keyed by stable IDs and preset references.
- `constraints` puts the three dependent settlement POIs into west/east/south domain regions by hard predicates. The accepted preset's `SiteProfile` chooses actual positions based on C1 rainfall, temperature and potential drainage, with deterministic RNG by ID. This is **semi-procedural controlled placement**, not a feature-position editor.
- Exact hand-picked coordinates for every dependent POI are NOT asserted supported. Spatial `point` and `region` selectors exist, but exact-pinning mechanics need a separate targeted feature if desired.
- The compositor reads `DomainData` after generation. No POI, river, lake, sea or elevation changes are made during rendering.

## Visual result

[Open successful GitHub Actions and download `tabletop-atlas-v02`](https://github.com/MysterioCrypto/domain_generator/actions/runs/43732653717).

Core deliverables:

- `08-atlas-preview.png`: frame/title, north arrow, 10 km scale bar and three POI name labels;
- `06-map-full.png`: combined technical-to-illustrative map;
- `07-map-no-labels.png`: clean aligned raster for an artist;
- `09-parchment-palette.png`: alternate palette without changing map geometry;
- `01-terrain.png` / `02-water.png` / `03-rivers.png` / `04-poi-markers.png` / `05-labels.png`: five dimensionally aligned PNG layers for an image editor or constrained imagegen workflow;
- `manifest.json`: source request checksum, world-to-pixel mapping and exact accepted POI coordinates.

Actual accepted POIs in the demo: `settlement-01` Тихий Брод (14.92, 23.42 km); `settlement-02` Зелёная Стража (44.42, 24.21 km); `settlement-03` Луговая Пристань (23.17, 3.71 km). Current map 64×48 km and 1536×1152 px, with 31 accepted river segments. Targeted placement/contract regression **54 passed** and alignment checks succeeded in the linked Actions run.

## Limits and next product iteration

Visuals are currently a subdued technical atlas, not final concept art: mountain/forest icons, road networks, sovereign boundaries, city-scale typology and text collision in dense maps are absent. Relief/greenness palette is a **continuous artistic visual encoding**, not a biome map. Rivers use accepted centerlines; sea/lakes use their authoritative area support. Map generation is deterministic at fixed versions and inputs; different seeds/generator versions may yield different realizations.

Possible next improvements, **only if visibly beneficial**: more legible cartographic contour/landform treatment, settlement tiers supplied by explicit user tags rather than invented population inference, separately aligned text/river layers, an art-direction palette. No more large C2 parameter sweeps without evidence of map quality gain.

Do not merge PR #101, #100 or #99 solely because green tests exist; operator's judgement applies to the map artifact. Frozen release is untouched.


## Tabletop atlas readability and optional art-direction slice — 2026-11-15

- Product-facing priority: **readable, expressive TTRPG/literary maps**, not increasingly elaborate climate physics. The first atlas was geographically coherent but low-contrast, with tiny labels and identical symbols for all settlements. Improve presentation only: stronger relief shading, subtle elevation contours, clearer label plaques, larger type, north/scale/legend framing, and icons selected by *explicit authored tags* `village` vs `fort` (never inferred settlement populations).
- Renderer `scripts/render_tabletop_domain_map_v02.py` now exports a sixth aligned transparency layer `10-relief-contours.png` in addition to the five original terrain/water/river/POI/text layers, and preserves the original named filenames. Contour interval is a **cartographic display choice** based on accepted elevation, not an extra geomorphological model. Confirm source POI coordinates and accepted rivers are byte-stable under renderer-only changes; the dedicated Actions job checks all three POI coordinates, symbols, aligned layers, visible contours and label placement. 
- Add `11-parchment-no-labels.png` and `12-stylization-brief.txt`: optional image-illustration source and a constraints-first art handoff. Keep coastlines, lake polygons, river paths, POI coordinates and text as separate authoritative overlays; ImageGen is NOT assumed to preserve precise topology by itself. Always recompose original RGBA water/rivers/markers/labels after stylization if needed. 
- All map visuals remain derived **only** from the already accepted `DomainData` and user `DomainSpec`. No hidden roads/biomes, no physically modelled river discharge, and no change to Core 0.2 generation or frozen prealpha. Example still uses editable `surface.water_moisture_decay_km=4.0`, while preserving other allowed positive values; three fixed-named, constrained semi-procedural settlements are unchanged. This is a display renderer checkpoint, not a new placement feature.
- Work remains in draft [PR #101](https://github.com/MysterioCrypto/domain_generator/pull/101), **OPEN / UNMERGED**. Independent H13 runtime PR #99 and gradient experiment PR #100 likewise remain draft/unmerged. Targeted map CI previously GREEN at [Actions run 43733960567](https://github.com/MysterioCrypto/domain_generator/actions/runs/43733960567); extended art handoff must be revalidated on its latest head before operator sees final checkpoint.
- Stop rule: do not expand scientific tuning on the strength of a nicer palette. Next valid operator feedback is on actual updated `08-atlas-preview.png` and `09-parchment-palette.png` in the latest GREEN GitHub Actions artifact `tabletop-atlas-v02`. Do not ask for acceptance of internal test design, and do not infer approval to merge drafts.
