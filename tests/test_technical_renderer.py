from __future__ import annotations

from pathlib import Path
import struct

import numpy as np
import pytest

from domain_generator.assembly import DomainAssembly
from domain_generator.contracts import DomainData
from domain_generator.technical_renderer import (
    TechnicalRenderError,
    render_technical_map,
)


def _domain_data(*, with_features: bool = False) -> DomainData:
    fields = {
        "elevation": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/elevation.npy",
            "dtype": "float32",
            "shape": [2, 4],
            "unit": "m",
        },
        "water_depth": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/water_depth.npy",
            "dtype": "float32",
            "shape": [2, 4],
            "unit": "m",
        },
        "moisture": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/moisture.npy",
            "dtype": "float32",
            "shape": [2, 4],
            "unit": "normalized",
        },
        "vegetation_density": {
            "role": "canonical",
            "format": "npy",
            "path": "fields/vegetation_density.npy",
            "dtype": "float32",
            "shape": [2, 4],
            "unit": "normalized",
        },
    }

    features: dict[str, object] = {}
    networks: dict[str, object] = {}
    if with_features:
        features = {
            "terrain-point": {
                "label": "Peak marker",
                "source": {"type": "specified", "preset": "test"},
                "family": "terrain",
                "geometry": {"type": "point", "x_km": 0.5, "y_km": 0.5},
            },
            "corridor": {
                "label": "Pass",
                "source": {"type": "specified", "preset": "test"},
                "family": "terrain",
                "geometry": {
                    "type": "corridor",
                    "centerline": [
                        {"x_km": 0.2, "y_km": 1.7},
                        {"x_km": 1.5, "y_km": 1.2},
                        {"x_km": 2.4, "y_km": 1.5},
                    ],
                },
            },
            "ridge": {
                "label": "Ridge",
                "source": {"type": "specified", "preset": "test"},
                "family": "terrain",
                "geometry": {
                    "type": "band",
                    "centerline": [
                        {"x_km": 0.4, "y_km": 0.8},
                        {"x_km": 2.0, "y_km": 1.0},
                        {"x_km": 3.4, "y_km": 0.7},
                    ],
                    "width_profile": [
                        {"t": 0.0, "width_km": 0.3},
                        {"t": 0.5, "width_km": 0.5},
                        {"t": 1.0, "width_km": 0.25},
                    ],
                },
            },
            "plateau": {
                "label": "Plateau",
                "source": {"type": "specified", "preset": "test"},
                "family": "terrain",
                "geometry": {
                    "type": "area",
                    "boundary": [
                        {"x_km": 2.5, "y_km": 1.1},
                        {"x_km": 3.5, "y_km": 1.1},
                        {"x_km": 3.4, "y_km": 1.8},
                        {"x_km": 2.6, "y_km": 1.7},
                    ],
                },
            },
            "forest": {
                "label": "Forest",
                "source": {"type": "specified", "preset": "test"},
                "family": "surface",
                "geometry": {
                    "type": "area",
                    "boundary": [
                        {"x_km": 0.2, "y_km": 0.2},
                        {"x_km": 1.2, "y_km": 0.2},
                        {"x_km": 1.1, "y_km": 0.7},
                        {"x_km": 0.3, "y_km": 0.8},
                    ],
                },
            },
            "village": {
                "label": "Village",
                "source": {"type": "specified", "preset": "test"},
                "family": "poi",
                "geometry": {"type": "point", "x_km": 2.2, "y_km": 0.4},
            },
            "lake-0001": {
                "source": {"type": "generated", "system": "hydrology"},
                "family": "hydro",
                "geometry": {
                    "type": "region_set",
                    "polygons": [
                        {
                            "outer": [
                                {"x_km": 2.6, "y_km": 0.2},
                                {"x_km": 3.5, "y_km": 0.2},
                                {"x_km": 3.5, "y_km": 0.8},
                                {"x_km": 2.6, "y_km": 0.8},
                            ],
                            "holes": [],
                        }
                    ],
                },
                "properties": {
                    "area_km2": 0.54,
                    "surface_elevation_m": 4.0,
                    "max_depth_m": 2.0,
                },
            },
        }
        networks = {
            "rivers": {
                "type": "directed",
                "nodes": {
                    "source": {
                        "kind": "source",
                        "position": {"x_km": 0.3, "y_km": 1.8},
                    },
                    "outlet": {
                        "kind": "domain_outlet",
                        "position": {"x_km": 4.0, "y_km": 0.9},
                        "boundary_side": "east",
                    },
                },
                "segments": {
                    "river-1": {
                        "from": "source",
                        "to": "outlet",
                        "centerline": [
                            {"x_km": 0.3, "y_km": 1.8},
                            {"x_km": 1.5, "y_km": 1.3},
                            {"x_km": 2.8, "y_km": 1.1},
                            {"x_km": 4.0, "y_km": 0.9},
                        ],
                        "properties": {"catchment_area_km2": 3.0},
                    }
                },
            }
        }

    return DomainData.model_validate(
        {
            "domain_data_version": "0.1",
            "identity": {"id": "renderer-test", "label": "Renderer Test"},
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
            "domain": {"width_km": 4.0, "height_km": 2.0},
            "grid": {"cell_size_km": 1.0, "rows": 2, "columns": 4},
            "fields": fields,
            "features": features,
            "networks": networks,
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


def _assembly(*, with_features: bool = False) -> DomainAssembly:
    return DomainAssembly(
        data=_domain_data(with_features=with_features),
        field_payloads={
            "elevation": np.array([[14.0, 18.0, 22.0, 30.0], [4.0, 8.0, 12.0, 20.0]], dtype=np.float32),
            "water_depth": np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.5, 1.0]], dtype=np.float32),
            "moisture": np.array([[1.0, 0.8, 0.5, 0.3], [0.6, 0.5, 0.8, 1.0]], dtype=np.float32),
            "vegetation_density": np.array([[0.0, 0.2, 0.5, 0.7], [0.8, 0.6, 0.2, 0.0]], dtype=np.float32),
        },
    )


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_renderer_writes_png_with_domain_aspect_ratio_and_creates_preview_parent(tmp_path: Path) -> None:
    target = tmp_path / "preview" / "technical-map.png"

    result = render_technical_map(assembly=_assembly(), output_path=target)

    assert result.path == target
    assert (result.width_px, result.height_px) == (1600, 800)
    assert _png_size(target) == (1600, 800)


