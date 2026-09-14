from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from .common import FrozenStrictModel
from .config import GenerationConfig
from .spec import DomainSpec


class GenerationRequest(FrozenStrictModel):
    """Serializable application request for one canonical generation run."""

    request_version: Literal["0.1", "0.2"]
    domain_spec: DomainSpec
    generation_config: GenerationConfig

    @model_validator(mode="after")
    def validate_version_alignment(self) -> "GenerationRequest":
        if self.request_version != self.domain_spec.schema_version:
            raise ValueError("request_version must match domain_spec.schema_version")
        return self


__all__ = ["GenerationRequest"]
