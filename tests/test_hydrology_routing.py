from __future__ import annotations

import numpy as np
import pytest

from domain_generator.contracts.plan import GenerationPlan, PlanDomain, PlanGrid, PlanSource
from domain_generator.hydrology import (
    HydrologyState,
    d8_flow_direction,
    flow_accumulation_km2,
    generate_hydrology,
    priority_flood_routing_surface,
    validate_hydrology,
)
from domain_generator.terrain.state import TerrainState


def make_plan(*, rows: int, columns: int, cell_size_km: float = 1.0) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="hydrology-test",
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
        features=(),
        constraints=(),
    )


def test_priority_flood_conditions_depression_without_mutating_terrain() -> None:
    elevation = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, 50.0, 100.0],
            [100.0, 100.0, 100.0],
        ],
        dtype=np.float32,
    )
    original = elevation.copy()

    routing = priority_flood_routing_surface(elevation)

    assert np.array_equal(elevation, original)
    assert routing.dtype == np.float64
    assert routing[1, 1] == np.nextafter(np.float64(100.0), np.float64(np.inf))
    assert routing[1, 1] > 100.0


def test_d8_uses_distance_normalization_and_canonical_tie_break() -> None:
    routing = np.array(
        [
            [100.0, 100.0, 100.0],
            [100.0, np.nextafter(100.0, np.inf), 100.0],
            [100.0, 100.0, 100.0],
        ],
        dtype=np.float64,
    )

    direction = d8_flow_direction(routing, cell_size_km=1.0)

    # N/E/S/W have the same height drop, but orthogonal slope beats diagonals;
    # exact orthogonal tie resolves to earliest canonical direction: N (0).
    assert direction[1, 1] == np.int8(0)
    edge = np.ones((3, 3), dtype=np.bool_)
    edge[1, 1] = False
    assert np.all(direction[edge] == -1)


def test_flat_surface_receives_minimal_gradient_and_routes_every_interior_cell() -> None:
    elevation = np.full((5, 5), 25.0, dtype=np.float32)

    routing = priority_flood_routing_surface(elevation)
    direction = d8_flow_direction(routing, cell_size_km=1.0)

    assert np.all(routing >= elevation.astype(np.float64))
    assert np.all(direction[1:-1, 1:-1] >= 0)
    assert np.all(direction[0, :] == -1)
    assert np.all(direction[-1, :] == -1)
    assert np.all(direction[:, 0] == -1)
    assert np.all(direction[:, -1] == -1)


def test_flow_accumulation_uses_physical_cell_area() -> None:
    routing = np.tile(
        np.array([5.0, 4.0, 3.0, 2.0, 1.0], dtype=np.float64),
        (5, 1),
    )
    direction = d8_flow_direction(routing, cell_size_km=0.5)

    accumulation = flow_accumulation_km2(
        routing,
        direction,
        cell_size_km=0.5,
    )

    assert direction[2, 1] == np.int8(2)  # E
    assert direction[2, 2] == np.int8(2)
    assert direction[2, 3] == np.int8(2)
    assert accumulation[2, 1] == pytest.approx(0.25)
    assert accumulation[2, 2] == pytest.approx(0.50)
    assert accumulation[2, 3] == pytest.approx(0.75)
    assert accumulation[2, 4] == pytest.approx(1.00)


def test_generate_hydrology_replays_and_preserves_canonical_terrain() -> None:
    plan = make_plan(rows=5, columns=5)
    elevation = np.array(
        [
            [10, 10, 10, 10, 10],
            [10, 9, 8, 7, 6],
            [10, 9, 1, 7, 5],
            [10, 9, 8, 7, 4],
            [10, 10, 10, 10, 3],
        ],
        dtype=np.float32,
    )
    terrain = TerrainState(elevation_m=elevation.copy())
    before = terrain.elevation_m.copy()

    first = generate_hydrology(plan, terrain)
    second = generate_hydrology(plan, terrain)

    assert np.array_equal(terrain.elevation_m, before)
    assert np.array_equal(first.routing_elevation_m, second.routing_elevation_m)
    assert np.array_equal(first.flow_direction, second.flow_direction)
    assert np.array_equal(first.flow_accumulation_km2, second.flow_accumulation_km2)


def test_hydrology_validation_accepts_generated_state() -> None:
    plan = make_plan(rows=4, columns=4, cell_size_km=0.25)
    terrain = TerrainState(
        elevation_m=np.array(
            [
                [4.0, 4.0, 4.0, 4.0],
                [4.0, 3.0, 2.0, 1.0],
                [4.0, 3.0, 2.0, 1.0],
                [4.0, 4.0, 4.0, 0.0],
            ],
            dtype=np.float32,
        )
    )
    hydrology = generate_hydrology(plan, terrain)

    validation = validate_hydrology(
        plan,
        terrain,
        hydrology,
        attempt_index=7,
    )

    assert validation.engine_invariants.passed is True
    assert validation.stage.value == "hydrology"
    assert hydrology.routing_elevation_m.dtype == np.float64
    assert hydrology.flow_direction.dtype == np.int8
    assert hydrology.flow_accumulation_km2.dtype == np.float64


def test_hydrology_validation_rejects_missing_upstream_terrain() -> None:
    plan = make_plan(rows=3, columns=3)

    validation = validate_hydrology(
        plan,
        None,
        None,
        attempt_index=0,
    )

    assert validation.engine_invariants.passed is False
    failed = {result.id for result in validation.engine_invariants.results if not result.passed}
    assert "hydrology-upstream-terrain-exists" in failed
    assert "hydrology-state-exists" in failed


def test_validation_rejects_non_lower_receiver() -> None:
    plan = make_plan(rows=3, columns=3)
    terrain = TerrainState(elevation_m=np.zeros((3, 3), dtype=np.float32))
    hydrology = HydrologyState(
        routing_elevation_m=np.zeros((3, 3), dtype=np.float64),
        flow_direction=np.array(
            [
                [-1, -1, -1],
                [-1, 0, -1],
                [-1, -1, -1],
            ],
            dtype=np.int8,
        ),
        flow_accumulation_km2=np.ones((3, 3), dtype=np.float64),
    )

    validation = validate_hydrology(plan, terrain, hydrology, attempt_index=0)

    receiver_invariant = next(
        result
        for result in validation.engine_invariants.results
        if result.id == "hydrology-receivers-strictly-lower"
    )
    assert receiver_invariant.passed is False
