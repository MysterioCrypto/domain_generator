from __future__ import annotations

import json
from pathlib import Path

import pytest

import domain_generator
from domain_generator.application import (
    ApplicationInputError,
    ApplicationOutputError,
    generate_domain,
    generate_domain_bundle,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.capabilities import CORE_OPERATOR_IDS
from domain_generator.cli import (
    EXIT_GENERATION_ERROR,
    EXIT_INPUT_ERROR,
    EXIT_OUTPUT_ERROR,
    EXIT_SUCCESS,
    main,
)
from domain_generator.contracts import GenerationRequest
from domain_generator.presets import PresetCatalog


def request_payload(*, with_feature: bool = False) -> dict:
    features = []
    if with_feature:
        features = [{"id": "terrain-01", "preset": "missing-preset"}]
    return {
        "request_version": "0.1",
        "domain_spec": {
            "schema_version": "0.1",
            "id": "application-test",
            "label": "Application Test",
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
            "features": features,
            "constraints": [],
        },
        "generation_config": {
            "generation_config_version": "0.1",
            "semantic": {
                "max_attempts": 1,
                "target_valid_candidates": 1,
            },
            "observability": {},
        },
    }


def request(*, with_feature: bool = False) -> GenerationRequest:
    return GenerationRequest.model_validate(request_payload(with_feature=with_feature))


def empty_catalog() -> PresetCatalog:
    return PresetCatalog(preset_catalog_version="0.1", presets=())


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_core_operator_capability_set_is_explicit() -> None:
    assert CORE_OPERATOR_IDS == {
        "raise",
        "depress",
        "ridge",
        "flatten",
        "moisture_bias",
        "vegetation_bias",
        "suitability_placement",
    }


def test_request_and_catalog_json_loaders(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    catalog_path = tmp_path / "presets.json"
    write_json(request_path, request_payload())
    write_json(catalog_path, {"preset_catalog_version": "0.1", "presets": []})

    loaded_request = load_generation_request(request_path)
    loaded_catalog = load_preset_catalog(catalog_path)

    assert loaded_request.domain_spec.id == "application-test"
    assert loaded_catalog.presets == ()


def test_loader_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "request.json"
    path.write_text("{bad", encoding="utf-8")

    with pytest.raises(ApplicationInputError, match="invalid JSON"):
        load_generation_request(path)


def test_nonempty_feature_set_requires_catalog() -> None:
    with pytest.raises(ApplicationInputError, match="--presets is required"):
        registry_for_request(request(with_feature=True), None)


def test_generate_domain_runs_canonical_pipeline() -> None:
    req = request()
    registry = registry_for_request(req, None)

    assembly = generate_domain(
        spec=req.domain_spec,
        config=req.generation_config,
        registry=registry,
    )

    assert assembly.data.identity.id == "application-test"
    assert assembly.data.provenance.generator.version == domain_generator.__version__
    assert assembly.data.provenance.accepted_attempt_index == 0
    assert tuple(assembly.data.fields) == (
        "elevation",
        "water_depth",
        "moisture",
        "vegetation_density",
    )


def test_generate_domain_bundle_publishes_complete_bundle(tmp_path: Path) -> None:
    req = request()
    registry = registry_for_request(req, None)
    target = tmp_path / "generated"

    result = generate_domain_bundle(
        request=req,
        registry=registry,
        output_dir=target,
    )

    assert result.output_dir == target
    assert result.technical_preview is None
    assert (target / "domain.json").is_file()
    assert (target / "manifest.json").is_file()
    assert (target / "fields" / "elevation.npy").is_file()
    assert not any(path.name.startswith(f".{target.name}.app-tmp-") for path in tmp_path.iterdir())


def test_generate_domain_bundle_with_preview_publishes_one_tree(tmp_path: Path) -> None:
    req = request()
    registry = registry_for_request(req, None)
    target = tmp_path / "generated"

    result = generate_domain_bundle(
        request=req,
        registry=registry,
        output_dir=target,
        render_preview=True,
    )

    assert result.technical_preview == target / "preview" / "technical-map.png"
    assert result.technical_preview.is_file()
    assert (target / "domain.json").is_file()


def test_application_rejects_existing_target_without_mutation(tmp_path: Path) -> None:
    target = tmp_path / "generated"
    target.mkdir()
    marker = target / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    req = request()

    with pytest.raises(ApplicationOutputError, match="already exists"):
        generate_domain_bundle(
            request=req,
            registry=registry_for_request(req, None),
            output_dir=target,
        )

    assert marker.read_text(encoding="utf-8") == "keep"


def test_application_cleans_staging_when_preview_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import domain_generator.technical_renderer as renderer

    def fail_render(*, assembly, output_path):
        raise renderer.TechnicalRenderError("synthetic renderer failure")

    monkeypatch.setattr(renderer, "render_technical_map", fail_render)
    req = request()
    target = tmp_path / "generated"

    with pytest.raises(ApplicationOutputError, match="technical preview"):
        generate_domain_bundle(
            request=req,
            registry=registry_for_request(req, None),
            output_dir=target,
            render_preview=True,
        )

    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


def test_cli_success_stdout_is_machine_readable_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request_path = tmp_path / "request.json"
    output_dir = tmp_path / "generated"
    write_json(request_path, request_payload())

    exit_code = main(["generate", str(request_path), "--output", str(output_dir)])

    captured = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    payload = json.loads(captured.out)
    assert payload == {
        "accepted_attempt_index": 0,
        "domain_id": "application-test",
        "output_dir": str(output_dir),
        "status": "ok",
        "technical_preview": None,
    }
    assert captured.err == ""


def test_cli_missing_required_catalog_is_input_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request_path = tmp_path / "request.json"
    write_json(request_path, request_payload(with_feature=True))

    exit_code = main(["generate", str(request_path), "--output", str(tmp_path / "generated")])

    captured = capsys.readouterr()
    assert exit_code == EXIT_INPUT_ERROR
    assert captured.out == ""
    assert "--presets is required" in captured.err


def test_cli_unknown_preset_is_generation_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request_path = tmp_path / "request.json"
    catalog_path = tmp_path / "presets.json"
    write_json(request_path, request_payload(with_feature=True))
    write_json(catalog_path, {"preset_catalog_version": "0.1", "presets": []})

    exit_code = main(
        [
            "generate",
            str(request_path),
            "--presets",
            str(catalog_path),
            "--output",
            str(tmp_path / "generated"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == EXIT_GENERATION_ERROR
    assert captured.out == ""
    assert "unknown preset id" in captured.err


def test_cli_existing_output_is_output_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request_path = tmp_path / "request.json"
    output_dir = tmp_path / "generated"
    output_dir.mkdir()
    write_json(request_path, request_payload())

    exit_code = main(["generate", str(request_path), "--output", str(output_dir)])

    captured = capsys.readouterr()
    assert exit_code == EXIT_OUTPUT_ERROR
    assert captured.out == ""
    assert "already exists" in captured.err
