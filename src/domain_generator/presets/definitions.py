from __future__ import annotations

from typing import Annotated

from pydantic import Field, StrictStr, model_validator

from ..contracts.common import FrozenStrictModel
from ..contracts.plan import (
    EffectRecipe,
    FeatureFamily,
    GeometryLayoutRecipe,
    ReservationLayoutRecipe,
)


class PresetDefinition(FrozenStrictModel):
    """Typed declarative preset consumed by the compiler registry.

    Core 0.1 keeps loader concerns outside this model. A future YAML loader may
    construct the same value object without changing compiler behavior.
    """

    id: Annotated[StrictStr, Field(min_length=1)]
    family: FeatureFamily
    layout: GeometryLayoutRecipe | ReservationLayoutRecipe
    effect: EffectRecipe

    @model_validator(mode="after")
    def validate_parameter_ownership(self) -> "PresetDefinition":
        layout_parameters = (
            set(self.layout.parameters)
            if isinstance(self.layout, GeometryLayoutRecipe)
            else set()
        )
        effect_parameters = set(self.effect.parameters)
        overlap = layout_parameters & effect_parameters
        if overlap:
            raise ValueError(
                "preset parameter names must have exactly one owner; duplicated in "
                f"layout/effect: {sorted(overlap)}"
            )
        return self
