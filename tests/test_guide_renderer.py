from __future__ import annotations

import json
from pathlib import Path
import struct

import matplotlib.image as mpimg
import numpy as np

from domain_generator.application import generate_domain_bundle, registry_for_request
from domain_generator.assembly import DomainAssembly
from domain_generator.cli import EXIT_SUCCESS, main
from domain_generator.contracts import DomainData, GenerationRequest
from domain_generator.guide_renderer import render_guide_map


def _domain_data() -> DomainData:
    fields = {
        "elevation": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/elevation.npy",
            "dtype": "float32",
            "shape": [3, 6],
            "unit": "m",
        },
        "water_depth": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/water_depth.npy",
            "dtype": "float32",
            "shape": [3, 6],
            "unit": "m",
        },
        "moisture": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/moisture.npy",
            "dtype": "float32",
            "shape": [3, 6],
            "unit": "normalized",
        },
        "vegetation_density": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/vegetation_density.npy",
            "dtype": "float32",
            "shape": [3, 6],
            "unit": "normalized",
        },
    }
    return DomainData.model_validate(
        {
            "domain_data_version": "0.1",
            "identity": {"id": "guide-test", "label": "Guide Test"},
            "provenance": {
                "spec_schema_version": "0.1",
                "spec_fingerprint": "sha256:spec",
                "plan_fingerprint": "sha256:plan",
                "generation_config_fingerprint": "sha256:config",
                "root_seed": 17,
                "accepted_attempt_index": 0,
                "generator": {"name": "domain_generator", "version": "0.1.0.dev0"},
                "rng_version": 1,
            },
            "domain": {"width_km": 6.0, "height_km": 3.0},
            "grid": {"cell_size_km": 1.0, "rows": 3, "columns": 6},
            "fields": fields,
            "features": {
                "village": {
                    "label": "Village",
                    "source": {"type": "specified", "preset": "test"},
                    "family": "poi",
                    "geometry": {"type": "point", "x_km": 4.6, "y_km": 0.8},
                }
            },
            "networks": {
                "rivers": {
                    "type": "directed",
                    "nodes": {
                        "source": {
                            "kind": "source",
                            "position": {"x_km": 0.3, "y_km": 2.7},
                        },
                        "outlet": {
                            "kind": "domain_outlet",
                            "position": {"x_km": 6.0, "y_km": 0.8},
                            "boundary_side": "east",
                        },
                    },
                    "segments": {
                        "river-1": {
                            "from": "source",
                            "to": "outlet",
                            "centerline": [
                                {"x_km": 0.3, "y_km": 2.7},
                                {"x_km": 2.2, "y_km": 2.0},
                                {"x_km": 4.0, "y_km": 1.4},
                                {"x_km": 6.0, "y_km": 0.8},
                            ],
                            "properties": {"catchment_area_km2": 12.0},
                        }
                    },
                }
            },
            "validation": {
                "engine_invariants_passed": True,
                "hard_constraints_passed": True,
                "soft": {
                    "worst_effective_violation": 0.0,
                    "weighted_mean_score": 1.0,
                },
            },
        }
    )


