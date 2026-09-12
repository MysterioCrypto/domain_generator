import math

import pytest
from pydantic import ValidationError

from domain_generator.contracts.config import GenerationConfig
from domain_generator.contracts.data import DomainData
from domain_generator.contracts.layout import LayoutCandidate
from domain_generator.contracts.plan import GenerationPlan
from domain_generator.contracts.validation import ValidationResult


def minimal_plan() -> dict:
    return {
        "plan_version": "0.1",
        "source": {
            "spec_id": "example-domain",
            "spec_schema_version": "0.1",
            "spec_fingerprint": "sha256:spec",
            "generator_version": "0.1.0.dev0",
        },
        "seed": 123,
        "domain": {"width_km": 120.0, "height_km": 100.0},
        "grid": {"cell_size_km": 0.25, "rows": 400, "columns": 480},
        "hydrology": {
            "stream_threshold_km2": 25.0,
            "lake_min_area_km2": 1.0,
            "lake_min_depth_m": 2.0,
            "river_depth_at_threshold_m": 0.5,
            "river_depth_exponent": 0.3,
        },
        "features": [
            {
                "id": "mountain-01",
                "metadata": {"source_preset": "mountain_range"},
                "family": "terrain",
                "layout": {
                    "mode": "geometry",
                    "shape": "band",
                    "parameters": {
                        "width_km": {
                            "kind": "range",
                            "type": "float",
                            "min": 15.0,
                            "max": 30.0,
                            "sampler": {"type": "triangular", "mode": 24.0},
                        }
                    },
                },
                "effect": {
                    "stage": "terrain",
                    "operator": "ridge",
                    "parameters": {
                        "roughness": {
                            "kind": "fixed",
                            "type": "float",
                            "value": 0.7,
                        }
                    },
                },
            }
        ],
        "constraints": [],
    }


def test_generation_plan_parses_and_is_frozen() -> None:
    plan = GenerationPlan.model_validate(minimal_plan())
    assert plan.features[0].layout.shape == "band"
    assert plan.hydrology.stream_threshold_km2 == 25.0
    assert plan.hydrology.river_depth_at_threshold_m == 0.5
    assert plan.hydrology.river_depth_exponent == 0.3
    with pytest.raises(ValidationError):
        plan.grid = plan.grid


def test_generation_plan_requires_hydrology_recipe() -> None:
    data = minimal_plan()
    del data["hydrology"]
    with pytest.raises(ValidationError):
        GenerationPlan.model_validate(data)


def test_generation_plan_rejects_grid_mismatch() -> None:
    data = minimal_plan()
    data["grid"]["columns"] = 479
    with pytest.raises(ValidationError, match="domain width"):
        GenerationPlan.model_validate(data)


def test_dependent_feature_requires_site_profile() -> None:
    data = minimal_plan()
    data["features"] = [
        {
            "id": "fort-01",
            "metadata": {"source_preset": "fort"},
            "family": "poi",
            "layout": {"mode": "reservation", "final_shape": "point"},
            "effect": {"stage": "dependent_placement", "operator": "suitability_placement"},
        }
    ]
    with pytest.raises(ValidationError, match="site_profile"):
        GenerationPlan.model_validate(data)


def test_layout_candidate_allows_empty_reservation() -> None:
    layout = LayoutCandidate.model_validate(
        {
            "layout_version": "0.1",
            "source_plan": {"fingerprint": "sha256:plan"},
            "attempt_index": 0,
            "placement_reservations": {
                "fort-01": {
                    "final_shape": "point",
                    "source_constraints": [],
                    "allowed_region": {"type": "region_set", "polygons": []},
                }
            },
        }
    )
    assert layout.placement_reservations["fort-01"].allowed_region.polygons == ()


def test_layout_candidate_rejects_same_feature_in_both_collections() -> None:
    data = {
        "layout_version": "0.1",
        "source_plan": {"fingerprint": "sha256:plan"},
        "attempt_index": 0,
        "geometry_realizations": {"x": {"type": "point", "x_km": 1.0, "y_km": 1.0}},
        "placement_reservations": {
            "x": {"final_shape": "point", "allowed_region": {"type": "region_set", "polygons": []}}
        },
    }
    with pytest.raises(ValidationError, match="both geometry and reservation"):
        LayoutCandidate.model_validate(data)


def test_validation_final_valid_requires_ranking() -> None:
    data = {
        "validation_version": "0.1",
        "attempt_index": 0,
        "stage": "final",
        "engine_invariants": {"passed": True, "results": []},
        "hard_constraints": {"passed": True, "results": []},
        "soft_constraints": {"results": []},
        "ranking": None,
    }
    with pytest.raises(ValidationError, match="requires ranking"):
        ValidationResult.model_validate(data)


