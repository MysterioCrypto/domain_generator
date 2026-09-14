from __future__ import annotations

from typing import Annotated

from pydantic import Field, StrictFloat, StrictStr, model_validator

from .common import FrozenStrictModel


class PlanTerrainNoiseLayer(FrozenStrictModel):
    id: Annotated[StrictStr, Field(min_length=1)]
    scale_km: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    amplitude_m: Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]


class PlanTerrain(FrozenStrictModel):
    base_elevation_m: Annotated[StrictFloat, Field(allow_inf_nan=False)]
    noise_layers: tuple[PlanTerrainNoiseLayer, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_layers(self) -> "PlanTerrain":
        ids = [layer.id for layer in self.noise_layers]
        if len(ids) != len(set(ids)):
            raise ValueError("terrain noise layer ids must be unique")
        if not any(layer.amplitude_m > 0.0 for layer in self.noise_layers):
            raise ValueError("terrain requires at least one non-zero noise layer")
        return self


__all__ = ["PlanTerrain", "PlanTerrainNoiseLayer"]
