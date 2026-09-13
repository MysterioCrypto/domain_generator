from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile

import numpy as np
from pydantic import ValidationError

from .assembly import DomainAssembly
from .contracts.bundle import BundleFileEntry, BundleFileKind, BundleManifest


class DomainBundleExportError(RuntimeError):
    """DomainAssembly cannot be persisted without violating bundle invariants."""


@dataclass(frozen=True, slots=True)
class ExportedDomainBundle:
    root: Path
    manifest: BundleManifest

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path):
            raise TypeError("root must be pathlib.Path")
        if not isinstance(self.manifest, BundleManifest):
            raise TypeError("manifest must be BundleManifest")


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _validate_field_paths(assembly: DomainAssembly) -> dict[str, PurePosixPath]:
    descriptor_ids = set(assembly.data.fields)
    payload_ids = set(assembly.field_payloads)
    if descriptor_ids != payload_ids:
        missing = sorted(descriptor_ids - payload_ids)
        extra = sorted(payload_ids - descriptor_ids)
        raise DomainBundleExportError(
            f"field descriptor/payload ids mismatch: missing={missing}, extra={extra}"
        )

    normalized_paths: dict[str, PurePosixPath] = {}
    seen: set[str] = {"domain.json", "manifest.json"}
    for field_id in sorted(assembly.data.fields):
        descriptor = assembly.data.fields[field_id]
        raw = descriptor.path
        if "\\" in raw:
            raise DomainBundleExportError(f"field {field_id!r} path must use POSIX separators")
        path = PurePosixPath(raw)
        if path.is_absolute() or ".." in path.parts:
            raise DomainBundleExportError(f"field {field_id!r} path is unsafe")
        normalized = path.as_posix()
        if normalized != raw:
            raise DomainBundleExportError(f"field {field_id!r} path must already be normalized")
        if normalized in seen:
            raise DomainBundleExportError(f"bundle path collision: {normalized!r}")
        seen.add(normalized)
        normalized_paths[field_id] = path

        payload = assembly.field_payloads[field_id]
        if not isinstance(payload, np.ndarray):
            raise DomainBundleExportError(f"field {field_id!r} payload must be numpy ndarray")
        if tuple(payload.shape) != descriptor.shape:
            raise DomainBundleExportError(
                f"field {field_id!r} shape must be {descriptor.shape}, got {payload.shape}"
            )
        if str(payload.dtype) != descriptor.dtype:
            raise DomainBundleExportError(
                f"field {field_id!r} dtype must be {descriptor.dtype!r}, got {str(payload.dtype)!r}"
            )
    return normalized_paths


def _digest_file(path: Path) -> tuple[str, int]:
    digest = sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            digest.update(block)
    return "sha256:" + digest.hexdigest(), size


def _write_npy_exact(path: Path, payload: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        np.save(handle, payload, allow_pickle=False)


def export_domain_bundle(*, assembly: DomainAssembly, output_dir: Path) -> ExportedDomainBundle:
    """Persist one already-assembled domain as an atomic canonical directory bundle."""
    if not isinstance(assembly, DomainAssembly):
        raise TypeError("assembly must be DomainAssembly")
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be pathlib.Path")

    field_paths = _validate_field_paths(assembly)

    if output_dir.exists():
        raise DomainBundleExportError("output directory already exists")
    parent = output_dir.parent
    if not parent.exists() or not parent.is_dir():
        raise DomainBundleExportError("output parent must already exist and be a directory")
    if not output_dir.name:
        raise DomainBundleExportError("output directory name must be non-empty")

    temp_root: Path | None = None
    try:
        temp_root = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=parent))

        domain_path = temp_root / "domain.json"
        domain_payload = assembly.data.model_dump(mode="json", by_alias=True, exclude_none=False)
        domain_path.write_bytes(_json_bytes(domain_payload))

        entries: list[BundleFileEntry] = []
        domain_sha, domain_size = _digest_file(domain_path)
        entries.append(
            BundleFileEntry(
                path="domain.json",
                kind=BundleFileKind.DOMAIN_DATA,
                sha256=domain_sha,
                size_bytes=domain_size,
            )
        )

        for field_id in sorted(field_paths):
            relative = field_paths[field_id]
            path = temp_root.joinpath(*relative.parts)
            _write_npy_exact(path, assembly.field_payloads[field_id])
            file_sha, file_size = _digest_file(path)
            entries.append(
                BundleFileEntry(
                    path=relative.as_posix(),
                    kind=BundleFileKind.FIELD,
                    sha256=file_sha,
                    size_bytes=file_size,
                    field_id=field_id,
                )
            )

        try:
            manifest = BundleManifest(
                bundle_version="0.1",
                domain_data_version=assembly.data.domain_data_version,
                domain_id=assembly.data.identity.id,
                canonical_files=tuple(entries),
            )
        except ValidationError as exc:
            raise DomainBundleExportError("generated bundle manifest failed contract validation") from exc

        manifest_payload = manifest.model_dump(mode="json", by_alias=True, exclude_none=False)
        (temp_root / "manifest.json").write_bytes(_json_bytes(manifest_payload))

        temp_root.rename(output_dir)
        temp_root = None
        return ExportedDomainBundle(root=output_dir, manifest=manifest)
    except DomainBundleExportError:
        raise
    except Exception as exc:
        raise DomainBundleExportError("failed to persist domain bundle") from exc
    finally:
        if temp_root is not None and temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)


__all__ = ["DomainBundleExportError", "ExportedDomainBundle", "export_domain_bundle"]
