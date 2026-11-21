"""P4-B conservative drainage overlay regression; SYNTHETIC maps only."""

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from scripts.render_region_drainage_evidence_v02 import (
    DrainageEvidenceError, build_evidence, screen_candidate_links,
)


def fixture():
    n = 15
    rr, cc = np.mgrid[:n, :n]
    elevation = 200.-2*cc-.25*rr
    child = {
        "child_elevation_m": elevation.astype("float32"),
        "east_km": np.arange(n, dtype="float64"),
        "north_km_north_first": np.arange(n-1, -1, -1, dtype="float64"),
    }
    child_meta = {
        "status": "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData": False,
        "detail_coordinate_system": "spherical_xyz_v1",
    }
    candidate = {
        "channel_mask": np.zeros((n, n), dtype="uint8"),
        "lake_proxy_mask": np.zeros((n, n), dtype="uint8"),
        "Core_dominant_receiver_index": np.full((n, n), -1, dtype="int32"),
        "channel_edge_flat_from_to": np.array([[7*n+6, 7*n+7]], dtype="int32"),
        "lake_proxy_jumps_flat_from_to": np.empty((0, 2), dtype="int32"),
        "Core_dominant_channel_area_km2_NOT_Q": np.full((n,n), 500., dtype="float32"),
    }
    candidate["channel_mask"][7, 6] = 1
    candidate["Core_dominant_receiver_index"][7, 6] = 7*n+7
    projection_report = {
        "status": "P2_B2_4_REFERENCE_EXIT_ALIGNMENT_NOT_ACCEPTED_HYDROLOGY",
        "is_author_approved_local_river_map": False,
        "is_accepted_Core_DomainData": False,
        "external_area_auto_injected_km2": 0.,
        "child_core_dominant_channel_ledger": {
            "status": "CONNECTED_CORE_DOMINANT_MFD_CHANNEL_PROJECTION_NOT_REAL_RIVERS",
            "is_physical_discharge_or_approved_river": False,
            "no_external_A8_source_area_auto_injected": True,
            "ordinary_adjacent_channel_edges": 1,
            "nonphysical_proxy_links_NOT_RIVERS": 0,
            "lake_topology_status": "NONE",
        },
    }
    p4a_audit = {
        "status": "P4A_NONCANONICAL_CARTOGRAPHIC_BASE",
        "is_author_canon": False,
        "image_size_pixels": [n*6, n*6],
        "detail_coordinate_system": "spherical_xyz_v1",
    }
    img = Image.new("RGB", (n*6, n*6), (91, 119, 94))
    return child, child_meta, candidate, projection_report, p4a_audit, img


def test_strict_core_mfd_edge_is_only_candidate_line_and_inputs_unchanged(tmp_path):
    child, cm, candidate, report, p4a, img = fixture()
    before_dem = child["child_elevation_m"].copy()
    before_receiver = candidate["Core_dominant_receiver_index"].copy()
    audit = build_evidence(child, cm, candidate, report, img, p4a, tmp_path/"out")
    assert audit["displayable_strictly_downhill_edges"] == 1
    assert audit["withheld_unsafe_ordinary_edges"] == 0
    assert audit["is_accepted_hydrology"] is False
    assert audit["is_water_occupancy_or_discharge"] is False
    assert audit["unknown_external_crop_inflows"] is True
    assert audit["river_continuity_across_withheld_edges"] == "NOT_ESTABLISHED"
    assert np.array_equal(before_dem, child["child_elevation_m"])
    assert np.array_equal(before_receiver, candidate["Core_dominant_receiver_index"])
    with np.load(tmp_path/"out/drainage-evidence-masks.npz") as f:
        assert f["candidate_display_edges_NOT_CONFIRMED_RIVERS"].shape == (1, 2)
        assert f["lake_proxy_jumps_NOT_RIVERS"].shape == (0, 2)
    with Image.open(tmp_path/"out/drainage-evidence-map.png") as image:
        assert image.size == (90, 90)
        assert np.any(np.asarray(image) != np.asarray(img))
    with Image.open(tmp_path/"out/drainage-evidence-sheet.png") as image:
        assert image.width > img.width


def test_bitwise_replay_and_existing_output_protection(tmp_path):
    data = fixture()
    for name in ("a", "b"):
        build_evidence(*data[:4], data[5], data[4], tmp_path/name)
    for suffix in ("map.png", "sheet.png", "masks.npz", "audit.json"):
        p = "drainage-evidence-"+suffix
        h = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        assert h(tmp_path/"a"/p) == h(tmp_path/"b"/p)
    with pytest.raises(DrainageEvidenceError, match="output must be empty"):
        build_evidence(*data[:4], data[5], data[4], tmp_path/"a")


