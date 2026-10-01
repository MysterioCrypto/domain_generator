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
    effective_surface_moisture_components,
    generate_surface,
    moisture_field,
    slope_degrees,
    vegetation_density_field,
)
from domain_generator.terrain.state import TerrainState


def _surface_payload(*, with_climate: bool) -> dict:
    payload = {
        "moisture_base": 0.35,
        "water_moisture_boost": 0.55,
        "water_moisture_decay_km": 4.0,
        "moisture_noise_amplitude": 0.12,
        "moisture_noise_scale_km": 8.0,
        "vegetation_slope_zero_deg": 45.0,
    }
    if with_climate:
        payload["climate"] = {
            "mean_temperature_c": 9.0,
            "north_minus_south_temperature_c": 0.0,
            "temperature_noise_amplitude_c": 0.0,
            "mean_annual_precipitation_mm": 900.0,
            "moisture_transport_bearing_deg": 90.0,
            "orographic_scale_km": 20.0,
            "orographic_strength": 0.0,
            "precipitation_noise_log_amplitude": 0.0,
            "climate_noise_scale_km": 24.0,
        }
    return payload


def _plan(
    *,
    version: str = "0.2",
    rows: int = 7,
    columns: int = 7,
    cell_size_km: float = 1.0,
    seed: int = 9001,
) -> GenerationPlan:
    payload = {
        "plan_version": version,
        "source": {
            "spec_id": f"surface-moisture-{version}",
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
            "stream_threshold_km2": 10.0,
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


def _hydrology(
    rows: int,
    columns: int,
    *,
    water: np.ndarray | None = None,
    accumulation: np.ndarray | None = None,
) -> HydrologyState:
    if water is None:
        water = np.zeros((rows, columns), dtype=np.float32)
    if accumulation is None:
        accumulation = np.ones((rows, columns), dtype=np.float64)
    return HydrologyState(
        routing_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        fill_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        flow_direction=np.full((rows, columns), -1, dtype=np.int8),
        flow_accumulation_km2=accumulation.astype(np.float64, copy=False),
        stream_mask=np.zeros((rows, columns), dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=water.astype(np.float32, copy=False),
    )


def _components(
    *,
    precipitation: np.ndarray,
    temperature: np.ndarray,
    accumulation: np.ndarray | None = None,
    water: np.ndarray | None = None,
    slope: np.ndarray | None = None,
):
    rows, columns = precipitation.shape
    plan = _plan(rows=rows, columns=columns)
    adapter = GridAdapter.from_plan(plan)
    if accumulation is None:
        accumulation = np.ones((rows, columns), dtype=np.float64)
    if water is None:
        water = np.zeros((rows, columns), dtype=np.float64)
    if slope is None:
        slope = np.zeros((rows, columns), dtype=np.float64)
    return effective_surface_moisture_components(
        adapter=adapter,
        annual_mean_temperature_c=temperature.astype(np.float64),
        annual_precipitation_mm=precipitation.astype(np.float64),
        flow_accumulation_km2=accumulation.astype(np.float64),
        water_depth_m=water.astype(np.float64),
        slope_deg=slope.astype(np.float64),
        stream_threshold_km2=10.0,
        water_moisture_boost=0.55,
        water_moisture_decay_km=4.0,
    )


def test_m01_higher_precipitation_increases_effective_moisture() -> None:
    temperature = np.full((1, 2), 15.0)
    precipitation = np.array([[300.0, 1200.0]])
    result = _components(precipitation=precipitation, temperature=temperature)
    assert result.effective_moisture[0, 1] > result.effective_moisture[0, 0]


def test_m02_warmer_temperature_increases_demand_and_reduces_moisture() -> None:
    temperature = np.array([[5.0, 25.0]])
    precipitation = np.full((1, 2), 700.0)
    result = _components(precipitation=precipitation, temperature=temperature)
    assert result.climatic_wetness[0, 0] > result.climatic_wetness[0, 1]
    assert result.effective_moisture[0, 0] > result.effective_moisture[0, 1]


def test_m03_canonical_water_is_exactly_one() -> None:
    water = np.zeros((5, 5), dtype=np.float64)
    water[2, 2] = 3.0
    result = _components(
        precipitation=np.full((5, 5), 600.0),
        temperature=np.full((5, 5), 15.0),
        water=water,
    )
    assert result.effective_moisture[2, 2] == 1.0


def test_m04_riparian_signal_decays_with_distance_from_isolated_water() -> None:
    water = np.zeros((1, 9), dtype=np.float64)
    water[0, 0] = 1.0
    accumulation = np.zeros((1, 9), dtype=np.float64)
    result = _components(
        precipitation=np.full((1, 9), 500.0),
        temperature=np.full((1, 9), 20.0),
        water=water,
        accumulation=accumulation,
    )
    signal = result.water_proximity_signal[0]
    assert np.all(np.diff(signal) <= 0.0)
    assert signal[1] > signal[-1]


def test_m05_larger_catchment_cannot_reduce_moisture() -> None:
    accumulation = np.array([[1.0, 10.0, 100.0]])
    result = _components(
        precipitation=np.full((1, 3), 700.0),
        temperature=np.full((1, 3), 15.0),
        accumulation=accumulation,
    )
    moisture = result.effective_moisture[0]
    assert moisture[0] <= moisture[1] <= moisture[2]


def test_m06_increasing_slope_cannot_increase_effective_moisture() -> None:
    result = _components(
        precipitation=np.full((1, 4), 900.0),
        temperature=np.full((1, 4), 15.0),
        slope=np.array([[0.0, 20.0, 45.0, 70.0]]),
    )
    moisture = result.effective_moisture[0]
    assert moisture[0] >= moisture[1] >= moisture[2] >= moisture[3]


def test_m07_core_v02_moisture_is_float32_ranged_and_replayable() -> None:
    plan = _plan(rows=8, columns=8)
    elevation = np.linspace(0.0, 600.0, 64, dtype=np.float64).reshape(8, 8)
    terrain = TerrainState(elevation_m=elevation)
    hydrology = _hydrology(
        8,
        8,
        accumulation=np.linspace(1.0, 80.0, 64).reshape(8, 8),
    )
    rng = RngFactory(plan.seed)
    first = generate_surface(
        plan,
        _layout(plan, 0),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=rng,
    )
    replay = generate_surface(
        plan,
        _layout(plan, 0),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=rng,
    )
    assert first.moisture.dtype == np.dtype(np.float32)
    assert np.isfinite(first.moisture).all()
    assert np.all((first.moisture >= 0.0) & (first.moisture <= 1.0))
    np.testing.assert_array_equal(first.moisture, replay.moisture)


def test_m08_c2_does_not_mutate_upstream_fields() -> None:
    plan = _plan(rows=6, columns=6)
    elevation = np.linspace(0.0, 500.0, 36, dtype=np.float64).reshape(6, 6)
    accumulation = np.linspace(1.0, 50.0, 36, dtype=np.float64).reshape(6, 6)
    water = np.zeros((6, 6), dtype=np.float32)
    water[3, 3] = 2.0
    terrain = TerrainState(elevation_m=elevation.copy())
    hydrology = _hydrology(6, 6, water=water.copy(), accumulation=accumulation.copy())
    before_elevation = terrain.elevation_m.copy()
    before_accumulation = hydrology.flow_accumulation_km2.copy()
    before_water = hydrology.water_depth_m.copy()

    surface = generate_surface(
        plan,
        _layout(plan),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    np.testing.assert_array_equal(terrain.elevation_m, before_elevation)
    np.testing.assert_array_equal(hydrology.flow_accumulation_km2, before_accumulation)
    np.testing.assert_array_equal(hydrology.water_depth_m, before_water)
    assert surface.annual_mean_temperature_c is not None
    assert surface.annual_precipitation_mm is not None


def test_m09_c2_keeps_vegetation_bit_identical_to_legacy_path() -> None:
    plan_v01 = _plan(version="0.1", rows=7, columns=7)
    plan_v02 = _plan(version="0.2", rows=7, columns=7)
    elevation = np.linspace(0.0, 500.0, 49, dtype=np.float64).reshape(7, 7)
    water = np.zeros((7, 7), dtype=np.float32)
    water[2, 4] = 1.0
    terrain = TerrainState(elevation_m=elevation)
    hydrology = _hydrology(7, 7, water=water)

    legacy = generate_surface(
        plan_v01,
        _layout(plan_v01),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan_v01.seed),
    )
    current = generate_surface(
        plan_v02,
        _layout(plan_v02),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan_v02.seed),
    )

    np.testing.assert_array_equal(current.vegetation_density, legacy.vegetation_density)
    assert not np.array_equal(current.moisture, legacy.moisture)


def test_m10_core_v01_moisture_and_vegetation_match_legacy_helpers() -> None:
    plan = _plan(version="0.1", rows=6, columns=6)
    elevation = np.linspace(10.0, 410.0, 36, dtype=np.float64).reshape(6, 6)
    water = np.zeros((6, 6), dtype=np.float32)
    water[1, 1] = 1.0
    terrain = TerrainState(elevation_m=elevation)
    hydrology = _hydrology(6, 6, water=water)
    rng = RngFactory(plan.seed)

    surface = generate_surface(
        plan,
        _layout(plan),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=rng,
    )
    adapter = GridAdapter.from_plan(plan)
    expected_moisture = moisture_field(
        adapter=adapter,
        water_depth_m=water,
        moisture_base=plan.surface.moisture_base,
        water_moisture_boost=plan.surface.water_moisture_boost,
        water_moisture_decay_km=plan.surface.water_moisture_decay_km,
        moisture_noise_amplitude=plan.surface.moisture_noise_amplitude,
        moisture_noise_scale_km=plan.surface.moisture_noise_scale_km,
        rng_factory=rng,
        attempt_index=0,
    )
    expected_vegetation = vegetation_density_field(
        moisture=expected_moisture,
        slope_deg=slope_degrees(elevation, cell_size_km=plan.grid.cell_size_km),
        water_depth_m=water,
        vegetation_slope_zero_deg=plan.surface.vegetation_slope_zero_deg,
    )

    np.testing.assert_array_equal(
        surface.moisture,
        expected_moisture.astype(np.float32),
    )
    np.testing.assert_array_equal(
        surface.vegetation_density,
        expected_vegetation.astype(np.float32),
    )
