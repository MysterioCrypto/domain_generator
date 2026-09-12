from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from ..contracts.geometry import AreaGeometry
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import (
    EffectStage,
    FeatureFamily,
    GenerationPlan,
    ParameterType,
)
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from ..grid import GridAdapter
from ..hydrology.state import HydrologyState
from ..layout.area import point_in_area
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngFactory, RngKey, RngStage
from ..pipeline.sampling import SamplingCapabilityError, sample_resolved_parameter
from ..terrain.state import TerrainState
from .derive import (
    SurfaceCapabilityError,
    moisture_potential_field,
    slope_degrees,
    vegetation_potential_field,
)
from .state import SurfaceState


@dataclass(frozen=True, slots=True)
class _SurfaceBuildResult:
    state: SurfaceState
    applied_feature_ids: tuple[str, ...]


def _parameter_stream_key(
    attempt_index: int,
    feature_id: str,
    parameter_name: str,
) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.SURFACE,
        scope=("feature", feature_id, "parameter", parameter_name),
        purpose="sample",
    )


def _sample_float_parameter(
    feature,
    parameter_name: str,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> float:
    recipe = feature.effect.parameters[parameter_name]
    if recipe.type is not ParameterType.FLOAT:
        raise SurfaceCapabilityError(
            f"surface parameter {parameter_name!r} for feature {feature.id!r} "
            "must be a float resolved parameter"
        )

    stream = rng_factory.stream(
        _parameter_stream_key(attempt_index, feature.id, parameter_name)
    )
    try:
        sampled = sample_resolved_parameter(recipe, stream)
    except SamplingCapabilityError as exc:
        raise SurfaceCapabilityError(
            f"surface parameter {parameter_name!r} recipe is unsupported for feature "
            f"{feature.id!r}"
        ) from exc

    if isinstance(sampled, bool) or not isinstance(sampled, (int, float)):
        raise SurfaceCapabilityError(
            f"surface parameter {parameter_name!r} must resolve to a numeric value"
        )
    value = float(sampled)
    if not isfinite(value):
        raise SurfaceCapabilityError(
            f"surface parameter {parameter_name!r} must resolve to a finite value"
        )
    return value


def _rasterize_area_cell_centers(
    plan: GenerationPlan,
    area: AreaGeometry,
) -> np.ndarray:
    adapter = GridAdapter.from_plan(plan)
    mask = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.bool_)
    for row in range(plan.grid.rows):
        for column in range(plan.grid.columns):
            if point_in_area(adapter.cell_center(row, column), area):
                mask[row, column] = True
    return mask


