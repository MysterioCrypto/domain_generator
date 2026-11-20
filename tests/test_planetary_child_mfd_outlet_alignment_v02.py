"""P2-B2.4: compare original A8 macro exits to connected child Core MFD paths."""

import numpy as np
import pytest

from scripts.compare_planetary_child_mfd_outlets_v02 import (
    OutletAlignmentError, analyze_outlets,
    connected_mfd_channel_projection, macro_outlet_candidates, match_outlets,
)


def _macro():
    lat = np.array([.6, .3, 0, -.3, -.6], dtype=np.float64)
    lon = np.array([-.6, -.3, 0, .3, .6], dtype=np.float64)
    d = np.full((5, 5), -1, dtype=np.int32)
    r = np.zeros((5, 5), dtype=np.uint8)
    for row in range(4):
        d[row, 2] = (row + 1)*5 + 2
        r[row, 2] = 1
    return {
        "latitude_deg_north_first": lat,
        "longitude_deg_west_to_east": lon,
        "local_downstream_index": d,
        "source_river_mask_D8": r,
        "source_catchment_km2_D8": np.ones((5, 5))*450,
        "source_downstream_exits_region": np.zeros((5, 5), dtype=np.uint8),
    }


def _child(size=81):
    yy, xx = np.indices((size, size))
    return {
        "child_elevation_m": (350 - .75*yy - .14*xx).astype(np.float32),
        "land_mask": np.ones((size,size), dtype=np.uint8),
        "east_km": np.arange(size, dtype=float) - (size-1)/2,
        "north_km_north_first": (size-1)/2 - np.arange(size, dtype=float),
    }


def _manifest():
    return {
        "center_lat_lon_deg":[0.,0.],
        "planet_radius_km":7008.1,
        "status":"NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData":False,
    }


def test_macro_old_river_exits_follow_directed_inside_to_outside():
    exits, ledger = macro_outlet_candidates(_macro(), _child(), _manifest())
    assert ledger["all_directed_A8_links_exiting_child_box"] == 1
    assert ledger["major_A8_river_links_exiting_child_box"] == 1
    assert ledger["macro_crop_insufficient_for_inside_major_links"] == 0
    assert len(exits) == 1
    assert exits[0]["side"] == "south"
    assert exits[0]["crossing_east_north_km"][1] == pytest.approx(-40)
    assert exits[0]["old_A8_upstream_area_km2_UNSAFE_HINT"] == 450
    assert not exits[0]["is_verified_child_MFD_outlet"]


def test_mfd_channels_are_connected_through_real_positive_core_receivers():
    child, macro, manifest = _child(), _macro(), _manifest()
    fields, ledger = connected_mfd_channel_projection(
        child, macro, manifest, stream_threshold_km2=15
    )
    assert ledger["routed_ordinary_channel_cells"] > 50
    assert ledger["ordinary_adjacent_channel_edges"] > 40
    assert ledger["connected_boundary_endpoints"]
    assert ledger["headwater_seed_cells"] > 0
    assert ledger["no_external_A8_source_area_auto_injected"]
    assert not ledger["is_physical_discharge_or_approved_river"]
    assert ledger["lake_topology_status"] == "NO_LAKES_QUALIFIED"
    nx = child["child_elevation_m"].shape[1]
    channel = fields["channel_mask"].astype(bool)
    edge_pairs = fields["channel_edge_flat_from_to"]
    assert edge_pairs.shape[1] == 2
    for u, v in edge_pairs:
        ur, uc = divmod(int(u), nx)
        vr, vc = divmod(int(v), nx)
        assert channel[ur,uc] and channel[vr,vc]
        assert max(abs(ur-vr),abs(uc-vc)) <= 1
    terminal_ids = [
        tuple(v["child_edge_cell_row_col"])
        for v in ledger["connected_boundary_endpoints"]
    ]
    assert len(set(terminal_ids)) == len(terminal_ids)
    assert all((r in (0,80) or c in (0,80)) for r,c in terminal_ids)