@pytest.mark.parametrize("change", [
    "wrong_status", "auto_inflow", "wrong_base_mode", "wrong_orientation",
    "uphill_edge", "nonadjacent", "two_receivers", "lake_link_overlap",
    "wrong_ledger", "accepted_map",
])
def test_provenance_and_mfd_topology_must_be_explicit(tmp_path, change):
    child, cm, candidate, report, p4a, img = fixture()
    n = 15
    if change == "wrong_status":
        report["status"] = "CANON"
    elif change == "auto_inflow":
        report["external_area_auto_injected_km2"] = 50
    elif change == "wrong_base_mode":
        p4a["detail_coordinate_system"] = "legacy_lat_scaled_easting_v1"
    elif change == "wrong_orientation":
        child["north_km_north_first"] = child["north_km_north_first"][::-1]
    elif change == "uphill_edge":
        candidate["channel_edge_flat_from_to"][0, 1] = 7*n+5
        candidate["Core_dominant_receiver_index"][7, 6] = 7*n+5
    elif change == "nonadjacent":
        candidate["channel_edge_flat_from_to"][0, 1] = 7*n+9
        candidate["Core_dominant_receiver_index"][7, 6] = 7*n+9
    elif change == "two_receivers":
        candidate["channel_edge_flat_from_to"] = np.array(
            [[7*n+6, 7*n+7], [7*n+6, 7*n+8]], dtype="int32")
        report["child_core_dominant_channel_ledger"]["ordinary_adjacent_channel_edges"] = 2
    elif change == "lake_link_overlap":
        candidate["lake_proxy_jumps_flat_from_to"] = np.array(
            [[7*n+6, 7*n+7]], dtype="int32")
        report["child_core_dominant_channel_ledger"]["nonphysical_proxy_links_NOT_RIVERS"] = 1
    elif change == "wrong_ledger":
        report["child_core_dominant_channel_ledger"]["ordinary_adjacent_channel_edges"] = 11
    elif change == "accepted_map":
        p4a["is_author_canon"] = True
    with pytest.raises(DrainageEvidenceError):
        build_evidence(child, cm, candidate, report, img, p4a, tmp_path/"bad")
    assert not (tmp_path/"bad").exists()


def test_no_ordinary_channels_produces_honest_empty_candidate_map(tmp_path):
    child, cm, candidate, report, p4a, img = fixture()
    candidate["channel_edge_flat_from_to"] = np.empty((0, 2), dtype="int32")
    report["child_core_dominant_channel_ledger"]["ordinary_adjacent_channel_edges"] = 0
    candidate["channel_mask"][:] = 0
    candidate["Core_dominant_receiver_index"][:] = -1
    audit = build_evidence(child, cm, candidate, report, img, p4a, tmp_path/"empty")
    assert audit["raw_candidate_ordinary_edges"] == 0
    assert audit["displayable_strictly_downhill_edges"] == 0
    assert audit["is_accepted_hydrology"] is False


def test_virtual_fill_is_flagged_as_numerical_uncertainty_not_water(monkeypatch):
    import scripts.render_region_drainage_evidence_v02 as mod
    child, cm, candidate, report, p4a, img = fixture()
    z = child["child_elevation_m"]
    original = mod.priority_flood_surfaces
    def fake_surface(elev):
        from types import SimpleNamespace
        real = original(elev)
        f = np.array(real.fill_elevation_m, copy=True)
        f[7, 6] += 8
        return SimpleNamespace(fill_elevation_m=f,
                               routing_elevation_m=real.routing_elevation_m)
    monkeypatch.setattr(mod, "priority_flood_surfaces", fake_surface)
    masks, audit = screen_candidate_links(child, cm, candidate, report, p4a)
    assert audit["unresolved_fill_cells_over_limit"] >= 1
    assert audit["withheld_unsafe_ordinary_edges"] == 1
    assert masks["candidate_display_edges_NOT_CONFIRMED_RIVERS"].shape == (0, 2)
    assert masks["withheld_ordinary_edges_NOT_DISPLAYED"].shape == (1, 2)



def test_min_display_area_omits_only_visual_minor_branches(tmp_path):
    child, cm, candidate, report, p4a, img = fixture()
    audit = build_evidence(
        child, cm, candidate, report, img, p4a, tmp_path/"major",
        min_display_dominant_area_km2=600.)
    assert audit["all_strictly_downhill_edges"] == 1
    assert audit["displayable_strictly_downhill_edges"] == 0
    assert audit["omitted_minor_strict_edges_display_only"] == 1
    assert audit["withheld_unsafe_ordinary_edges"] == 0
    with np.load(tmp_path/"major/drainage-evidence-masks.npz") as z:
        assert len(z["all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS"]) == 1
        assert len(z["omitted_minor_strict_edges_NOT_DISPLAYED"]) == 1
        assert len(z["candidate_display_edges_NOT_CONFIRMED_RIVERS"]) == 0
    # Restore normal default without modifying any model state.
    ref = build_evidence(
        child, cm, candidate, report, img, p4a, tmp_path/"all",
        min_display_dominant_area_km2=0)
    assert ref["displayable_strictly_downhill_edges"] == 1
    with pytest.raises(DrainageEvidenceError, match="minimum display area"):
        screen_candidate_links(
            child, cm, candidate, report, p4a,
            min_display_dominant_area_km2=-1)
