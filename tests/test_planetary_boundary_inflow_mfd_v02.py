"""P2-B2.2: no automatic D8 catchment injection and Core lake topology parity."""

import numpy as np
import pytest

from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.continuous import (
    choose_lake_outlets, continuous_routing_field, distributed_flow_accumulation_km2,
)
from domain_generator.hydrology.routing import priority_flood_surfaces
from scripts.condition_planetary_child_boundary_mfd_v02 import (
    BoundaryIntegrationError, accumulate_mfd_with_lake_nodes,
    analyze_boundary, source_inlet_candidates, validate_declared_inlets,
)


def _bowl():
    rows = cols = 21
    dem = np.empty((rows, cols), dtype=float)
    for row in range(rows):
        y = rows - row - .5
        for col in range(cols):
            x = col + .5
            dem[row, col] = 200 - .8 * x + .03 * (y - 10.5) ** 2
    dem[8:13, 8:13] -= 18
    return dem


def _source():
    lat = np.array([.6, .3, 0, -.3, -.6])
    lon = lat[::-1].copy()
    river = np.zeros((5, 5), dtype=np.uint8)
    river[:, 2] = 1
    receiver = np.full((5, 5), -1, dtype=np.int64)
    for r in range(4):
        receiver[r, 2] = (r + 1) * 5 + 2
    return {
        "latitude_deg_north_first": lat,
        "longitude_deg_west_to_east": lon,
        "source_river_mask_D8": river,
        "local_downstream_index": receiver,
        "source_catchment_km2_D8": np.full((5, 5), 143.5, dtype=float),
    }


def _child(size=81):
    yy, xx = np.indices((size, size))
    return {
        "child_elevation_m": (350 - .75 * yy - .14 * xx).astype(np.float32),
        "land_mask": np.ones((size, size), dtype=np.uint8),
        "east_km": np.arange(size, dtype=float) - (size - 1) / 2,
        "north_km_north_first": (size - 1) / 2 - np.arange(size, dtype=float),
    }


def _manifest():
    return {"center_lat_lon_deg": [0.0, 0.0],
            "planet_radius_km": 7008.1,
            "status": "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
            "is_accepted_Core_DomainData": False}


def test_inlet_proposal_uses_A8_guide_only_and_does_not_inject_unsafe_area():
    props = source_inlet_candidates(_source(), _child(), _manifest())
    assert len(props) == 1
    p = props[0]
    assert p["side"] == "north"
    assert p["suggested_child_row_col"][0] == 1
    assert p["a8_upstream_catchment_km2_UNSAFE_HINT"] == 143.5
    assert p["can_auto_inject_area"] is False
    assert p["is_verified_external_only_area"] is False
    data, report = validate_declared_inlets(None, props, (81, 81))
    assert data == ()
    assert report["injected_external_area_km2"] == 0


def test_explicit_boundary_area_requires_provenance_and_does_not_copy_A8_hint():
    props = source_inlet_candidates(_source(), _child(), _manifest())
    body = {
        "schema": "P2_B2_2_EXPLICIT_A8_INFLOW_SCENARIO",
        "inflows": [{
            "source_link_key": props[0]["key"],
            "external_area_km2": 999.0,
            "area_semantics": "EXTERNAL_ONLY_AREA_EXCLUDING_CHILD",
            "operator_note": "Synthetic test explicitly assumes distinct outside area",
        }],
    }
    inlets, ledger = validate_declared_inlets(body, props, (81, 81))
    assert ledger["injected_external_area_km2"] == 999
    assert sum(v for _, _, v in inlets) == 999
    assert ledger["status"].startswith("EXPLICIT_UNVALIDATED")
    bad = dict(body)
    bad["inflows"] = [dict(body["inflows"][0], area_semantics="TOTAL_SOURCE_CATCHMENT")]
    with pytest.raises(BoundaryIntegrationError, match="EXTERNAL_ONLY"):
        validate_declared_inlets(bad, props, (81, 81))
    bad["inflows"] = [dict(body["inflows"][0], source_link_key="unknown")]
    with pytest.raises(BoundaryIntegrationError, match="absent"):
        validate_declared_inlets(bad, props, (81, 81))
    with pytest.raises(BoundaryIntegrationError, match="duplicate"):
        validate_declared_inlets(body | {"inflows": body["inflows"] * 2}, props, (81, 81))


def test_fast_no_lake_routing_matches_unmodified_Core_area():
    dem = _bowl()
    surface = priority_flood_surfaces(dem)
    f = continuous_routing_field(surface.routing_elevation_m, cell_size_km=1)
    expected = distributed_flow_accumulation_km2(f, cell_size_km=1)
    found, ledger = accumulate_mfd_with_lake_nodes(f, cell_size_km=1)
    np.testing.assert_allclose(found, expected, rtol=1e-12, atol=2e-11)
    assert ledger["lake_supernode_count"] == 0
    assert abs(ledger["balance_error_km2"]) < 1e-9


