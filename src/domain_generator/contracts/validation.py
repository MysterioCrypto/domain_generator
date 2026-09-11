from __future__ import annotations

from enum import StrEnum
from math import isclose
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictFloat, StrictInt, StrictStr, model_validator

from .common import FrozenStrictModel, Number, ScalarParameterValue


class ValidationStage(StrEnum):
    LAYOUT = "layout"
    TERRAIN = "terrain"
    HYDROLOGY = "hydrology"
    SURFACE = "surface"
    PLACEMENT = "placement"
    FINAL = "final"


class EngineInvariantResult(FrozenStrictModel):
    id: Annotated[StrictStr, Field(min_length=1)]
    passed: StrictBool
    measured: dict[StrictStr, ScalarParameterValue] = Field(default_factory=dict)
    message: StrictStr | None = None


class EngineInvariantGroup(FrozenStrictModel):
    passed: StrictBool
    results: tuple[EngineInvariantResult, ...] = ()

    @model_validator(mode="after")
    def validate_aggregate(self) -> "EngineInvariantGroup":
        if self.passed != all(result.passed for result in self.results):
            raise ValueError("engine_invariants.passed must equal all(result.passed)")
        return self


class Measurement(FrozenStrictModel):
    type: Annotated[StrictStr, Field(min_length=1)]
    value: Number
    unit: StrictStr | None = None


class PredicateSnapshot(FrozenStrictModel):
    type: Annotated[StrictStr, Field(min_length=1)]
    threshold: Number


class HardConstraintResult(FrozenStrictModel):
    constraint_id: Annotated[StrictStr, Field(min_length=1)]
    satisfied: StrictBool
    measurement: Measurement
    predicate: PredicateSnapshot


class HardConstraintGroup(FrozenStrictModel):
    passed: StrictBool
    results: tuple[HardConstraintResult, ...] = ()

    @model_validator(mode="after")
    def validate_aggregate(self) -> "HardConstraintGroup":
        if self.passed != all(result.satisfied for result in self.results):
            raise ValueError("hard_constraints.passed must equal all(result.satisfied)")
        return self


class SoftConstraintResult(FrozenStrictModel):
    constraint_id: Annotated[StrictStr, Field(min_length=1)]
    score: Annotated[StrictFloat, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
    weight: Annotated[StrictFloat, Field(gt=0.0, le=1.0, allow_inf_nan=False)] = 1.0
    effective_violation: Annotated[StrictFloat, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
    measurement: Measurement

    @model_validator(mode="after")
    def validate_effective_violation(self) -> "SoftConstraintResult":
        expected = (1.0 - self.score) * self.weight
        if not isclose(self.effective_violation, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("effective_violation must equal (1 - score) * weight")
        return self


class SoftConstraintGroup(FrozenStrictModel):
    results: tuple[SoftConstraintResult, ...] = ()


class RankingResult(FrozenStrictModel):
    worst_effective_violation: Annotated[StrictFloat, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
    weighted_mean_score: Annotated[StrictFloat, Field(ge=0.0, le=1.0, allow_inf_nan=False)]


class ValidationResult(FrozenStrictModel):
    validation_version: Literal["0.1"]
    attempt_index: Annotated[StrictInt, Field(ge=0)]
    stage: ValidationStage
    engine_invariants: EngineInvariantGroup
    hard_constraints: HardConstraintGroup
    soft_constraints: SoftConstraintGroup
    ranking: RankingResult | None = None

    @model_validator(mode="after")
    def validate_ranking_state(self) -> "ValidationResult":
        valid = self.engine_invariants.passed and self.hard_constraints.passed
        if not valid and self.ranking is not None:
            raise ValueError("rejected validation result must have ranking=null")
        if self.stage is ValidationStage.FINAL and valid and self.ranking is None:
            raise ValueError("valid final validation result requires ranking")
        return self
