from __future__ import annotations

from math import sqrt
from typing import TypeAlias

from ..contracts.plan import (
    CategoricalSampler,
    ChoiceParameter,
    FixedParameter,
    IntegerUniformSampler,
    ParameterType,
    RangeParameter,
    ResolvedParameter,
    TriangularSampler,
    UniformSampler,
)
from .rng import Xoshiro256StarStar

SampledParameter: TypeAlias = bool | int | float | str


class SamplingCapabilityError(RuntimeError):
    """The runtime sampler does not implement a structurally valid recipe combination."""


def triangular_sample(
    stream: Xoshiro256StarStar,
    low: float,
    high: float,
    mode: float,
) -> float:
    """Sample triangular(low, high, mode) with the RNG-v1 inverse-CDF mapping."""
    if low > high:
        raise ValueError("triangular low must be <= high")
    if not low <= mode <= high:
        raise ValueError("triangular mode must lie inside [low, high]")
    if low == high:
        return low

    u = stream.uniform01()
    span = high - low
    c = (mode - low) / span
    if u < c:
        return low + sqrt(u * span * (mode - low))
    return high - sqrt((1.0 - u) * span * (high - mode))


def sample_resolved_parameter(
    recipe: ResolvedParameter,
    stream: Xoshiro256StarStar,
) -> SampledParameter:
    """Materialize one resolved parameter using only its dedicated RNG stream."""
    if isinstance(recipe, FixedParameter):
        return recipe.value

    if isinstance(recipe, ChoiceParameter):
        if not isinstance(recipe.sampler, CategoricalSampler):
            raise SamplingCapabilityError("choice parameter requires categorical sampler")
        return stream.choice(recipe.values)

    if isinstance(recipe, RangeParameter):
        if recipe.min == recipe.max:
            return int(recipe.min) if recipe.type is ParameterType.INTEGER else float(recipe.min)

        if isinstance(recipe.sampler, UniformSampler):
            if recipe.type is not ParameterType.FLOAT:
                raise SamplingCapabilityError("uniform range sampler requires float parameter")
            return stream.uniform(float(recipe.min), float(recipe.max))

        if isinstance(recipe.sampler, IntegerUniformSampler):
            if recipe.type is not ParameterType.INTEGER:
                raise SamplingCapabilityError("integer_uniform sampler requires integer parameter")
            return stream.integer_uniform(int(recipe.min), int(recipe.max))

        if isinstance(recipe.sampler, TriangularSampler):
            if recipe.type is not ParameterType.FLOAT:
                raise SamplingCapabilityError("triangular sampler v1 requires float parameter")
            return triangular_sample(
                stream,
                float(recipe.min),
                float(recipe.max),
                float(recipe.sampler.mode),
            )

    raise SamplingCapabilityError(f"unsupported resolved parameter recipe: {recipe!r}")