def _assembly(*, flat: bool = False) -> DomainAssembly:
    if flat:
        elevation = np.zeros((3, 6), dtype=np.float32)
    else:
        elevation = np.array(
            [
                [30.0, 55.0, 90.0, 140.0, 110.0, 70.0],
                [10.0, 30.0, 65.0, 120.0, 85.0, 40.0],
                [-10.0, 5.0, 25.0, 65.0, 45.0, 15.0],
            ],
            dtype=np.float32,
        )
    return DomainAssembly(
        data=_domain_data(),
        field_payloads={
            "elevation": elevation,
            "water_depth": np.array(
                [
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.6],
                    [0.0, 0.0, 0.0, 0.5, 1.5, 1.0],
                ],
                dtype=np.float32,
            ),
            "moisture": np.array(
                [
                    [0.35, 0.35, 0.4, 0.45, 0.5, 0.55],
                    [0.4, 0.45, 0.55, 0.7, 1.0, 1.0],
                    [0.45, 0.55, 0.65, 1.0, 1.0, 1.0],
                ],
                dtype=np.float32,
            ),
            "vegetation_density": np.array(
                [
                    [0.65, 0.6, 0.5, 0.35, 0.2, 0.25],
                    [0.75, 0.7, 0.55, 0.3, 0.0, 0.0],
                    [0.8, 0.75, 0.6, 0.0, 0.0, 0.0],
                ],
                dtype=np.float32,
            ),
        },
    )


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def _request_payload() -> dict:
    return {
        "request_version": "0.1",
        "domain_spec": {
            "schema_version": "0.1",
            "id": "guide-application-test",
            "seed": 42,
            "domain": {"size": {"width_km": 4.0, "height_km": 2.0}},
            "simulation": {"cell_size_km": 1.0},
            "hydrology": {
                "stream_threshold_km2": 100.0,
                "lake_min_area_km2": 100.0,
                "lake_min_depth_m": 100.0,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
            },
            "surface": {
                "moisture_base": 0.35,
                "water_moisture_boost": 0.0,
                "water_moisture_decay_km": 5.0,
                "moisture_noise_amplitude": 0.0,
                "moisture_noise_scale_km": 8.0,
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


def test_guide_renderer_writes_map_like_png_with_domain_aspect_ratio(tmp_path: Path) -> None:
    target = tmp_path / "preview" / "guide-map.png"

    result = render_guide_map(assembly=_assembly(), output_path=target)

    assert result.path == target
    assert (result.width_px, result.height_px) == (1600, 800)
    assert _png_size(target) == (1600, 800)
    pixels = mpimg.imread(target)
    assert float(np.std(pixels[..., :3])) > 0.03
    blue_dominant = (pixels[..., 2] > pixels[..., 0] + 0.08) & (
        pixels[..., 2] > pixels[..., 1] + 0.03
    )
    assert int(np.count_nonzero(blue_dominant)) > 500


def test_guide_renderer_is_byte_deterministic_and_does_not_mutate_assembly(tmp_path: Path) -> None:
    assembly = _assembly()
    before = {name: array.copy() for name, array in assembly.field_payloads.items()}
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"

    render_guide_map(assembly=assembly, output_path=first)
    render_guide_map(assembly=assembly, output_path=second)

    assert first.read_bytes() == second.read_bytes()
    for name, expected in before.items():
        np.testing.assert_array_equal(assembly.field_payloads[name], expected)


def test_guide_renderer_handles_flat_elevation_without_black_square(tmp_path: Path) -> None:
    target = tmp_path / "flat.png"

    render_guide_map(assembly=_assembly(flat=True), output_path=target)

    pixels = mpimg.imread(target)
    land = pixels[..., :3]
    assert float(np.mean(land)) > 0.12
    assert float(np.std(land)) > 0.01


def test_application_can_publish_guide_and_technical_previews_together(tmp_path: Path) -> None:
    request = GenerationRequest.model_validate(_request_payload())
    target = tmp_path / "generated"

    result = generate_domain_bundle(
        request=request,
        registry=registry_for_request(request, None),
        output_dir=target,
        render_preview=True,
        render_guide_preview=True,
    )

    assert result.technical_preview == target / "preview" / "technical-map.png"
    assert result.guide_preview == target / "preview" / "guide-map.png"
    assert result.technical_preview.is_file()
    assert result.guide_preview.is_file()


def test_cli_guide_preview_reports_path_without_redefining_technical_preview(
    tmp_path: Path,
    capsys,
) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(_request_payload()), encoding="utf-8")
    target = tmp_path / "generated"

    exit_code = main(
        [
            "generate",
            str(request_path),
            "--output",
            str(target),
            "--guide-preview",
        ]
    )

    assert exit_code == EXIT_SUCCESS
    payload = json.loads(capsys.readouterr().out)
    assert payload["technical_preview"] is None
    assert payload["guide_preview"] == "preview/guide-map.png"
    assert (target / "preview" / "guide-map.png").is_file()
    assert not (target / "preview" / "technical-map.png").exists()
