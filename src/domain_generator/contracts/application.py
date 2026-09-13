from __future__ import annotations

from typing import Literal

from .common import FrozenStrictModel
from .config import GenerationConfig
from .spec import DomainSpec


class GenerationRequest(FrozenStrictModel):
    """Serializable application request for one canonical generation run."""

    request_version: Literal["0.1"]
    domain_spec: DomainSpec
    generation_config: GenerationConfig


__all__ = ["GenerationRequest"]
