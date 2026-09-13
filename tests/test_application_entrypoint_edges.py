from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain_generator.application import (
    ApplicationInputError,
    load_preset_catalog,
    registry_from_catalog,
)
from domain_generator.cli import EXIT_OUTPUT_ERROR, EXIT_SUCCESS, main
from domain_generator.presets import PresetCatalog


def _request_payload() -> dict:
    return {
        "request_version": "0.1",
        "domain_spec": {
            "schema_version": "0.1",
            "id": "edge-test",
            "seed": 9,
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


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _preset(preset_id: str, operator: str) -> dict:
    return {
        "id": preset_id,
        "family": "terrain",
        "layout": {
            "mode": "geometry",
            "shape": "area",
            "parameters": {},
        },
        "effect": {
            "stage": "terrain",
            "operator": operator,
            "parameters": {},
        },
    }


def test_preset_catalog_loader_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "presets.json"
    _write_json(
        path,
        {
            "preset_catalog_version": "0.1",
            "presets": [
                _preset("duplicate", "raise"),
                _preset("duplicate", "raise"),
            ],
        },
    )

    with pytest.raises(ApplicationInputError, match="contract validation"):
        load_preset_catalog(path)


def test_registry_rejects_catalog_operator_outside_core_capabilities() -> None:
    catalog = PresetCatalog.model_validate(
        {
            "preset_catalog_version": "0.1",
            "presets": [_preset("unsupported", "not_a_core_operator")],
        }
    )

    with pytest.raises(ApplicationInputError, match="unknown operator"):
        registry_from_catalog(catalog)


def test_cli_invalid_arguments_use_argparse_exit_2() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["generate"])

    assert exc_info.value.code == 2


def test_cli_missing_output_parent_is_output_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    _write_json(request_path, _request_payload())
    target = tmp_path / "missing" / "generated"

    exit_code = main(["generate", str(request_path), "--output", str(target)])

    captured = capsys.readouterr()
    assert exit_code == EXIT_OUTPUT_ERROR
    assert captured.out == ""
    assert "output parent" in captured.err
    assert not target.parent.exists()


def test_cli_preview_success_reports_relative_preview_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    output_dir = tmp_path / "generated"
    _write_json(request_path, _request_payload())

    exit_code = main(
        [
            "generate",
            str(request_path),
            "--output",
            str(output_dir),
            "--preview",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    payload = json.loads(captured.out)
    assert payload["technical_preview"] == "preview/technical-map.png"
    assert (output_dir / "preview" / "technical-map.png").is_file()
