from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import FrozenStrictModel, NormalizedValue, NonNegativeFloat, PositiveFloat


class WorldPoint(FrozenStrictModel):
    x_km: NonNegativeFloat
    y_km: NonNegativeFloat


class PointGeometry(WorldPoint):
    type: Literal["point"] = "point"


class CorridorGeometry(FrozenStrictModel):
    type: Literal["corridor"] = "corridor"
    centerline: tuple[WorldPoint, ...] = Field(min_length=2)


class WidthSample(FrozenStrictModel):
    t: NormalizedValue
    width_km: PositiveFloat


class BandGeometry(FrozenStrictModel):
    type: Literal["band"] = "band"
    centerline: tuple[WorldPoint, ...] = Field(min_length=2)
    width_profile: tuple[WidthSample, ...] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_width_profile(self) -> "BandGeometry":
        samples = self.width_profile
        if samples[0].t != 0.0 or samples[-1].t != 1.0:
            raise ValueError("width_profile must include t=0 and t=1 endpoints")
        if any(left.t >= right.t for left, right in zip(samples, samples[1:])):
            raise ValueError("width_profile t values must be strictly increasing")
        return self


class AreaGeometry(FrozenStrictModel):
    type: Literal["area"] = "area"
    boundary: tuple[WorldPoint, ...] = Field(min_length=3)

    @model_validator(mode="after")
    def validate_open_ring_encoding(self) -> "AreaGeometry":
        if self.boundary[0] == self.boundary[-1]:
            raise ValueError("area boundary must not repeat the first point as the last point")
        return self


Geometry = Annotated[
    PointGeometry | CorridorGeometry | BandGeometry | AreaGeometry,
    Field(discriminator="type"),
]


class RegionPolygon(FrozenStrictModel):
    outer: tuple[WorldPoint, ...] = Field(min_length=3)
    holes: tuple[tuple[WorldPoint, ...], ...] = ()

    @model_validator(mode="after")
    def validate_rings(self) -> "RegionPolygon":
        if self.outer[0] == self.outer[-1]:
            raise ValueError("outer ring must not repeat the first point as the last point")
        for hole in self.holes:
            if len(hole) < 3:
                raise ValueError("hole rings must contain at least three points")
            if hole[0] == hole[-1]:
                raise ValueError("hole rings must not repeat the first point as the last point")
        return self


class RegionSet(FrozenStrictModel):
    type: Literal["region_set"] = "region_set"
    polygons: tuple[RegionPolygon, ...] = ()
