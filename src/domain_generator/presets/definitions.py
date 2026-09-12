from __future__ import annotations

from typing import Annotated

from pydantic import Field, StrictStr, model_validator

from ..contracts.common import FrozenStrictModel
from ..contracts.plan import (
    EffectRecipe,
    EffectStage,
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
    def validate_definition(self) -> "PresetDefinition":
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

        if self.family is FeatureFamily.TERRAIN and self.effect.stage is not EffectStage.TERRAIN:
            raise ValueError("terrain preset requires terrain effect stage in Core 0.1")
        if self.family is FeatureFamily.SURFACE and self.effect.stage is not EffectStage.SURFACE:
            raise ValueError("surface preset requires surface effect stage in Core 0.1")

        if isinstance(self.layout, ReservationLayoutRecipe):
            if self.family is not FeatureFamily.POI:
                raise ValueError("reservation layout is only supported for poi presets in Core 0.1")
            if self.effect.stage is not EffectStage.DEPENDENT_PLACEMENT:
                raise ValueError("reservation layout requires dependent_placement effect stage")
        return self
