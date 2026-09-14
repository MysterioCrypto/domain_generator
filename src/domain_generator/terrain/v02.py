from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from ..contracts.geometry import AreaGeometry, BandGeometry
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import EffectStage, FeatureFamily, GenerationPlan
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from ..fields.noise import value_noise_2d
from ..grid import GridAdapter
from ..layout.area import distance_point_area_boundary, point_in_area
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngFactory, RngStage
from .base import TerrainBaseCapabilityError, synthesize_base_elevation
from .generate import (
    TerrainCapabilityError,
    _flatten_spec,
    _sample_float_parameter,
    generate_terrain as _generate_terrain_v01,
    terrain_stage as _terrain_stage_v01,
    validate_terrain as _validate_terrain_v01,
)
from .ridge import prepare_band, nearest_centerline_distance_and_t, width_at
from .shaping import FlattenSpec, compose_nonoverlapping_flatten, flatten_conflicts
from .state import TerrainState


@dataclass(frozen=True, slots=True)
class _TerrainBuildResult:
    state: TerrainState
    applied_feature_ids: tuple[str, ...]
    shaping_conflicts: tuple[tuple[str, str], ...]


def _smoothstep01(value: float) -> float:
    x = min(1.0, max(0.0, float(value)))
    return x * x * (3.0 - 2.0 * x)


def _area_blend_contribution(
    plan: GenerationPlan,
    feature,
    geometry,
    *,
    magnitude_m: float,
    blend_width_km: float,
) -> np.ndarray:
    if not isinstance(geometry, AreaGeometry):
        raise TerrainCapabilityError(
            f"terrain {feature.effect.operator} feature {feature.id!r} requires AreaGeometry"
        )
    if not isfinite(magnitude_m) or magnitude_m <= 0.0:
        raise TerrainCapabilityError("terrain Area magnitude must be finite and > 0")
    if not isfinite(blend_width_km) or blend_width_km <= 0.0:
        raise TerrainCapabilityError("terrain Area blend_width_km must be finite and > 0")

    adapter = GridAdapter.from_plan(plan)
    result = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.float64)
    for row in range(adapter.rows):
        for column in range(adapter.columns):
            point = adapter.cell_center(row, column)
            if not point_in_area(point, geometry):
                continue
            distance = distance_point_area_boundary(point, geometry)
            weight = _smoothstep01(distance / blend_width_km)
            result[row, column] = magnitude_m * weight
    return result


