from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from ..contracts.geometry import AreaGeometry, BandGeometry
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
from .ridge import prepare_band, ridge_contribution_at
from .shaping import FlattenSpec, compose_nonoverlapping_flatten, flatten_conflicts
from .state import TerrainState


class TerrainCapabilityError(RuntimeError):
    """A valid plan construct is outside implemented terrain Core 0.1 capability."""


@dataclass(frozen=True, slots=True)
class _TerrainBuildResult:
    state: TerrainState
    applied_feature_ids: tuple[str, ...]
    shaping_conflicts: tuple[tuple[str, str], ...]


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


def _sample_float_parameter(
    plan_feature,
    parameter_name: str,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> float:
    recipe = plan_feature.effect.parameters[parameter_name]
    if recipe.type is not ParameterType.FLOAT:
        raise TerrainCapabilityError(
            f"terrain parameter {parameter_name!r} for feature {plan_feature.id!r} "
            "must be a float resolved parameter"
        )

    stream = rng_factory.stream(
        _parameter_stream_key(attempt_index, plan_feature.id, parameter_name)
    )
    try:
        sampled = sample_resolved_parameter(recipe, stream)
    except SamplingCapabilityError as exc:
        raise TerrainCapabilityError(
            f"terrain parameter {parameter_name!r} recipe is unsupported for feature "
            f"{plan_feature.id!r}"
        ) from exc

    if isinstance(sampled, bool) or not isinstance(sampled, (int, float)):
        raise TerrainCapabilityError(
            f"terrain parameter {parameter_name!r} must resolve to a numeric value"
        )
    value = float(sampled)
    if not isfinite(value):
        raise TerrainCapabilityError(
            f"terrain parameter {parameter_name!r} must resolve to a finite value"
        )
    return value


def _raise_contribution(
    plan: GenerationPlan,
    feature,
    geometry,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> np.ndarray:
    if not isinstance(geometry, AreaGeometry):
        raise TerrainCapabilityError(
            f"terrain raise feature {feature.id!r} requires AreaGeometry"
        )
    if set(feature.effect.parameters) != {"height_m"}:
        raise TerrainCapabilityError(
            f"terrain raise feature {feature.id!r} requires exactly effect parameter "
            "['height_m']"
        )

    height_m = _sample_float_parameter(
        feature,
        "height_m",
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    if height_m <= 0.0:
        raise TerrainCapabilityError("terrain raise height_m must resolve to finite value > 0")

    contribution = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.float64)
    contribution[rasterize_area_cell_centers(plan, geometry)] = height_m
    return contribution


def _depress_contribution(
    plan: GenerationPlan,
    feature,
    geometry,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> np.ndarray:
    if not isinstance(geometry, AreaGeometry):
        raise TerrainCapabilityError(
            f"terrain depress feature {feature.id!r} requires AreaGeometry"
        )
    if set(feature.effect.parameters) != {"depth_m"}:
        raise TerrainCapabilityError(
            f"terrain depress feature {feature.id!r} requires exactly effect parameter "
            "['depth_m']"
        )

    depth_m = _sample_float_parameter(
        feature,
        "depth_m",
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    if depth_m <= 0.0:
        raise TerrainCapabilityError("terrain depress depth_m must resolve to finite value > 0")

    contribution = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.float64)
    contribution[rasterize_area_cell_centers(plan, geometry)] = -depth_m
    return contribution


def _ridge_contribution(
    plan: GenerationPlan,
    feature,
    geometry,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> np.ndarray:
    if not isinstance(geometry, BandGeometry):
        raise TerrainCapabilityError(
            f"unsupported geometry for terrain ridge feature {feature.id!r}; requires BandGeometry"
        )

    expected_parameters = {
        "height_m",
        "profile_power",
        "roughness",
        "roughness_scale_km",
    }
    if set(feature.effect.parameters) != expected_parameters:
        raise TerrainCapabilityError(
            f"terrain ridge feature {feature.id!r} requires exactly effect parameters "
            f"{sorted(expected_parameters)!r}"
        )

    height_m = _sample_float_parameter(
        feature, "height_m", attempt_index=attempt_index, rng_factory=rng_factory
    )
    profile_power = _sample_float_parameter(
        feature, "profile_power", attempt_index=attempt_index, rng_factory=rng_factory
    )
    roughness = _sample_float_parameter(
        feature, "roughness", attempt_index=attempt_index, rng_factory=rng_factory
    )
    roughness_scale_km = _sample_float_parameter(
        feature,
        "roughness_scale_km",
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )

    if height_m <= 0.0:
        raise TerrainCapabilityError("terrain ridge height_m must be > 0")
    if profile_power <= 0.0:
        raise TerrainCapabilityError("terrain ridge profile_power must be > 0")
    if not 0.0 <= roughness <= 1.0:
        raise TerrainCapabilityError("terrain ridge roughness must be in [0,1]")
    if roughness_scale_km <= 0.0:
        raise TerrainCapabilityError("terrain ridge roughness_scale_km must be > 0")

    try:
        prepared = prepare_band(geometry)
    except ValueError as exc:
        raise TerrainCapabilityError(
            f"terrain ridge band geometry is invalid for feature {feature.id!r}"
        ) from exc

    adapter = GridAdapter.from_plan(plan)
    contribution = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.float64)
    for row in range(plan.grid.rows):
        for column in range(plan.grid.columns):
            point = adapter.cell_center(row, column)
            try:
                contribution[row, column] = ridge_contribution_at(
                    prepared,
                    x_km=point.x_km,
                    y_km=point.y_km,
                    height_m=height_m,
                    profile_power=profile_power,
                    roughness=roughness,
                    roughness_scale_km=roughness_scale_km,
                    feature_id=feature.id,
                    attempt_index=attempt_index,
                    rng_factory=rng_factory,
                )
            except ValueError as exc:
                raise TerrainCapabilityError(
                    f"terrain ridge evaluation failed for feature {feature.id!r}"
                ) from exc
    return contribution


def _flatten_spec(
    feature,
    geometry,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> FlattenSpec:
    if not isinstance(geometry, AreaGeometry):
        raise TerrainCapabilityError(
            f"terrain flatten feature {feature.id!r} requires AreaGeometry"
        )
    expected_parameters = {"target_elevation_m", "blend_width_km"}
    if set(feature.effect.parameters) != expected_parameters:
        raise TerrainCapabilityError(
            f"terrain flatten feature {feature.id!r} requires exactly effect parameters "
            f"{sorted(expected_parameters)!r}"
        )

    target_elevation_m = _sample_float_parameter(
        feature,
        "target_elevation_m",
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    blend_width_km = _sample_float_parameter(
        feature,
        "blend_width_km",
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    if blend_width_km < 0.0:
        raise TerrainCapabilityError("terrain flatten blend_width_km must be >= 0")

    return FlattenSpec(
        feature_id=feature.id,
        geometry=geometry,
        target_elevation_m=target_elevation_m,
        blend_width_km=blend_width_km,
    )


def _build_terrain(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> _TerrainBuildResult:
    structural = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.float64)
    flatten_specs: list[FlattenSpec] = []
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

        try:
            geometry = layout.geometry_realizations[feature.id]
        except KeyError as exc:
            raise TerrainCapabilityError(
                f"terrain feature {feature.id!r} has no materialized layout geometry"
            ) from exc

        operator = feature.effect.operator
        if operator == "raise":
            structural += _raise_contribution(
                plan,
                feature,
                geometry,
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        elif operator == "depress":
            structural += _depress_contribution(
                plan,
                feature,
                geometry,
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        elif operator == "ridge":
            structural += _ridge_contribution(
                plan,
                feature,
                geometry,
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        elif operator == "flatten":
            flatten_specs.append(
                _flatten_spec(
                    feature,
                    geometry,
                    attempt_index=attempt_index,
                    rng_factory=rng_factory,
                )
            )
        else:
            raise TerrainCapabilityError(
                f"terrain operator {operator!r} is unsupported"
            )
        applied.append(feature.id)

    structural_snapshot = np.array(structural, dtype=np.float64, copy=True)
    structural_snapshot.setflags(write=False)
    specs = tuple(flatten_specs)
    conflicts = flatten_conflicts(specs)
    shaped = compose_nonoverlapping_flatten(plan, structural_snapshot, specs)

    elevation = shaped.astype(np.float32, copy=True)
    return _TerrainBuildResult(
        state=TerrainState(elevation_m=elevation),
        applied_feature_ids=tuple(applied),
        shaping_conflicts=conflicts,
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
    shaping_conflicts: tuple[tuple[str, str], ...] = (),
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
    shaping_compatible = not shaping_conflicts

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
        EngineInvariantResult(
            id="terrain-shaping-regions-compatible",
            passed=shaping_compatible,
            measured={"conflict_count": len(shaping_conflicts)},
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
        shaping_conflicts=build.shaping_conflicts,
    )
