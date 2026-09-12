from __future__ import annotations

import numpy as np
import pytest

from domain_generator.compiler import semantic_plan_fingerprint
from domain_generator.contracts.data import RiverNetwork
from domain_generator.contracts.layout import LayoutCandidate, SourcePlanRef
from domain_generator.contracts.plan import (
    GenerationPlan,
    PlanDomain,
    PlanGrid,
    PlanHydrology,
    PlanSource,
    PlanSurface,
)
from domain_generator.hydrology.state import HydrologyState
from domain_generator.pipeline.attempts import AttemptContext, CandidateState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.surface import (
    SurfaceState,
    distance_to_water_km,
    generate_surface,
    slope_degrees,
    surface_stage,
    validate_surface,
)
from domain_generator.terrain.state import TerrainState


def make_plan(
    *,
    rows: int = 3,
    columns: int = 3,
    cell_size_km: float = 1.0,
    moisture_base: float = 0.25,
    water_moisture_boost: float = 0.5,
    water_moisture_decay_km: float = 2.0,
    moisture_noise_amplitude: float = 0.0,
    moisture_noise_scale_km: float = 4.0,
    vegetation_slope_zero_deg: float = 45.0,
) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="surface-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=123456,
        domain=PlanDomain(
            width_km=columns * cell_size_km,
            height_km=rows * cell_size_km,
        ),
        grid=PlanGrid(
            cell_size_km=cell_size_km,
            rows=rows,
            columns=columns,
        ),
        hydrology=PlanHydrology(
            stream_threshold_km2=1.0,
            lake_min_area_km2=1.0,
            lake_min_depth_m=1.0,
            river_depth_at_threshold_m=0.5,
            river_depth_exponent=0.3,
        ),
        surface=PlanSurface(
            moisture_base=moisture_base,
            water_moisture_boost=water_moisture_boost,
            water_moisture_decay_km=water_moisture_decay_km,
            moisture_noise_amplitude=moisture_noise_amplitude,
            moisture_noise_scale_km=moisture_noise_scale_km,
            vegetation_slope_zero_deg=vegetation_slope_zero_deg,
        ),
        features=(),
        constraints=(),
    )


def make_layout(plan: GenerationPlan, *, attempt_index: int = 0) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations={},
        placement_reservations={},
    )


