from __future__ import annotations

from pathlib import Path

import pytest

from domain_generator.adapters import local_model as lm
from domain_generator.contracts import GenerationRequest
from domain_generator.presets import PresetCatalog


def request_payload() -> dict:
    return {
        "request_version": "0.1",
        "domain_spec": {
            "schema_version": "0.1",
            "id": "adapter-test",
            "label": "Adapter Test",
            "seed": 1234,
            "domain": {"size": {"width_km": 2.0, "height_km": 2.0}},
            "simulation": {"cell_size_km": 1.0},
            "hydrology": {
                "stream_threshold_km2": 10.0,
                "lake_min_area_km2": 1.0,
                "lake_min_depth_m": 1.0,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
            },
            "surface": {
                "moisture_base": 0.35,
                "water_moisture_boost": 0.55,
                "water_moisture_decay_km": 8.0,
                "moisture_noise_amplitude": 0.0,
                "moisture_noise_scale_km": 12.0,
                "vegetation_slope_zero_deg": 45.0,
            },
            "features": [],
            "constraints": [],
        },
        "generation_config": {
            "generation_config_version": "0.1",
            "semantic": {"max_attempts": 1, "target_valid_candidates": 1},
            "observability": {},
        },
    }


def request() -> GenerationRequest:
    return GenerationRequest.model_validate(request_payload())


def empty_catalog() -> PresetCatalog:
    return PresetCatalog(preset_catalog_version="0.1", presets=())


def sample_catalog() -> PresetCatalog:
    return PresetCatalog.model_validate(
        {
            "preset_catalog_version": "0.1",
            "presets": [
                {
                    "id": "z-ridge",
                    "family": "terrain",
                    "layout": {
                        "mode": "geometry",
                        "shape": "band",
                        "parameters": {
                            "width_km": {
                                "kind": "range",
                                "type": "float",
                                "min": 1.0,
                                "max": 5.0,
                                "sampler": {"type": "uniform"},
                            }
                        },
                    },
                    "effect": {
                        "stage": "terrain",
                        "operator": "ridge",
                        "parameters": {
                            "height_m": {"kind": "fixed", "type": "float", "value": 500.0}
                        },
                    },
                },
                {
                    "id": "a-area",
                    "family": "terrain",
                    "layout": {"mode": "geometry", "shape": "area", "parameters": {}},
                    "effect": {"stage": "terrain", "operator": "raise", "parameters": {}},
                },
            ],
        }
    )


class ScriptedModel:
    def __init__(self, *drafts: object) -> None:
        self.drafts = list(drafts)
        self.contexts: list[lm.ModelAuthoringContext] = []

    def create_decision(self, context: lm.ModelAuthoringContext) -> object:
        self.contexts.append(context)
        return self.drafts[len(self.contexts) - 1]


def ready_payload(req: GenerationRequest) -> dict:
    return {
        "decision_version": "0.1",
        "status": "ready",
        "request": req.model_dump(mode="json"),
        "assumptions": [],
    }


def test_projection_is_sorted_and_preserves_canonical_parameter_domains() -> None:
    projection = lm.build_model_preset_projection(sample_catalog())

    assert [preset.id for preset in projection] == ["a-area", "z-ridge"]
    ridge = projection[1]
    assert ridge.geometry == "band"
    assert ridge.operator == "ridge"
    assert [(parameter.name, parameter.owner) for parameter in ridge.parameters] == [
        ("width_km", "layout"),
        ("height_m", "effect"),
    ]
    assert ridge.parameters[0].min == 1.0
    assert ridge.parameters[0].max == 5.0
    assert ridge.parameters[1].value == 500.0


def test_guide_must_reference_existing_preset_parameters() -> None:
    guide = lm.PresetGuideCatalog.model_validate(
        {
            "preset_guide_version": "0.1",
            "presets": [
                {
                    "id": "z-ridge",
                    "summary": "ridge",
                    "parameter_notes": {"not-real": "bad"},
                }
            ],
        }
    )

    with pytest.raises(lm.LocalModelAdapterInputError, match="unknown parameters"):
        lm.validate_preset_guide(sample_catalog(), guide)


def test_default_edit_policy_rejects_hidden_seed_change() -> None:
    base = request()
    changed_payload = request_payload()
    changed_payload["domain_spec"]["seed"] = 999
    changed = GenerationRequest.model_validate(changed_payload)

    with pytest.raises(lm.LocalModelEditPolicyError, match="domain_spec.seed"):
        lm.validate_request_edit_policy(
            base_request=base,
            request=changed,
            policy=lm.LocalModelEditPolicy(),
        )


