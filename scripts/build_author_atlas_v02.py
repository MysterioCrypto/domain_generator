from __future__ import annotations

"""Build one source-verified P2-A -> P3 -> author atlas bundle (NONCANONICAL).

External read-only adapter: no source mutation, Core changes or auto-accepted
landmarks. Run from repository root as a Python module.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.condition_planetary_child_terrain_v02 import ChildTerrainSettings, generate_child
from scripts.derive_author_natural_cover_v02 import classify_cover, render_preview
from scripts.render_author_region_atlas_v02 import audit_atlas, notes, render_sheet


class AtlasBuildError(ValueError):
    """Incompatible original sources must not be silently mixed."""


def load_npz(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as z:
        return {key: z[key].copy() for key in z.files}


def verify_source_identity(macro: dict, eco: dict, manifest: dict) -> dict:
    """Compare cropped A8-derived parent stations to the original A12 grid.

    A8 macro is north-first. A12 may be south-first or north-first. Coordinate,
    land and elevation equality are required; approximate overlap is insufficient.
    """
    if (manifest.get("status") != "PRIVATE_SOURCE_DERIVED_WORKING_MODEL_NOT_CANON"
            or manifest.get("is_DomainData") is not False):
        raise AtlasBuildError("expected noncanonical exported macro source")
    if any(k not in macro for k in ("latitude_deg_north_first",
            "longitude_deg_west_to_east", "elevation_m", "land_mask")):
        raise AtlasBuildError("missing macro geographic source fields")
    if any(k not in eco for k in ("lat", "lon", "elevation_m", "land")):
        raise AtlasBuildError("A12 needs original coordinates, elevation and land")

    ml = np.asarray(macro["latitude_deg_north_first"], dtype=float)
    mx = np.asarray(macro["longitude_deg_west_to_east"], dtype=float)
    al = np.asarray(eco["lat"], dtype=float)
    ax = np.asarray(eco["lon"], dtype=float)
    if (any(v.ndim != 1 or len(v) < 3 or not np.isfinite(v).all()
            for v in (ml, mx, al, ax))
            or not np.all(np.diff(ml) < 0) or not np.all(np.diff(mx) > 0)
            or not np.all(np.diff(ax) > 0)
            or not (np.all(np.diff(al) > 0) or np.all(np.diff(al) < 0))):
        raise AtlasBuildError("malformed source grid axes")
    north_first = bool(al[0] > al[-1])
    ascending = al[::-1] if north_first else al
    rows = np.searchsorted(ascending, ml[::-1])
    cols = np.searchsorted(ax, mx)
    if (np.any(rows >= len(ascending)) or np.any(cols >= len(ax))
            or not np.array_equal(ascending[rows], ml[::-1])
            or not np.array_equal(ax[cols], mx)):
        raise AtlasBuildError("macro station coordinates do not match original A12")
    a12_rows = len(al) - 1 - rows[::-1] if north_first else rows[::-1]
    if (any(np.asarray(macro[k]).shape != (len(ml), len(mx))
            for k in ("elevation_m", "land_mask"))
            or any(np.asarray(eco[k]).shape != (len(al), len(ax))
            for k in ("elevation_m", "land"))):
        raise AtlasBuildError("source raster shapes disagree")
    if not np.array_equal(macro["elevation_m"],
                          np.asarray(eco["elevation_m"])[np.ix_(a12_rows, cols)]):
        raise AtlasBuildError("macro/A12 original elevation mismatch")
    if not np.array_equal(macro["land_mask"],
                          np.asarray(eco["land"])[np.ix_(a12_rows, cols)]):
        raise AtlasBuildError("macro/A12 original land mismatch")
    return {"status": "EXACT_MACRO_A12_PARENT_STATIONS_MATCH",
            "matching_parent_stations": int(len(ml) * len(mx)),
            "a12_north_first": north_first, "is_author_canon": False}


def build(macro, eco, macro_manifest, ledger, profile, *,
          half_width_km, half_height_km, spacing_km=1.0,
          seed=1406, relief_strength=2.0):
    source_identity = verify_source_identity(macro, eco, macro_manifest)
    center = ledger.get("region", {}).get("center_lat_lon_deg")
    original_center = macro_manifest.get("center_degrees")
    if (not isinstance(center, list) or len(center) != 2
            or any(isinstance(x, bool) or not isinstance(x, (int, float))
                   or not np.isfinite(x) for x in center)
            or not isinstance(original_center, list) or len(original_center) != 2
            or not np.allclose(center, original_center, rtol=0, atol=1e-7)):
        raise AtlasBuildError("ledger and macro source centers must match")
    settings = ChildTerrainSettings(
        center_lat_deg=float(center[0]), center_lon_deg=float(center[1]),
        half_width_km=half_width_km, half_height_km=half_height_km,
        spacing_km=spacing_km, seed=seed, relief_strength=relief_strength,
        planet_radius_km=float(macro_manifest["planet_radius_km"]),
        planetary_year_earth_days=float(macro_manifest["planetary_year_earth_days"]),
    )
    child, child_meta = generate_child(macro, settings)
    original_terrain = child["child_elevation_m"].copy()
    cover, cover_meta = classify_cover(child, eco, child_meta, profile)
    if not np.array_equal(original_terrain, child["child_elevation_m"]):
        raise AtlasBuildError("P3 must not mutate P2 terrain")
    atlas = audit_atlas(ledger, child, child_meta)
    atlas["natural_cover"] = {
        "status": "MODEL_CANDIDATE_NOT_CANON",
        "class_fractions": cover_meta["land_cover_area_fractions"],
        "source_sample_resolution": cover_meta["source_sample_resolution"],
    }
    return child, child_meta, cover, cover_meta, atlas, source_identity


def load_verified_archives(a8_zip: Path, a12_zip: Path, ledger: dict, *,
                           half_width_km: float, half_height_km: float,
                           planet_radius_km: float, planetary_year_earth_days: float):
    """Direct private A8/A12 ZIP entry: reuse the SAME validated P1 source.

    Nothing is extracted to a public path. P1 checks full-world DEM/land/axes
    identity before cropping; P3 needs the uncropped ORIGINAL A12 scenario fields.
    """
    from scripts.export_planetary_macro_region_v02 import (
        _read_member, load_archives, region_crop,
    )
    center = ledger.get("region", {}).get("center_lat_lon_deg")
    if (not isinstance(center, list) or len(center) != 2
            or any(isinstance(x, bool) or not isinstance(x, (int, float))
                   or not np.isfinite(x) for x in center)):
        raise AtlasBuildError("ledger needs a finite region center [lat,lon]")
    source = load_archives(a8_zip, a12_zip)
    original_a12 = _read_member(a12_zip, "A12_biome_fields.npz", (
        "lat", "lon", "land", "elevation_m", "biome_base",
        "biome_moderate", "biome_precip_minus20", "biome_precip_plus20",
        "stable4", "wetland_candidate",
    ))
    macro, manifest = region_crop(
        source, center_lat_deg=float(center[0]), center_lon_deg=float(center[1]),
        half_width_km=half_width_km, half_height_km=half_height_km,
        planet_radius_km=planet_radius_km,
        planetary_year_earth_days=planetary_year_earth_days,
    )
    return macro, original_a12, manifest


def _file_sha256(path: Path) -> str:
    from hashlib import file_digest
    with path.open("rb") as f:
        return file_digest(f, "sha256").hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    # Either two verified original archives or three already-exported inputs.
    for name in ("macro-npz", "macro-manifest", "eco-npz", "a8-zip", "a12-zip"):
        p.add_argument("--" + name, type=Path)
    for name in ("ledger-json", "profile-json"):
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--planet-radius-km", type=float,
                   help="Mandatory for direct ZIP mode; never assume Earth radius")
    p.add_argument("--planet-year-earth-days", type=float,
                   help="Mandatory for direct ZIP mode; no Earth calendar default")
    p.add_argument("--expected-a8-sha256", help="Optional original ZIP digest pin")
    p.add_argument("--expected-a12-sha256", help="Optional original ZIP digest pin")
    p.add_argument("--half-width-km", required=True, type=float)
    p.add_argument("--half-height-km", required=True, type=float)
    p.add_argument("--spacing-km", type=float, default=1.)
    p.add_argument("--seed", type=int, default=1406)
    p.add_argument("--relief-strength", type=float, default=2.)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    zip_mode = args.a8_zip is not None or args.a12_zip is not None
    exported_mode = any(getattr(args, k) is not None
                        for k in ("macro_npz", "macro_manifest", "eco_npz"))
    if zip_mode == exported_mode:
        p.error("provide either --a8-zip + --a12-zip OR "
                "--macro-npz + --macro-manifest + --eco-npz")
    ledger = json.loads(args.ledger_json.read_text(encoding="utf-8"))
    profile = json.loads(args.profile_json.read_text(encoding="utf-8"))
    if zip_mode:
        if (args.a8_zip is None or args.a12_zip is None
                or args.planet_radius_km is None
                or args.planet_year_earth_days is None):
            p.error("direct ZIP mode requires both archives, --planet-radius-km "
                    "and --planet-year-earth-days")
        files = {"a8_zip": args.a8_zip, "a12_zip": args.a12_zip,
                 "ledger_json": args.ledger_json, "profile_json": args.profile_json}
        for label in ("a8", "a12"):
            expected = getattr(args, "expected_" + label + "_sha256")
            if expected is not None and _file_sha256(files[label + "_zip"]) != expected.lower():
                raise AtlasBuildError(label.upper() + " archive SHA-256 mismatch")
        macro, eco, meta = load_verified_archives(
            args.a8_zip, args.a12_zip, ledger,
            half_width_km=args.half_width_km, half_height_km=args.half_height_km,
            planet_radius_km=args.planet_radius_km,
            planetary_year_earth_days=args.planet_year_earth_days,
        )
    else:
        if any(getattr(args, k) is None
               for k in ("macro_npz", "macro_manifest", "eco_npz")):
            p.error("exported mode needs --macro-npz, --macro-manifest, --eco-npz")
        if (args.planet_radius_km is not None or args.planet_year_earth_days is not None
                or args.expected_a8_sha256 is not None or args.expected_a12_sha256 is not None):
            p.error("planet radius/year and original archive SHA options are ZIP-only")
        files = {"macro_npz": args.macro_npz, "macro_manifest": args.macro_manifest,
                 "eco_npz": args.eco_npz, "ledger_json": args.ledger_json,
                 "profile_json": args.profile_json}
        macro = load_npz(args.macro_npz)
        eco = load_npz(args.eco_npz)
        meta = json.loads(args.macro_manifest.read_text(encoding="utf-8"))
    child, child_meta, cover, cover_meta, atlas, alignment = build(
        macro, eco, meta, ledger, profile,
        half_width_km=args.half_width_km, half_height_km=args.half_height_km,
        spacing_km=args.spacing_km, seed=args.seed, relief_strength=args.relief_strength,
    )
    if args.output.exists() and (not args.output.is_dir()
                                  or any(args.output.iterdir())):
        raise AtlasBuildError("output directory must be empty (no stale maps)")
    for dirname in (("child", "cover", "atlas", "source") if zip_mode
                    else ("child", "cover", "atlas")):
        (args.output / dirname).mkdir(parents=True, exist_ok=True)
    if zip_mode:
        # Retain only PRIVATE derived source crop in the user-specified output;
        # it is never included in GitHub's public synthetic workflow artifacts.
        np.savez_compressed(args.output / "source/macro-region-source.npz", **macro)
        meta["source_sha256"] = {k: _file_sha256(files[k])
                                 for k in ("a8_zip", "a12_zip")}
        (args.output / "source/manifest.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    np.savez_compressed(args.output / "child/child-terrain-generated.npz", **child)
    np.savez_compressed(args.output / "cover/natural-cover-candidates.npz", **cover)
    (args.output / "child/manifest.json").write_text(
        json.dumps(child_meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output / "cover/manifest.json").write_text(
        json.dumps(cover_meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    render_preview(child, cover, cover_meta,
                   args.output / "cover/cover-before-after.png")
    render_sheet(ledger, child, atlas,
                 args.output / "atlas/author-atlas-sheet.png",
                 cover=cover["cover_class_candidate"])
    (args.output / "atlas/author-atlas-audit.json").write_text(
        json.dumps(atlas, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output / "atlas/author-atlas-notes.md").write_text(
        notes(ledger, atlas), encoding="utf-8")
    audit = {
        "status": "P3_EXACT_CHECKOUT_BUILD_NONCANONICAL",
        "is_author_canon": False,
        "is_verified_hydrology_or_travel_time": False,
        "source_identity": alignment,
        "input_mode": "ORIGINAL_PRIVATE_A8_A12_ZIP" if zip_mode else "EXPORTED_NPZ",
        "input_sha256": {k: _file_sha256(v) for k, v in files.items()},
        "parent_anchor_count": child_meta["source_elevation_anchors_in_child"],
        "parent_anchor_max_error_m": child_meta["max_parent_anchor_error_m"],
        "child_shape": child_meta["child_shape"],
        "cover_fractions": cover_meta["land_cover_area_fractions"],
        "landmarks_unplaced": atlas["landmarks_unplaced"],
        "routes_without_distance": sum(r["distance_km"] is None for r in atlas["routes"]),
        "code_chain": ["generate_child", "classify_cover", "audit_atlas", "render_sheet"],
        "limitations": [
            "1-km pixels are procedural, not measured",
            "A12 codes do not establish forests, wetlands or water",
            "no validated river/road network or travel time",
            "private user inputs must never be uploaded to public CI",
        ],
    }
    (args.output / "build-audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
