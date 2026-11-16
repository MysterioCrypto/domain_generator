"""P2-B child MFD audit; no fake global inflows or accepted-source D8 substitution."""

import numpy as np
import pytest

from domain_generator.hydrology.continuous import (
    continuous_routing_field,
    distributed_flow_accumulation_km2,
)
from domain_generator.hydrology.routing import priority_flood_surfaces
from scripts.diagnose_planetary_child_mfd_v02 import (
    ChildDrainageError, fast_mfd_accumulation, derive_drainage,
)


def _terrain(rows=21, cols=25):
    rng = np.random.default_rng(22)
    yy, xx = np.indices((rows, cols))
    return (400 - 2.5 * xx - 3.2 * yy
            + rng.normal(0, 0.4, (rows, cols)))


def _child(rows=71, cols=71):
    return {
        "child_elevation_m": _terrain(rows, cols).astype(np.float32),
        "land_mask": np.ones((rows, cols), dtype=np.uint8),
        "east_km": np.arange(cols) - (cols - 1) / 2,
        "north_km_north_first": (rows - 1) / 2 - np.arange(rows),
    }


def _macro():
    lat = np.array([.6, .3, 0, -.3, -.6], dtype=np.float64)
    lon = lat[::-1].copy()
    r, c = np.indices((5, 5))
    # Old D8 river southward through central column, spanning the child region.
    downstream = np.full((5, 5), -1, dtype=np.int64)
    for row in range(4):
        downstream[row, 2] = (row + 1) * 5 + 2
    mask = np.zeros((5, 5), dtype=np.uint8)
    mask[:, 2] = 1
    return {
        "latitude_deg_north_first": lat,
        "longitude_deg_west_to_east": lon,
        "source_river_mask_D8": mask,
        "local_downstream_index": downstream,
    }


def _manifest():
    return {
        "status": "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData": False,
        "planet_radius_km": 7008.1,
        "center_lat_lon_deg": [0.0, 0.0],
    }


def test_fast_accumulation_matches_accepted_core_weighted_dag_exact_fraction_semantics():
    heights = _terrain(17, 19)
    surfaces = priority_flood_surfaces(heights)
    field = continuous_routing_field(surfaces.routing_elevation_m, cell_size_km=1.0)
    fast, ledger = fast_mfd_accumulation(field.fractions, surfaces.routing_elevation_m, 1.0)
    accepted = distributed_flow_accumulation_km2(field, cell_size_km=1.0)
    np.testing.assert_allclose(fast, accepted, rtol=3e-14, atol=3e-12)
    assert ledger["local_source_area_km2"] == 17 * 19
    assert abs(ledger["boundary_balance_error_km2"]) < 1e-8
    assert ledger["boundary_cells"] == 2 * (17 + 19) - 4


def test_diagnostic_uses_real_mfd_not_d8_and_tracks_outside_boundary_loss():
    child, macro = _child(), _macro()
    data, report, reference = derive_drainage(
        child, macro, _manifest(), stream_threshold_km2=15.0
    )
    assert data["child_MFD_accumulation_km2"].shape == (71, 71)
    assert data["child_MFD_major_channel_support_mask"].sum() > 0
    assert report["child_MFD"]["method"].startswith("accepted Core 0.2")
    assert "NOT YET ENFORCED" in report["parent_child_consistency"]
    assert report["outlets"]["boundary_inflow_missing"]
    assert abs(report["mass_ledger"]["boundary_balance_error_km2"]) < 1e-7
    assert report["mass_ledger"]["local_source_area_km2"] == 71 * 71
    assert reference.shape[1:] == (2, 2)
    assert report["source_reference"]["source_d8_visible_river_links"] > 0
    assert "D8" in report["source_reference"]["source_d8_limit"]
    assert report["child_MFD"]["lake_and_marine_handling"].startswith("NOT IMPLEMENTED")


def test_changed_mfd_source_terrain_changes_drainage_but_not_macro_guide():
    child = _child()
    a, report_a, guide_a = derive_drainage(
        child, _macro(), _manifest(), stream_threshold_km2=20
    )
    changed = {**child, "child_elevation_m": child["child_elevation_m"] + (
        np.sin(np.arange(71)[None, :] / 7) * 12
    )}
    b, report_b, guide_b = derive_drainage(
        changed, _macro(), _manifest(), stream_threshold_km2=20
    )
    np.testing.assert_array_equal(guide_a, guide_b)
    assert not np.array_equal(a["child_MFD_accumulation_km2"],
                              b["child_MFD_accumulation_km2"])
    assert report_a["mass_ledger"]["local_source_area_km2"] == (
        report_b["mass_ledger"]["local_source_area_km2"]
    )


def test_inland_only_does_not_silently_claim_h12_coastal_and_lake_physics():
    child = _child()
    child["land_mask"][0, 0] = 0
    with pytest.raises(ChildDrainageError, match="inland-only"):
        derive_drainage(child, _macro(), _manifest())
    child["land_mask"][0, 0] = 1
    with pytest.raises(ChildDrainageError, match="positive"):
        derive_drainage(child, _macro(), _manifest(), stream_threshold_km2=-1)


def test_accumulation_rejects_bad_fractions_and_non_downhill_receivers():
    dem = _terrain(9, 9)
    s = priority_flood_surfaces(dem)
    flow = continuous_routing_field(s.routing_elevation_m, cell_size_km=1)
    fractions = flow.fractions.copy()
    fractions[3, 3, :] = 0
    with pytest.raises(ChildDrainageError, match="sum"):
        fast_mfd_accumulation(fractions, s.routing_elevation_m, 1)
    with pytest.raises(ChildDrainageError, match="shape"):
        fast_mfd_accumulation(flow.fractions[:, :, :4], s.routing_elevation_m, 1)
    bad_dem = np.zeros_like(s.routing_elevation_m)
    with pytest.raises(ChildDrainageError, match="strictly downhill"):
        fast_mfd_accumulation(flow.fractions, bad_dem, 1)


def test_fixed_input_exactly_replays_drainage_and_outlet_ledger():
    child, macro = _child(), _macro()
    a, ra, ga = derive_drainage(child, macro, _manifest(), stream_threshold_km2=15)
    b, rb, gb = derive_drainage(child, macro, _manifest(), stream_threshold_km2=15)
    for name in a:
        np.testing.assert_array_equal(a[name], b[name])
    assert ra == rb
    np.testing.assert_array_equal(ga, gb)
