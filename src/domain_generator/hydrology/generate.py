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
from ..pipeline.attempts import AttemptContext, CandidateState
from ..terrain.state import TerrainState
from .routing import D8_DIRECTIONS, HydrologyCapabilityError, d8_flow_direction, flow_accumulation_km2, priority_flood_routing_surface
from .state import HydrologyState


def generate_hydrology(plan: GenerationPlan, terrain: TerrainState) -> HydrologyState:
    elevation = terrain.elevation_m
    expected_shape = (plan.grid.rows, plan.grid.columns)
    if not isinstance(elevation, np.ndarray) or elevation.shape != expected_shape:
        raise HydrologyCapabilityError("terrain elevation shape must match plan grid")
    if not np.isfinite(elevation).all():
        raise HydrologyCapabilityError("terrain elevation must contain only finite values")

    routing = priority_flood_routing_surface(elevation)
    direction = d8_flow_direction(routing, cell_size_km=plan.grid.cell_size_km)
    accumulation = flow_accumulation_km2(
        routing,
        direction,
        cell_size_km=plan.grid.cell_size_km,
    )
    return HydrologyState(
        routing_elevation_m=routing,
        flow_direction=direction,
        flow_accumulation_km2=accumulation,
    )


def _edge_mask(rows: int, columns: int) -> np.ndarray:
    mask = np.zeros((rows, columns), dtype=np.bool_)
    mask[0, :] = True
    mask[-1, :] = True
    mask[:, 0] = True
    mask[:, -1] = True
    return mask


def _receivers_are_strictly_lower(state: HydrologyState) -> bool:
    routing = state.routing_elevation_m
    direction = state.flow_direction
    rows, columns = routing.shape
    for row in range(rows):
        for column in range(columns):
            code = int(direction[row, column])
            if code == -1:
                continue
            if not 0 <= code < len(D8_DIRECTIONS):
                return False
            delta_row, delta_column, _ = D8_DIRECTIONS[code]
            receiver_row = row + delta_row
            receiver_column = column + delta_column
            if not (0 <= receiver_row < rows and 0 <= receiver_column < columns):
                return False
            if not routing[receiver_row, receiver_column] < routing[row, column]:
                return False
    return True


