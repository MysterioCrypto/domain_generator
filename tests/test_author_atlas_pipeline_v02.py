"""P3 exact-checkout product tests; all source arrays here are SYNTHETIC."""

import json
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from scripts.build_author_atlas_v02 import AtlasBuildError, build, verify_source_identity
from scripts.derive_author_natural_cover_v02 import _defaults


def _synthetic(north_first_a12=False):
    lat = np.linspace(-49.0, -45.0, 13)
    lon = np.linspace(-99.1, -97.5, 15)
    yy, xx = np.meshgrid(lat, lon, indexing="ij")
    height = (400 + 75 * np.sin((xx + 98.25) * 3)
              + 35 * np.cos((yy + 47.25) * 2)).astype("float32")
    land = np.ones(height.shape, dtype="uint8")
    classes = np.where(np.indices(height.shape)[1] <= 5, 7,
                       np.where(np.indices(height.shape)[1] >= 11, 6, 8)).astype("uint8")
    eco = {
        "lat": lat.copy(), "lon": lon.copy(), "elevation_m": height.copy(),
        "land": land.copy(), "biome_base": classes.copy(),
        "biome_moderate": classes.copy(),
        "biome_precip_minus20": classes.copy(),
        "biome_precip_plus20": classes.copy(),
        "stable4": np.ones(height.shape, dtype="uint8"),
        "wetland_candidate": np.zeros(height.shape, dtype="uint8"),
    }
    if north_first_a12:
        eco["lat"] = lat[::-1].copy()
        for key in list(eco):
            if np.asarray(eco[key]).shape == height.shape:
                eco[key] = eco[key][::-1].copy()
    macro = {
        "latitude_deg_north_first": lat[::-1].copy(),
        "longitude_deg_west_to_east": lon.copy(),
        "elevation_m": height[::-1].copy(),
        "land_mask": land[::-1].copy(),
    }
    manifest = {
        "status": "PRIVATE_SOURCE_DERIVED_WORKING_MODEL_NOT_CANON",
        "is_DomainData": False, "center_degrees": [-47.25, -98.25],
        "planet_radius_km": 7008.1, "planetary_year_earth_days": 202.755,
    }
    ledger = json.loads(
        (Path(__file__).resolve().parents[1]
         / "examples/world-fixtures/osvera-first-arc-author-ledger.json").read_text(
             encoding="utf-8"))
    ledger["world"]["name"] = "SYNTHETIC TEST, NOT OSVERA"
    ledger["story"]["protagonist"] = "Synthetic actor"
    return macro, eco, manifest, ledger, _defaults()


@pytest.mark.parametrize("north_first", [False, True])
def test_real_parent_station_identity_both_a12_orientations(north_first):
    macro, eco, manifest, ledger, profile = _synthetic(north_first)
    aligned = verify_source_identity(macro, eco, manifest)
    assert aligned["matching_parent_stations"] == 13 * 15
    assert aligned["a12_north_first"] == north_first
    result = build(macro, eco, manifest, ledger, profile,
                   half_width_km=30, half_height_km=30)
    child, child_meta, cover, cover_meta, atlas, source = result
    assert child["child_elevation_m"].shape == (61, 61)
    assert child_meta["source_elevation_anchors_in_child"] > 0
    assert child_meta["max_parent_anchor_error_m"] <= 1e-6
    assert source == aligned
    assert cover["cover_class_candidate"].shape == (61, 61)
    assert cover_meta["cover_is_author_canon"] is False
    assert atlas["landmarks_unplaced"] == 5
    assert all(route["distance_km"] is None for route in atlas["routes"])
    assert atlas["natural_cover"]["status"] == "MODEL_CANDIDATE_NOT_CANON"
    assert not atlas["map_is_author_canon"]


def test_mixed_world_dem_or_land_are_rejected_before_build():
    macro, eco, meta, ledger, profile = _synthetic()
    eco["elevation_m"][0, 0] += 1
    with pytest.raises(AtlasBuildError, match="elevation mismatch"):
        build(macro, eco, meta, ledger, profile,
              half_width_km=30, half_height_km=30)
    eco["elevation_m"][0, 0] -= 1
    eco["land"][0, 0] = 0
    with pytest.raises(AtlasBuildError, match="land mismatch"):
        build(macro, eco, meta, ledger, profile,
              half_width_km=30, half_height_km=30)


