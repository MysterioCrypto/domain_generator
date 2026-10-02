from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from domain_generator.application import (
    generate_domain,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.compiler import (
    compile_domain_spec,
    domain_spec_fingerprint,
    semantic_plan_fingerprint,
)
from domain_generator.contracts import GenerationRequest
from domain_generator.contracts.data import FieldRole, RiverNetwork
from domain_generator.contracts.layout import LayoutCandidate, SourcePlanRef
from domain_generator.contracts.plan import GenerationPlan
from domain_generator.contracts.spec import DomainSpec
from domain_generator.hydrology.state import HydrologyState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.surface import (
    generate_surface,
    monthly_precipitation_fields,
    monthly_temperature_fields,
)
from domain_generator.terrain.state import TerrainState


ROOT = Path(__file__).resolve().parents[1]
A08 = ROOT / "tests" / "acceptance" / "cases" / "a08-core-v02-integrated"


def _plan(
    *,
    seasonality: bool,
    temperature_amplitude_c: float = 7.0,
    temperature_peak_month: int = 7,
    precipitation_log_amplitude: float = 1.0,
    precipitation_peak_month: int = 1,
    seed: int = 44117,
) -> GenerationPlan:
    climate: dict[str, object] = {
        "mean_temperature_c": 9.0,
        "north_minus_south_temperature_c": -3.0,
        "temperature_noise_amplitude_c": 0.8,
        "mean_annual_precipitation_mm": 850.0,
        "moisture_transport_bearing_deg": 90.0,
        "orographic_scale_km": 18.0,
        "orographic_strength": 1.2,
        "precipitation_noise_log_amplitude": 0.15,
        "climate_noise_scale_km": 24.0,
    }
    if seasonality:
        climate["seasonality"] = {
            "temperature_seasonal_amplitude_c": temperature_amplitude_c,
            "temperature_peak_month": temperature_peak_month,
            "precipitation_seasonality_log_amplitude": precipitation_log_amplitude,
            "precipitation_peak_month": precipitation_peak_month,
        }

    return GenerationPlan.model_validate(
        {
            "plan_version": "0.2",
            "source": {
                "spec_id": "c4-seasonality",
                "spec_schema_version": "0.2",
                "spec_fingerprint": "sha256:c4-test",
                "generator_version": "0.2-test",
            },
            "seed": seed,
            "domain": {"width_km": 8.0, "height_km": 6.0},
            "grid": {"cell_size_km": 1.0, "rows": 6, "columns": 8},
            "terrain": {
                "base_elevation_m": 100.0,
                "noise_layers": [
                    {"id": "test", "scale_km": 8.0, "amplitude_m": 1.0}
                ],
            },
            "hydrology": {
                "stream_threshold_km2": 8.0,
                "lake_min_area_km2": 1.0,
                "lake_min_depth_m": 0.5,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
            },
            "surface": {
                "moisture_base": 0.35,
                "water_moisture_boost": 0.55,
                "water_moisture_decay_km": 2.0,
                "moisture_noise_amplitude": 0.1,
                "moisture_noise_scale_km": 8.0,
                "vegetation_slope_zero_deg": 45.0,
                "climate": climate,
            },
            "features": [],
            "constraints": [],
        }
    )


def _layout(plan: GenerationPlan) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=0,
        geometry_realizations={},
        placement_reservations={},
    )


def _hydrology(rows: int = 6, columns: int = 8) -> HydrologyState:
    return HydrologyState(
        routing_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        fill_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        flow_direction=np.full((rows, columns), -1, dtype=np.int8),
        flow_accumulation_km2=np.ones((rows, columns), dtype=np.float64),
        stream_mask=np.zeros((rows, columns), dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=np.zeros((rows, columns), dtype=np.float32),
    )


def _surface(plan: GenerationPlan):
    elevation = np.linspace(0.0, 500.0, 48, dtype=np.float64).reshape(6, 8)
    return generate_surface(
        plan,
        _layout(plan),
        TerrainState(elevation_m=elevation),
        _hydrology(),
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )


def _seasonal_a08_request(
    *,
    temperature_amplitude_c: float = 7.0,
    temperature_peak_month: int = 7,
    precipitation_log_amplitude: float = 1.0,
    precipitation_peak_month: int = 1,
) -> GenerationRequest:
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    payload["domain_spec"]["surface"]["climate"]["seasonality"] = {
        "temperature_seasonal_amplitude_c": temperature_amplitude_c,
        "temperature_peak_month": temperature_peak_month,
        "precipitation_seasonality_log_amplitude": precipitation_log_amplitude,
        "precipitation_peak_month": precipitation_peak_month,
    }
    return GenerationRequest.model_validate(payload)


def _generate_a08(request: GenerationRequest):
    catalog = load_preset_catalog(A08 / "presets.json")
    return generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry_for_request(request, catalog),
    )


