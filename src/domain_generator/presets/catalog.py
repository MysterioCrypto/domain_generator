from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts.common import FrozenStrictModel
from .definitions import PresetDefinition


class PresetCatalog(FrozenStrictModel):
    """Serializable reusable collection of external preset definitions."""

    preset_catalog_version: Literal["0.1"]
    presets: tuple[PresetDefinition, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "PresetCatalog":
        ids = [preset.id for preset in self.presets]
        if len(ids) != len(set(ids)):
            raise ValueError("preset ids must be unique")
        return self


__all__ = ["PresetCatalog"]
