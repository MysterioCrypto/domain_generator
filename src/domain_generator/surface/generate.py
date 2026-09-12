from __future__ import annotations

import numpy as np

from ..contracts.plan import GenerationPlan
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
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngFactory
from ..terrain.state import TerrainState
from .derive import (
    SurfaceCapabilityError,
    moisture_field,
    slope_degrees,
    vegetation_density_field,
)
from .state import SurfaceState


def generate_surface(
    plan: GenerationPlan,
    terrain: TerrainState,
    hydrology: HydrologyState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> SurfaceState:
    expected_shape = (plan.grid.rows, plan.grid.columns)
    elevation = terrain.elevation_m
    water_depth = hydrology.water_depth_m

    if not isinstance(elevation, np.ndarray) or elevation.shape != expected_shape:
        raise SurfaceCapabilityError("terrain elevation shape must match plan grid")
    if not isinstance(water_depth, np.ndarray) or water_depth.shape != expected_shape:
        raise SurfaceCapabilityError("hydrology water depth shape must match plan grid")
    if not np.isfinite(elevation).all():
        raise SurfaceCapabilityError("terrain elevation must contain only finite values")
    if not np.isfinite(water_depth).all() or bool(np.any(water_depth < 0.0)):
        raise SurfaceCapabilityError("hydrology water depth must be finite and non-negative")

    adapter = GridAdapter.from_plan(plan)
    moisture64 = moisture_field(
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
    slope64 = slope_degrees(
        elevation,
        cell_size_km=plan.grid.cell_size_km,
    )
    vegetation64 = vegetation_density_field(
        moisture=moisture64,
        slope_deg=slope64,
        water_depth_m=water_depth,
        vegetation_slope_zero_deg=plan.surface.vegetation_slope_zero_deg,
    )

    return SurfaceState(
        moisture=moisture64.astype(np.float32),
        vegetation_density=vegetation64.astype(np.float32),
    )


def _recomputed_surface_matches(
    plan: GenerationPlan,
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
    terrain: TerrainState | None,
    hydrology: HydrologyState | None,
    surface: SurfaceState | None,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> ValidationResult:
    expected_shape = (plan.grid.rows, plan.grid.columns)

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

    if (
        terrain_exists
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
            terrain,
            hydrology,
            surface,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )

    results = (
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
    if state.terrain is None or state.hydrology is None:
        return validate_surface(
            context.plan,
            state.terrain,
            state.hydrology,
            None,
            attempt_index=context.attempt_index,
            rng_factory=context.rng_factory,
        )

    surface = generate_surface(
        context.plan,
        state.terrain,
        state.hydrology,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
    state.surface = surface
    return validate_surface(
        context.plan,
        state.terrain,
        state.hydrology,
        state.surface,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