def validate_hydrology(
    plan: GenerationPlan,
    terrain: TerrainState | None,
    hydrology: HydrologyState | None,
    *,
    attempt_index: int,
) -> ValidationResult:
    expected_shape = (plan.grid.rows, plan.grid.columns)
    cell_area_km2 = plan.grid.cell_size_km * plan.grid.cell_size_km

    terrain_exists = terrain is not None
    terrain_shape = False
    terrain_finite = False
    if terrain_exists:
        terrain_shape = isinstance(terrain.elevation_m, np.ndarray) and terrain.elevation_m.shape == expected_shape
        terrain_finite = isinstance(terrain.elevation_m, np.ndarray) and bool(np.isfinite(terrain.elevation_m).all())

    hydrology_exists = hydrology is not None
    routing_shape = direction_shape = accumulation_shape = False
    routing_dtype = direction_dtype = accumulation_dtype = False
    routing_finite = accumulation_finite = False
    routing_not_below_terrain = False
    direction_codes_valid = False
    edge_outlets = False
    interior_receivers_present = False
    receivers_lower = False
    accumulation_minimum = False

    if hydrology_exists:
        routing = hydrology.routing_elevation_m
        direction = hydrology.flow_direction
        accumulation = hydrology.flow_accumulation_km2

        routing_shape = isinstance(routing, np.ndarray) and routing.shape == expected_shape
        direction_shape = isinstance(direction, np.ndarray) and direction.shape == expected_shape
        accumulation_shape = isinstance(accumulation, np.ndarray) and accumulation.shape == expected_shape

        routing_dtype = isinstance(routing, np.ndarray) and routing.dtype == np.dtype(np.float64)
        direction_dtype = isinstance(direction, np.ndarray) and direction.dtype == np.dtype(np.int8)
        accumulation_dtype = isinstance(accumulation, np.ndarray) and accumulation.dtype == np.dtype(np.float64)

        routing_finite = isinstance(routing, np.ndarray) and bool(np.isfinite(routing).all())
        accumulation_finite = isinstance(accumulation, np.ndarray) and bool(np.isfinite(accumulation).all())

        if terrain_exists and terrain_shape and routing_shape:
            routing_not_below_terrain = bool(
                np.all(routing >= terrain.elevation_m.astype(np.float64, copy=False))
            )

        if direction_shape:
            direction_codes_valid = bool(np.all((direction >= -1) & (direction <= 7)))
            edge = _edge_mask(*expected_shape)
            edge_outlets = bool(np.all(direction[edge] == -1))
            interior = ~edge
            interior_receivers_present = bool(np.all(direction[interior] >= 0)) if bool(interior.any()) else True

        if routing_shape and direction_shape and direction_codes_valid:
            receivers_lower = _receivers_are_strictly_lower(hydrology)

        if accumulation_shape and accumulation_finite:
            accumulation_minimum = bool(np.all(accumulation >= cell_area_km2))

    results = (
        EngineInvariantResult(id="hydrology-upstream-terrain-exists", passed=terrain_exists),
        EngineInvariantResult(id="hydrology-terrain-shape-matches-grid", passed=terrain_shape),
        EngineInvariantResult(id="hydrology-terrain-finite", passed=terrain_finite),
        EngineInvariantResult(id="hydrology-state-exists", passed=hydrology_exists),
        EngineInvariantResult(id="hydrology-routing-shape-matches-grid", passed=routing_shape),
        EngineInvariantResult(id="hydrology-routing-dtype-float64", passed=routing_dtype),
        EngineInvariantResult(id="hydrology-routing-finite", passed=routing_finite),
        EngineInvariantResult(id="hydrology-routing-not-below-terrain", passed=routing_not_below_terrain),
        EngineInvariantResult(id="hydrology-direction-shape-matches-grid", passed=direction_shape),
        EngineInvariantResult(id="hydrology-direction-dtype-int8", passed=direction_dtype),
        EngineInvariantResult(id="hydrology-direction-codes-valid", passed=direction_codes_valid),
        EngineInvariantResult(id="hydrology-edge-cells-are-outlets", passed=edge_outlets),
        EngineInvariantResult(id="hydrology-interior-cells-have-receivers", passed=interior_receivers_present),
        EngineInvariantResult(id="hydrology-receivers-strictly-lower", passed=receivers_lower),
        EngineInvariantResult(id="hydrology-accumulation-shape-matches-grid", passed=accumulation_shape),
        EngineInvariantResult(id="hydrology-accumulation-dtype-float64", passed=accumulation_dtype),
        EngineInvariantResult(id="hydrology-accumulation-finite", passed=accumulation_finite),
        EngineInvariantResult(
            id="hydrology-accumulation-at-least-cell-area",
            passed=accumulation_minimum,
            measured={"cell_area_km2": cell_area_km2},
        ),
    )
    passed = all(result.passed for result in results)

    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.HYDROLOGY,
        engine_invariants=EngineInvariantGroup(passed=passed, results=results),
        hard_constraints=HardConstraintGroup(passed=True, results=()),
        soft_constraints=SoftConstraintGroup(results=()),
        ranking=None,
    )


def hydrology_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    if state.terrain is None:
        return validate_hydrology(
            context.plan,
            None,
            None,
            attempt_index=context.attempt_index,
        )

    hydrology = generate_hydrology(context.plan, state.terrain)
    state.hydrology = hydrology
    return validate_hydrology(
        context.plan,
        state.terrain,
        state.hydrology,
        attempt_index=context.attempt_index,
    )
