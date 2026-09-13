from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import Field, StrictInt, StrictStr, model_validator

from .common import FrozenStrictModel


class BundleFileKind(StrEnum):
    DOMAIN_DATA = "domain_data"
    FIELD = "field"


class BundleFileEntry(FrozenStrictModel):
    path: Annotated[StrictStr, Field(min_length=1)]
    kind: BundleFileKind
    sha256: Annotated[StrictStr, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
    size_bytes: Annotated[StrictInt, Field(ge=0)]
    field_id: StrictStr | None = None

    @model_validator(mode="after")
    def validate_entry(self) -> "BundleFileEntry":
        if "\\" in self.path:
            raise ValueError("bundle file path must use POSIX separators")
        parsed = PurePosixPath(self.path)
        if parsed.is_absolute() or ".." in parsed.parts:
            raise ValueError("bundle file path must be relative and must not contain '..'")
        if parsed.as_posix() != self.path:
            raise ValueError("bundle file path must already be normalized")

        if self.kind is BundleFileKind.DOMAIN_DATA:
            if self.path != "domain.json":
                raise ValueError("domain_data entry path must be 'domain.json'")
            if self.field_id is not None:
                raise ValueError("domain_data entry must not define field_id")
        elif not self.field_id:
            raise ValueError("field entry requires field_id")
        return self


class BundleManifest(FrozenStrictModel):
    bundle_version: Literal["0.1"]
    domain_data_version: Literal["0.1"]
    domain_id: Annotated[StrictStr, Field(min_length=1)]
    canonical_files: tuple[BundleFileEntry, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_manifest(self) -> "BundleManifest":
        paths = [entry.path for entry in self.canonical_files]
        if len(paths) != len(set(paths)):
            raise ValueError("canonical file paths must be unique")
        if "manifest.json" in paths:
            raise ValueError("manifest.json must not hash itself")

        domain_entries = [entry for entry in self.canonical_files if entry.kind is BundleFileKind.DOMAIN_DATA]
        if len(domain_entries) != 1:
            raise ValueError("manifest requires exactly one domain_data entry")

        field_ids = [
            entry.field_id
            for entry in self.canonical_files
            if entry.kind is BundleFileKind.FIELD
        ]
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("manifest field ids must be unique")
        return self


__all__ = ["BundleFileEntry", "BundleFileKind", "BundleManifest"]