def _area_bias_contribution(
    plan: GenerationPlan,
    feature,
    geometry,
    *,
    parameter_name: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> np.ndarray:
    if not isinstance(geometry, AreaGeometry):
        raise SurfaceCapabilityError(
            f"surface feature {feature.id!r} requires AreaGeometry"
        )
    if set(feature.effect.parameters) != {parameter_name}:
        raise SurfaceCapabilityError(
            f"surface {feature.effect.operator} feature {feature.id!r} requires exactly "
            f"effect parameter [{parameter_name!r}]"
        )

    delta = _sample_float_parameter(
        feature,
        parameter_name,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    if not -1.0 <= delta <= 1.0:
        raise SurfaceCapabilityError(
            f"surface {parameter_name} must resolve to a finite value in [-1, 1]"
        )

    contribution = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.float64)
    contribution[_rasterize_area_cell_centers(plan, geometry)] = delta
    return contribution


def _build_surface(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    terrain: TerrainState,
    hydrology: HydrologyState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> _SurfaceBuildResult:
    expected_shape = (plan.grid.rows, plan.grid.columns)
    elevation = terrain.elevation_m
    water_depth = hydrology.water_depth_m

    if layout.attempt_index != attempt_index:
        raise SurfaceCapabilityError("surface layout attempt index must match current attempt")
    if not isinstance(elevation, np.ndarray) or elevation.shape != expected_shape:
        raise SurfaceCapabilityError("terrain elevation shape must match plan grid")
    if not isinstance(water_depth, np.ndarray) or water_depth.shape != expected_shape:
        raise SurfaceCapabilityError("hydrology water depth shape must match plan grid")
    if not np.isfinite(elevation).all():
        raise SurfaceCapabilityError("terrain elevation must contain only finite values")
    if not np.isfinite(water_depth).all() or bool(np.any(water_depth < 0.0)):
        raise SurfaceCapabilityError("hydrology water depth must be finite and non-negative")

    adapter = GridAdapter.from_plan(plan)
    moisture_potential = moisture_potential_field(
        adapter=adapter,
        water_depth_m=water_depth,
        moisture_base=plan.surface.moisture_base,
        water_moisture_boost=plan.surface.water_moisture_boost,
        water_moisture_decay_km=plan.surface.water_moisture_decay_km,
        moisture_noise_amplitude=plan.surface.moisture_noise_amplitude,
        moisture_noise_scale_km=plan.surface.moisture_noise_scale_km,
        rng_factory=rng_factory,
        attempt_index=attempt_index,
    )

    moisture_bias = np.zeros(expected_shape, dtype=np.float64)
    vegetation_bias = np.zeros(expected_shape, dtype=np.float64)
    applied: list[str] = []

    surface_features = sorted(
        (feature for feature in plan.features if feature.family is FeatureFamily.SURFACE),
        key=lambda feature: feature.id,
    )
    for feature in surface_features:
        if feature.effect.stage is not EffectStage.SURFACE:
            raise SurfaceCapabilityError(
                f"surface feature {feature.id!r} must use surface effect stage"
            )
        try:
            geometry = layout.geometry_realizations[feature.id]
        except KeyError as exc:
            raise SurfaceCapabilityError(
                f"surface feature {feature.id!r} has no materialized layout geometry"
            ) from exc

        operator = feature.effect.operator
        if operator == "moisture_bias":
            moisture_bias += _area_bias_contribution(
                plan,
                feature,
                geometry,
                parameter_name="delta_moisture",
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        elif operator == "vegetation_bias":
            vegetation_bias += _area_bias_contribution(
                plan,
                feature,
                geometry,
                parameter_name="delta_vegetation",
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        else:
            raise SurfaceCapabilityError(
                f"surface operator {operator!r} is unsupported"
            )
        applied.append(feature.id)

    water_mask = water_depth > 0.0
    moisture64 = np.clip(moisture_potential + moisture_bias, 0.0, 1.0)
    moisture64[water_mask] = 1.0

    slope64 = slope_degrees(
        elevation,
        cell_size_km=plan.grid.cell_size_km,
    )
    vegetation_potential = vegetation_potential_field(
        moisture=moisture64,
        slope_deg=slope64,
        vegetation_slope_zero_deg=plan.surface.vegetation_slope_zero_deg,
    )
    vegetation64 = np.clip(vegetation_potential + vegetation_bias, 0.0, 1.0)
    vegetation64[water_mask] = 0.0

    return _SurfaceBuildResult(
        state=SurfaceState(
            moisture=moisture64.astype(np.float32),
            vegetation_density=vegetation64.astype(np.float32),
        ),
        applied_feature_ids=tuple(applied),
    )


def generate_surface(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    terrain: TerrainState,
    hydrology: HydrologyState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> SurfaceState:
    return _build_surface(
        plan,
        layout,
        terrain,
        hydrology,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    ).state


def _expected_surface_feature_ids(plan: GenerationPlan) -> tuple[str, ...]:
    return tuple(
        sorted(feature.id for feature in plan.features if feature.family is FeatureFamily.SURFACE)
    )


def _recomputed_surface_matches(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    terrain: TerrainState,
    hydrology: HydrologyState,
    surface: SurfaceState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> bool:
    try:
        expected = generate_surface(
            plan,
            layout,
            terrain,
            hydrology,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )
    except SurfaceCapabilityError:
        return False
    return np.array_equal(surface.moisture, expected.moisture) and np.array_equal(
        surface.vegetation_density,
        expected.vegetation_density,
    )


def validate_surface(
    plan: GenerationPlan,
    layout: LayoutCandidate | None,
    terrain: TerrainState | None,
    hydrology: HydrologyState | None,
    surface: SurfaceState | None,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
    applied_feature_ids: tuple[str, ...] = (),
) -> ValidationResult:
    expected_shape = (plan.grid.rows, plan.grid.columns)
    expected_features = _expected_surface_feature_ids(plan)

    layout_exists = layout is not None
    layout_attempt_matches = layout_exists and layout.attempt_index == attempt_index
    terrain_exists = terrain is not None
    hydrology_exists = hydrology is not None
    surface_exists = surface is not None

    terrain_shape = terrain_finite = False
    water_shape = water_finite = water_nonnegative = False
    moisture_shape = vegetation_shape = False
    moisture_dtype = vegetation_dtype = False
    moisture_finite = vegetation_finite = False
    moisture_range = vegetation_range = False
    water_moisture_exact = water_vegetation_exact = False
    deterministic_recompute = False

    if terrain_exists:
        elevation = terrain.elevation_m
        terrain_shape = isinstance(elevation, np.ndarray) and elevation.shape == expected_shape
        terrain_finite = isinstance(elevation, np.ndarray) and bool(np.isfinite(elevation).all())

    if hydrology_exists:
        water = hydrology.water_depth_m
        water_shape = isinstance(water, np.ndarray) and water.shape == expected_shape
        water_finite = isinstance(water, np.ndarray) and bool(np.isfinite(water).all())
        water_nonnegative = water_finite and bool(np.all(water >= 0.0))

    if surface_exists:
        moisture = surface.moisture
        vegetation = surface.vegetation_density
        moisture_shape = isinstance(moisture, np.ndarray) and moisture.shape == expected_shape
        vegetation_shape = isinstance(vegetation, np.ndarray) and vegetation.shape == expected_shape
        moisture_dtype = isinstance(moisture, np.ndarray) and moisture.dtype == np.dtype(np.float32)
        vegetation_dtype = isinstance(vegetation, np.ndarray) and vegetation.dtype == np.dtype(np.float32)
        moisture_finite = isinstance(moisture, np.ndarray) and bool(np.isfinite(moisture).all())
        vegetation_finite = isinstance(vegetation, np.ndarray) and bool(np.isfinite(vegetation).all())
        moisture_range = moisture_finite and bool(np.all((moisture >= 0.0) & (moisture <= 1.0)))
        vegetation_range = vegetation_finite and bool(
            np.all((vegetation >= 0.0) & (vegetation <= 1.0))
        )

        if hydrology_exists and water_shape and moisture_shape and vegetation_shape:
            water_mask = hydrology.water_depth_m > 0.0
            water_moisture_exact = bool(
                np.all(surface.moisture[water_mask] == np.float32(1.0))
            )
            water_vegetation_exact = bool(
                np.all(surface.vegetation_density[water_mask] == np.float32(0.0))
            )

    applied_complete = (
        tuple(sorted(applied_feature_ids)) == expected_features
        and len(applied_feature_ids) == len(set(applied_feature_ids))
    )

    if (
        layout_exists
        and layout_attempt_matches
        and terrain_exists
        and hydrology_exists
        and surface_exists
        and terrain_shape
        and terrain_finite
        and water_shape
        and water_finite
        and water_nonnegative
        and moisture_shape
        and vegetation_shape
        and moisture_dtype
        and vegetation_dtype
    ):
        deterministic_recompute = _recomputed_surface_matches(
            plan,
            layout,
            terrain,
            hydrology,
            surface,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )

    results = (
        EngineInvariantResult(id="surface-upstream-layout-exists", passed=layout_exists),
        EngineInvariantResult(id="surface-layout-attempt-index-matches", passed=layout_attempt_matches),
        EngineInvariantResult(id="surface-upstream-terrain-exists", passed=terrain_exists),
        EngineInvariantResult(id="surface-upstream-hydrology-exists", passed=hydrology_exists),
        EngineInvariantResult(id="surface-terrain-shape-matches-grid", passed=terrain_shape),
        EngineInvariantResult(id="surface-terrain-finite", passed=terrain_finite),
        EngineInvariantResult(id="surface-water-depth-shape-matches-grid", passed=water_shape),
        EngineInvariantResult(id="surface-water-depth-finite", passed=water_finite),
        EngineInvariantResult(id="surface-water-depth-nonnegative", passed=water_nonnegative),
        EngineInvariantResult(id="surface-state-exists", passed=surface_exists),
        EngineInvariantResult(id="surface-moisture-shape-matches-grid", passed=moisture_shape),
        EngineInvariantResult(id="surface-moisture-dtype-float32", passed=moisture_dtype),
        EngineInvariantResult(id="surface-moisture-finite", passed=moisture_finite),
        EngineInvariantResult(id="surface-moisture-range", passed=moisture_range),
        EngineInvariantResult(id="surface-vegetation-shape-matches-grid", passed=vegetation_shape),
        EngineInvariantResult(id="surface-vegetation-dtype-float32", passed=vegetation_dtype),
        EngineInvariantResult(id="surface-vegetation-finite", passed=vegetation_finite),
        EngineInvariantResult(id="surface-vegetation-range", passed=vegetation_range),
        EngineInvariantResult(id="surface-water-moisture-is-one", passed=water_moisture_exact),
        EngineInvariantResult(id="surface-water-vegetation-is-zero", passed=water_vegetation_exact),
        EngineInvariantResult(
            id="surface-feature-effects-applied-exactly",
            passed=applied_complete,
            measured={
                "expected_feature_count": len(expected_features),
                "applied_feature_count": len(applied_feature_ids),
            },
        ),
        EngineInvariantResult(id="surface-deterministic-recompute", passed=deterministic_recompute),
    )
    passed = all(item.passed for item in results)
    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.SURFACE,
        engine_invariants=EngineInvariantGroup(passed=passed, results=results),
        hard_constraints=HardConstraintGroup(passed=True, results=()),
        soft_constraints=SoftConstraintGroup(results=()),
        ranking=None,
    )


def surface_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    if state.layout is None or state.terrain is None or state.hydrology is None:
        return validate_surface(
            context.plan,
            state.layout,
            state.terrain,
            state.hydrology,
            None,
            attempt_index=context.attempt_index,
            rng_factory=context.rng_factory,
            applied_feature_ids=(),
        )

    build = _build_surface(
        context.plan,
        state.layout,
        state.terrain,
        state.hydrology,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
    state.surface = build.state
    return validate_surface(
        context.plan,
        state.layout,
        state.terrain,
        state.hydrology,
        state.surface,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
        applied_feature_ids=build.applied_feature_ids,
    )