def test_small_bowl_with_Core_supernode_matches_unmodified_Core_area():
    dem = _bowl()
    surface = priority_flood_surfaces(dem)
    f = continuous_routing_field(surface.routing_elevation_m, cell_size_km=1)
    lakes = extract_lake_candidates(
        dem, surface.fill_elevation_m, cell_size_km=1,
        lake_min_area_km2=2, lake_min_depth_m=1
    )
    assert len(lakes) == 1
    outlets = choose_lake_outlets(
        dem, surface.routing_elevation_m, f, lakes
    )
    expected = distributed_flow_accumulation_km2(
        f, cell_size_km=1, lake_candidates=lakes, lake_outlets=outlets
    )
    found, ledger = accumulate_mfd_with_lake_nodes(
        f, cell_size_km=1, lakes=lakes, outlets=outlets
    )
    np.testing.assert_allclose(found, expected, rtol=5e-12, atol=2e-10)
    assert ledger["lake_supernode_count"] == 1
    assert abs(ledger["balance_error_km2"]) < 1e-9


def test_external_inflow_conserved_through_lake_supernode_and_downstream():
    dem = _bowl()
    surface = priority_flood_surfaces(dem)
    f = continuous_routing_field(surface.routing_elevation_m, cell_size_km=1)
    lakes = extract_lake_candidates(
        dem, surface.fill_elevation_m, cell_size_km=1,
        lake_min_area_km2=2, lake_min_depth_m=1
    )
    outlets = choose_lake_outlets(dem, surface.routing_elevation_m, f, lakes)
    before, _ = accumulate_mfd_with_lake_nodes(
        f, cell_size_km=1, lakes=lakes, outlets=outlets
    )
    one = lakes[0].cells[0]
    after, ledger = accumulate_mfd_with_lake_nodes(
        f, cell_size_km=1, lakes=lakes, outlets=outlets,
        external_inflows=((one[0], one[1], 103.25),)
    )
    assert ledger["explicit_external_area_km2"] == 103.25
    assert abs(ledger["balance_error_km2"]) < 1e-8
    np.testing.assert_allclose(
        after[one] - before[one], 103.25, atol=1e-7, rtol=0
    )
    assert after[outlets[0].receiver_cell] > before[outlets[0].receiver_cell]


def test_synthetic_boundary_injection_changes_accumulation_not_terrain():
    child, macro, manifest = _child(), _source(), _manifest()
    before = child["child_elevation_m"].copy()
    fields0, r0 = analyze_boundary(child, macro, manifest)
    p = r0["boundary_source_A8_D8_candidates"][0]
    assert r0["external_inflow"]["injected_external_area_km2"] == 0
    assert r0["river_network_consistency_with_macro"] == "NOT YET VALIDATED"
    cfg = {"schema": "P2_B2_2_EXPLICIT_A8_INFLOW_SCENARIO",
           "inflows": [{"source_link_key": p["key"],
                        "external_area_km2": 500.0,
                        "area_semantics": "EXTERNAL_ONLY_AREA_EXCLUDING_CHILD",
                        "operator_note": "Research hypothetical only"}]}
    fields1, r1 = analyze_boundary(child, macro, manifest, inflow_config=cfg)
    assert r1["external_inflow"]["injected_external_area_km2"] == 500
    assert abs(r1["area_mass_ledger"]["balance_error_km2"]) < 1e-7
    assert r1["area_mass_ledger"]["boundary_terminal_area_km2"] == pytest.approx(
        81*81 + 500
    )
    assert np.max(fields1["mfd_contributing_area_with_explicit_inflows_km2"]
                  - fields0["mfd_contributing_area_with_explicit_inflows_km2"]) > 100
    np.testing.assert_array_equal(child["child_elevation_m"], before)


def test_reject_invalid_inflow_area_and_marine():
    child, macro, manifest = _child(), _source(), _manifest()
    p = source_inlet_candidates(macro, child, manifest)[0]
    for val in (-3, 0, float("nan"), float("inf"), True):
        config = {"schema": "P2_B2_2_EXPLICIT_A8_INFLOW_SCENARIO",
                  "inflows": [{"source_link_key": p["key"],
                               "external_area_km2": val,
                               "area_semantics": "EXTERNAL_ONLY_AREA_EXCLUDING_CHILD",
                               "operator_note": "test"}]}
        with pytest.raises(BoundaryIntegrationError):
            validate_declared_inlets(config, [p], (81,81))
    child["land_mask"][0,0]=0
    with pytest.raises(BoundaryIntegrationError, match="inland-only"):
        analyze_boundary(child, macro, manifest)


def test_stable_graph_order_and_replay():
    child, macro, manifest = _child(), _source(), _manifest()
    a, x = analyze_boundary(child,macro,manifest)
    b, y = analyze_boundary(child,macro,manifest)
    for key in a:
        np.testing.assert_array_equal(a[key],b[key])
    assert x == y