def _raise_contribution(
    plan: GenerationPlan,
    feature,
    geometry,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> np.ndarray:
    expected = {"height_m", "blend_width_km"}
    if set(feature.effect.parameters) != expected:
        raise TerrainCapabilityError(
            f"terrain raise feature {feature.id!r} requires exactly effect parameters {sorted(expected)!r}"
        )
    height_m = _sample_float_parameter(
        feature, "height_m", attempt_index=attempt_index, rng_factory=rng_factory
    )
    blend = _sample_float_parameter(
        feature, "blend_width_km", attempt_index=attempt_index, rng_factory=rng_factory
    )
    return _area_blend_contribution(
        plan,
        feature,
        geometry,
        magnitude_m=height_m,
        blend_width_km=blend,
    )


def _depress_contribution(
    plan: GenerationPlan,
    feature,
    geometry,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> np.ndarray:
    expected = {"depth_m", "blend_width_km"}
    if set(feature.effect.parameters) != expected:
        raise TerrainCapabilityError(
            f"terrain depress feature {feature.id!r} requires exactly effect parameters {sorted(expected)!r}"
        )
    depth_m = _sample_float_parameter(
        feature, "depth_m", attempt_index=attempt_index, rng_factory=rng_factory
    )
    blend = _sample_float_parameter(
        feature, "blend_width_km", attempt_index=attempt_index, rng_factory=rng_factory
    )
    return -_area_blend_contribution(
        plan,
        feature,
        geometry,
        magnitude_m=depth_m,
        blend_width_km=blend,
    )


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
            f"terrain ridge feature {feature.id!r} requires BandGeometry"
        )
    expected = {"height_m", "profile_power", "roughness", "roughness_scale_km"}
    if set(feature.effect.parameters) != expected:
        raise TerrainCapabilityError(
            f"terrain ridge feature {feature.id!r} requires exactly effect parameters {sorted(expected)!r}"
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
    if height_m <= 0.0 or profile_power <= 0.0 or roughness_scale_km <= 0.0:
        raise TerrainCapabilityError("ridge height/profile/scale must resolve to > 0")
    if not 0.0 <= roughness <= 1.0:
        raise TerrainCapabilityError("ridge roughness must be in [0,1]")

    prepared = prepare_band(geometry)
    adapter = GridAdapter.from_plan(plan)
    result = np.zeros((adapter.rows, adapter.columns), dtype=np.float64)

    for row in range(adapter.rows):
        for column in range(adapter.columns):
            point = adapter.cell_center(row, column)
            distance, t = nearest_centerline_distance_and_t(
                prepared,
                x_km=point.x_km,
                y_km=point.y_km,
            )
            width = width_at(geometry, t)
            half_width = 0.5 * width

            broad_noise = value_noise_2d(
                x_km=point.x_km,
                y_km=point.y_km,
                scale_km=max(width, roughness_scale_km * 3.0),
                rng_factory=rng_factory,
                attempt_index=attempt_index,
                stage=RngStage.TERRAIN,
                scope=("feature", feature.id, "massif", "broad"),
                purpose="value",
            )
            effective_half_width = half_width * max(
                0.55,
                1.0 + roughness * 0.30 * broad_noise,
            )
            u = distance / effective_half_width
            if u >= 1.0:
                continue

            envelope = (1.0 - _smoothstep01(u)) ** profile_power
            detail_noise = value_noise_2d(
                x_km=point.x_km,
                y_km=point.y_km,
                scale_km=roughness_scale_km,
                rng_factory=rng_factory,
                attempt_index=attempt_index,
                stage=RngStage.TERRAIN,
                scope=("feature", feature.id, "massif", "relief"),
                purpose="value",
            )
            # Positive bounded modulation keeps this operator an uplift while
            # introducing internal peaks/shoulders rather than a uniform tube.
            relief_factor = max(0.35, 1.0 + roughness * 0.55 * detail_noise)
            result[row, column] = height_m * envelope * relief_factor

    return result


def _build_terrain_v02(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> _TerrainBuildResult:
    try:
        base = synthesize_base_elevation(
            plan,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )
    except TerrainBaseCapabilityError as exc:
        raise TerrainCapabilityError(str(exc)) from exc

    structural = base.astype(np.float64, copy=True)
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
            raise TerrainCapabilityError(f"terrain operator {operator!r} is unsupported")
        applied.append(feature.id)

    snapshot = np.array(structural, dtype=np.float64, copy=True)
    snapshot.setflags(write=False)
    specs = tuple(flatten_specs)
    conflicts = flatten_conflicts(specs)
    shaped = compose_nonoverlapping_flatten(plan, snapshot, specs)
    return _TerrainBuildResult(
        state=TerrainState(
            base_elevation_m=base.copy(),
            elevation_m=shaped.astype(np.float32, copy=True),
        ),
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
    if plan.plan_version == "0.1":
        return _generate_terrain_v01(
            plan,
            layout,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )
    return _build_terrain_v02(
        plan,
        layout,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    ).state


def validate_terrain(
    plan: GenerationPlan,
    layout: LayoutCandidate | None,
    terrain: TerrainState | None,
    *,
    attempt_index: int,
    applied_feature_ids: tuple[str, ...],
    shaping_conflicts: tuple[tuple[str, str], ...] = (),
    rng_factory: RngFactory | None = None,
) -> ValidationResult:
    if plan.plan_version == "0.1":
        return _validate_terrain_v01(
            plan,
            layout,
            terrain,
            attempt_index=attempt_index,
            applied_feature_ids=applied_feature_ids,
            shaping_conflicts=shaping_conflicts,
        )

    expected_shape = (plan.grid.rows, plan.grid.columns)
    expected_features = tuple(
        sorted(feature.id for feature in plan.features if feature.family is FeatureFamily.TERRAIN)
    )
    layout_exists = layout is not None
    layout_attempt_matches = layout_exists and layout.attempt_index == attempt_index
    terrain_exists = terrain is not None

    base_shape = base_dtype = base_finite = False
    elevation_shape = elevation_dtype = elevation_finite = False
    deterministic_recompute = False
    if terrain_exists:
        base = terrain.base_elevation_m
        elevation = terrain.elevation_m
        base_shape = isinstance(base, np.ndarray) and base.shape == expected_shape
        base_dtype = isinstance(base, np.ndarray) and base.dtype == np.dtype(np.float32)
        base_finite = isinstance(base, np.ndarray) and bool(np.isfinite(base).all())
        elevation_shape = isinstance(elevation, np.ndarray) and elevation.shape == expected_shape
        elevation_dtype = isinstance(elevation, np.ndarray) and elevation.dtype == np.dtype(np.float32)
        elevation_finite = isinstance(elevation, np.ndarray) and bool(np.isfinite(elevation).all())

    if (
        layout is not None
        and terrain is not None
        and rng_factory is not None
        and base_shape
        and elevation_shape
    ):
        try:
            rebuilt = _build_terrain_v02(
                plan,
                layout,
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            ).state
            deterministic_recompute = bool(
                np.array_equal(terrain.base_elevation_m, rebuilt.base_elevation_m)
                and np.array_equal(terrain.elevation_m, rebuilt.elevation_m)
            )
        except TerrainCapabilityError:
            deterministic_recompute = False

    applied_complete = (
        tuple(sorted(applied_feature_ids)) == expected_features
        and len(applied_feature_ids) == len(set(applied_feature_ids))
    )
    results = (
        EngineInvariantResult(id="terrain-upstream-layout-exists", passed=layout_exists),
        EngineInvariantResult(id="terrain-layout-attempt-index-matches", passed=layout_attempt_matches),
        EngineInvariantResult(id="terrain-state-exists", passed=terrain_exists),
        EngineInvariantResult(id="terrain-base-shape-matches-grid", passed=base_shape),
        EngineInvariantResult(id="terrain-base-dtype-float32", passed=base_dtype),
        EngineInvariantResult(id="terrain-base-finite", passed=base_finite),
        EngineInvariantResult(id="terrain-elevation-shape-matches-grid", passed=elevation_shape),
        EngineInvariantResult(id="terrain-elevation-dtype-float32", passed=elevation_dtype),
        EngineInvariantResult(id="terrain-elevation-finite", passed=elevation_finite),
        EngineInvariantResult(id="terrain-deterministic-recompute", passed=deterministic_recompute),
        EngineInvariantResult(
            id="terrain-feature-application-complete",
            passed=applied_complete,
            measured={
                "expected_feature_count": len(expected_features),
                "applied_feature_count": len(applied_feature_ids),
            },
        ),
        EngineInvariantResult(
            id="terrain-shaping-regions-compatible",
            passed=not shaping_conflicts,
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
    if context.plan.plan_version == "0.1":
        return _terrain_stage_v01(context, state)
    if state.layout is None:
        return validate_terrain(
            context.plan,
            None,
            None,
            attempt_index=context.attempt_index,
            applied_feature_ids=(),
            rng_factory=context.rng_factory,
        )

    build = _build_terrain_v02(
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
        rng_factory=context.rng_factory,
    )


__all__ = ["generate_terrain", "terrain_stage", "validate_terrain"]
