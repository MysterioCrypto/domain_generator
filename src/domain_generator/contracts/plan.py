from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StrictFloat, StrictInt, StrictStr, model_validator

from .common import (
    ConstraintStrength,
    FeaturePart,
    FiniteFloat,
    FrozenStrictModel,
    Number,
    Relation,
)


class FeatureFamily(StrEnum):
    TERRAIN = "terrain"
    SURFACE = "surface"
    POI = "poi"


class LayoutMode(StrEnum):
    GEOMETRY = "geometry"
    RESERVATION = "reservation"


class GeometryShape(StrEnum):
    POINT = "point"
    CORRIDOR = "corridor"
    BAND = "band"
    AREA = "area"


class EffectStage(StrEnum):
    TERRAIN = "terrain"
    SURFACE = "surface"
    DEPENDENT_PLACEMENT = "dependent_placement"


class ParameterType(StrEnum):
    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ENUM = "enum"


class UniformSampler(FrozenStrictModel):
    type: Literal["uniform"] = "uniform"


class IntegerUniformSampler(FrozenStrictModel):
    type: Literal["integer_uniform"] = "integer_uniform"


class TriangularSampler(FrozenStrictModel):
    type: Literal["triangular"] = "triangular"
    mode: Number


class CategoricalSampler(FrozenStrictModel):
    type: Literal["categorical"] = "categorical"


RangeSampler = Annotated[
    UniformSampler | IntegerUniformSampler | TriangularSampler,
    Field(discriminator="type"),
]


class FixedParameter(FrozenStrictModel):
    kind: Literal["fixed"] = "fixed"
    type: ParameterType
    value: bool | StrictInt | FiniteFloat | StrictStr


class RangeParameter(FrozenStrictModel):
    kind: Literal["range"] = "range"
    type: Literal[ParameterType.FLOAT, ParameterType.INTEGER]
    min: Number
    max: Number
    sampler: RangeSampler

    @model_validator(mode="after")
    def validate_range(self) -> "RangeParameter":
        if self.min > self.max:
            raise ValueError("min must be <= max")
        if isinstance(self.sampler, TriangularSampler) and not self.min <= self.sampler.mode <= self.max:
            raise ValueError("triangular mode must lie inside the parameter range")
        if self.type is ParameterType.INTEGER:
            if not isinstance(self.min, int) or not isinstance(self.max, int):
                raise ValueError("integer ranges require integer min/max")
            if isinstance(self.sampler, UniformSampler):
                raise ValueError("integer ranges must use integer_uniform or a compatible integer sampler")
        return self


class ChoiceParameter(FrozenStrictModel):
    kind: Literal["choice"] = "choice"
    type: Literal[ParameterType.ENUM] = ParameterType.ENUM
    values: tuple[StrictStr, ...] = Field(min_length=1)
    sampler: CategoricalSampler

    @model_validator(mode="after")
    def validate_unique_values(self) -> "ChoiceParameter":
        if len(set(self.values)) != len(self.values):
            raise ValueError("choice values must be unique")
        return self


ResolvedParameter = Annotated[
    FixedParameter | RangeParameter | ChoiceParameter,
    Field(discriminator="kind"),
]


class FeatureMetadata(FrozenStrictModel):
    label: StrictStr | None = None
    tags: tuple[StrictStr, ...] = ()
    source_preset: Annotated[StrictStr, Field(min_length=1)]


class GeometryLayoutRecipe(FrozenStrictModel):
    mode: Literal["geometry"] = "geometry"
    shape: GeometryShape
    parameters: dict[StrictStr, ResolvedParameter] = Field(default_factory=dict)


class ReservationLayoutRecipe(FrozenStrictModel):
    mode: Literal["reservation"] = "reservation"
    final_shape: Literal[GeometryShape.POINT] = GeometryShape.POINT


LayoutRecipe = Annotated[
    GeometryLayoutRecipe | ReservationLayoutRecipe,
    Field(discriminator="mode"),
]


class SiteRequirement(FrozenStrictModel):
    metric: Annotated[StrictStr, Field(min_length=1)]
    evaluator: Annotated[StrictStr, Field(min_length=1)]
    value: Number


class SitePreference(FrozenStrictModel):
    metric: Annotated[StrictStr, Field(min_length=1)]
    evaluator: Annotated[StrictStr, Field(min_length=1)]
    weight: Annotated[StrictFloat, Field(gt=0.0, le=1.0, allow_inf_nan=False)] = 1.0
    min: Number | None = None
    max: Number | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> "SitePreference":
        if (self.min is None) != (self.max is None):
            raise ValueError("preference min/max must be provided together")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("preference min must be <= max")
        if self.evaluator == "preferred_range" and self.min is None:
            raise ValueError("preferred_range requires min/max")
        return self


class SiteProfile(FrozenStrictModel):
    footprint_radius_km: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)] = 0.0
    requirements: tuple[SiteRequirement, ...] = ()
    preferences: tuple[SitePreference, ...] = ()


class EffectRecipe(FrozenStrictModel):
    stage: EffectStage
    operator: Annotated[StrictStr, Field(min_length=1)]
    parameters: dict[StrictStr, ResolvedParameter] = Field(default_factory=dict)
    site_profile: SiteProfile | None = None

    @model_validator(mode="after")
    def validate_stage_specific_fields(self) -> "EffectRecipe":
        if self.stage is EffectStage.DEPENDENT_PLACEMENT and self.site_profile is None:
            raise ValueError("dependent_placement effect requires site_profile")
        if self.stage is not EffectStage.DEPENDENT_PLACEMENT and self.site_profile is not None:
            raise ValueError("site_profile is only valid for dependent_placement effects")
        return self