def test_unaligned_grid_or_center_is_rejected_not_interpolated():
    macro, eco, meta, ledger, profile = _synthetic()
    eco["lat"] = eco["lat"] + 0.0001
    with pytest.raises(AtlasBuildError, match="coordinates"):
        verify_source_identity(macro, eco, meta)
    macro, eco, meta, ledger, profile = _synthetic()
    ledger["region"]["center_lat_lon_deg"][0] += 0.01
    with pytest.raises(AtlasBuildError, match="centers"):
        build(macro, eco, meta, ledger, profile,
              half_width_km=30, half_height_km=30)


def test_deterministic_same_checkout_does_not_modify_originals():
    macro, eco, meta, ledger, profile = _synthetic()
    original_macro = {k: v.copy() for k, v in macro.items()}
    original_eco = {k: v.copy() for k, v in eco.items()}
    kwargs = {"half_width_km": 30, "half_height_km": 30}
    a = build(macro, eco, meta, ledger, profile, **kwargs)
    b = build(macro, eco, meta, ledger, profile, **kwargs)
    for layer in (0, 2):
        for key in a[layer]:
            np.testing.assert_array_equal(a[layer][key], b[layer][key])
    for layer in (1, 3, 4, 5):
        assert a[layer] == b[layer]
    for k in macro:
        np.testing.assert_array_equal(macro[k], original_macro[k])
    for k in eco:
        np.testing.assert_array_equal(eco[k], original_eco[k])


def test_cli_creates_one_audited_atlas_and_rejects_stale_output(tmp_path):
    macro, eco, meta, ledger, profile = _synthetic()
    in_dir = tmp_path / "source"
    in_dir.mkdir()
    np.savez_compressed(in_dir / "macro.npz", **macro)
    np.savez_compressed(in_dir / "eco.npz", **eco)
    for filename, payload in (("macro.json", meta), ("ledger.json", ledger),
                              ("profile.json", profile)):
        (in_dir / filename).write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "product"
    command = [
        sys.executable, "-m", "scripts.build_author_atlas_v02",
        "--macro-npz", str(in_dir / "macro.npz"),
        "--macro-manifest", str(in_dir / "macro.json"),
        "--eco-npz", str(in_dir / "eco.npz"),
        "--ledger-json", str(in_dir / "ledger.json"),
        "--profile-json", str(in_dir / "profile.json"),
        "--half-width-km", "30", "--half-height-km", "30",
        "--output", str(output),
    ]
    cwd = Path(__file__).resolve().parents[1]
    first = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    report = json.loads((output / "build-audit.json").read_text(encoding="utf-8"))
    assert report["status"] == "P3_EXACT_CHECKOUT_BUILD_NONCANONICAL"
    assert report["parent_anchor_max_error_m"] < 1e-6
    assert len(report["input_sha256"]) == 5
    assert report["child_shape"] == [61, 61]
    assert report["landmarks_unplaced"] == 5
    assert report["routes_without_distance"] == 2
    assert (output / "atlas/author-atlas-sheet.png").stat().st_size > 10_000
    assert (output / "cover/cover-before-after.png").stat().st_size > 10_000
    second = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    assert second.returncode != 0
    assert "must be empty" in second.stderr


def _synthetic_archives(tmp_path, *, damage_a12=False):
    """A8 north-first and A12 south-first, same physical planet, no private data."""
    macro, eco, _, _, _ = _synthetic()
    a8 = {
        "lat": macro["latitude_deg_north_first"],
        "lon": macro["longitude_deg_west_to_east"],
        "elevation_m": macro["elevation_m"], "land": macro["land_mask"],
        "downstream_index": np.full(macro["elevation_m"].shape, -1, dtype=np.int32),
        "catchment_area_km2": np.ones(macro["elevation_m"].shape, dtype=np.float32),
        "river_mask": np.zeros(macro["elevation_m"].shape, dtype=np.uint8),
    }
    a12 = dict(eco)
    a12["temperature_annual_C"] = np.ones(eco["land"].shape, dtype=np.float32) * 18
    a12["precip_planet_year_mm"] = np.ones(eco["land"].shape, dtype=np.float32) * 900
    if damage_a12:
        a12["elevation_m"][4, 6] += 2
    paths = []
    for filename, member, arrays in (
        ("A8.zip", "planet_A8/A8_hydrology.npz", a8),
        ("A12.zip", "planet_A12/A12_biome_fields.npz", a12),
    ):
        p = tmp_path / filename
        buffer = BytesIO()
        np.savez_compressed(buffer, **arrays)
        with ZipFile(p, "w") as zip_file:
            zip_file.writestr(member, buffer.getvalue())
        paths.append(p)
    return paths