def test_s01_monthly_temperature_preserves_annual_mean_per_cell() -> None:
    annual = np.linspace(-5.0, 20.0, 20, dtype=np.float64).reshape(4, 5)
    monthly = monthly_temperature_fields(
        annual_mean_temperature_c=annual,
        temperature_seasonal_amplitude_c=7.0,
        temperature_peak_month=7,
    )
    np.testing.assert_allclose(
        np.mean(monthly, axis=0, dtype=np.float64),
        annual,
        rtol=0.0,
        atol=1e-12,
    )


def test_s02_monthly_precipitation_preserves_annual_total_per_cell() -> None:
    annual = np.linspace(120.0, 2400.0, 20, dtype=np.float64).reshape(4, 5)
    monthly = monthly_precipitation_fields(
        annual_precipitation_mm=annual,
        precipitation_seasonality_log_amplitude=1.0,
        precipitation_peak_month=1,
    )
    np.testing.assert_allclose(
        np.sum(monthly, axis=0, dtype=np.float64),
        annual,
        rtol=1e-14,
        atol=1e-10,
    )


def test_s03_temperature_peak_and_opposite_month_are_extrema() -> None:
    annual = np.full((2, 3), 10.0, dtype=np.float64)
    monthly = monthly_temperature_fields(
        annual_mean_temperature_c=annual,
        temperature_seasonal_amplitude_c=6.0,
        temperature_peak_month=7,
    )
    assert np.all(np.argmax(monthly, axis=0) == 6)
    assert np.all(np.argmin(monthly, axis=0) == 0)
    np.testing.assert_allclose(monthly[6], 16.0, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(monthly[0], 4.0, rtol=0.0, atol=1e-12)


def test_s04_precipitation_peak_month_is_maximal() -> None:
    annual = np.full((2, 3), 1200.0, dtype=np.float64)
    monthly = monthly_precipitation_fields(
        annual_precipitation_mm=annual,
        precipitation_seasonality_log_amplitude=1.2,
        precipitation_peak_month=3,
    )
    assert np.all(np.argmax(monthly, axis=0) == 2)


def test_s05_zero_temperature_amplitude_repeats_annual_field_exactly() -> None:
    annual = np.linspace(-2.0, 14.0, 12, dtype=np.float64).reshape(3, 4)
    monthly = monthly_temperature_fields(
        annual_mean_temperature_c=annual,
        temperature_seasonal_amplitude_c=0.0,
        temperature_peak_month=9,
    )
    for month in monthly:
        np.testing.assert_array_equal(month, annual)


def test_s06_zero_precipitation_seasonality_is_uniform() -> None:
    annual = np.linspace(120.0, 1440.0, 12, dtype=np.float64).reshape(3, 4)
    monthly = monthly_precipitation_fields(
        annual_precipitation_mm=annual,
        precipitation_seasonality_log_amplitude=0.0,
        precipitation_peak_month=11,
    )
    expected = annual / 12.0
    for month in monthly:
        np.testing.assert_array_equal(month, expected)


def test_s07_monthly_arrays_are_finite_and_precipitation_positive() -> None:
    state = _surface(_plan(seasonality=True))
    assert state.monthly_mean_temperature_c is not None
    assert state.monthly_precipitation_mm is not None
    assert state.monthly_mean_temperature_c.dtype == np.dtype(np.float32)
    assert state.monthly_precipitation_mm.dtype == np.dtype(np.float32)
    assert np.isfinite(state.monthly_mean_temperature_c).all()
    assert np.isfinite(state.monthly_precipitation_mm).all()
    assert np.all(state.monthly_precipitation_mm > 0.0)


def test_s08_monthly_precipitation_fraction_is_spatially_constant() -> None:
    state = _surface(_plan(seasonality=True))
    assert state.annual_precipitation_mm is not None
    assert state.monthly_precipitation_mm is not None
    for month in range(12):
        ratio = (
            state.monthly_precipitation_mm[month].astype(np.float64)
            / state.annual_precipitation_mm.astype(np.float64)
        )
        assert float(np.max(ratio) - np.min(ratio)) < 2e-7


def test_s09_enabling_seasonality_does_not_change_annual_c1_c2_c3_fields() -> None:
    annual_only = _surface(_plan(seasonality=False))
    seasonal = _surface(_plan(seasonality=True))

    np.testing.assert_array_equal(
        seasonal.annual_mean_temperature_c,
        annual_only.annual_mean_temperature_c,
    )
    np.testing.assert_array_equal(
        seasonal.annual_precipitation_mm,
        annual_only.annual_precipitation_mm,
    )
    np.testing.assert_array_equal(seasonal.moisture, annual_only.moisture)
    np.testing.assert_array_equal(
        seasonal.vegetation_density,
        annual_only.vegetation_density,
    )


def test_s10_absent_seasonality_preserves_frozen_prealpha_contract() -> None:
    state = _surface(_plan(seasonality=False))
    assert state.annual_mean_temperature_c is not None
    assert state.annual_precipitation_mm is not None
    assert state.monthly_mean_temperature_c is None
    assert state.monthly_precipitation_mm is None

    request = GenerationRequest.model_validate(
        json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    )
    catalog = load_preset_catalog(A08 / "presets.json")
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version="0.2.0.dev0",
    )

    assert domain_spec_fingerprint(request.domain_spec) == (
        "sha256:ae27f9151850fe61e789a182aeaa055cb2c511c2f352bd093c21283901e67bb9"
    )
    assert semantic_plan_fingerprint(plan) == (
        "sha256:15970c8b771e049ec958f2182419ee1f8316dd73e4e81e9b1014435ed3d6f1d8"
    )


