"""P2-B2.5: candidate DEM corridor may NEVER silently become a canonical river."""

import numpy as np
import pytest

from scripts.propose_planetary_river_corridor_v02 import (
    CorridorConditioningError, bounded_corridor_delta,
    candidate_corridor_terrain, compare_candidate,
    macro_river_segments,
)


def _world():
    lat = np.array([.6, .3, 0., -.3, -.6], dtype=float)
    lon = np.array([-.6, -.3, 0., .3, .6], dtype=float)
    xx, yy = np.meshgrid(lon, lat)
    height = (350 + yy*70 + xx*5).astype(np.float32)
    river = np.zeros((5, 5), dtype=np.uint8)
    down = np.full((5, 5), -1, dtype=np.int32)
    for r in range(1, 4):
        river[r, 2] = 1
        down[r, 2] = (r+1)*5+2
    macro = {
        "latitude_deg_north_first": lat,
        "longitude_deg_west_to_east": lon,
        "source_river_mask_D8": river,
        "local_downstream_index": down,
        "source_catchment_km2_D8": np.ones((5, 5))*200,
        "elevation_m": height,
        "land_mask": np.ones((5, 5), dtype=np.uint8),
    }
    east = np.arange(-40., 41., 1.)
    north = east[::-1].copy()
    X, Y = np.meshgrid(east, north)
    child = {
        "east_km": east,
        "north_km_north_first": north,
        "child_elevation_m": (280 + .9*Y + .035*X).astype(np.float32),
        "land_mask": np.ones((81,81), dtype=np.uint8),
    }
    manifest = {
        "status": "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData": False,
        "planet_radius_km": 7008.1,
        "center_lat_lon_deg": [0., 0.],
    }
    return child, macro, manifest


def test_exact_original_A8_macro_anchor_corrections_and_fixed_edges():
    child, macro, m = _world()
    arrays, note = candidate_corridor_terrain(child, macro, m)
    assert note["original_macro_river_segments"] == 3
    assert note["source_anchor_correction_error_m"] <= 1e-9
    assert note["source_boundary_max_change_m"] == 0
    assert note["source_macro_station_elevations_preserved_analytically"]
    assert note["shoreline_sign_preserved"]
    assert note["maximum_excavation_m"] <= 15.001
    assert note["modified_child_pixels"] > 0
    assert np.max(arrays["source_guidance_delta_m"]) <= 1e-4
    assert not np.array_equal(
        arrays["new_child_elevation_m"], child["child_elevation_m"]
    )
    assert not note["not_physically_validated"] is False
    assert note["not_seamless_for_different_crop_windows"]


def test_candidate_cannot_change_parent_and_input_is_not_mutated():
    child, macro, m = _world()
    original = child["child_elevation_m"].copy()
    a, ra = candidate_corridor_terrain(child,macro,m)
    b, rb = candidate_corridor_terrain(child,macro,m)
    assert ra == rb
    for k in a:
        np.testing.assert_array_equal(a[k], b[k])
    np.testing.assert_array_equal(child["child_elevation_m"], original)
    assert not np.any(a["new_child_elevation_m"] < 0)


def test_delta_evaluated_at_every_true_macro_station_is_zero():
    child, macro, m = _world()
    seg = macro_river_segments(
        macro,center_lat=0,center_lon=0,planet_radius_km=7008.1
    )
    degrees = np.pi*7008.1/180.
    X, Y = np.meshgrid(
        macro["longitude_deg_west_to_east"]*degrees,
        macro["latitude_deg_north_first"]*degrees
    )
    delta = bounded_corridor_delta(
        X,Y,segments=seg,
        xnodes=macro["longitude_deg_west_to_east"]*degrees,
        ynodes=macro["latitude_deg_north_first"]*degrees,
        bounds=(-40,40,-40,40),depth_m=15,width_km=5,
        anchor_taper_km=2,boundary_taper_km=5
    )
    np.testing.assert_allclose(delta,0,atol=1e-12,rtol=0)


def test_empty_river_source_never_makes_up_its_own_canyon():
    child, macro, m = _world()
    macro["source_river_mask_D8"][:]=0
    arr, note = candidate_corridor_terrain(child,macro,m)
    assert note["original_macro_river_segments"] == 0
    assert note["modified_child_pixels"] == 0
    np.testing.assert_array_equal(
        arr["new_child_elevation_m"],child["child_elevation_m"]
    )


def test_bad_original_graph_and_coastline_rejected():
    child, macro, m = _world()
    child["land_mask"][10,10] = 0
    with pytest.raises(CorridorConditioningError,match="inland-only"):
        candidate_corridor_terrain(child,macro,m)
    child,macro,m=_world()
    macro["local_downstream_index"][1,2]=999
    with pytest.raises(CorridorConditioningError,match="invalid aligned"):
        candidate_corridor_terrain(child,macro,m)
    child,macro,m=_world()
    m["is_accepted_Core_DomainData"]=True
    with pytest.raises(CorridorConditioningError,match="noncanonical"):
        candidate_corridor_terrain(child,macro,m)


def test_negative_depth_and_zero_width_fails_closed():
    child,macro,m=_world()
    for kwargs in ({"depth_m":-5},{"width_km":0},{"anchor_taper_km":0},
                   {"boundary_taper_km":float("inf")}):
        with pytest.raises(CorridorConditioningError,match="positive"):
            candidate_corridor_terrain(child,macro,m,**kwargs)


def test_compare_before_after_core_mfd_does_not_approve_candidate():
    child, macro, m = _world()
    a,note=compare_candidate(child,macro,m,stream_threshold_km2=20)
    assert note["before"]["major_macro_exits"] == 1
    assert note["after"]["major_macro_exits"] == 1
    assert note["decision"] in {
        "BASELINE_MACRO_EXITS_ALREADY_NEAR_NO_AUTOCORRECTION",
        "NO_GEOMETRIC_IMPROVEMENT_REJECT_CANDIDATE",
        "GEOMETRICALLY_IMPROVED_ONLY_REQUIRES_AUTHOR_AND_BASIN_REVIEW",
    }
    assert not note["accepted_into_Core_or_original_child"]
    assert not note["new_P2B25_original_river_alignment_approved"]
    assert note["no_A8_auto_injected_area"]
    assert a["before_channel"].shape == a["after_channel"].shape == (81,81)


def test_without_old_major_A8_exit_improvement_is_unverifiable():
    child,macro,m=_world()
    # River guide runs INTO region, but does not EXIT according to old mask.
    macro["source_river_mask_D8"][3,2] = 0
    a,note=compare_candidate(child,macro,m,stream_threshold_km2=25)
    assert note["before"]["major_macro_exits"] == 0
    assert note["decision"] == "NO_MAJOR_MACRO_OUTLETS_CANNOT_VALIDATE_CORRIDOR"
    assert not note["accepted_into_Core_or_original_child"]
