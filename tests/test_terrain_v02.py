from __future__ import annotations

import copy

import numpy as np
import pytest
from pydantic import ValidationError

from domain_generator.application import registry_for_request
from domain_generator.compiler import compile_domain_spec, semantic_plan_fingerprint
from domain_generator.contracts import GenerationRequest, WorldPoint
from domain_generator.layout import generate_layout, smooth_band_centerline
from domain_generator.pipeline.rng import RngFactory
from domain_generator.presets import PresetCatalog
from domain_generator.terrain import generate_terrain
from domain_generator.terrain.base import synthesize_base_elevation


def _request_payload(
    *,
    width_km: float = 24.0,
    height_km: float = 16.0,
    layers: list[dict] | None = None,
    features: list[dict] | None = None,
) -> dict:
    if layers is None:
        layers = [
            {"id": "macro", "scale_km": 64.0, "amplitude_m": 240.0},
            {"id": "regional", "scale_km": 20.0, "amplitude_m": 90.0},
            {"id": "detail", "scale_km": 6.0, "amplitude_m": 24.0},
        ]
    return {
        "request_version": "0.2",
        "domain_spec": {
            "schema_version": "0.2",
            "id": "terrain-v02-test",
            "seed": 20260914,
            "domain": {"size": {"width_km": width_km, "height_km": height_km}},
            "simulation": {"cell_size_km": 1.0},
            "terrain": {
                "base_elevation_m": 120.0,
                "noise_layers": layers,
            },
            "hydrology": {
                "stream_threshold_km2": 10000.0,
                "lake_min_area_km2": 10000.0,
                "lake_min_depth_m": 10000.0,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
            },
            "surface": {
                "moisture_base": 0.35,
                "water_moisture_boost": 0.0,
                "water_moisture_decay_km": 8.0,
                "moisture_noise_amplitude": 0.0,
                "moisture_noise_scale_km": 12.0,
                "vegetation_slope_zero_deg": 45.0,
            },
            "features": features or [],
            "constraints": [],
        },
        "generation_config": {
            "generation_config_version": "0.1",
            "semantic": {"max_attempts": 1, "target_valid_candidates": 1},
            "observability": {},
        },
    }


def _compile(payload: dict, catalog: PresetCatalog | None = None):
    request = GenerationRequest.model_validate(payload)
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version="test-v0.2",
    )
    return request, registry, plan


def _terrain(payload: dict, catalog: PresetCatalog | None = None):
    request, registry, plan = _compile(payload, catalog)
    rng = RngFactory(plan.seed)
    layout = generate_layout(plan, attempt_index=0, rng_factory=rng)
    terrain = generate_terrain(plan, layout, attempt_index=0, rng_factory=rng)
    return request, plan, layout, terrain


def test_domain_spec_v02_requires_explicit_terrain() -> None:
    payload = _request_payload()
    del payload["domain_spec"]["terrain"]
    with pytest.raises(ValidationError, match="requires terrain"):
        GenerationRequest.model_validate(payload)


def test_base_elevation_is_nonconstant_and_layer_order_independent() -> None:
    payload = _request_payload()
    _, _, first_plan = _compile(payload)
    reversed_payload = copy.deepcopy(payload)
    reversed_payload["domain_spec"]["terrain"]["noise_layers"].reverse()
    _, _, second_plan = _compile(reversed_payload)

    first = synthesize_base_elevation(
        first_plan,
        attempt_index=0,
        rng_factory=RngFactory(first_plan.seed),
    )
    second = synthesize_base_elevation(
        second_plan,
        attempt_index=0,
        rng_factory=RngFactory(second_plan.seed),
    )

    assert first.dtype == np.dtype(np.float32)
    assert float(np.std(first)) > 1.0
    np.testing.assert_array_equal(first, second)


def test_base_elevation_is_world_space_consistent_across_domain_extension() -> None:
    _, _, small_plan = _compile(_request_payload(width_km=12.0, height_km=10.0))
    _, _, wide_plan = _compile(_request_payload(width_km=18.0, height_km=10.0))

    small = synthesize_base_elevation(
        small_plan,
        attempt_index=0,
        rng_factory=RngFactory(small_plan.seed),
    )
    wide = synthesize_base_elevation(
        wide_plan,
        attempt_index=0,
        rng_factory=RngFactory(wide_plan.seed),
    )

    np.testing.assert_array_equal(small, wide[:, : small.shape[1]])


def test_semantic_plan_fingerprint_includes_terrain_synthesis() -> None:
    first_payload = _request_payload()
    second_payload = copy.deepcopy(first_payload)
    second_payload["domain_spec"]["terrain"]["noise_layers"][0]["amplitude_m"] = 241.0
    _, _, first_plan = _compile(first_payload)
    _, _, second_plan = _compile(second_payload)

    assert semantic_plan_fingerprint(first_plan) != semantic_plan_fingerprint(second_plan)


