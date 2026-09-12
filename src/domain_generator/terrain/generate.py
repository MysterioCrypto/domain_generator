from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from ..contracts.geometry import AreaGeometry
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import EffectStage, FeatureFamily, GenerationPlan, ParameterType
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from ..grid import GridAdapter
from ..layout.area import point_in_area
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngFactory, RngKey, RngStage
from ..pipeline.sampling import SamplingCapabilityError, sample_resolved_parameter
from .state import TerrainState


class TerrainCapabilityError(RuntimeError):
    """A valid plan construct is outside terrain area-raise v0.1 capability."""


@dataclass(frozen=True, slots=True)
class _TerrainBuildResult:
    state: TerrainState
    applied_feature_ids: tuple[str, ...]


def _parameter_stream_key(
    attempt_index: int,
    feature_id: str,
    parameter_name: str,
) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.TERRAIN,
        scope=("feature", feature_id, "parameter", parameter_name),
        purpose="sample",
    )


def rasterize_area_cell_centers(
    plan: GenerationPlan,
    area: AreaGeometry,
) -> np.ndarray:
    """Rasterize an area using the canonical world-coordinate cell-center rule."""
    adapter = GridAdapter.from_plan(plan)
    mask = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.bool_)
    for row in range(plan.grid.rows):
        for column in range(plan.grid.columns):
            if point_in_area(adapter.cell_center(row, column), area):
                mask[row, column] = True
    return mask


def _sample_raise_height_m(
    plan_feature,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> float:
    parameters = plan_feature.effect.parameters
    if set(parameters) != {"height_m"}:
        raise TerrainCapabilityError(
            f"terrain raise feature {plan_feature.id!r} requires exactly effect parameter "
            "['height_m']"
        )

    recipe = parameters["height_m"]
    if recipe.type is not ParameterType.FLOAT:
        raise TerrainCapabilityError("terrain raise height_m must be a float resolved parameter")

    stream = rng_factory.stream(
        _parameter_stream_key(attempt_index, plan_feature.id, "height_m")
    )
    try:
        sampled = sample_resolved_parameter(recipe, stream)
    except SamplingCapabilityError as exc:
        raise TerrainCapabilityError(
            f"terrain raise height_m recipe is unsupported for feature {plan_feature.id!r}"
        ) from exc

    if isinstance(sampled, bool) or not isinstance(sampled, (int, float)):
        raise TerrainCapabilityError("terrain raise height_m must resolve to a numeric value")
    value = float(sampled)
    if not isfinite(value) or value <= 0.0:
        raise TerrainCapabilityError("terrain raise height_m must resolve to finite value > 0")
    return value


def _build_terrain(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> _TerrainBuildResult:
    structural = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.float64)
    applied: list[str] = []

    terrain_features = sorted(
        (feature for feature in plan.features if feature.family is FeatureFamily.TERRAIN),
        key=lambda feature: feature.id,
    )

    for feature in terrain_features:
        if feature.effect.stage is not EffectStage.TERRAIN:
            raise TerrainCapabilityError(
                f"terrain feature {feature.id!r} must use terrain effect stage"
            )
        if feature.effect.operator != "raise":
            raise TerrainCapabilityError(
                f"terrain operator {feature.effect.operator!r} is unsupported in area-raise v0.1"
            )

        try:
            geometry = layout.geometry_realizations[feature.id]
        except KeyError as exc:
            raise TerrainCapabilityError(
                f"terrain feature {feature.id!r} has no materialized layout geometry"
            ) from exc
        if not isinstance(geometry, AreaGeometry):
            raise TerrainCapabilityError(
                f"terrain raise feature {feature.id!r} requires AreaGeometry"
            )

        height_m = _sample_raise_height_m(
            feature,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )
        mask = rasterize_area_cell_centers(plan, geometry)
        contribution = np.zeros_like(structural)
        contribution[mask] = height_m
        structural += contribution
        applied.append(feature.id)

    elevation = structural.astype(np.float32, copy=True)
    return _TerrainBuildResult(
        state=TerrainState(elevation_m=elevation),
        applied_feature_ids=tuple(applied),
    )


def generate_terrain(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> TerrainState:
    return _build_terrain(
        plan,
        layout,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    ).state


def _expected_terrain_feature_ids(plan: GenerationPlan) -> tuple[str, ...]:
    return tuple(
        sorted(feature.id for feature in plan.features if feature.family is FeatureFamily.TERRAIN)
    )


def validate_terrain(
    plan: GenerationPlan,
    layout: LayoutCandidate | None,
    terrain: TerrainState | None,
    *,
    attempt_index: int,
    applied_feature_ids: tuple[str, ...],
) -> ValidationResult:
    expected_shape = (plan.grid.rows, plan.grid.columns)
    expected_features = _expected_terrain_feature_ids(plan)
    applied = applied_feature_ids

    layout_exists = layout is not None
    layout_attempt_matches = layout_exists and layout.attempt_index == attempt_index
    terrain_exists = terrain is not None

    shape_matches = False
    dtype_matches = False
    finite = False
    if terrain_exists:
        elevation = terrain.elevation_m
        shape_matches = isinstance(elevation, np.ndarray) and elevation.shape == expected_shape
        dtype_matches = isinstance(elevation, np.ndarray) and elevation.dtype == np.dtype(np.float32)
        finite = isinstance(elevation, np.ndarray) and bool(np.isfinite(elevation).all())

    applied_complete = (
        tuple(sorted(applied)) == expected_features
        and len(applied) == len(set(applied))
    )

    results = (
        EngineInvariantResult(
            id="terrain-upstream-layout-exists",
            passed=layout_exists,
        ),
        EngineInvariantResult(
            id="terrain-layout-attempt-index-matches",
            passed=layout_attempt_matches,
        ),
        EngineInvariantResult(
            id="terrain-state-exists",
            passed=terrain_exists,
        ),
        EngineInvariantResult(
            id="terrain-elevation-shape-matches-grid",
            passed=shape_matches,
            measured={
                "expected_rows": plan.grid.rows,
                "expected_columns": plan.grid.columns,
            },
        ),
        EngineInvariantResult(
            id="terrain-elevation-dtype-float32",
            passed=dtype_matches,
        ),
        EngineInvariantResult(
            id="terrain-elevation-finite",
            passed=finite,
        ),
        EngineInvariantResult(
            id="terrain-feature-application-complete",
            passed=applied_complete,
            measured={
                "expected_feature_count": len(expected_features),
                "applied_feature_count": len(applied),
            },
        ),
    )
    passed = all(result.passed for result in results)

    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.TERRAIN,
        engine_invariants=EngineInvariantGroup(passed=passed, results=results),
        hard_constraints=HardConstraintGroup(passed=True, results=()),
        soft_constraints=SoftConstraintGroup(results=()),
        ranking=None,
    )


def terrain_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    if state.layout is None:
        return validate_terrain(
            context.plan,
            None,
            None,
            attempt_index=context.attempt_index,
            applied_feature_ids=(),
        )

    build = _build_terrain(
        context.plan,
        state.layout,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
    state.terrain = build.state
    return validate_terrain(
        context.plan,
        state.layout,
        state.terrain,
        attempt_index=context.attempt_index,
        applied_feature_ids=build.applied_feature_ids,
    )
