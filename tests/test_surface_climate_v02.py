from __future__ import annotations

import numpy as np
import pytest

from domain_generator.compiler import semantic_plan_fingerprint
from domain_generator.contracts.data import RiverNetwork
from domain_generator.contracts.layout import LayoutCandidate, SourcePlanRef
from domain_generator.contracts.plan import GenerationPlan
from domain_generator.grid import GridAdapter
from domain_generator.hydrology.state import HydrologyState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.surface import (
    annual_mean_temperature_field,
    annual_precipitation_field,
    generate_surface,
)
from domain_generator.terrain.state import TerrainState


def _surface_payload(*, with_climate: bool) -> dict:
    payload = {
        "moisture_base": 0.35,
        "water_moisture_boost": 0.4,
        "water_moisture_decay_km": 5.0,
        "moisture_noise_amplitude": 0.12,
        "moisture_noise_scale_km": 8.0,
        "vegetation_slope_zero_deg": 45.0,
    }
    if with_climate:
        payload["climate"] = {
            "mean_temperature_c": 9.0,
            "north_minus_south_temperature_c": -4.0,
            "temperature_noise_amplitude_c": 1.5,
            "mean_annual_precipitation_mm": 900.0,
            "moisture_transport_bearing_deg": 90.0,
            "orographic_scale_km": 20.0,
            "orographic_strength": 2.0,
            "precipitation_noise_log_amplitude": 0.2,
            "climate_noise_scale_km": 24.0,
        }
    return payload


def _plan(
    *,
    version: str = "0.2",
    rows: int = 9,
    columns: int = 9,
    cell_size_km: float = 1.0,
    seed: int = 4242,
) -> GenerationPlan:
    payload = {
        "plan_version": version,
        "source": {
            "spec_id": f"surface-climate-{version}",
            "spec_schema_version": version,
            "spec_fingerprint": "sha256:test",
            "generator_version": "0.2-test",
        },
        "seed": seed,
        "domain": {
            "width_km": columns * cell_size_km,
            "height_km": rows * cell_size_km,
        },
        "grid": {
            "cell_size_km": cell_size_km,
            "rows": rows,
            "columns": columns,
        },
        "hydrology": {
            "stream_threshold_km2": 8.0,
            "lake_min_area_km2": 1.0,
            "lake_min_depth_m": 0.5,
            "river_depth_at_threshold_m": 0.5,
            "river_depth_exponent": 0.3,
        },
        "surface": _surface_payload(with_climate=version == "0.2"),
        "features": [],
        "constraints": [],
    }
    if version == "0.2":
        payload["terrain"] = {
            "base_elevation_m": 100.0,
            "noise_layers": [{"id": "test", "scale_km": 10.0, "amplitude_m": 1.0}],
        }
    return GenerationPlan.model_validate(payload)


def _layout(plan: GenerationPlan, attempt_index: int = 0) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations={},
        placement_reservations={},
    )