def make_hydrology(water_depth_m: np.ndarray) -> HydrologyState:
    rows, columns = water_depth_m.shape
    return HydrologyState(
        routing_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        fill_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        flow_direction=np.full((rows, columns), -1, dtype=np.int8),
        flow_accumulation_km2=np.ones((rows, columns), dtype=np.float64),
        stream_mask=np.zeros((rows, columns), dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=water_depth_m.astype(np.float32, copy=False),
    )


def test_distance_to_water_is_exact_center_to_center_euclidean_km() -> None:
    water = np.zeros((5, 5), dtype=np.bool_)
    water[2, 2] = True
    distance = distance_to_water_km(water, cell_size_km=0.5)
    assert distance.dtype == np.float64
    assert distance[2, 2] == 0.0
    assert distance[2, 4] == pytest.approx(1.0)
    assert distance[0, 0] == pytest.approx(np.sqrt(2.0))


def test_distance_to_water_without_water_is_infinite_derived_intermediate() -> None:
    water = np.zeros((2, 3), dtype=np.bool_)
    distance = distance_to_water_km(water, cell_size_km=1.0)
    assert np.isinf(distance).all()


def test_slope_uses_maximum_distance_normalized_8_neighbor_gradient() -> None:
    elevation = np.array(
        [[0.0, 0.0, 0.0], [0.0, 0.0, 1000.0], [0.0, 0.0, 0.0]],
        dtype=np.float32,
    )
    slope = slope_degrees(elevation, cell_size_km=1.0)
    assert slope[1, 1] == pytest.approx(45.0)
    assert slope[0, 0] == pytest.approx(0.0)


def test_single_cell_domain_has_zero_slope() -> None:
    elevation = np.array([[123.0]], dtype=np.float32)
    assert slope_degrees(elevation, cell_size_km=1.0)[0, 0] == 0.0


def test_no_water_no_noise_yields_base_moisture_and_flat_vegetation() -> None:
    plan = make_plan(moisture_base=0.3, moisture_noise_amplitude=0.0)
    terrain = TerrainState(elevation_m=np.zeros((3, 3), dtype=np.float32))
    hydrology = make_hydrology(np.zeros((3, 3), dtype=np.float32))
    state = generate_surface(
        plan,
        make_layout(plan),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    assert state.moisture.dtype == np.float32
    assert state.vegetation_density.dtype == np.float32
    assert np.array_equal(state.moisture, np.full((3, 3), 0.3, dtype=np.float32))
    assert np.array_equal(state.vegetation_density, np.full((3, 3), 0.3, dtype=np.float32))


def test_water_cell_forces_moisture_one_and_terrestrial_vegetation_zero() -> None:
    plan = make_plan(
        moisture_base=0.0,
        water_moisture_boost=0.5,
        water_moisture_decay_km=1.0,
        moisture_noise_amplitude=0.0,
    )
    terrain = TerrainState(elevation_m=np.zeros((3, 3), dtype=np.float32))
    water = np.zeros((3, 3), dtype=np.float32)
    water[1, 1] = 2.0
    hydrology = make_hydrology(water)
    state = generate_surface(
        plan,
        make_layout(plan),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    assert state.moisture[1, 1] == np.float32(1.0)
    assert state.vegetation_density[1, 1] == np.float32(0.0)
    assert state.moisture[1, 2] == pytest.approx(np.float32(0.5 * np.exp(-1.0)))


def test_slope_reduces_vegetation_without_changing_moisture() -> None:
    plan = make_plan(moisture_base=1.0, moisture_noise_amplitude=0.0, vegetation_slope_zero_deg=45.0)
    elevation = np.zeros((3, 3), dtype=np.float32)
    elevation[1, 2] = 1000.0
    terrain = TerrainState(elevation_m=elevation)
    hydrology = make_hydrology(np.zeros((3, 3), dtype=np.float32))
    state = generate_surface(
        plan,
        make_layout(plan),
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    assert state.moisture[1, 1] == np.float32(1.0)
    assert state.vegetation_density[1, 1] == np.float32(0.0)


def test_surface_noise_replays_per_attempt_and_changes_across_attempts() -> None:
    plan = make_plan(rows=4, columns=4, moisture_base=0.5, moisture_noise_amplitude=0.25, moisture_noise_scale_km=2.0)
    terrain = TerrainState(elevation_m=np.zeros((4, 4), dtype=np.float32))
    hydrology = make_hydrology(np.zeros((4, 4), dtype=np.float32))
    first = generate_surface(
        plan,
        make_layout(plan, attempt_index=2),
        terrain,
        hydrology,
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    replay = generate_surface(
        plan,
        make_layout(plan, attempt_index=2),
        terrain,
        hydrology,
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    other = generate_surface(
        plan,
        make_layout(plan, attempt_index=3),
        terrain,
        hydrology,
        attempt_index=3,
        rng_factory=RngFactory(plan.seed),
    )
    assert np.array_equal(first.moisture, replay.moisture)
    assert np.array_equal(first.vegetation_density, replay.vegetation_density)
    assert not np.array_equal(first.moisture, other.moisture)


def test_surface_validation_detects_tampered_output() -> None:
    plan = make_plan(moisture_base=0.4)
    layout = make_layout(plan)
    terrain = TerrainState(elevation_m=np.zeros((3, 3), dtype=np.float32))
    hydrology = make_hydrology(np.zeros((3, 3), dtype=np.float32))
    state = generate_surface(
        plan,
        layout,
        terrain,
        hydrology,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    tampered = state.moisture.copy()
    tampered[1, 1] = np.float32(0.9)
    mutated = SurfaceState(moisture=tampered, vegetation_density=state.vegetation_density)
    validation = validate_surface(
        plan,
        layout,
        terrain,
        hydrology,
        mutated,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    invariant = next(item for item in validation.engine_invariants.results if item.id == "surface-deterministic-recompute")
    assert invariant.passed is False


def test_surface_stage_stores_runtime_state() -> None:
    plan = make_plan()
    terrain = TerrainState(elevation_m=np.zeros((3, 3), dtype=np.float32))
    hydrology = make_hydrology(np.zeros((3, 3), dtype=np.float32))
    candidate = CandidateState(
        attempt_index=0,
        layout=make_layout(plan),
        terrain=terrain,
        hydrology=hydrology,
    )
    context = AttemptContext(plan=plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    validation = surface_stage(context, candidate)
    assert candidate.surface is not None
    assert validation.stage.value == "surface"
    assert validation.engine_invariants.passed is True


def test_surface_stage_requires_layout_upstream() -> None:
    plan = make_plan()
    terrain = TerrainState(elevation_m=np.zeros((3, 3), dtype=np.float32))
    hydrology = make_hydrology(np.zeros((3, 3), dtype=np.float32))
    candidate = CandidateState(attempt_index=0, terrain=terrain, hydrology=hydrology)
    context = AttemptContext(plan=plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    validation = surface_stage(context, candidate)
    assert candidate.surface is None
    invariant = next(item for item in validation.engine_invariants.results if item.id == "surface-upstream-layout-exists")
    assert invariant.passed is False
