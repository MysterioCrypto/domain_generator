"""P2 draft: source-constrained finer terrain, with no fabricated source resolution."""

import numpy as np
import pytest

from scripts.condition_planetary_child_terrain_v02 import (
    ChildTerrainError,
    ChildTerrainSettings,
    evaluate_terrain,
    generate_child,
)


RADIUS = 7008.1


def _macro(with_coast=False):
    lat = np.round(np.arange(1.8, -1.80001, -.3), 2)
    lon = np.round(np.arange(-1.8, 1.80001, .3), 2)
    xx, yy = np.meshgrid(lon, lat)
    height = 300 + 130 * xx + 90 * yy + 80 * np.cos(xx * 1.4)
    if with_coast:
        height = 120 * xx + 40 * yy - 20
    return {
        "latitude_deg_north_first": lat,
        "longitude_deg_west_to_east": lon,
        "elevation_m": height.astype(np.float32),
        "land_mask": (height >= 0).astype(np.uint8),
    }


def _settings(**kwargs):
    values = dict(center_lat_deg=0., center_lon_deg=0.,
                  half_width_km=95., half_height_km=80.,
                  planet_radius_km=RADIUS, planetary_year_earth_days=202.755,
                  spacing_km=1., seed=42, relief_strength=2.)
    return ChildTerrainSettings(**(values | kwargs))


def test_new_detail_is_nontrivial_and_original_macro_nodes_exact():
    fields, manifest = generate_child(_macro(), _settings())
    assert fields["child_elevation_m"].shape == (161, 191)
    assert manifest["source_elevation_anchors_in_child"] >= 12
    assert manifest["max_parent_anchor_error_m"] <= 1e-6
    assert np.std(fields["new_local_relief_m"]) > .05
    assert np.max(abs(fields["new_local_relief_m"])) > 1.
    assert fields["north_km_north_first"][0] > fields["north_km_north_first"][-1]
    assert manifest["is_accepted_Core_DomainData"] is False
    assert "NOT_RECOMPUTED" in manifest["routing_status"]


def test_seed_changes_only_fine_detail_and_is_exactly_replayable():
    macro = _macro()
    a, report = generate_child(macro, _settings())
    replay, report_replay = generate_child(macro, _settings())
    different, changed_report = generate_child(macro, _settings(seed=43))
    for key in a:
        np.testing.assert_array_equal(a[key], replay[key])
    assert report == report_replay
    np.testing.assert_array_equal(a["parent_interpolated_m"],
                                  different["parent_interpolated_m"])
    assert not np.array_equal(a["new_local_relief_m"],
                              different["new_local_relief_m"])
    assert changed_report["max_parent_anchor_error_m"] <= 1e-6


def test_evaluations_on_parent_station_coordinates_are_exact():
    macro = _macro()
    lat = macro["latitude_deg_north_first"]
    lon = macro["longitude_deg_west_to_east"]
    center = _settings()
    km_per_deg = np.pi * RADIUS / 180
    east = lon * km_per_deg
    north = lat * km_per_deg
    grid_x, grid_y = np.meshgrid(east, north)
    interpolated, baseline, detail = evaluate_terrain(
        macro, center, grid_x, grid_y
    )
    np.testing.assert_allclose(interpolated, macro["elevation_m"],
                               atol=1e-7, rtol=0)
    np.testing.assert_allclose(baseline, macro["elevation_m"],
                               atol=1e-7, rtol=0)
    np.testing.assert_allclose(detail, 0, atol=1e-7, rtol=0)


def test_no_accidental_new_seas_islands_and_marine_detail():
    fields, meta = generate_child(_macro(with_coast=True), _settings())
    assert meta["land_marine_sign_preserved"] is True
    np.testing.assert_array_equal(
        fields["child_elevation_m"] >= 0,
        fields["parent_interpolated_m"] >= 0
    )
    assert np.all(fields["new_local_relief_m"][
        fields["parent_interpolated_m"] < 0] == 0)


def test_same_world_coordinates_match_across_adjacent_crops():
    macro = _macro()
    # Same source planet coordinates, different crop centers/origins.
    first = _settings(center_lon_deg=0.)
    second = _settings(center_lon_deg=.15)
    lon_world = np.array([[.1, .15, .2]])
    lat_world = np.array([[.1, .1, .1]])
    km_per_deg = np.pi * RADIUS / 180
    x1 = (lon_world - first.center_lon_deg) * km_per_deg
    x2 = (lon_world - second.center_lon_deg) * km_per_deg
    y = lat_world * km_per_deg
    first_heights, _, _ = evaluate_terrain(macro, first, x1, y)
    second_heights, _, _ = evaluate_terrain(macro, second, x2, y)
    np.testing.assert_allclose(first_heights, second_heights, atol=1e-10, rtol=0)


def test_small_source_window_is_rejected_and_no_extrapolation():
    macro = _macro()
    with pytest.raises(ChildTerrainError, match="outside source station"):
        evaluate_terrain(macro, _settings(), np.array([320.]), np.array([0.]))
    with pytest.raises(ChildTerrainError, match="positive"):
        generate_child(macro, _settings(planetary_year_earth_days=0))
    with pytest.raises(ChildTerrainError, match="relief_strength"):
        generate_child(macro, _settings(relief_strength=3.))
    with pytest.raises(ChildTerrainError, match="poles"):
        generate_child(macro, _settings(center_lat_deg=85.))


def test_cubic_interpolation_continuously_joins_macro_grid_cells():
    """No false straight square ridges at 0.3-degree DEM sample boundaries."""
    macro = _macro()
    setting = _settings(relief_strength=0)
    km_per_deg = np.pi * RADIUS / 180
    boundary_km = .3 * km_per_deg
    eps = 1e-3  # km
    xs = np.array([boundary_km - eps, boundary_km, boundary_km + eps])
    ys = np.array([.17 * km_per_deg] * 3)
    heights, baseline, details = evaluate_terrain(macro, setting, xs, ys)
    left_slope = (baseline[1] - baseline[0]) / eps
    right_slope = (baseline[2] - baseline[1]) / eps
    assert abs(left_slope - right_slope) < 0.01
    np.testing.assert_array_equal(heights, baseline)
    np.testing.assert_array_equal(details, np.zeros_like(details))


def test_planet_parameters_cannot_come_from_hidden_default():
    with pytest.raises(TypeError):
        ChildTerrainSettings(
            center_lat_deg=0, center_lon_deg=0,
            half_width_km=95, half_height_km=95
        )
