from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, model_validator

from .common import FrozenStrictModel


class SemanticGenerationConfig(FrozenStrictModel):
    max_attempts: Annotated[StrictInt, Field(ge=1)]
    target_valid_candidates: Annotated[StrictInt, Field(ge=1)]

    @model_validator(mode="after")
    def validate_budget(self) -> "SemanticGenerationConfig":
        if self.target_valid_candidates > self.max_attempts:
            raise ValueError("target_valid_candidates must be <= max_attempts")
        return self


class ObservabilityConfig(FrozenStrictModel):
    debug: StrictBool = False
    save_rejected_attempts: StrictBool = False
    save_validation_details: StrictBool = False
    save_intermediate_fields: StrictBool = False


class GenerationConfig(FrozenStrictModel):
    generation_config_version: Literal["0.1"]
    semantic: SemanticGenerationConfig
    observability: ObservabilityConfig = ObservabilityConfig()
