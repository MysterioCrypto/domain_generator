from __future__ import annotations

import numpy as np
import pytest

from domain_generator.compiler import semantic_plan_fingerprint
from domain_generator.contracts.data import RiverNetwork
from domain_generator.contracts.geometry import AreaGeometry, WorldPoint
from domain_generator.contracts.layout import LayoutCandidate, SourcePlanRef
from domain_generator.contracts.plan import (
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    FeatureMetadata,
    FixedParameter,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
    ParameterType,
    ResolvedFeature,
)
from domain_generator.grid import GridAdapter
from domain_generator.hydrology.state import HydrologyState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.surface import (
    climate_aware_vegetation_components,
    generate_surface,
    moisture_field,
    slope_degrees,
    vegetation_density_field,
)
from domain_generator.terrain.state import TerrainState


def _feature(
    feature_id: str,
    *,
    operator: str,
    parameter_name: str,
    value: float,
) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="c3-test"),
        family=FeatureFamily.SURFACE,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.AREA,
            parameters={
                "vertex_count": FixedParameter(type=ParameterType.INTEGER, value=4),
                "radial_extent": FixedParameter(type=ParameterType.FLOAT, value=0.5),
                "radial_irregularity": FixedParameter(type=ParameterType.FLOAT, value=0.0),
            },
        ),
        effect=EffectRecipe(
            stage=EffectStage.SURFACE,
            operator=operator,
            parameters={
                parameter_name: FixedParameter(type=ParameterType.FLOAT, value=value)
            },
        ),
    )


