# P3.5 — full REAL A8/A12 Region A legacy-vs-spherical author atlases (2026-11-21)

**Status:** PRIVATE-SOURCE WORKING MODEL / NOT CANON / operator review still pending. **Repository:** MysterioCrypto/domain_generator, PR #103 DRAFT/UNMERGED. Computation pinned to HEAD `8248e97fd4e99d5a2ecca1b7c12074e1a2e0ffb9`. Accepted `dev/0.2` and frozen release unchanged.

## Functional checkpoint

For the first time, BOTH `legacy_lat_scaled_easting_v1` and opt-in `spherical_xyz_v1` were run through the **complete actual private-source computational path**: original A8/A12 → P1 whole-grid parity and 9×11 macro crop with interpolation halo → P2-A child DEM (231×231 at 1 km) → P3 natural-cover candidates → same-layout author atlas. The EXACT six GitHub module/ledger/profile blob SHA-1 identifiers were confirmed against local temporary checkout before execution.

**Execution precision:** the four exact checkout implementation MODULES and canonical author ledger/profile were invoked from a small one-shot orchestration script. The `scripts/build_author_atlas_v02.py` CLI wrapper itself was NOT executed on private inputs, so this is function-chain equivalence, not proof of private wrapper execution. Public synthetic CI remains the wrapper regression.

- Original A8 SHA-256: `6824ccf2a4aea7b2514a4e694e84ad13fd3ff4e18dba6c3be6b4b7753dc019ec`.
- Original A12 SHA-256: `db9f0f91fca845058c658dfdd639c882b9cf0514736b3677184a4c84ff20b3a4`.
- Exact P1 blob: `d4ba7a11f6a04d786a4971cb969b61f36e5a8900`.
- Exact P2-A blob: `fd89baba3f7c93c565b91ca88b3296bc2244b276`.
- Exact P3 blob: `edbb8267fe97a7b2c44f97c96616c84c5e8c682f`.
- Exact atlas blob: `099ce94c77684613405277d16da5b35b68f0630d`.
- Author ledger blob: `0b2c4f77023ec6b6756a51af03f7cfe96cf3553c`.
- Cover profile blob: `3af9d0a9498c425ab3b53a08ab0df37033252fa0`.

**Private comparison image (permanent Drive):**
https://drive.google.com/file/d/12T79Z9GcKD41LyDGOaKli-WJlNK3emNQ/view

## Exact paired results

Same region center (-47.25°, -98.25°), planet radius 7008.1 km, calendar year 202.755 Earth days, 230×230 km map extent, 1 km child pixels, seed 1406, strength 2, exact parent DEM and cover profile. Same 63 original A8 station elevations, max station error **0.0 m**, same entire 231×231 parent interpolation and land mask. Neither variant establishes real watercourses or roads.

| Metric | Legacy P3.3 replay | Spherical P3.5 |
| --- | ---: | ---: |
| Woodland candidate | 64.058% | 66.663% |
| Open ground candidate | 16.731% | 17.275% |
| Wet-lowland candidate | 19.211% | 16.062% |
| Rocky-slope candidate | 0% | 0% |
| Sparse-cover candidate | 0% | 0% |
| Local relief standard deviation | 9.632 m | 7.478 m |
| Total terrain standard deviation | 88.175 m | 89.398 m |
| Parent anchors | 63 / 63 | 63 / 63 |
| Max original anchor error | 0 m | 0 m |
| Unplaced author POI | 5 | 5 |
| Unresolved author routes | 2 | 2 |

Pixelwise comparison: terrain delta (spherical minus legacy) **RMSE 11.927 m**, mean absolute difference **8.910 m**, maximum absolute difference **77.676 m**. Model-cover label changed in **13,510 of 53,361** cells (**25.318%**). **Zero land/sea pixel changes**. These are numerical differences between alternatives, not error relative to measured terrain.

The full sheets show much less high-frequency diagonal striping with spherical detail, while coarse aligned landscape corridors persist because P1 DEM and ecological scenario inputs are unchanged. A cleaner image does **not** prove physically faithful geology or ecology. The 0% rocky/sparse classes and broad lowlands reflect current classifier/source assumptions and remain candidates for author scrutiny, not automatic calibration requests.

## Acceptance and privacy boundaries

- **NOT ACCEPTED:** no user choice of legacy vs spherical; no canon promotion of planet/locations; five landmarks unplaced and two route distances unknown.
- **NOT COMPUTED:** new accepted 1-km MFD rivers, road network, waterfalls, perennial/wetland water balance, travel time.
- **NOT UPLOADED TO GITHUB:** original A8/A12 archives, source rasters, derived DEM, raw cover arrays.
- **Drive contains** only derived side-by-side comparison PNG for private review. Full derived-only ZIP is available as a conversation artifact; do not assume persistent Drive storage of this ZIP unless a separate upload is confirmed.
- **Next bounded product decision:** review the TWO full maps; only after author preference, choose a default for the author profile (NOT generic universal Core), then advance one dependent spatial layer (river topology or story placement) with evidence. Do not merge PR #103 automatically.

## Anti-confusion

P3.4 was only a short-form local detail comparison via independent probe. P3.5 confirms the appearance and numerical consequences in the complete P1→P2-A→P3→atlas *function chain* on real source; the CLI wrapper remained unexecuted privately. Legacy P3.3 numerical cover fractions reproduce exactly to the published five decimals.
