from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import Field, StrictFloat, StrictInt, StrictStr, model_validator

from .common import (
    ConstraintStrength,
    DomainCompass,
    FeaturePart,
    FrozenStrictModel,
    NumericRangeOverride,
    ParameterOverride,
    Relation,
    StrictModel,
)


class DomainSize(FrozenStrictModel):
    width_km: Annotated[StrictFloat, Field(gt=0.0)]
    height_km: Annotated[StrictFloat, Field(gt=0.0)]


class DomainConfig(FrozenStrictModel):
    size: DomainSize


class SimulationConfig(FrozenStrictModel):
    cell_size_km: Annotated[StrictFloat, Field(gt=0.0)]


class HydrologySpec(FrozenStrictModel):
    stream_threshold_km2: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    lake_min_area_km2: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    lake_min_depth_m: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]


class FeatureSpec(FrozenStrictModel):
    id: Annotated[StrictStr, Field(min_length=1)]
    preset: Annotated[StrictStr, Field(min_length=1)]
    label: StrictStr | None = None
    parameters: dict[str, ParameterOverride] = Field(default_factory=dict)
    tags: tuple[StrictStr, ...] = ()


class FeatureSelector(FrozenStrictModel):
    feature: Annotated[StrictStr, Field(min_length=1)]
    part: FeaturePart = FeaturePart.WHOLE


class DomainAnchorSelector(FrozenStrictModel):
    domain_anchor: DomainCompass


class DomainRegionSelector(FrozenStrictModel):
    domain_region: DomainCompass


class KmPoint(FrozenStrictModel):
    x_km: Annotated[StrictFloat, Field(ge=0.0)]
    y_km: Annotated[StrictFloat, Field(ge=0.0)]


class NormalizedPointCoordinates(FrozenStrictModel):
    x: Annotated[StrictFloat, Field(ge=0.0, le=1.0)]
    y: Annotated[StrictFloat, Field(ge=0.0, le=1.0)]


class NormalizedPoint(FrozenStrictModel):
    normalized: NormalizedPointCoordinates


class PointSelector(FrozenStrictModel):
    point: KmPoint | NormalizedPoint


class KmRegion(FrozenStrictModel):
    x_km: NumericRangeOverride
    y_km: NumericRangeOverride

    @model_validator(mode="after")
    def validate_non_negative(self) -> "KmRegion":
        if self.x_km.min < 0 or self.y_km.min < 0:
            raise ValueError("km region coordinates must be non-negative")
        return self


class NormalizedAxisRange(FrozenStrictModel):
    min: Annotated[StrictFloat, Field(ge=0.0, le=1.0)]
    max: Annotated[StrictFloat, Field(ge=0.0, le=1.0)]

    @model_validator(mode="after")
    def validate_order(self) -> "NormalizedAxisRange":
        if self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class NormalizedRegionCoordinates(FrozenStrictModel):
    x: NormalizedAxisRange
    y: NormalizedAxisRange


class NormalizedRegion(FrozenStrictModel):
    normalized: NormalizedRegionCoordinates


class RegionSelector(FrozenStrictModel):
    region: KmRegion | NormalizedRegion


SpatialSelector = FeatureSelector | DomainAnchorSelector | DomainRegionSelector | PointSelector | RegionSelector


class ConstraintSpec(FrozenStrictModel):
    @model_validator(mode="before")
    @classmethod
    def default_soft_weight(cls, data: object) -> object:
        if isinstance(data, dict) and data.get("strength") == ConstraintStrength.SOFT and "weight" not in data:
            normalized = dict(data)
            normalized["weight"] = 1.0
            return normalized
        return data

    id: Annotated[StrictStr, Field(min_length=1)]
    relation: Relation
    subject: SpatialSelector
    target: SpatialSelector
    strength: ConstraintStrength
    parameters: dict[StrictStr, StrictFloat] = Field(default_factory=dict)
    weight: Annotated[StrictFloat, Field(gt=0.0, le=1.0)] | None = None

    @model_validator(mode="after")
    def validate_strength_and_parameters(self) -> "ConstraintSpec":
        if self.strength is ConstraintStrength.HARD and self.weight is not None:
            raise ValueError("weight is only allowed for soft constraints")

        params = self.parameters
        expected: dict[Relation, set[str]] = {
            Relation.NEAR: {"max_distance_km"},
            Relation.FAR_FROM: {"min_distance_km"},
            Relation.INSIDE: set(),
            Relation.OUTSIDE: set(),
            Relation.CROSSES: {"minimum_crossing_length_km"},
            Relation.OVERLAPS: {"minimum_fraction"},
            Relation.ADJACENT: {"max_gap_km"},
        }
        required: dict[Relation, set[str]] = {
            Relation.NEAR: {"max_distance_km"},
            Relation.FAR_FROM: {"min_distance_km"},
            Relation.OVERLAPS: {"minimum_fraction"},
            Relation.ADJACENT: {"max_gap_km"},
        }

        unknown = set(params) - expected[self.relation]
        missing = required.get(self.relation, set()) - set(params)
        if unknown:
            raise ValueError(f"unsupported parameters for {self.relation}: {sorted(unknown)}")
        if missing:
            raise ValueError(f"missing parameters for {self.relation}: {sorted(missing)}")
        if any(value < 0 for key, value in params.items() if key != "minimum_fraction"):
            raise ValueError("distance/crossing parameters must be non-negative")
        if "minimum_fraction" in params and not 0.0 <= params["minimum_fraction"] <= 1.0:
            raise ValueError("minimum_fraction must be in [0, 1]")
        return self


class DomainSpec(StrictModel):
    schema_version: Annotated[StrictStr, Field(pattern=r"^0\.1$")]
    id: Annotated[StrictStr, Field(min_length=1)]
    seed: StrictInt
    domain: DomainConfig
    simulation: SimulationConfig
    hydrology: HydrologySpec
    features: tuple[FeatureSpec, ...] = ()
    constraints: tuple[ConstraintSpec, ...] = ()
    label: StrictStr | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> "DomainSpec":
        self._validate_exact_grid_divisibility()
        self._validate_unique_ids()
        self._validate_literal_km_selectors()
        return self

    def _validate_exact_grid_divisibility(self) -> None:
        cell = Decimal(str(self.simulation.cell_size_km))
        for name, value in (
            ("width_km", self.domain.size.width_km),
            ("height_km", self.domain.size.height_km),
        ):
            ratio = Decimal(str(value)) / cell
            if ratio != ratio.to_integral_value():
                raise ValueError(f"{name} must be exactly divisible by cell_size_km")

    def _validate_unique_ids(self) -> None:
        feature_ids = [feature.id for feature in self.features]
        if len(feature_ids) != len(set(feature_ids)):
            raise ValueError("feature ids must be unique")
        constraint_ids = [constraint.id for constraint in self.constraints]
        if len(constraint_ids) != len(set(constraint_ids)):
            raise ValueError("constraint ids must be unique")

    def _validate_literal_km_selectors(self) -> None:
        width = self.domain.size.width_km
        height = self.domain.size.height_km

        for constraint in self.constraints:
            for selector in (constraint.subject, constraint.target):
                if isinstance(selector, PointSelector) and isinstance(selector.point, KmPoint):
                    if selector.point.x_km > width or selector.point.y_km > height:
                        raise ValueError("literal km point must lie inside the domain")
                if isinstance(selector, RegionSelector) and isinstance(selector.region, KmRegion):
                    if selector.region.x_km.max > width or selector.region.y_km.max > height:
                        raise ValueError("literal km region must lie inside the domain")