def test_band_smoothing_preserves_endpoints_and_removes_raw_corner() -> None:
    raw = (
        WorldPoint(x_km=0.0, y_km=0.0),
        WorldPoint(x_km=5.0, y_km=7.0),
        WorldPoint(x_km=10.0, y_km=0.0),
    )
    smooth = smooth_band_centerline(raw)

    assert smooth[0] == raw[0]
    assert smooth[-1] == raw[-1]
    assert len(smooth) > len(raw)
    assert raw[1] not in smooth[1:-1]
    assert all(0.0 <= point.x_km <= 10.0 for point in smooth)
    assert all(0.0 <= point.y_km <= 7.0 for point in smooth)


def _ridge_catalog() -> PresetCatalog:
    return PresetCatalog.model_validate(
        {
            "preset_catalog_version": "0.1",
            "presets": [
                {
                    "id": "massif",
                    "family": "terrain",
                    "layout": {
                        "mode": "geometry",
                        "shape": "band",
                        "parameters": {
                            "control_point_count": {"kind": "fixed", "type": "integer", "value": 4},
                            "curvature": {"kind": "fixed", "type": "float", "value": 0.35},
                            "width_km": {"kind": "fixed", "type": "float", "value": 14.0},
                            "width_sample_count": {"kind": "fixed", "type": "integer", "value": 7},
                        },
                    },
                    "effect": {
                        "stage": "terrain",
                        "operator": "ridge",
                        "parameters": {
                            "height_m": {"kind": "fixed", "type": "float", "value": 520.0},
                            "profile_power": {"kind": "fixed", "type": "float", "value": 1.25},
                            "roughness": {"kind": "fixed", "type": "float", "value": 0.55},
                            "roughness_scale_km": {"kind": "fixed", "type": "float", "value": 3.0},
                        },
                    },
                }
            ],
        }
    )


def test_ridge_is_broad_massif_over_nonflat_background() -> None:
    payload = _request_payload(
        width_km=48.0,
        height_km=32.0,
        features=[{"id": "ridge-01", "preset": "massif"}],
    )
    _, _, layout, terrain = _terrain(payload, _ridge_catalog())

    assert terrain.base_elevation_m is not None
    contribution = terrain.elevation_m.astype(np.float64) - terrain.base_elevation_m.astype(np.float64)
    strong = contribution > 40.0
    rows, columns = np.where(strong)

    assert layout.geometry_realizations["ridge-01"].type == "band"
    assert len(layout.geometry_realizations["ridge-01"].centerline) > 6
    assert int(np.count_nonzero(strong)) > 40
    assert int(np.ptp(rows)) >= 4
    assert int(np.ptp(columns)) >= 4
    assert float(np.max(contribution)) > 250.0
    background = contribution < 1e-5
    assert int(np.count_nonzero(background)) > 100
    assert float(np.std(terrain.base_elevation_m[background])) > 1.0


def _area_catalog() -> PresetCatalog:
    return PresetCatalog.model_validate(
        {
            "preset_catalog_version": "0.1",
            "presets": [
                {
                    "id": "upland",
                    "family": "terrain",
                    "layout": {
                        "mode": "geometry",
                        "shape": "area",
                        "parameters": {
                            "vertex_count": {"kind": "fixed", "type": "integer", "value": 8},
                            "radial_extent": {"kind": "fixed", "type": "float", "value": 0.4},
                            "radial_irregularity": {"kind": "fixed", "type": "float", "value": 0.12},
                        },
                    },
                    "effect": {
                        "stage": "terrain",
                        "operator": "raise",
                        "parameters": {
                            "height_m": {"kind": "fixed", "type": "float", "value": 180.0},
                            "blend_width_km": {"kind": "fixed", "type": "float", "value": 4.0},
                        },
                    },
                }
            ],
        }
    )


def test_area_raise_blends_instead_of_binary_step() -> None:
    payload = _request_payload(
        width_km=36.0,
        height_km=30.0,
        features=[{"id": "upland-01", "preset": "upland"}],
    )
    _, _, _, terrain = _terrain(payload, _area_catalog())
    assert terrain.base_elevation_m is not None
    contribution = terrain.elevation_m.astype(np.float64) - terrain.base_elevation_m.astype(np.float64)
    positive = contribution[contribution > 0.01]

    assert positive.size > 10
    assert float(np.max(positive)) <= 180.01
    # A binary Core 0.1 Area step had only {0, height}; v0.2 must contain
    # multiple transition magnitudes at grid cell centers.
    assert np.unique(np.round(positive, 2)).size >= 4
    assert bool(np.any((positive > 1.0) & (positive < 170.0)))
