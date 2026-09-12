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

        expected_stage = {
            FeatureFamily.TERRAIN: EffectStage.TERRAIN,
            FeatureFamily.SURFACE: EffectStage.SURFACE,
            FeatureFamily.POI: EffectStage.DEPENDENT_PLACEMENT,
        }[self.family]
        if self.effect.stage is not expected_stage:
            raise ValueError(
                f"preset family {self.family.value!r} requires effect stage "
                f"{expected_stage.value!r} in Core 0.1"
            )
        if isinstance(self.layout, ReservationLayoutRecipe) and self.family is not FeatureFamily.POI:
            raise ValueError("reservation layout is only supported for poi presets in Core 0.1")
        return self