def test_validation_soft_effective_violation_checked() -> None:
    data = {
        "validation_version": "0.1",
        "attempt_index": 0,
        "stage": "final",
        "engine_invariants": {"passed": True, "results": []},
        "hard_constraints": {"passed": True, "results": []},
        "soft_constraints": {
            "results": [
                {
                    "constraint_id": "soft-1",
                    "score": 0.8,
                    "weight": 0.5,
                    "effective_violation": 0.2,
                    "measurement": {"type": "distance", "value": 7.0, "unit": "km"},
                }
            ]
        },
        "ranking": {"worst_effective_violation": 0.1, "weighted_mean_score": 0.8},
    }
    with pytest.raises(ValidationError, match="effective_violation"):
        ValidationResult.model_validate(data)


def test_generation_config_budget() -> None:
    with pytest.raises(ValidationError, match="target_valid_candidates"):
        GenerationConfig.model_validate(
            {
                "generation_config_version": "0.1",
                "semantic": {"max_attempts": 3, "target_valid_candidates": 4},
            }
        )


def domain_data() -> dict:
    fields = {
        "elevation": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/elevation.npy",
            "dtype": "float32",
            "shape": [400, 480],
            "unit": "m",
        },
        "water_depth": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/water_depth.npy",
            "dtype": "float32",
            "shape": [400, 480],
            "unit": "m",
        },
        "moisture": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/moisture.npy",
            "dtype": "float32",
            "shape": [400, 480],
            "unit": "normalized",
        },
        "vegetation_density": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/vegetation_density.npy",
            "dtype": "float32",
            "shape": [400, 480],
            "unit": "normalized",
        },
    }
    return {
        "domain_data_version": "0.1",
        "identity": {"id": "example-domain", "label": "Example"},
        "provenance": {
            "spec_schema_version": "0.1",
            "spec_fingerprint": "sha256:spec",
            "plan_fingerprint": "sha256:plan",
            "generation_config_fingerprint": "sha256:config",
            "root_seed": 123,
            "accepted_attempt_index": 2,
            "generator": {"name": "domain_generator", "version": "0.1.0.dev0"},
            "rng_version": 1,
        },
        "domain": {"width_km": 120.0, "height_km": 100.0},
        "grid": {"cell_size_km": 0.25, "rows": 400, "columns": 480},
        "fields": fields,
        "features": {},
        "networks": {},
        "validation": {
            "engine_invariants_passed": True,
            "hard_constraints_passed": True,
            "soft": {"worst_effective_violation": 0.0, "weighted_mean_score": 1.0},
        },
    }


def test_domain_data_minimal_world_parses() -> None:
    data = DomainData.model_validate(domain_data())
    assert data.fields["water_depth"].dtype == "float32"


def test_domain_data_rejects_path_traversal() -> None:
    data = domain_data()
    data["fields"]["elevation"]["path"] = "../elevation.npy"
    with pytest.raises(ValidationError, match="must be relative"):
        DomainData.model_validate(data)


def test_domain_data_requires_canonical_fields() -> None:
    data = domain_data()
    del data["fields"]["moisture"]
    with pytest.raises(ValidationError, match="missing canonical fields"):
        DomainData.model_validate(data)


def test_domain_data_rejects_nonfinite_geometry() -> None:
    data = domain_data()
    data["features"]["fort"] = {
        "source": {"type": "specified", "preset": "fort"},
        "family": "poi",
        "geometry": {"type": "point", "x_km": math.inf, "y_km": 1.0},
    }
    with pytest.raises(ValidationError):
        DomainData.model_validate(data)


def test_river_segment_serializes_from_to_aliases() -> None:
    data = domain_data()
    data["networks"] = {
        "rivers": {
            "type": "directed",
            "nodes": {
                "a": {"kind": "source", "position": {"x_km": 1.0, "y_km": 2.0}},
                "b": {
                    "kind": "domain_outlet",
                    "position": {"x_km": 120.0, "y_km": 2.0},
                    "boundary_side": "east",
                },
            },
            "segments": {
                "s": {
                    "from": "a",
                    "to": "b",
                    "centerline": [
                        {"x_km": 1.0, "y_km": 2.0},
                        {"x_km": 120.0, "y_km": 2.0},
                    ],
                    "properties": {"catchment_area_km2": 10.0},
                }
            },
        }
    }
    model = DomainData.model_validate(data)
    dumped = model.model_dump(by_alias=True)
    segment = dumped["networks"]["rivers"]["segments"]["s"]
    assert segment["from"] == "a"
    assert segment["to"] == "b"
