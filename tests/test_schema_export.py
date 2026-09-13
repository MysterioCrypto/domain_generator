from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from domain_generator.contracts import (
    BundleManifest,
    DomainData,
    DomainSpec,
    GenerationConfig,
    GenerationPlan,
    LayoutCandidate,
    ValidationResult,
)
from domain_generator.schema_export import (
    ROOT_CONTRACT_MODELS,
    generate_schema_documents,
    render_schema_document,
)


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas" / "v0.1"


def sample_payloads() -> dict[type, dict]:
    fields = {
        "elevation": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/elevation.npy",
            "dtype": "float32",
            "shape": [2, 2],
            "unit": "m",
        },
        "water_depth": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/water_depth.npy",
            "dtype": "float32",
            "shape": [2, 2],
            "unit": "m",
        },
        "moisture": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/moisture.npy",
            "dtype": "float32",
            "shape": [2, 2],
            "unit": "normalized",
        },
        "vegetation_density": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/vegetation_density.npy",
            "dtype": "float32",
            "shape": [2, 2],
            "unit": "normalized",
        },
    }

    hydrology = {
        "stream_threshold_km2": 1.0,
        "lake_min_area_km2": 1.0,
        "lake_min_depth_m": 1.0,
        "river_depth_at_threshold_m": 0.5,
        "river_depth_exponent": 0.3,
    }
    surface = {
        "moisture_base": 0.35,
        "water_moisture_boost": 0.55,
        "water_moisture_decay_km": 8.0,
        "moisture_noise_amplitude": 0.1,
        "moisture_noise_scale_km": 12.0,
        "vegetation_slope_zero_deg": 45.0,
    }

    return {
        DomainSpec: {
            "schema_version": "0.1",
            "id": "schema-test-domain",
            "seed": 7,
            "domain": {"size": {"width_km": 2.0, "height_km": 2.0}},
            "simulation": {"cell_size_km": 1.0},
            "hydrology": hydrology,
            "surface": surface,
            "features": [],
            "constraints": [],
        },
        GenerationPlan: {
            "plan_version": "0.1",
            "source": {
                "spec_id": "schema-test-domain",
                "spec_schema_version": "0.1",
                "spec_fingerprint": "sha256:spec",
                "generator_version": "0.1.0.dev0",
            },
            "seed": 7,
            "domain": {"width_km": 2.0, "height_km": 2.0},
            "grid": {"cell_size_km": 1.0, "rows": 2, "columns": 2},
            "hydrology": hydrology,
            "surface": surface,
            "features": [],
            "constraints": [],
        },
        LayoutCandidate: {
            "layout_version": "0.1",
            "source_plan": {"fingerprint": "sha256:plan"},
            "attempt_index": 0,
            "geometry_realizations": {},
            "placement_reservations": {},
        },
        ValidationResult: {
            "validation_version": "0.1",
            "attempt_index": 0,
            "stage": "final",
            "engine_invariants": {"passed": True, "results": []},
            "hard_constraints": {"passed": True, "results": []},
            "soft_constraints": {"results": []},
            "ranking": {
                "worst_effective_violation": 0.0,
                "weighted_mean_score": 1.0,
            },
        },
        GenerationConfig: {
            "generation_config_version": "0.1",
            "semantic": {
                "max_attempts": 4,
                "target_valid_candidates": 2,
            },
            "observability": {},
        },
        DomainData: {
            "domain_data_version": "0.1",
            "identity": {"id": "schema-test-domain"},
            "provenance": {
                "spec_schema_version": "0.1",
                "spec_fingerprint": "sha256:spec",
                "plan_fingerprint": "sha256:plan",
                "generation_config_fingerprint": "sha256:config",
                "root_seed": 7,
                "accepted_attempt_index": 0,
                "generator": {"name": "domain_generator", "version": "0.1.0.dev0"},
                "rng_version": 1,
            },
            "domain": {"width_km": 2.0, "height_km": 2.0},
            "grid": {"cell_size_km": 1.0, "rows": 2, "columns": 2},
            "fields": fields,
            "features": {},
            "networks": {},
            "validation": {
                "engine_invariants_passed": True,
                "hard_constraints_passed": True,
                "soft": {
                    "worst_effective_violation": 0.0,
                    "weighted_mean_score": 1.0,
                },
            },
        },
        BundleManifest: {
            "bundle_version": "0.1",
            "domain_data_version": "0.1",
            "domain_id": "schema-test-domain",
            "canonical_files": [
                {
                    "path": "domain.json",
                    "kind": "domain_data",
                    "sha256": "sha256:" + "0" * 64,
                    "size_bytes": 1,
                },
                {
                    "path": "fields/elevation.npy",
                    "kind": "field",
                    "sha256": "sha256:" + "1" * 64,
                    "size_bytes": 2,
                    "field_id": "elevation",
                },
            ],
        },
    }


def test_schema_snapshots_match_current_models() -> None:
    documents = generate_schema_documents()
    assert set(documents) == set(ROOT_CONTRACT_MODELS)

    for filename, schema in documents.items():
        committed = (SCHEMA_DIR / filename).read_text(encoding="utf-8")
        assert committed == render_schema_document(schema)


@pytest.mark.parametrize("filename", sorted(ROOT_CONTRACT_MODELS))
def test_generated_schema_is_valid_draft_2020_12(filename: str) -> None:
    schema = generate_schema_documents()[filename]
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("model", list(ROOT_CONTRACT_MODELS.values()))
def test_root_contract_json_round_trip_and_schema_validation(model: type) -> None:
    instance = model.model_validate(sample_payloads()[model])

    serialized_json = instance.model_dump_json(by_alias=True)
    reparsed = model.model_validate_json(serialized_json)
    assert reparsed == instance

    payload = json.loads(serialized_json)
    filename = next(name for name, candidate in ROOT_CONTRACT_MODELS.items() if candidate is model)
    Draft202012Validator(generate_schema_documents()[filename]).validate(payload)


def test_domain_spec_schema_rejects_unknown_root_property() -> None:
    payload = dict(sample_payloads()[DomainSpec])
    payload["unexpected"] = True

    schema = generate_schema_documents()["domain-spec.schema.json"]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)
