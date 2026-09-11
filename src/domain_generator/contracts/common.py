from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr, model_validator


class StrictModel(BaseModel):
    """Base for canonical parsed contracts: exact structure and validated scalar types."""

    model_config = ConfigDict(extra="forbid")


class FrozenStrictModel(BaseModel):
    """Base for completed immutable serialized value objects/contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ConstraintStrength(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class Relation(StrEnum):
    NEAR = "near"
    FAR_FROM = "far_from"
    INSIDE = "inside"
    OUTSIDE = "outside"
    CROSSES = "crosses"
    OVERLAPS = "overlaps"
    ADJACENT = "adjacent"


class FeaturePart(StrEnum):
    WHOLE = "whole"
    CENTER = "center"
    START = "start"
    END = "end"
    ENDPOINTS = "endpoints"
    BOUNDARY = "boundary"


class DomainCompass(StrEnum):
    SOUTHWEST = "southwest"
    SOUTH = "south"
    SOUTHEAST = "southeast"
    WEST = "west"
    CENTER = "center"
    EAST = "east"
    NORTHWEST = "northwest"
    NORTH = "north"
    NORTHEAST = "northeast"


Number = StrictInt | StrictFloat
ScalarParameterValue = StrictBool | StrictInt | StrictFloat | StrictStr


class NumericRangeOverride(FrozenStrictModel):
    min: Number
    max: Number

    @model_validator(mode="after")
    def validate_order(self) -> "NumericRangeOverride":
        if self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class OneOfOverride(FrozenStrictModel):
    one_of: tuple[StrictStr, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique(self) -> "OneOfOverride":
        if len(set(self.one_of)) != len(self.one_of):
            raise ValueError("one_of values must be unique")
        return self


ParameterOverride = ScalarParameterValue | NumericRangeOverride | OneOfOverride


NormalizedValue = Annotated[StrictFloat, Field(ge=0.0, le=1.0)]
NonNegativeFloat = Annotated[StrictFloat, Field(ge=0.0)]
PositiveFloat = Annotated[StrictFloat, Field(gt=0.0)]