def test_macro_outlet_match_is_geometric_only_and_can_fail():
    macro = [
        {"key": "A", "side": "south", "crossing_east_north_km": [0,-40]},
        {"key": "B", "side": "south", "crossing_east_north_km": [3,-40]},
        {"key": "C", "side": "north", "crossing_east_north_km": [0,40]},
    ]
    child = [
        {"child_edge_cell_row_col": [80,40], "side": "south",
         "crossing_east_north_km": [0,-40]},
        {"child_edge_cell_row_col": [0,40], "side": "east",
         "crossing_east_north_km": [0,40]},
    ]
    out = match_outlets(macro, child, tolerance_km=5)
    assert out["same_side_near_matches"] == 1
    assert out["unmatched_major_macro_exits"] == 2
    assert out["unmatched_child_terminals"] == 1
    assert not out["is_hydrologically_validated"]
    assert out["comparisons"][0]["status"].startswith("GEOMETRICALLY_")
    assert out["comparisons"][1]["status"] == "UNMATCHED_MACRO_EXIT"
    assert out["comparisons"][2]["status"] == "UNMATCHED_MACRO_EXIT"


def test_complete_child_reference_has_repeatable_arrays_and_explicit_mismatch():
    child, macro, manifest = _child(), _macro(), _manifest()
    a, report_a = analyze_outlets(child, macro, manifest, stream_threshold_km2=25)
    b, report_b = analyze_outlets(child, macro, manifest, stream_threshold_km2=25)
    for key in a:
        np.testing.assert_array_equal(a[key], b[key])
    assert report_a == report_b
    assert report_a["status"].startswith("P2_B2_4")
    assert not report_a["is_author_approved_local_river_map"]
    assert report_a["external_area_auto_injected_km2"] == 0.0
    assert not report_a["coarse_to_fine_outlet_alignment"]["is_hydrologically_validated"]


def test_no_source_exit_does_not_invent_match():
    macro = _macro()
    macro["source_river_mask_D8"] = np.zeros_like(macro["source_river_mask_D8"])
    fields, r = analyze_outlets(_child(), macro, _manifest(), stream_threshold_km2=20)
    assert r["source_macro_A8_outlet_ledger"]["major_A8_river_links_exiting_child_box"] == 0
    assert r["coarse_to_fine_outlet_alignment"]["same_side_near_matches"] == 0
    assert r["child_core_dominant_channel_ledger"]["routed_ordinary_channel_cells"] > 0
    assert fields["channel_mask"].sum() > 0


def test_invalid_A8_macro_link_and_threshold_fail_closed():
    macro = _macro()
    macro["local_downstream_index"][3,2] = 9999
    with pytest.raises(OutletAlignmentError, match="flattened"):
        macro_outlet_candidates(macro, _child(), _manifest())
    with pytest.raises(OutletAlignmentError, match="positive"):
        match_outlets([], [], tolerance_km=0)
    with pytest.raises(OutletAlignmentError, match="positive"):
        connected_mfd_channel_projection(
            _child(), _macro(), _manifest(), stream_threshold_km2=-1
        )


def test_unresolvable_geometric_lake_is_flagged_not_called_real_lake():
    child, macro, manifest = _child(), _macro(), _manifest()
    child["child_elevation_m"][33:48,33:48] -= 25
    a, report = connected_mfd_channel_projection(
        child, macro, manifest,
        stream_threshold_km2=25,
        lake_min_area_km2=10, lake_min_depth_m=3,
        max_lake_supernodes=0,  # explicitly force unresolved lake topology
    )
    assert "UNRESOLVED" in report["lake_topology_status"]
    assert not report["is_physical_discharge_or_approved_river"]
    assert report["geometric_lake_proxy_cells_traversed"] == 0
    assert a["channel_mask"].sum() > 0