class ResolvedFeature(FrozenStrictModel):
    id: Annotated[StrictStr, Field(min_length=1)]
    metadata: FeatureMetadata
    family: FeatureFamily
    layout: LayoutRecipe
    effect: EffectRecipe

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "ResolvedFeature":
        if isinstance(self.layout, ReservationLayoutRecipe):
            if self.family is not FeatureFamily.POI:
                raise ValueError("reservation layout is only supported for poi features in Core 0.1")
            if self.effect.stage is not EffectStage.DEPENDENT_PLACEMENT:
                raise ValueError("reservation layout requires dependent_placement effect")
        return self


class CompiledFeatureRef(FrozenStrictModel):
    type: Literal["feature"] = "feature"
    feature_id: Annotated[StrictStr, Field(min_length=1)]
    part: FeaturePart = FeaturePart.WHOLE


class CompiledPoint(FrozenStrictModel):
    type: Literal["point"] = "point"
    x_km: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]
    y_km: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]


class CompiledRectangle(FrozenStrictModel):
    type: Literal["rectangle"] = "rectangle"
    min_x_km: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]
    max_x_km: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]
    min_y_km: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]
    max_y_km: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]

    @model_validator(mode="after")
    def validate_bounds(self) -> "CompiledRectangle":
        if self.min_x_km > self.max_x_km or self.min_y_km > self.max_y_km:
            raise ValueError("rectangle min bounds must be <= max bounds")
        return self


CompiledSpatialRef = Annotated[
    CompiledFeatureRef | CompiledPoint | CompiledRectangle,
    Field(discriminator="type"),
]


class CompiledEvaluator(FrozenStrictModel):
    type: Annotated[StrictStr, Field(min_length=1)]
    subject: CompiledSpatialRef
    target: CompiledSpatialRef


class CompiledPredicate(FrozenStrictModel):
    type: Annotated[StrictStr, Field(min_length=1)]
    value: Number


class CompiledScoring(FrozenStrictModel):
    type: Annotated[StrictStr, Field(min_length=1)]
    ideal: Number | None = None
    worst: Number | None = None

    @model_validator(mode="after")
    def validate_pair(self) -> "CompiledScoring":
        if (self.ideal is None) != (self.worst is None):
            raise ValueError("scoring ideal/worst must be provided together")
        return self


class CompiledConstraint(FrozenStrictModel):
    id: Annotated[StrictStr, Field(min_length=1)]
    strength: ConstraintStrength
    evaluator: CompiledEvaluator
    predicate: CompiledPredicate | None = None
    scoring: CompiledScoring | None = None
    weight: Annotated[StrictFloat, Field(gt=0.0, le=1.0, allow_inf_nan=False)] | None = None
    unit: StrictStr | None = None
    source_relation: Relation | None = None

    @model_validator(mode="before")
    @classmethod
    def default_soft_weight(cls, data: object) -> object:
        if isinstance(data, dict) and data.get("strength") == ConstraintStrength.SOFT and "weight" not in data:
            normalized = dict(data)
            normalized["weight"] = 1.0
            return normalized
        return data

    @model_validator(mode="after")
    def validate_strength_mode(self) -> "CompiledConstraint":
        if self.strength is ConstraintStrength.HARD:
            if self.predicate is None or self.scoring is not None or self.weight is not None:
                raise ValueError("hard compiled constraint requires predicate and forbids scoring/weight")
        else:
            if self.scoring is None or self.predicate is not None:
                raise ValueError("soft compiled constraint requires scoring and forbids predicate")
        return self


class PlanSource(FrozenStrictModel):
    spec_id: Annotated[StrictStr, Field(min_length=1)]
    spec_schema_version: Literal["0.1"]
    spec_fingerprint: Annotated[StrictStr, Field(min_length=1)]
    generator_version: Annotated[StrictStr, Field(min_length=1)]


class PlanDomain(FrozenStrictModel):
    width_km: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    height_km: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]


class PlanGrid(FrozenStrictModel):
    cell_size_km: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    rows: Annotated[StrictInt, Field(gt=0)]
    columns: Annotated[StrictInt, Field(gt=0)]


class PlanHydrology(FrozenStrictModel):
    stream_threshold_km2: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    lake_min_area_km2: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    lake_min_depth_m: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    river_depth_at_threshold_m: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    river_depth_exponent: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]


class GenerationPlan(FrozenStrictModel):
    plan_version: Literal["0.1"]
    source: PlanSource
    seed: StrictInt
    domain: PlanDomain
    grid: PlanGrid
    hydrology: PlanHydrology
    features: tuple[ResolvedFeature, ...] = ()
    constraints: tuple[CompiledConstraint, ...] = ()

    @model_validator(mode="after")
    def validate_plan(self) -> "GenerationPlan":
        if self.grid.columns * self.grid.cell_size_km != self.domain.width_km:
            raise ValueError("grid columns must exactly match domain width")
        if self.grid.rows * self.grid.cell_size_km != self.domain.height_km:
            raise ValueError("grid rows must exactly match domain height")
        feature_ids = [feature.id for feature in self.features]
        if len(feature_ids) != len(set(feature_ids)):
            raise ValueError("resolved feature ids must be unique")
        constraint_ids = [constraint.id for constraint in self.constraints]
        if len(constraint_ids) != len(set(constraint_ids)):
            raise ValueError("compiled constraint ids must be unique")
        return self