def _plan(
    *,
    version: str = "0.2",
    rows: int = 6,
    columns: int = 6,
    seed: int = 5511,
    mean_temperature_c: float = 10.0,
    moisture_base: float = 0.35,
    moisture_noise_amplitude: float = 0.1,
    moisture_noise_scale_km: float = 8.0,
    vegetation_slope_zero_deg: float = 45.0,
    features: tuple[ResolvedFeature, ...] = (),
) -> GenerationPlan:
    surface = {
        "moisture_base": float(moisture_base),
        "water_moisture_boost": 0.55,
        "water_moisture_decay_km": 2.0,
        "moisture_noise_amplitude": float(moisture_noise_amplitude),
        "moisture_noise_scale_km": float(moisture_noise_scale_km),
        "vegetation_slope_zero_deg": float(vegetation_slope_zero_deg),
    }
    if version == "0.2":
        surface["climate"] = {
            "mean_temperature_c": float(mean_temperature_c),
            "north_minus_south_temperature_c": 0.0,
            "temperature_noise_amplitude_c": 0.0,
            "mean_annual_precipitation_mm": 900.0,
            "moisture_transport_bearing_deg": 90.0,
            "orographic_scale_km": 20.0,
            "orographic_strength": 0.0,
            "precipitation_noise_log_amplitude": 0.0,
            "climate_noise_scale_km": 24.0,
        }

    payload = {
        "plan_version": version,
        "source": {
            "spec_id": f"c3-vegetation-{version}",
            "spec_schema_version": version,
            "spec_fingerprint": "sha256:c3-test",
            "generator_version": "0.2-test",
        },
        "seed": seed,
        "domain": {
            "width_km": float(columns),
            "height_km": float(rows),
        },
        "grid": {
            "cell_size_km": 1.0,
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
        "surface": surface,
        "features": list(features),
        "constraints": [],
    }
    if version == "0.2":
        payload["terrain"] = {
            "base_elevation_m": 100.0,
            "noise_layers": [{"id": "test", "scale_km": 10.0, "amplitude_m": 1.0}],
        }
    return GenerationPlan.model_validate(payload)


def _layout(
    plan: GenerationPlan,
    *,
    attempt_index: int = 0,
    geometries: dict[str, AreaGeometry] | None = None,
) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations=geometries or {},
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


def _whole_area(rows: int, columns: int) -> AreaGeometry:
    return AreaGeometry(
        boundary=(
            WorldPoint(x_km=0.0, y_km=0.0),
            WorldPoint(x_km=float(columns), y_km=0.0),
            WorldPoint(x_km=float(columns), y_km=float(rows)),
            WorldPoint(x_km=0.0, y_km=float(rows)),
        )
    )


def _generate(
    plan: GenerationPlan,
    *,
    elevation: np.ndarray | None = None,
    hydrology: HydrologyState | None = None,
    attempt_index: int = 0,
    geometries: dict[str, AreaGeometry] | None = None,
):
    rows, columns = plan.grid.rows, plan.grid.columns
    if elevation is None:
        elevation = np.zeros((rows, columns), dtype=np.float64)
    if hydrology is None:
        hydrology = _hydrology(rows, columns)
    return generate_surface(
        plan,
        _layout(plan, attempt_index=attempt_index, geometries=geometries),
        TerrainState(elevation_m=elevation),
        hydrology,
        attempt_index=attempt_index,
        rng_factory=RngFactory(plan.seed),
    )


def test_v01_greater_moisture_cannot_reduce_vegetation_potential() -> None:
    moisture = np.array([[0.0, 0.2, 0.5, 0.9, 1.0]], dtype=np.float64)
    temperature = np.full_like(moisture, 15.0)
    result = climate_aware_vegetation_components(
        moisture=moisture,
        annual_mean_temperature_c=temperature,
    )
    assert np.all(np.diff(result.vegetation_potential[0]) >= 0.0)


def test_v02_warming_below_30_c_cannot_reduce_thermal_suitability() -> None:
    temperature = np.array([[-20.0, -5.0, 0.0, 10.0, 20.0, 29.0]])
    moisture = np.ones_like(temperature)
    result = climate_aware_vegetation_components(
        moisture=moisture,
        annual_mean_temperature_c=temperature,
    )
    assert np.all(np.diff(result.thermal_suitability[0]) > 0.0)
    assert np.all(np.diff(result.vegetation_potential[0]) > 0.0)


def test_v03_temperature_response_saturates_at_30_c() -> None:
    temperature = np.array([[30.0, 35.0, 80.0]])
    result = climate_aware_vegetation_components(
        moisture=np.ones_like(temperature),
        annual_mean_temperature_c=temperature,
    )
    np.testing.assert_array_equal(
        result.thermal_suitability,
        np.ones_like(temperature, dtype=np.float64),
    )


def test_v04_zero_moisture_gives_zero_base_vegetation() -> None:
    temperature = np.array([[-10.0, 0.0, 15.0, 30.0]])
    result = climate_aware_vegetation_components(
        moisture=np.zeros_like(temperature),
        annual_mean_temperature_c=temperature,
    )
    np.testing.assert_array_equal(
        result.vegetation_potential,
        np.zeros_like(temperature, dtype=np.float64),
    )


def test_v05_canonical_water_has_exactly_zero_vegetation() -> None:
    plan = _plan(rows=5, columns=5, mean_temperature_c=20.0)
    water = np.zeros((5, 5), dtype=np.float32)
    water[2, 3] = 2.0
    state = _generate(plan, hydrology=_hydrology(5, 5, water=water))
    assert state.moisture[2, 3] == np.float32(1.0)
    assert state.vegetation_density[2, 3] == np.float32(0.0)


def test_v06_existing_surface_bias_semantics_are_preserved() -> None:
    rows = columns = 4
    vegetation_feature = _feature(
        "green",
        operator="vegetation_bias",
        parameter_name="delta_vegetation",
        value=0.2,
    )
    moisture_feature = _feature(
        "wet",
        operator="moisture_bias",
        parameter_name="delta_moisture",
        value=0.1,
    )
    plain = _plan(rows=rows, columns=columns, mean_temperature_c=15.0)
    green = _plan(
        rows=rows,
        columns=columns,
        mean_temperature_c=15.0,
        features=(vegetation_feature,),
    )
    wet = _plan(
        rows=rows,
        columns=columns,
        mean_temperature_c=15.0,
        features=(moisture_feature,),
    )
    whole = _whole_area(rows, columns)

    base_state = _generate(plain)
    green_state = _generate(green, geometries={"green": whole})
    wet_state = _generate(wet, geometries={"wet": whole})

    np.testing.assert_array_equal(green_state.moisture, base_state.moisture)
    np.testing.assert_allclose(
        green_state.vegetation_density,
        np.clip(base_state.vegetation_density.astype(np.float64) + 0.2, 0.0, 1.0),
        rtol=0.0,
        atol=1e-7,
    )

    assert np.all(wet_state.moisture > base_state.moisture)
    assert np.all(wet_state.vegetation_density > base_state.vegetation_density)


def test_v07_core_v02_vegetation_is_float32_ranged_and_replayable() -> None:
    plan = _plan(rows=7, columns=7, mean_temperature_c=12.0)
    first = _generate(plan)
    replay = _generate(plan)
    assert first.vegetation_density.dtype == np.dtype(np.float32)
    assert np.isfinite(first.vegetation_density).all()
    assert np.all((first.vegetation_density >= 0.0) & (first.vegetation_density <= 1.0))
    np.testing.assert_array_equal(first.vegetation_density, replay.vegetation_density)


def test_v08_c3_does_not_mutate_upstream_or_canonical_c2_fields() -> None:
    plan = _plan(rows=5, columns=5, mean_temperature_c=8.0)
    elevation = np.linspace(0.0, 400.0, 25, dtype=np.float64).reshape(5, 5)
    accumulation = np.linspace(1.0, 40.0, 25, dtype=np.float64).reshape(5, 5)
    hydrology = _hydrology(5, 5, accumulation=accumulation.copy())
    before_elevation = elevation.copy()
    before_accumulation = hydrology.flow_accumulation_km2.copy()
    before_water = hydrology.water_depth_m.copy()

    first = _generate(plan, elevation=elevation, hydrology=hydrology)
    second = _generate(plan, elevation=elevation.copy(), hydrology=_hydrology(
        5,
        5,
        accumulation=accumulation.copy(),
    ))

    np.testing.assert_array_equal(elevation, before_elevation)
    np.testing.assert_array_equal(hydrology.flow_accumulation_km2, before_accumulation)
    np.testing.assert_array_equal(hydrology.water_depth_m, before_water)
    np.testing.assert_array_equal(first.moisture, second.moisture)
    np.testing.assert_array_equal(
        first.annual_mean_temperature_c,
        second.annual_mean_temperature_c,
    )
    np.testing.assert_array_equal(
        first.annual_precipitation_mm,
        second.annual_precipitation_mm,
    )


def test_v09_core_v01_remains_legacy_compatible() -> None:
    plan = _plan(version="0.1", rows=5, columns=5)
    elevation = np.linspace(0.0, 300.0, 25, dtype=np.float64).reshape(5, 5)
    water = np.zeros((5, 5), dtype=np.float32)
    water[1, 2] = 1.0
    hydrology = _hydrology(5, 5, water=water)
    state = _generate(plan, elevation=elevation, hydrology=hydrology)

    adapter = GridAdapter.from_plan(plan)
    rng = RngFactory(plan.seed)
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
        slope_deg=slope_degrees(elevation, cell_size_km=1.0),
        water_depth_m=water,
        vegetation_slope_zero_deg=plan.surface.vegetation_slope_zero_deg,
    )

    np.testing.assert_array_equal(
        state.moisture,
        expected_moisture.astype(np.float32),
    )
    np.testing.assert_array_equal(
        state.vegetation_density,
        expected_vegetation.astype(np.float32),
    )


