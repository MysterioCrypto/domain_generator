from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StrictInt, StrictStr, model_validator

from .common import FrozenStrictModel
from .geometry import Geometry, RegionSet


class SourcePlanRef(FrozenStrictModel):
    fingerprint: Annotated[StrictStr, Field(min_length=1)]


class PlacementReservation(FrozenStrictModel):
    final_shape: Literal["point"] = "point"
    source_constraints: tuple[StrictStr, ...] = ()
    allowed_region: RegionSet


class LayoutCandidate(FrozenStrictModel):
    layout_version: Literal["0.1"]
    source_plan: SourcePlanRef
    attempt_index: Annotated[StrictInt, Field(ge=0)]
    geometry_realizations: dict[StrictStr, Geometry] = Field(default_factory=dict)
    placement_reservations: dict[StrictStr, PlacementReservation] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_feature_partition(self) -> "LayoutCandidate":
        overlap = set(self.geometry_realizations) & set(self.placement_reservations)
        if overlap:
            raise ValueError(f"features cannot have both geometry and reservation: {sorted(overlap)}")
        if any(not feature_id for feature_id in self.geometry_realizations):
            raise ValueError("geometry realization ids must be non-empty")
        if any(not feature_id for feature_id in self.placement_reservations):
            raise ValueError("placement reservation ids must be non-empty")
        return self