def test_renderer_is_byte_deterministic_for_same_assembly(tmp_path: Path) -> None:
    assembly = _assembly(with_features=True)
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"

    render_technical_map(assembly=assembly, output_path=first)
    render_technical_map(assembly=assembly, output_path=second)

    assert first.read_bytes() == second.read_bytes()


def test_renderer_does_not_mutate_domain_payloads(tmp_path: Path) -> None:
    assembly = _assembly(with_features=True)
    before = {name: array.copy() for name, array in assembly.field_payloads.items()}

    render_technical_map(assembly=assembly, output_path=tmp_path / "map.png")

    for name, expected in before.items():
        np.testing.assert_array_equal(assembly.field_payloads[name], expected)


def test_renderer_handles_all_current_semantic_feature_geometry_and_river_network(tmp_path: Path) -> None:
    target = tmp_path / "map.png"

    render_technical_map(assembly=_assembly(with_features=True), output_path=target)

    assert target.is_file()
    assert target.stat().st_size > 1000


def test_renderer_rejects_existing_target_without_overwriting(tmp_path: Path) -> None:
    target = tmp_path / "map.png"
    target.write_bytes(b"keep")

    with pytest.raises(TechnicalRenderError, match="already exists"):
        render_technical_map(assembly=_assembly(), output_path=target)

    assert target.read_bytes() == b"keep"


def test_renderer_rejects_missing_grandparent(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "preview" / "map.png"

    with pytest.raises(TechnicalRenderError, match="own parent"):
        render_technical_map(assembly=_assembly(), output_path=target)

    assert not target.parent.exists()


def test_renderer_rejects_descriptor_payload_mismatch_before_writing(tmp_path: Path) -> None:
    assembly = _assembly()
    broken = DomainAssembly(
        data=assembly.data,
        field_payloads={key: value for key, value in assembly.field_payloads.items() if key != "moisture"},
    )
    target = tmp_path / "preview" / "map.png"

    with pytest.raises(TechnicalRenderError, match="ids mismatch"):
        render_technical_map(assembly=broken, output_path=target)

    assert not target.parent.exists()


def test_renderer_requires_png_suffix(tmp_path: Path) -> None:
    with pytest.raises(TechnicalRenderError, match="must end with .png"):
        render_technical_map(assembly=_assembly(), output_path=tmp_path / "map.jpg")


def test_renderer_cleans_temporary_file_after_render_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import domain_generator.technical_renderer as module

    def fail_render(*args, **kwargs) -> None:
        raise OSError("synthetic render failure")

    monkeypatch.setattr(module, "_render_png", fail_render)
    target = tmp_path / "map.png"

    with pytest.raises(TechnicalRenderError, match="failed to render"):
        render_technical_map(assembly=_assembly(), output_path=target)

    assert not target.exists()
    assert list(tmp_path.iterdir()) == []