def test_v10_core_v02_ignores_legacy_only_surface_parameters() -> None:
    first_plan = _plan(
        rows=6,
        columns=6,
        mean_temperature_c=12.0,
        moisture_base=0.05,
        moisture_noise_amplitude=0.0,
        moisture_noise_scale_km=2.0,
        vegetation_slope_zero_deg=5.0,
    )
    second_plan = _plan(
        rows=6,
        columns=6,
        mean_temperature_c=12.0,
        moisture_base=0.95,
        moisture_noise_amplitude=1.0,
        moisture_noise_scale_km=50.0,
        vegetation_slope_zero_deg=90.0,
    )

    first = _generate(first_plan)
    second = _generate(second_plan)

    np.testing.assert_array_equal(first.moisture, second.moisture)
    np.testing.assert_array_equal(first.vegetation_density, second.vegetation_density)


def test_v11_no_hidden_vegetation_noise_when_upstream_fields_are_attempt_invariant() -> None:
    plan = _plan(rows=6, columns=6, mean_temperature_c=14.0)
    first = _generate(plan, attempt_index=0)
    other_attempt = _generate(plan, attempt_index=5)

    np.testing.assert_array_equal(
        first.annual_mean_temperature_c,
        other_attempt.annual_mean_temperature_c,
    )
    np.testing.assert_array_equal(
        first.annual_precipitation_mm,
        other_attempt.annual_precipitation_mm,
    )
    np.testing.assert_array_equal(first.moisture, other_attempt.moisture)
    np.testing.assert_array_equal(
        first.vegetation_density,
        other_attempt.vegetation_density,
    )


def test_temperature_response_matches_accepted_reference_points() -> None:
    temperature = np.array([[0.0, 10.0, 20.0, 30.0]])
    result = climate_aware_vegetation_components(
        moisture=np.ones_like(temperature),
        annual_mean_temperature_c=temperature,
    )
    np.testing.assert_allclose(
        result.thermal_suitability[0],
        np.array([0.2338479948, 0.5179543609, 0.8216335668, 1.0]),
        rtol=0.0,
        atol=1e-9,
    )