def test_needs_clarification_does_not_generate(tmp_path: Path) -> None:
    model = ScriptedModel(
        {
            "decision_version": "0.1",
            "status": "needs_clarification",
            "questions": ["Where should the river enter?"],
        }
    )
    output = tmp_path / "generated"

    result = lm.run_local_model_adapter(
        user_intent="make a region",
        base_request=request(),
        catalog=empty_catalog(),
        model=model,
        output_dir=output,
    )

    assert result.status == "needs_clarification"
    assert result.generation is None
    assert not output.exists()
    assert result.audit.draft_count == 1


def test_invalid_first_draft_repairs_then_generates_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = request()
    model = ScriptedModel("{bad", ready_payload(base))
    output = tmp_path / "generated"
    calls = 0
    original = lm.generate_domain_bundle

    def counted(**kwargs):
        nonlocal calls
        calls += 1
        return original(**kwargs)

    monkeypatch.setattr(lm, "generate_domain_bundle", counted)

    result = lm.run_local_model_adapter(
        user_intent="make a minimal region",
        base_request=base,
        catalog=empty_catalog(),
        model=model,
        output_dir=output,
    )

    assert result.status == "success"
    assert calls == 1
    assert len(model.contexts) == 2
    assert model.contexts[1].draft_index == 1
    assert model.contexts[1].diagnostics[0].code == "decision_validation"
    assert result.audit.draft_count == 2
    assert result.audit.repair_count == 1
    assert (output / "domain.json").is_file()


def test_repair_budget_stops_after_three_drafts(tmp_path: Path) -> None:
    model = ScriptedModel("bad", "bad", "bad")

    result = lm.run_local_model_adapter(
        user_intent="make a region",
        base_request=request(),
        catalog=empty_catalog(),
        model=model,
        output_dir=tmp_path / "generated",
    )

    assert result.status == "preflight_failed"
    assert len(model.contexts) == 3
    assert result.audit.draft_count == 3
    assert result.audit.repair_count == 2
    assert len(result.audit.diagnostics) == 3


def test_compiler_preflight_error_is_repairable_but_does_not_generate(tmp_path: Path) -> None:
    payload = request_payload()
    payload["domain_spec"]["features"] = [{"id": "x", "preset": "missing"}]
    candidate = GenerationRequest.model_validate(payload)
    model = ScriptedModel(ready_payload(candidate))

    result = lm.run_local_model_adapter(
        user_intent="add a feature",
        base_request=request(),
        catalog=empty_catalog(),
        model=model,
        output_dir=tmp_path / "generated",
        max_repairs=0,
    )

    assert result.status == "preflight_failed"
    assert result.audit.diagnostics[0].code == "compiler"
    assert not (tmp_path / "generated").exists()


def test_generation_failure_does_not_trigger_model_repair(tmp_path: Path) -> None:
    output = tmp_path / "generated"
    output.mkdir()
    model = ScriptedModel(ready_payload(request()))

    result = lm.run_local_model_adapter(
        user_intent="make a region",
        base_request=request(),
        catalog=empty_catalog(),
        model=model,
        output_dir=output,
    )

    assert result.status == "generation_failed"
    assert len(model.contexts) == 1
    assert result.audit.diagnostics[-1].code == "generation"


def test_edit_policy_violation_can_be_reported_for_repair(tmp_path: Path) -> None:
    base = request()
    changed_payload = request_payload()
    changed_payload["domain_spec"]["seed"] = 999
    changed = GenerationRequest.model_validate(changed_payload)
    model = ScriptedModel(ready_payload(changed), ready_payload(base))

    result = lm.run_local_model_adapter(
        user_intent="make a region",
        base_request=base,
        catalog=empty_catalog(),
        model=model,
        output_dir=tmp_path / "generated",
    )

    assert result.status == "success"
    assert model.contexts[1].diagnostics[0].code == "edit_policy"
    assert result.final_request is not None
    assert result.final_request.domain_spec.seed == 1234


def test_max_repairs_is_bounded() -> None:
    with pytest.raises(lm.LocalModelAdapterInputError, match="\[0, 2\]"):
        lm.run_local_model_adapter(
            user_intent="x",
            base_request=request(),
            catalog=empty_catalog(),
            model=ScriptedModel("bad"),
            output_dir=Path("unused"),
            max_repairs=3,
        )


def test_audit_digests_are_stable_and_do_not_contain_reasoning(tmp_path: Path) -> None:
    base = request()
    model = ScriptedModel(ready_payload(base))

    result = lm.run_local_model_adapter(
        user_intent="make a region",
        base_request=base,
        catalog=empty_catalog(),
        model=model,
        output_dir=tmp_path / "generated",
    )

    assert result.status == "success"
    assert result.audit.base_request_sha256.startswith("sha256:")
    assert result.audit.preset_catalog_sha256.startswith("sha256:")
    assert result.audit.final_request_sha256 == result.audit.base_request_sha256
    assert "reason" not in result.audit.model_dump(mode="json")
