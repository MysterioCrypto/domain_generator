from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from domain_generator.assembly import DomainAssembly
from domain_generator.bundle_export import DomainBundleExportError, export_domain_bundle
from domain_generator.contracts import BundleFileKind, BundleManifest, DomainData


def _domain_data(*, elevation_path: str = "fields/elevation.npy") -> DomainData:
    fields = {
        "elevation": {
            "role": "canonical",
            "format": "npy",
            "path": elevation_path,
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
    return DomainData.model_validate(
        {
            "domain_data_version": "0.1",
            "identity": {"id": "bundle-test", "label": "Bundle Test"},
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
        }
    )


def _assembly(*, elevation_path: str = "fields/elevation.npy") -> DomainAssembly:
    payloads = {
        "elevation": np.array([[10.0, 11.0], [12.0, 13.0]], dtype=np.float32),
        "water_depth": np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.float32),
        "moisture": np.array([[0.2, 1.0], [0.4, 0.5]], dtype=np.float32),
        "vegetation_density": np.array([[0.1, 0.0], [0.3, 0.4]], dtype=np.float32),
    }
    return DomainAssembly(data=_domain_data(elevation_path=elevation_path), field_payloads=payloads)


def _sha(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def test_export_writes_canonical_bundle_and_manifest(tmp_path: Path) -> None:
    assembly = _assembly()
    target = tmp_path / "world"

    result = export_domain_bundle(assembly=assembly, output_dir=target)

    assert result.root == target
    assert sorted(path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()) == [
        "domain.json",
        "fields/elevation.npy",
        "fields/moisture.npy",
        "fields/vegetation_density.npy",
        "fields/water_depth.npy",
        "manifest.json",
    ]

    domain_payload = json.loads((target / "domain.json").read_text(encoding="utf-8"))
    assert domain_payload == assembly.data.model_dump(mode="json", by_alias=True, exclude_none=False)
    assert (target / "domain.json").read_bytes().endswith(b"\n")

    for field_id, descriptor in assembly.data.fields.items():
        persisted = np.load(target / Path(*descriptor.path.split("/")), allow_pickle=False)
        np.testing.assert_array_equal(persisted, assembly.field_payloads[field_id])
        assert persisted.dtype == np.float32

    manifest = BundleManifest.model_validate_json((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == result.manifest
    assert manifest.domain_id == "bundle-test"
    assert all(entry.path != "manifest.json" for entry in manifest.canonical_files)
    assert manifest.canonical_files[0].kind is BundleFileKind.DOMAIN_DATA
    for entry in manifest.canonical_files:
        file_path = target / Path(*entry.path.split("/"))
        assert entry.sha256 == _sha(file_path)
        assert entry.size_bytes == file_path.stat().st_size


def test_export_is_byte_deterministic_for_same_assembly(tmp_path: Path) -> None:
    assembly = _assembly()
    first = tmp_path / "first"
    second = tmp_path / "second"

    export_domain_bundle(assembly=assembly, output_dir=first)
    export_domain_bundle(assembly=assembly, output_dir=second)

    first_files = sorted(path.relative_to(first).as_posix() for path in first.rglob("*") if path.is_file())
    second_files = sorted(path.relative_to(second).as_posix() for path in second.rglob("*") if path.is_file())
    assert first_files == second_files
    for relative in first_files:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()


def test_export_rejects_existing_target_without_mutation(tmp_path: Path) -> None:
    target = tmp_path / "world"
    target.mkdir()
    marker = target / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    with pytest.raises(DomainBundleExportError, match="already exists"):
        export_domain_bundle(assembly=_assembly(), output_dir=target)

    assert marker.read_text(encoding="utf-8") == "keep"
    assert list(target.iterdir()) == [marker]


def test_export_rejects_missing_parent(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "world"

    with pytest.raises(DomainBundleExportError, match="parent"):
        export_domain_bundle(assembly=_assembly(), output_dir=target)

    assert not target.parent.exists()


def test_export_rejects_descriptor_payload_id_mismatch_before_writing(tmp_path: Path) -> None:
    assembly = _assembly()
    broken = DomainAssembly(
        data=assembly.data,
        field_payloads={key: value for key, value in assembly.field_payloads.items() if key != "moisture"},
    )
    target = tmp_path / "world"

    with pytest.raises(DomainBundleExportError, match="ids mismatch"):
        export_domain_bundle(assembly=broken, output_dir=target)

    assert not target.exists()


def test_export_rejects_non_normalized_internal_path(tmp_path: Path) -> None:
    assembly = _assembly(elevation_path="fields/./elevation.npy")

    with pytest.raises(DomainBundleExportError, match="normalized"):
        export_domain_bundle(assembly=assembly, output_dir=tmp_path / "world")


def test_export_cleans_temporary_directory_after_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import domain_generator.bundle_export as module

    def fail_write(path: Path, payload: np.ndarray) -> None:
        raise OSError("synthetic failure")

    monkeypatch.setattr(module, "_write_npy_exact", fail_write)
    target = tmp_path / "world"

    with pytest.raises(DomainBundleExportError, match="failed to persist"):
        export_domain_bundle(assembly=_assembly(), output_dir=target)

    assert not target.exists()
    assert list(tmp_path.iterdir()) == []
