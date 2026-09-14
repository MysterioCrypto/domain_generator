from __future__ import annotations

from domain_generator.compiler import compile_domain_spec
from domain_generator.contracts.spec import DomainSpec
from domain_generator.layout import generate_layout, validate_layout
from domain_generator.pipeline.rng import RngFactory
from domain_generator.presets import PresetDefinition, PresetRegistry


def _ridge_preset() -> PresetDefinition:
    return PresetDefinition.model_validate(
        {
            "id": "ridge",
            "family": "terrain",
            "layout": {
                "mode": "geometry",
                "shape": "band",
                "parameters": {
                    "control_point_count": {
                        "kind": "fixed",
                        "type": "integer",
                        "value": 3,
                    },
                    "curvature": {
                        "kind": "fixed",
                        "type": "float",
                        "value": 0.35,
                    },
                    "width_km": {
                        "kind": "fixed",
                        "type": "float",
                        "value": 4.0,
                    },
                    "width_sample_count": {
                        "kind": "fixed",
                        "type": "integer",
                        "value": 5,
                    },
                },
            },
            "effect": {
                "stage": "terrain",
                "operator": "ridge",
                "parameters": {
                    "height_m": {
                        "kind": "fixed",
                        "type": "float",
                        "value": 200.0,
                    },
                    "profile_power": {
                        "kind": "fixed",
                        "type": "float",
                        "value": 1.2,
                    },
                    "roughness": {
                        "kind": "fixed",
                        "type": "float",
                        "value": 0.0,
                    },
                    "roughness_scale_km": {
                        "kind": "fixed",
                        "type": "float",
                        "value": 2.0,
                    },
                },
            },
        }
    )


def _spec() -> DomainSpec:
    return DomainSpec.model_validate(
        {
            "schema_version": "0.1",
            "id": "layout-soft-boundary",
            "seed": 6006,
            "domain": {"size": {"width_km": 24.0, "height_km": 16.0}},
            "simulation": {"cell_size_km": 1.0},
            "hydrology": {
                "stream_threshold_km2": 1000.0,
                "lake_min_area_km2": 1000.0,
                "lake_min_depth_m": 1000.0,
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
            "features": [
                {"id": "ridge-01", "preset": "ridge"},
            ],
            "constraints": [
                {
                    "id": "ridge-center-near-center",
                    "relation": "near",
                    "subject": {"feature": "ridge-01", "part": "center"},
                    "target": {"domain_anchor": "center"},
                    "strength": "soft",
                    "parameters": {"max_distance_km": 15.0},
                    "weight": 1.0,
                }
            ],
        }
    )


def test_layout_ignores_soft_constraints_and_leaves_them_for_final_scoring() -> None:
    registry = PresetRegistry([_ridge_preset()], operator_ids={"ridge"})
    plan = compile_domain_spec(_spec(), registry=registry, generator_version="test")

    candidate = generate_layout(
        plan,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    validation = validate_layout(plan, candidate, attempt_index=0)

    assert validation.engine_invariants.passed is True
    assert validation.hard_constraints.passed is True
    assert validation.hard_constraints.results == ()
    assert validation.soft_constraints.results == ()
    assert validation.ranking is None
