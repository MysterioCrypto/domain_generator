"""P4-A map-first product tests using SYNTHETIC geography ONLY."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

from scripts.render_region_cartographic_base_v02 import (
    CartographicBaseError, render_cartographic_base,
)


def _fixture():
    y, x = np.mgrid[0:49, 0:65]
    z = (220 + 2*x + 3*y + 190*np.exp(-((x-23)**2/130+(y-22)**2/190))
         + 35*np.cos(x/6)*np.sin(y/9)).astype("float32")
    cls = np.where(y < 18, 1, np.where(x < 24, 4, 2)).astype("uint8")
    child = {
        "east_km": np.linspace(-32, 32, 65),
        "north_km_north_first": np.linspace(24, -24, 49),
        "child_elevation_m": z,
        "land_mask": np.ones_like(z, dtype="uint8"),
    }
    cover = {"cover_class_candidate": cls}
    cm = {
        "status": "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData": False,
        "detail_coordinate_system": "spherical_xyz_v1",
    }
    cv = {
        "status": "P3_MVP_NONCANONICAL_SOURCE_CONDITIONED_COVER",
        "cover_is_author_canon": False,
        "wetland_is_confirmed_water": False,
    }
    ledger = json.loads(
        (Path(__file__).resolve().parents[1] /
         "examples/world-fixtures/osvera-first-arc-author-ledger.json").read_text(
             encoding="utf-8"))
    ledger["world"]["name"] = "SYNTHETIC — NOT OSVERA"
    return child, cover, cm, cv, ledger


def test_map_is_independent_and_story_geometry_stays_unknown(tmp_path):
    child, cover, cm, cv, ledger = _fixture()
    orig = {k: v.copy() for k, v in child.items()}
    orig_cover = cover["cover_class_candidate"].copy()
    result = render_cartographic_base(
        child, cover, cm, cv, ledger, tmp_path/"map", pixels_per_cell=5)
    assert result["status"] == "P4A_NONCANONICAL_CARTOGRAPHIC_BASE"
    assert result["detail_coordinate_system"] == "spherical_xyz_v1"
    assert result["image_size_pixels"] == [325, 245]
    assert result["region_km"] == [64., 48.]
    assert result["unplaced_landmarks"] == 5
    assert result["unresolved_routes"] == 2
    assert not result["is_author_canon"]
    assert not result["is_verified_hydrology"]
    assert "lakes and open water" in result["unsupported_or_undrawn"]
    for key, value in orig.items():
        np.testing.assert_array_equal(child[key], value)
    np.testing.assert_array_equal(cover["cover_class_candidate"], orig_cover)
    with Image.open(tmp_path/"map/region-cartographic-base.png") as im:
        assert im.size == (325, 245)
        pixels = np.asarray(im)
        # Geographic north-first: northern forest renders darker than southern open land.
        assert pixels[:30, :, :].mean() < pixels[-30:, :, :].mean()
    with Image.open(tmp_path/"map/region-cartographic-sheet.png") as im:
        assert im.width == 325+140 and im.height == 245+102+200


def test_bitwise_replay_with_same_inputs(tmp_path):
    child, cover, cm, cv, ledger = _fixture()
    render_cartographic_base(child, cover, cm, cv, ledger, tmp_path/"a", pixels_per_cell=4)
    render_cartographic_base(child, cover, cm, cv, ledger, tmp_path/"b", pixels_per_cell=4)
    for name in ("region-cartographic-base.png",
                 "region-cartographic-sheet.png",
                 "region-cartographic-audit.json"):
        def digest(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest(tmp_path/"a"/name) == digest(tmp_path/"b"/name)


@pytest.mark.parametrize("bad", [
    "missing_cover", "invalid_class", "false_water", "wrong_orientation",
    "positioned_landmark", "positioned_route", "accepted_core",
])
def test_missing_or_inconsistent_geographic_evidence_is_rejected(tmp_path, bad):
    child, cover, cm, cv, ledger = _fixture()
    if bad == "missing_cover":
        cover.pop("cover_class_candidate")
    elif bad == "invalid_class":
        cover["cover_class_candidate"][10, 10] = 255
    elif bad == "false_water":
        cv["wetland_is_confirmed_water"] = True
    elif bad == "wrong_orientation":
        child["north_km_north_first"] = child["north_km_north_first"][::-1]
    elif bad == "positioned_landmark":
        ledger["landmarks"][0]["position"] = [0, 0]
    elif bad == "positioned_route":
        ledger["routes"][0]["polyline_east_north_km"] = [[0, 0], [2, 2]]
    elif bad == "accepted_core":
        cm["is_accepted_Core_DomainData"] = True
    with pytest.raises(CartographicBaseError):
        render_cartographic_base(child, cover, cm, cv, ledger, tmp_path/"bad",
                                 pixels_per_cell=4)
    assert not (tmp_path/"bad").exists()


def test_cli_five_inputs_and_sha256_audit(tmp_path):
    child, cover, cm, cv, ledger = _fixture()
    inputs = tmp_path/"in"
    inputs.mkdir()
    np.savez_compressed(inputs/"child.npz", **child)
    np.savez_compressed(inputs/"cover.npz", **cover)
    for name, data in (("child.json", cm), ("cover.json", cv), ("ledger.json", ledger)):
        (inputs/name).write_text(json.dumps(data), encoding="utf-8")
    cmd = [
        sys.executable, "-m", "scripts.render_region_cartographic_base_v02",
        "--child-npz", str(inputs/"child.npz"),
        "--child-manifest", str(inputs/"child.json"),
        "--cover-npz", str(inputs/"cover.npz"),
        "--cover-manifest", str(inputs/"cover.json"),
        "--ledger-json", str(inputs/"ledger.json"),
        "--pixels-per-cell", "4",
        "--output", str(tmp_path/"output"),
    ]
    result = subprocess.run(
        cmd, cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    audit = json.loads((tmp_path/"output/region-cartographic-audit.json").read_text())
    assert set(audit["input_sha256"]) == {
        "child_npz", "child_manifest", "cover_npz", "cover_manifest", "ledger_json"
    }
    assert all(len(h) == 64 for h in audit["input_sha256"].values())
    again = subprocess.run(
        cmd, cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert again.returncode != 0 and "empty directory" in again.stderr