def _hydrology(rows: int, columns: int, water: np.ndarray | None = None) -> HydrologyState:
    if water is None:
        water = np.zeros((rows, columns), dtype=np.float32)
    return HydrologyState(
        routing_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        fill_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        flow_direction=np.full((rows, columns), -1, dtype=np.int8),
        flow_accumulation_km2=np.ones((rows, columns), dtype=np.float64),
        stream_mask=np.zeros((rows, columns), dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=water.astype(np.float32, copy=False),
    )


def test_c01_flat_zero_noise_climate_is_uniform_at_configured_means() -> None:
    plan = _plan(rows=5, columns=7)
    adapter = GridAdapter.from_plan(plan)
    elevation = np.full((5, 7), 400.0, dtype=np.float64)
    water = np.zeros((5, 7), dtype=np.float32)
    rng = RngFactory(plan.seed)

    temperature = annual_mean_temperature_field(
        adapter=adapter,
        elevation_m=elevation,
        mean_temperature_c=12.0,
        north_minus_south_temperature_c=0.0,
        temperature_noise_amplitude_c=0.0,
        climate_noise_scale_km=10.0,
        rng_factory=rng,
        attempt_index=0,
    )
    precipitation = annual_precipitation_field(
        adapter=adapter,
        elevation_m=elevation,
        water_depth_m=water,
        mean_annual_precipitation_mm=750.0,
        moisture_transport_bearing_deg=90.0,
        orographic_scale_km=10.0,
        orographic_strength=3.0,
        precipitation_noise_log_amplitude=0.0,
        climate_noise_scale_km=10.0,
        rng_factory=rng,
        attempt_index=0,
    )

    np.testing.assert_array_equal(temperature, np.full((5, 7), 12.0, dtype=np.float64))
    np.testing.assert_allclose(precipitation, 750.0, rtol=0.0, atol=1e-12)


def test_c02_one_kilometre_relative_elevation_changes_temperature_by_6_5_c() -> None:
    plan = _plan(rows=1, columns=2)
    adapter = GridAdapter.from_plan(plan)
    elevation = np.array([[0.0, 1000.0]], dtype=np.float64)
    temperature = annual_mean_temperature_field(
        adapter=adapter,
        elevation_m=elevation,
        mean_temperature_c=10.0,
        north_minus_south_temperature_c=0.0,
        temperature_noise_amplitude_c=0.0,
        climate_noise_scale_km=10.0,
        rng_factory=RngFactory(plan.seed),
        attempt_index=0,
    )
    assert float(temperature[0, 1] - temperature[0, 0]) == pytest.approx(-6.5)


def test_c03_north_south_macro_gradient_matches_world_space_formula() -> None:
    plan = _plan(rows=5, columns=1)
    adapter = GridAdapter.from_plan(plan)
    delta = -10.0
    temperature = annual_mean_temperature_field(
        adapter=adapter,
        elevation_m=np.zeros((5, 1), dtype=np.float64),
        mean_temperature_c=10.0,
        north_minus_south_temperature_c=delta,
        temperature_noise_amplitude_c=0.0,
        climate_noise_scale_km=10.0,
        rng_factory=RngFactory(plan.seed),
        attempt_index=0,
    )
    expected_sampled_delta = delta * (1.0 - plan.grid.cell_size_km / plan.domain.height_km)
    assert float(temperature[0, 0] - temperature[-1, 0]) == pytest.approx(
        expected_sampled_delta
    )


def _ridge(rows: int = 21, columns: int = 21) -> np.ndarray:
    result = np.zeros((rows, columns), dtype=np.float64)
    center = (columns - 1) / 2.0
    for column in range(columns):
        result[:, column] = max(0.0, 1200.0 - 180.0 * abs(column - center))
    return result


def test_c04_eastward_transport_makes_windward_ridge_wetter_than_lee() -> None:
    plan = _plan(rows=21, columns=21)
    adapter = GridAdapter.from_plan(plan)
    precipitation = annual_precipitation_field(
        adapter=adapter,
        elevation_m=_ridge(),
        water_depth_m=np.zeros((21, 21), dtype=np.float32),
        mean_annual_precipitation_mm=900.0,
        moisture_transport_bearing_deg=90.0,
        orographic_scale_km=8.0,
        orographic_strength=3.0,
        precipitation_noise_log_amplitude=0.0,
        climate_noise_scale_km=10.0,
        rng_factory=RngFactory(plan.seed),
        attempt_index=0,
    )
    row = 10
    assert float(precipitation[row, 8]) > float(precipitation[row, 12])


def test_c05_rotating_terrain_and_transport_together_rotates_precipitation() -> None:
    plan = _plan(rows=17, columns=17)
    adapter = GridAdapter.from_plan(plan)
    yy, xx = np.mgrid[0:17, 0:17]
    terrain = (
        600.0 * np.exp(-((xx - 5.0) ** 2 + (yy - 9.0) ** 2) / 16.0)
        + 250.0 * np.exp(-((xx - 12.0) ** 2 + (yy - 4.0) ** 2) / 9.0)
    )
    common = dict(
        adapter=adapter,
        water_depth_m=np.zeros((17, 17), dtype=np.float32),
        mean_annual_precipitation_mm=700.0,
        orographic_scale_km=7.0,
        orographic_strength=2.0,
        precipitation_noise_log_amplitude=0.0,
        climate_noise_scale_km=10.0,
        rng_factory=RngFactory(plan.seed),
        attempt_index=0,
    )
    eastward = annual_precipitation_field(
        elevation_m=terrain,
        moisture_transport_bearing_deg=90.0,
        **common,
    )
    northward_rotated = annual_precipitation_field(
        elevation_m=np.rot90(terrain),
        moisture_transport_bearing_deg=0.0,
        **common,
    )
    np.testing.assert_allclose(
        northward_rotated,
        np.rot90(eastward),
        rtol=1e-12,
        atol=1e-10,
    )


def test_c06_land_mean_precipitation_matches_requested_mean() -> None:
    plan = _plan(rows=9, columns=11)
    adapter = GridAdapter.from_plan(plan)
    elevation = np.linspace(0.0, 900.0, 99, dtype=np.float64).reshape(9, 11)
    water = np.zeros((9, 11), dtype=np.float32)
    water[0:2, 0:3] = 2.0
    precipitation = annual_precipitation_field(
        adapter=adapter,
        elevation_m=elevation,
        water_depth_m=water,
        mean_annual_precipitation_mm=1234.0,
        moisture_transport_bearing_deg=225.0,
        orographic_scale_km=12.0,
        orographic_strength=2.0,
        precipitation_noise_log_amplitude=0.25,
        climate_noise_scale_km=15.0,
        rng_factory=RngFactory(plan.seed),
        attempt_index=0,
    )
    assert float(np.mean(precipitation[water <= 0.0])) == pytest.approx(
        1234.0,
        rel=0.0,
        abs=1e-10,
    )


def test_c07_climate_replays_and_changes_with_attempt_when_noise_enabled() -> None:
    plan = _plan(rows=8, columns=8)
    terrain = TerrainState(elevation_m=np.linspace(0.0, 600.0, 64).reshape(8, 8))
    hydrology = _hydrology(8, 8)
    rng = RngFactory(plan.seed)

    first = generate_surface(
        plan,
        _layout(plan, 2),
        terrain,
        hydrology,
        attempt_index=2,
        rng_factory=rng,
    )
    replay = generate_surface(
        plan,
        _layout(plan, 2),
        terrain,
        hydrology,
        attempt_index=2,
        rng_factory=rng,
    )
    other = generate_surface(
        plan,
        _layout(plan, 3),
        terrain,
        hydrology,
        attempt_index=3,
        rng_factory=rng,
    )

    assert np.array_equal(first.annual_mean_temperature_c, replay.annual_mean_temperature_c)
    assert np.array_equal(first.annual_precipitation_mm, replay.annual_precipitation_mm)
    assert not np.array_equal(first.annual_mean_temperature_c, other.annual_mean_temperature_c)
    assert not np.array_equal(first.annual_precipitation_mm, other.annual_precipitation_mm)


def test_c08_surface_climate_does_not_mutate_terrain_or_hydrology() -> None:
    plan = _plan(rows=7, columns=7)
    elevation = np.linspace(50.0, 500.0, 49, dtype=np.float64).reshape(7, 7)
    water = np.zeros((7, 7), dtype=np.float32)
    water[3, 3] = 2.0
    terrain = TerrainState(elevation_m=elevation.copy())
    hydrology = _hydrology(7, 7, water.copy())
    before_elevation = terrain.elevation_m.copy()
    before_water = hydrology.water_depth_m.copy()

    generate_surface(
        plan,
        _layout(plan),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    np.testing.assert_array_equal(terrain.elevation_m, before_elevation)
    np.testing.assert_array_equal(hydrology.water_depth_m, before_water)


def test_c09_c2_and_c3_supersede_legacy_surface_semantics() -> None:
    plan_v01 = _plan(version="0.1", rows=7, columns=7)
    plan_v02 = _plan(version="0.2", rows=7, columns=7)
    elevation = np.linspace(0.0, 500.0, 49, dtype=np.float64).reshape(7, 7)
    water = np.zeros((7, 7), dtype=np.float32)
    water[2, 4] = 1.0
    terrain = TerrainState(elevation_m=elevation)
    hydrology = _hydrology(7, 7, water)

    legacy = generate_surface(
        plan_v01,
        _layout(plan_v01),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan_v01.seed),
    )
    climate = generate_surface(
        plan_v02,
        _layout(plan_v02),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan_v02.seed),
    )

    assert not np.array_equal(climate.moisture, legacy.moisture)
    assert not np.array_equal(climate.vegetation_density, legacy.vegetation_density)
    assert climate.annual_mean_temperature_c is not None
    assert climate.annual_precipitation_mm is not None
