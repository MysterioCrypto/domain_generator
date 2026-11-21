"""P2-B2.6: exact Core lake geometry and proxy routing != actual lakes."""

import numpy as np
import pytest

from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.continuous import (
    choose_lake_outlets, continuous_routing_field,
    distributed_flow_accumulation_km2,
)
from domain_generator.hydrology.routing import priority_flood_surfaces
from scripts.diagnose_planetary_child_lake_topology_v02 import (
    BasinTopologyReviewError, audit_child_lake_routing,
)


def _child(size=21, *, basin=True):
    yy, xx = np.indices((size, size), dtype=float)
    dem = 230. - .8*xx + .03*(size-yy-10.5)**2
    if basin:
        c = size//2
        dem[c-2:c+3,c-2:c+3] -= 18.
    return {
        "child_elevation_m": dem.astype(np.float32),
        "land_mask": np.ones((size,size), dtype=np.uint8),
        "east_km": np.arange(size, dtype=float),
        "north_km_north_first": np.arange(size-1,-1,-1,dtype=float),
    }


def test_actual_core_spill_plus_accumulator_matches_unchanged_slow_core_small():
    child = _child()
    copy = child["child_elevation_m"].copy()
    result, report = audit_child_lake_routing(
        child, lake_min_area_km2=2, lake_min_depth_m=1,
    )
    dem = copy.astype(float)
    surf = priority_flood_surfaces(dem)
    f = continuous_routing_field(surf.routing_elevation_m, cell_size_km=1)
    candidates = extract_lake_candidates(
        dem, surf.fill_elevation_m, cell_size_km=1,
        lake_min_area_km2=2, lake_min_depth_m=1,
    )
    assert len(candidates) == report["geometric_candidate_count"] == 1
    outlets = choose_lake_outlets(dem, surf.routing_elevation_m, f, candidates)
    reference = distributed_flow_accumulation_km2(
        f, cell_size_km=1, lake_candidates=candidates, lake_outlets=outlets,
    )
    np.testing.assert_allclose(
        result["area_with_candidate_lake_proxy_km2_UNRESOLVED_ZERO_IF_ABSENT"],
        reference, rtol=5e-12, atol=2e-8,
    )
    no_lake = distributed_flow_accumulation_km2(f, cell_size_km=1)
    np.testing.assert_allclose(
        result["area_baseline_without_lake_proxy_km2"],
        no_lake, rtol=5e-12, atol=2e-8,
    )
    assert report["with_vs_without_lakes_comparable"]
    assert report["candidate_lake_mass_balance"]["lake_supernode_count"] == 1
    assert abs(report["candidate_lake_mass_balance"]["balance_error_km2"]) < 1e-7
    assert abs(report["no_lake_mass_balance"]["balance_error_km2"]) < 1e-7
    assert report["actual_lakes_inferred"] is False
    assert report["original_terrain_modified"] is False
    assert report["river_discharge_m3s_inferred"] is False
    np.testing.assert_array_equal(child["child_elevation_m"], copy)


def test_dry_slope_does_not_invent_depression_or_water():
    a, report = audit_child_lake_routing(_child(basin=False))
    assert report["geometric_candidate_count"] == 0
    assert report["candidate_routing_status"] == "NO_THRESHOLD_QUALIFIED_BASINS"
    assert not report["with_vs_without_lakes_comparable"]
    assert not a["lake_comparison_available_mask"].any()
    assert not a["geometric_candidate_id_NOT_WATER"].any()
    assert report["candidate_lake_mass_balance"] is None


def test_basin_limit_fails_closed_not_equal_zero_impact():
    fields, report = audit_child_lake_routing(
        _child(), lake_min_area_km2=2, lake_min_depth_m=1,
        max_lake_supernodes=0
    )
    assert report["geometric_candidate_count"] == 1
    assert report["candidate_routing_status"] == "UNRESOLVED_TOO_MANY_CANDIDATE_BASINS"
    assert not report["with_vs_without_lakes_comparable"]
    assert report["absolute_terminal_redistribution_km2"] is None
    assert report["candidate_lake_mass_balance"] is None
    assert np.all(fields["lake_comparison_available_mask"] == 0)
    assert np.all(fields["display_area_difference_km2_NOT_COMPARABLE_IF_UNRESOLVED"] == 0)


def test_lake_cell_complexity_limit_is_an_explicit_review_gate():
    _, note = audit_child_lake_routing(
        _child(), lake_min_area_km2=2, lake_min_depth_m=1,
        max_total_candidate_cells=1,
    )
    assert note["candidate_routing_status"] == "UNRESOLVED_LAKE_CELL_COMPLEXITY_LIMIT"
    assert note["geometric_candidate_total_cells"] > 1


def test_threshold_sensitivity_only_changes_candidates_not_priority_flood():
    child = _child()
    soft, low = audit_child_lake_routing(
        child, lake_min_area_km2=2, lake_min_depth_m=1
    )
    hard, high = audit_child_lake_routing(
        child, lake_min_area_km2=300, lake_min_depth_m=100
    )
    assert low["geometric_candidate_count"] >= high["geometric_candidate_count"]
    np.testing.assert_array_equal(
        soft["virtual_fill_depth_m_NOT_WATER"],
        hard["virtual_fill_depth_m_NOT_WATER"],
    )
    assert not hard["actual_lakes_inferred"]
    assert not low["actual_lakes_inferred"]


def test_reproducible_proxy_spills_and_mass_balance_fields():
    a, r1 = audit_child_lake_routing(
        _child(), lake_min_area_km2=2, lake_min_depth_m=1
    )
    b, r2 = audit_child_lake_routing(
        _child(), lake_min_area_km2=2, lake_min_depth_m=1
    )
    assert r1 == r2
    for k in a:
        np.testing.assert_array_equal(a[k],b[k])
    assert r1["basins"][0]["spill"] is not None
    assert r1["basins"][0]["spill"]["is_perennial_water_discharge"] is False
    assert abs(sum([r1["candidate_lake_mass_balance"]["boundary_terminal_area_km2"]])
               -21*21) < 1e-7


def test_input_marine_and_distorted_axes_rejected_without_reinterpretation():
    child = _child()
    child["land_mask"][0,0] = 0
    with pytest.raises(BasinTopologyReviewError, match="inland-only"):
        audit_child_lake_routing(child)
    child = _child()
    child["east_km"] = child["east_km"]**2
    with pytest.raises(BasinTopologyReviewError, match="uniform square"):
        audit_child_lake_routing(child)


def test_nonfinite_invalid_controls_fail_closed():
    for kwargs in (
        {"lake_min_area_km2": -1},
        {"lake_min_depth_m": float("nan")},
        {"max_lake_supernodes": -1},
        {"max_total_candidate_cells": -1},
        {"hierarchy_cell_limit": -1},
    ):
        with pytest.raises(BasinTopologyReviewError):
            audit_child_lake_routing(_child(), **kwargs)


def test_large_synthetic_region_uses_real_core_and_separate_mass_conserving_lake_graph():
    child = _child(65)
    fields, note = audit_child_lake_routing(
        child, lake_min_area_km2=4, lake_min_depth_m=2,
        max_total_candidate_cells=500,
    )
    assert fields["virtual_fill_depth_m_NOT_WATER"].shape == (65,65)
    assert note["no_lake_mass_balance"]["mfd_node_count"] == 65**2
    assert abs(note["no_lake_mass_balance"]["balance_error_km2"]) < 1e-7
    assert not note["external_macro_A8_inflow_applied"]
    assert not note["actual_lakes_inferred"]
