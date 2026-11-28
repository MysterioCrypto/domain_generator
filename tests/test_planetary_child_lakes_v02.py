"""P2-B2.1: never promote Priority-Flood geometry to real surface lakes."""

import numpy as np
import pytest

from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.routing import priority_flood_surfaces
from scripts.audit_planetary_child_lakes_v02 import (
    ChildLakeAuditError,
    audit_child_depressions,
)


def _bowl(rows=21, cols=21):
    """Known one-basin example from accepted Core H07 regression."""
    terrain = np.empty((rows, cols), dtype=np.float64)
    for row in range(rows):
        yy = rows - row - .5
        for col in range(cols):
            xx = col + .5
            terrain[row, col] = 200 - .8 * xx + .03 * (yy - 10.5) ** 2
    terrain[8:13, 8:13] -= 18
    return {
        "child_elevation_m": terrain.copy(),
        "land_mask": np.ones((rows, cols), dtype=np.uint8),
        "east_km": np.arange(cols, dtype=float),
        "north_km_north_first": np.arange(rows - 1, -1, -1, dtype=float),
    }


def test_actual_accepted_core_candidate_detection_and_spill_reference():
    data = _bowl()
    before = data["child_elevation_m"].copy()
    arrays, report = audit_child_depressions(
        data, lake_min_area_km2=2, lake_min_depth_m=1
    )
    actual = extract_lake_candidates(
        before, priority_flood_surfaces(before).fill_elevation_m,
        cell_size_km=1, lake_min_area_km2=2, lake_min_depth_m=1,
    )
    assert len(actual) == len(report["basins"]) == 1
    assert report["threshold_qualified_basins"] == 1
    assert report["candidate_spill_count"] == 1
    assert report["small_grid_core_supernode_area_ledger"]["passed"] is True
    assert abs(report["small_grid_core_supernode_area_ledger"]["balance_error_km2"]) < 1e-8
    basin = report["basins"][0]
    assert basin["area_km2"] == actual[0].area_km2
    assert basin["max_required_fill_m"] == actual[0].max_depth_m
    assert basin["storage_to_spill_proxy_km3"] > 0
    assert basin["outlet"] is not None
    assert basin["outlet"]["lake_cell"] in [list(c) for c in actual[0].cells]
    assert np.array_equal(data["child_elevation_m"], before)
    assert np.count_nonzero(arrays["provisional_lake_basin_id"]) == len(actual[0].cells)
    assert basin["status"].startswith("geometrically-qualified-")


def test_depression_not_equal_water_and_author_approval_never_inferred():
    _, report = audit_child_depressions(
        _bowl(), lake_min_area_km2=2, lake_min_depth_m=1
    )
    assert not report["physical_water_coverage_inferred"]
    assert report["author_approved_lakes"] == 0
    assert not report["external_macro_inflow_used"]
    assert not report["macro_A8_D8_forced"]
    assert report["status"].endswith("NOT_WATER_OCCUPANCY")
    assert report["thresholds"]["lake_min_depth_m"] == 1


def test_shallow_depression_remains_unqualified_and_not_called_real_lake():
    child = _bowl()
    terrain = child["child_elevation_m"]
    # Preserve a genuine shallow pit but apply a much higher depth requirement.
    _, report = audit_child_depressions(
        child, lake_min_area_km2=2, lake_min_depth_m=50
    )
    assert report["threshold_qualified_basins"] == 0
    assert report["candidate_spill_count"] == 0
    assert report["fill_required_cells"] > 0
    assert report["other_virtual_fill_cells"] == report["fill_required_cells"]
    assert not report["physical_water_coverage_inferred"]


def test_thresholds_are_explicit_and_monotonic_for_same_geometry():
    child = _bowl()
    a, ra = audit_child_depressions(
        child, lake_min_area_km2=2, lake_min_depth_m=1
    )
    b, rb = audit_child_depressions(
        child, lake_min_area_km2=10000, lake_min_depth_m=1
    )
    assert rb["threshold_qualified_cells"] <= ra["threshold_qualified_cells"]
    assert rb["threshold_qualified_basins"] <= ra["threshold_qualified_basins"]
    np.testing.assert_array_equal(
        a["required_fill_depth_m"], b["required_fill_depth_m"]
    )


def test_exact_replay_and_stable_basin_outlet_ids():
    x, ledger1 = audit_child_depressions(_bowl(), lake_min_area_km2=2,
                                         lake_min_depth_m=1)
    y, ledger2 = audit_child_depressions(_bowl(), lake_min_area_km2=2,
                                         lake_min_depth_m=1)
    assert ledger1 == ledger2
    for name in x:
        np.testing.assert_array_equal(x[name], y[name])


def test_prohibit_silent_marine_and_invalid_grid_or_thresholds():
    child = _bowl()
    child["land_mask"][0, 0] = 0
    with pytest.raises(ChildLakeAuditError, match="inland-only"):
        audit_child_depressions(child)
    child = _bowl()
    with pytest.raises(ChildLakeAuditError, match="positive"):
        audit_child_depressions(child, lake_min_area_km2=0)
    with pytest.raises(ChildLakeAuditError, match="uniform"):
        warped = child | {"east_km": child["east_km"]**2}
        audit_child_depressions(warped)


def test_large_grid_does_not_fake_lake_supernode_conservation():
    child = _bowl(21, 21)
    _, ledger = audit_child_depressions(
        child, lake_min_area_km2=2, lake_min_depth_m=1,
        reference_graph_cell_limit=100,
    )
    assert not ledger["small_grid_core_supernode_area_ledger"]["attempted"]
    assert not ledger["small_grid_core_supernode_area_ledger"]["passed"]
    assert ledger["candidate_spill_count"] == 1


def test_ambiguous_or_unbounded_lake_spill_review_is_not_accepted():
    child = _bowl()
    _, ledger = audit_child_depressions(
        child, lake_min_area_km2=2, lake_min_depth_m=1,
        max_outlet_review=1
    )
    assert ledger["threshold_qualified_basins"] == 1
    assert ledger["candidate_spill_count"] == 1
    assert ledger["physical_water_coverage_inferred"] is False