def test_s11_core_v01_cannot_contain_climate_or_seasonality() -> None:
    payload = {
        "schema_version": "0.1",
        "id": "c4-v01-reject",
        "seed": 1,
        "domain": {"size": {"width_km": 2.0, "height_km": 2.0}},
        "simulation": {"cell_size_km": 1.0},
        "hydrology": {
            "stream_threshold_km2": 1.0,
            "lake_min_area_km2": 1.0,
            "lake_min_depth_m": 1.0,
            "river_depth_at_threshold_m": 0.5,
            "river_depth_exponent": 0.3,
        },
        "surface": {
            "moisture_base": 0.3,
            "water_moisture_boost": 0.4,
            "water_moisture_decay_km": 2.0,
            "moisture_noise_amplitude": 0.1,
            "moisture_noise_scale_km": 3.0,
            "vegetation_slope_zero_deg": 45.0,
            "climate": {
                "mean_temperature_c": 10.0,
                "north_minus_south_temperature_c": 0.0,
                "temperature_noise_amplitude_c": 0.0,
                "mean_annual_precipitation_mm": 800.0,
                "moisture_transport_bearing_deg": 90.0,
                "orographic_scale_km": 10.0,
                "orographic_strength": 0.0,
                "precipitation_noise_log_amplitude": 0.0,
                "climate_noise_scale_km": 10.0,
                "seasonality": {
                    "temperature_seasonal_amplitude_c": 5.0,
                    "temperature_peak_month": 7,
                    "precipitation_seasonality_log_amplitude": 1.0,
                    "precipitation_peak_month": 1,
                },
            },
        },
        "features": [],
        "constraints": [],
    }
    with pytest.raises(ValidationError, match="surface.climate is only valid"):
        DomainSpec.model_validate(payload)


def test_s12_seasonality_exports_exact_monthly_derived_field_contract() -> None:
    assembly = _generate_a08(_seasonal_a08_request())
    fields = assembly.data.fields

    temperature_ids = [f"temperature_month_{month:02d}" for month in range(1, 13)]
    precipitation_ids = [
        f"precipitation_month_{month:02d}" for month in range(1, 13)
    ]
    assert all(field_id in fields for field_id in temperature_ids)
    assert all(field_id in fields for field_id in precipitation_ids)
    assert len([name for name in fields if name.startswith("temperature_month_")]) == 12
    assert len([name for name in fields if name.startswith("precipitation_month_")]) == 12

    assert fields["temperature"].role is FieldRole.CANONICAL
    assert fields["annual_precipitation"].role is FieldRole.CANONICAL

    for field_id in temperature_ids:
        descriptor = fields[field_id]
        assert descriptor.role is FieldRole.DERIVED
        assert descriptor.unit == "degC"
        assert descriptor.dtype == "float32"
        assert descriptor.shape == (
            assembly.data.grid.rows,
            assembly.data.grid.columns,
        )
        assert assembly.field_payloads[field_id].dtype == np.dtype(np.float32)

    for field_id in precipitation_ids:
        descriptor = fields[field_id]
        assert descriptor.role is FieldRole.DERIVED
        assert descriptor.unit == "mm/month"
        assert descriptor.dtype == "float32"
        assert descriptor.shape == (
            assembly.data.grid.rows,
            assembly.data.grid.columns,
        )
        assert assembly.field_payloads[field_id].dtype == np.dtype(np.float32)


def test_s13_replay_is_exact_and_seasonality_changes_plan_fingerprint() -> None:
    request = _seasonal_a08_request()
    first = _generate_a08(request)
    replay = _generate_a08(request)

    assert set(first.field_payloads) == set(replay.field_payloads)
    for field_id in first.field_payloads:
        np.testing.assert_array_equal(
            first.field_payloads[field_id],
            replay.field_payloads[field_id],
        )

    catalog = load_preset_catalog(A08 / "presets.json")
    registry = registry_for_request(request, catalog)
    first_plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version="0.2-test",
    )
    changed_request = _seasonal_a08_request(temperature_amplitude_c=8.0)
    changed_registry = registry_for_request(changed_request, catalog)
    changed_plan = compile_domain_spec(
        changed_request.domain_spec,
        registry=changed_registry,
        generator_version="0.2-test",
    )
    assert semantic_plan_fingerprint(first_plan) != semantic_plan_fingerprint(
        changed_plan
    )
