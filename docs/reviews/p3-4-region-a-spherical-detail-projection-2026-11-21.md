# P3.4 — Region A directional texture provenance / opt-in spherical detail (NOT CANON)

**Date:** 2026-11-21. **Branch:** draft PR #103, **Core accepted dev/0.2 unchanged**. **Operator acceptance:** pending. **Private source policy:** original A8/A12 and derived arrays stay outside public GitHub.

## Problem and isolated cause

P3.3 single-sheet map shows strongly diagonal short ridges and cover streaks. To avoid the renderer/cover-classifier masking a source error, split the REAL private region-A P2-A bundle into:
- **P1 interpolated macro DEM** `parent_interpolated_m` (smooth broad east/north relief, std **87.83 m**);
- **P2-A generated local correction** `new_local_relief_m` (pronounced repeated diagonal high-frequency streaks, std **9.63 m**);
- their sum `child_elevation_m`, and optional P3 land-cover visualization.

The old P2-A world-noise coordinate was `east = R * radians(longitude) * cos(latitude)`, `north = R * radians(latitude)`. Its meridional derivative is `d(east)/d(north) = -radians(longitude)*sin(latitude)`; at region A (~-98.25° lon, -47.25° lat) this is about **-1.26**. An absolute longitude changes how noise is sheared even on an otherwise identical local surface. The old landscape's 2D value-noise grid is **not an orthogonal local distance chart**, and the strong oblique small relief is therefore not proof of tectonic alignment.

## One bounded change: opt-in projected noise

Added `spherical_xyz_v1` to the external P2-A child terrain settings and P3 one-command atlas CLI. Longitude/latitude are mapped into a 3D sphere (`R cos(lat) cos(lon), R cos(lat) sin(lon), R sin(lat)`) and the same deterministic 48/18/7/3-km, 0.42/0.32/0.18/0.08 multi-scale weights sample a 3D smoothly interpolated hash lattice. This removes the *mathematical coordinate skew* and is continuous at the date line, while preserving crop-independent position anchoring.

- **Backward-compatible default remains `legacy_lat_scaled_easting_v1`**; no silent changes to P3.3 or Core 0.2.
- `detail_coordinate_system` is an explicitly validated P2 setting, stored in the P2 manifest and top-level P3 build audit.
- Parent DEM interpolation, source-height pinning, coastal sign preservation, A12 source fields, vegetation rules, river network and site ledger **are unchanged**.
- `spherical_xyz_v1` produces a new **candidate** geography. Directional statistics and appearance are evidence for comparing alternatives, NOT a guarantee of geology or a final acceptance.

## Real private region A — measurement (source SHA pinned in P3.3)

Input: previously archived 231×231 at 1 km P3.3 bundle; P1/P2 parents identical. The new spherical noise was **independently calculated in an ephemeral Python comparison probe** using the same formula/weights/seed/radius (1406, 7008.1 km, relief strength 2). The private full `build_author_atlas_v02.py` CLI and new spherical GitHub module were **NOT** run against these private inputs in this checkpoint. This is comparative evidence, not exact-checkout private integration acceptance.

| Measurement | Legacy local detail | New spherical local detail |
| --- | ---: | ---: |
| STD, meters | 9.63 | 7.48 |
| Min / max correction, meters | −46.71 / +52.57 | −28.45 / +42.40 |
| Centered gradient-direction anisotropy, lag 1 km | 0.869 | 0.022 |
| Same, lag 4 km | 0.712 | 0.066 |
| Same, lag 8 km | 0.522 | 0.120 |

Anisotropy metric is `(lambda_max-lambda_min)/lambda_max` from the 2×2 covariance of central finite differences of model relief (the mean gradient removed); 1 indicates strongly preferred gradient axis, 0 means isotropic gradient variance. These are **descriptive measurements of one map**, not universal physical claims. Local relief pattern visibly changes from slanted ribbons to more equiaxed patches. Macro DEM remains the same; no child rivers calculated.

**Permanent private visual comparison**: https://drive.google.com/file/d/1RBUPKmqR5ICBX-pZ6KjNQRvf6_3qMGCc/view

## Verification / gate

Synthetic regression tests check opt-in isolation, deterministic replay, exact parent anchors, continuous global coordinates across longitude ±180°, crop-invariant evaluation and unchanged noncanonical story map. Product workflow runs the P2-A → P3 → atlas chain in BOTH coordinate schemes using toy sources only.

**Current gate:** operator can compare the two local relief models visually. No new region A P3 natural-cover or hydrology, roads, waterfall or story positions are accepted by this document. Do not merge PR #103 automatically. If spherical candidate is preferred, next bounded iteration is an exact private full atlas build in that mode, with a source/hash audit and side-by-side map review.