def _archive_command(tmp_path, a8, a12, *, output):
    return [
        sys.executable, "-m", "scripts.build_author_atlas_v02",
        "--a8-zip", str(a8), "--a12-zip", str(a12),
        "--ledger-json", str(tmp_path / "ledger.json"),
        "--profile-json", str(tmp_path / "profile.json"),
        "--planet-radius-km", "7008.1", "--planet-year-earth-days", "202.755",
        "--half-width-km", "45", "--half-height-km", "45", "--output", str(output),
    ]


def test_original_zip_to_map_one_command_preserves_private_source_provenance(tmp_path):
    from scripts.derive_author_natural_cover_v02 import _defaults
    repo = Path(__file__).resolve().parents[1]
    a8, a12 = _synthetic_archives(tmp_path)
    _, _, _, ledger, _ = _synthetic()
    (tmp_path / "ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    (tmp_path / "profile.json").write_text(json.dumps(_defaults()), encoding="utf-8")
    output = tmp_path / "author-product"
    cmd = _archive_command(tmp_path, a8, a12, output=output)
    result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads((output / "build-audit.json").read_text(encoding="utf-8"))
    assert report["status"] == "P3_EXACT_CHECKOUT_BUILD_NONCANONICAL"
    assert report["input_mode"] == "ORIGINAL_PRIVATE_A8_A12_ZIP"
    assert set(report["input_sha256"]) == {"a8_zip", "a12_zip", "ledger_json", "profile_json"}
    assert report["parent_anchor_count"] > 0
    assert report["parent_anchor_max_error_m"] <= 1e-6
    assert report["child_shape"] == [91, 91]
    assert report["landmarks_unplaced"] == 5
    assert report["routes_without_distance"] == 2
    assert not report["is_author_canon"]
    assert (output / "source/macro-region-source.npz").exists()
    manifest = json.loads((output / "source/manifest.json").read_text(encoding="utf-8"))
    assert manifest["author_child_half_extent_km"] == [45, 45]
    assert all(v > 0 for v in manifest["macro_interpolation_halo_km"])
    assert manifest["source_sha256"] == {
        "a8_zip": report["input_sha256"]["a8_zip"],
        "a12_zip": report["input_sha256"]["a12_zip"],
    }
    assert (output / "atlas/author-atlas-sheet.png").stat().st_size > 10_000
    with np.load(output / "cover/natural-cover-candidates.npz", allow_pickle=False) as z:
        assert z["cover_class_candidate"].shape == (91, 91)


def test_original_archive_digest_guard_and_mixed_planet_fail_before_output(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    a8, a12 = _synthetic_archives(tmp_path)
    _, _, _, ledger, profile = _synthetic()
    (tmp_path / "ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    (tmp_path / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
    out = tmp_path / "reject"
    cmd = _archive_command(tmp_path, a8, a12, output=out)
    result = subprocess.run(
        cmd + ["--expected-a8-sha256", "0" * 64],
        cwd=repo, capture_output=True, text=True,
    )
    assert result.returncode != 0 and "archive SHA-256 mismatch" in result.stderr
    assert not out.exists()
    a8, a12 = _synthetic_archives(tmp_path, damage_a12=True)
    result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    assert result.returncode != 0 and "elevation" in result.stderr
    assert not out.exists()


def test_archive_mode_rejects_ambiguous_or_incomplete_input(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    a8, a12 = _synthetic_archives(tmp_path)
    _, _, _, ledger, profile = _synthetic()
    (tmp_path / "ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    (tmp_path / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
    command = _archive_command(tmp_path, a8, a12, output=tmp_path / "bad")
    both = subprocess.run(command + ["--macro-npz", "other.npz"],
                          cwd=repo, capture_output=True, text=True)
    assert both.returncode != 0 and "either" in both.stderr
    absent = subprocess.run(
        [v for i, v in enumerate(command)
         if i not in (command.index("--planet-radius-km"),
                       command.index("--planet-radius-km") + 1)],
        cwd=repo, capture_output=True, text=True,
    )
    assert absent.returncode != 0 and "--planet-radius-km" in absent.stderr
