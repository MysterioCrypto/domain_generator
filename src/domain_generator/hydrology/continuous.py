from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from math import atan2, cos, hypot, isfinite, pi, sin
from typing import Literal

import numpy as np

from ..contracts.data import (
    BoundarySide,
    RiverNetwork,
    RiverNode,
    RiverNodeKind,
    RiverSegment,
    RiverSegmentProperties,
)
from ..contracts.geometry import WorldPoint
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
from ..terrain.state import TerrainState
from .classification import classify_stream_mask, extract_lake_candidates
from .ids import lake_feature_id
from .materialize import materialize_lake_features, validate_river_lake_references
from .routing import HydrologyCapabilityError, priority_flood_surfaces
from .state import (
    Cell,
    ContinuousRoutingField,
    HydrologyState,
    LakeCandidate,
    LakeOutlet,
)
from .water import accepted_lake_cell_map, build_water_depth_m


_TWO_PI = 2.0 * pi
_EIGHTH_TURN = pi / 4.0
_EPS = 1e-12

# Counter-clockwise world-space order from +x/east. row 0 is north, therefore
# negative raster row is positive world y.
_DIRS: tuple[tuple[int, int, float, float, float], ...] = (
    (0, 1, 1.0, 0.0, 0.0),
    (-1, 1, 1.0, 1.0, pi / 4.0),
    (-1, 0, 0.0, 1.0, pi / 2.0),
    (-1, -1, -1.0, 1.0, 3.0 * pi / 4.0),
    (0, -1, -1.0, 0.0, pi),
    (1, -1, -1.0, -1.0, 5.0 * pi / 4.0),
    (1, 0, 0.0, -1.0, 3.0 * pi / 2.0),
    (1, 1, 1.0, -1.0, 7.0 * pi / 4.0),
)


@dataclass(frozen=True, slots=True)
class _FacetChoice:
    angle_rad: float
    slope: float
    first: Cell
    second: Cell | None
    first_fraction: float
    second_fraction: float


@dataclass(frozen=True, slots=True)
class _NodeDescriptor:
    key: tuple[object, ...]
    kind: RiverNodeKind
    position: WorldPoint
    boundary_side: BoundarySide | None = None
    feature_id: str | None = None
    anchor_cell: Cell | None = None


@dataclass(frozen=True, slots=True)
class _TraceTerminal:
    kind: Literal["confluence", "lake_inflow", "domain_outlet"]
    position: WorldPoint
    anchor_cell: Cell | None = None
    feature_id: str | None = None
    boundary_side: BoundarySide | None = None


@dataclass(frozen=True, slots=True)
class _TraceResult:
    points: tuple[WorldPoint, ...]
    terminal: _TraceTerminal
    traversed_cells: tuple[Cell, ...]
    catchment_area_km2: float


@dataclass(frozen=True, slots=True)
class _ChannelSkeleton:
    receiver_index: np.ndarray
    channel_area_km2: np.ndarray
    convergence: np.ndarray
    initiation_score_km2: np.ndarray
    mask: np.ndarray
    sources: frozenset[Cell]
    confluences: frozenset[Cell]


def _require_2d_finite(name: str, values: np.ndarray) -> None:
    if not isinstance(values, np.ndarray) or values.ndim != 2 or min(values.shape) < 1:
        raise HydrologyCapabilityError(f"{name} must be a non-empty 2D numpy array")
    if not np.isfinite(values).all():
        raise HydrologyCapabilityError(f"{name} must contain only finite values")


def _flat_index(cell: Cell, columns: int) -> int:
    return cell[0] * columns + cell[1]


def _cell_from_index(index: int, columns: int) -> Cell:
    return divmod(index, columns)


def _is_edge(cell: Cell, shape: tuple[int, int]) -> bool:
    row, column = cell
    rows, columns = shape
    return row == 0 or column == 0 or row == rows - 1 or column == columns - 1


def _angle_delta_ccw(angle: float, start: float) -> float:
    return (angle - start) % _TWO_PI


def _inside_facet(angle: float, start: float) -> bool:
    return _angle_delta_ccw(angle, start) <= _EIGHTH_TURN + 1e-12


def _neighbor(cell: Cell, direction: int, shape: tuple[int, int]) -> Cell | None:
    row, column = cell
    delta_row, delta_column, _, _, _ = _DIRS[direction]
    result = (row + delta_row, column + delta_column)
    if 0 <= result[0] < shape[0] and 0 <= result[1] < shape[1]:
        return result
    return None


def _edge_choice(
    *,
    current: float,
    neighbor_cell: Cell,
    neighbor_value: float,
    direction: int,
    cell_size_km: float,
) -> _FacetChoice | None:
    if not neighbor_value < current:
        return None
    _, _, vx, vy, angle = _DIRS[direction]
    distance = cell_size_km * hypot(vx, vy)
    slope = (current - neighbor_value) / distance
    return _FacetChoice(
        angle_rad=angle,
        slope=slope,
        first=neighbor_cell,
        second=None,
        first_fraction=1.0,
        second_fraction=0.0,
    )


def _best_facet_choice(
    routing: np.ndarray,
    cell: Cell,
    *,
    cell_size_km: float,
) -> _FacetChoice:
    row, column = cell
    current = float(routing[cell])
    shape = routing.shape
    best: _FacetChoice | None = None

    for first_direction in range(8):
        second_direction = (first_direction + 1) % 8
        first = _neighbor(cell, first_direction, shape)
        second = _neighbor(cell, second_direction, shape)
        if first is None or second is None:
            continue

        _, _, v1x_unit, v1y_unit, start_angle = _DIRS[first_direction]
        _, _, v2x_unit, v2y_unit, _ = _DIRS[second_direction]
        v1x = v1x_unit * cell_size_km
        v1y = v1y_unit * cell_size_km
        v2x = v2x_unit * cell_size_km
        v2y = v2y_unit * cell_size_km
        d1 = float(routing[first]) - current
        d2 = float(routing[second]) - current
        det = v1x * v2y - v1y * v2x
        if abs(det) <= _EPS:
            continue

        gx = (d1 * v2y - v1y * d2) / det
        gy = (v1x * d2 - d1 * v2x) / det
        downhill_x = -gx
        downhill_y = -gy
        slope = hypot(downhill_x, downhill_y)

        candidate: _FacetChoice | None = None
        if slope > _EPS:
            angle = atan2(downhill_y, downhill_x) % _TWO_PI
            if _inside_facet(angle, start_angle):
                t = min(1.0, max(0.0, _angle_delta_ccw(angle, start_angle) / _EIGHTH_TURN))
                w1 = 1.0 - t
                w2 = t
                if not float(routing[first]) < current:
                    w1 = 0.0
                if not float(routing[second]) < current:
                    w2 = 0.0
                total = w1 + w2
                if total > _EPS:
                    w1 /= total
                    w2 /= total
                    if w1 <= _EPS:
                        candidate = _edge_choice(
                            current=current,
                            neighbor_cell=second,
                            neighbor_value=float(routing[second]),
                            direction=second_direction,
                            cell_size_km=cell_size_km,
                        )
                    elif w2 <= _EPS:
                        candidate = _edge_choice(
                            current=current,
                            neighbor_cell=first,
                            neighbor_value=float(routing[first]),
                            direction=first_direction,
                            cell_size_km=cell_size_km,
                        )
                    else:
                        candidate = _FacetChoice(
                            angle_rad=angle,
                            slope=slope,
                            first=first,
                            second=second,
                            first_fraction=w1,
                            second_fraction=w2,
                        )

        if candidate is None:
            edges = (
                _edge_choice(
                    current=current,
                    neighbor_cell=first,
                    neighbor_value=float(routing[first]),
                    direction=first_direction,
                    cell_size_km=cell_size_km,
                ),
                _edge_choice(
                    current=current,
                    neighbor_cell=second,
                    neighbor_value=float(routing[second]),
                    direction=second_direction,
                    cell_size_km=cell_size_km,
                ),
            )
            candidate = max(
                (edge for edge in edges if edge is not None),
                key=lambda edge: (edge.slope, -edge.angle_rad),
                default=None,
            )

        if candidate is None:
            continue
        if best is None or (candidate.slope, -candidate.angle_rad) > (best.slope, -best.angle_rad):
            best = candidate

    if best is None:
        raise HydrologyCapabilityError(
            f"conditioned interior cell ({row},{column}) has no continuous downslope facet"
        )
    return best


def _local_slope_field(
    routing_elevation_m: np.ndarray,
    *,
    cell_size_km: float,
) -> np.ndarray:
    """Return deterministic dimensionless terrain gradient magnitude."""
    rows, columns = routing_elevation_m.shape
    spacing_m = float(cell_size_km) * 1000.0
    dz_dx = np.zeros((rows, columns), dtype=np.float64)
    dz_dy = np.zeros((rows, columns), dtype=np.float64)

    if columns > 1:
        dz_dx[:, 1:-1] = (routing_elevation_m[:, 2:] - routing_elevation_m[:, :-2]) / (2.0 * spacing_m)
        dz_dx[:, 0] = (routing_elevation_m[:, 1] - routing_elevation_m[:, 0]) / spacing_m
        dz_dx[:, -1] = (routing_elevation_m[:, -1] - routing_elevation_m[:, -2]) / spacing_m
    if rows > 1:
        dz_dy[1:-1, :] = (routing_elevation_m[:-2, :] - routing_elevation_m[2:, :]) / (2.0 * spacing_m)
        dz_dy[0, :] = (routing_elevation_m[0, :] - routing_elevation_m[1, :]) / spacing_m
        dz_dy[-1, :] = (routing_elevation_m[-2, :] - routing_elevation_m[-1, :]) / spacing_m

    return np.hypot(dz_dx, dz_dy)


def continuous_routing_field(
    routing_elevation_m: np.ndarray,
    *,
    cell_size_km: float,
) -> ContinuousRoutingField:
    """Build deterministic low-bias MFD routing over all downslope neighbours.

    Core 0.2 Batch B2 uses Freeman-style slope-weighted multiple flow direction
    with fixed exponent p=1.1. The same flux fractions define both contributing
    area transport and the resultant continuous direction used by vector tracing.
    """
    _require_2d_finite("routing_elevation_m", routing_elevation_m)
    if not isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise HydrologyCapabilityError("cell_size_km must be finite and > 0")

    exponent = 1.1
    rows, columns = routing_elevation_m.shape
    fractions = np.zeros((rows, columns, len(_DIRS)), dtype=np.float64)
    angle = np.full((rows, columns), np.nan, dtype=np.float64)

    for row in range(rows):
        for column in range(columns):
            cell = (row, column)
            if _is_edge(cell, (rows, columns)):
                continue

            current = float(routing_elevation_m[cell])
            weights = np.zeros(len(_DIRS), dtype=np.float64)
            for direction, (delta_row, delta_column, vx, vy, _direction_angle) in enumerate(_DIRS):
                target = (row + delta_row, column + delta_column)
                target_elevation = float(routing_elevation_m[target])
                if not target_elevation < current:
                    continue
                distance = cell_size_km * hypot(vx, vy)
                slope = (current - target_elevation) / distance
                if slope > 0.0:
                    weights[direction] = slope ** exponent

            total = float(np.sum(weights))
            if not total > 0.0:
                raise HydrologyCapabilityError(
                    f"conditioned interior cell ({row},{column}) has no MFD downslope receiver"
                )
            fractions[cell] = weights / total

            resultant_x = 0.0
            resultant_y = 0.0
            for direction, fraction in enumerate(fractions[cell]):
                if fraction <= _EPS:
                    continue
                _, _, vx, vy, _direction_angle = _DIRS[direction]
                length = hypot(vx, vy)
                resultant_x += float(fraction) * vx / length
                resultant_y += float(fraction) * vy / length

            resultant_length = hypot(resultant_x, resultant_y)
            if resultant_length <= _EPS:
                # Deterministic fallback; np.argmax returns the first fixed-order
                # direction on exact ties.
                direction = int(np.argmax(fractions[cell]))
                angle[cell] = _DIRS[direction][4]
            else:
                angle[cell] = atan2(resultant_y, resultant_x) % _TWO_PI

    return ContinuousRoutingField(
        flow_angle_rad=angle,
        fractions=fractions,
        local_slope=_local_slope_field(
            routing_elevation_m,
            cell_size_km=cell_size_km,
        ),
    )

def _field_edges(field: ContinuousRoutingField, cell: Cell) -> tuple[tuple[Cell, float], ...]:
    rows, columns, directions = field.fractions.shape
    if directions != len(_DIRS):
        raise HydrologyCapabilityError("continuous MFD fractions must use eight directions")
    row, column = cell
    result: list[tuple[Cell, float]] = []
    for direction, fraction_value in enumerate(field.fractions[cell]):
        fraction = float(fraction_value)
        if fraction <= _EPS:
            continue
        delta_row, delta_column, *_ = _DIRS[direction]
        target = (row + delta_row, column + delta_column)
        if not (0 <= target[0] < rows and 0 <= target[1] < columns):
            raise HydrologyCapabilityError("continuous MFD fraction points outside domain")
        result.append((target, fraction))
    return tuple(result)

def _reaches_component(
    field: ContinuousRoutingField,
    start: Cell,
    component: set[Cell],
) -> bool:
    queue = [start]
    visited: set[Cell] = set()
    while queue:
        cell = queue.pop()
        if cell in component:
            return True
        if cell in visited:
            continue
        visited.add(cell)
        for receiver, _ in _field_edges(field, cell):
            if receiver not in visited:
                queue.append(receiver)
    return False


def choose_lake_outlets(
    terrain_elevation_m: np.ndarray,
    routing_elevation_m: np.ndarray,
    field: ContinuousRoutingField,
    lake_candidates: tuple[LakeCandidate, ...],
) -> tuple[LakeOutlet, ...]:
    shape = terrain_elevation_m.shape
    rows, columns = shape
    outlets: list[LakeOutlet] = []
    for index, candidate in enumerate(lake_candidates):
        lake_id = lake_feature_id(index)
        component = set(candidate.cells)
        choices: list[tuple[tuple[float, float, int, int, int, int], Cell, Cell, float]] = []
        for lake_cell in sorted(component):
            row, column = lake_cell
            for delta_row, delta_column, *_ in _DIRS:
                outside = (row + delta_row, column + delta_column)
                if not (0 <= outside[0] < rows and 0 <= outside[1] < columns):
                    continue
                if outside in component:
                    continue
                if not float(routing_elevation_m[outside]) < float(routing_elevation_m[lake_cell]):
                    continue
                if not _is_edge(outside, shape) and _reaches_component(field, outside, component):
                    continue
                saddle = max(
                    float(terrain_elevation_m[lake_cell]),
                    float(terrain_elevation_m[outside]),
                )
                key = (
                    saddle,
                    float(routing_elevation_m[outside]),
                    lake_cell[0],
                    lake_cell[1],
                    outside[0],
                    outside[1],
                )
                choices.append((key, lake_cell, outside, saddle))
        if not choices:
            raise HydrologyCapabilityError(f"accepted lake {lake_id!r} has no acyclic spill outlet")
        _, lake_cell, receiver_cell, saddle = min(choices, key=lambda item: item[0])
        outlets.append(
            LakeOutlet(
                lake_id=lake_id,
                lake_cell=lake_cell,
                receiver_cell=receiver_cell,
                saddle_elevation_m=saddle,
            )
        )
    return tuple(outlets)


def distributed_flow_accumulation_km2(
    field: ContinuousRoutingField,
    *,
    cell_size_km: float,
    lake_candidates: tuple[LakeCandidate, ...] = (),
    lake_outlets: tuple[LakeOutlet, ...] = (),
) -> np.ndarray:
    """Accumulate contributing area on a weighted DAG with lakes as routing supernodes."""
    if not isinstance(field.fractions, np.ndarray) or field.fractions.ndim != 3:
        raise HydrologyCapabilityError("continuous MFD fractions must be a 3D array")
    shape = field.flow_angle_rad.shape
    rows, columns = shape
    if field.fractions.shape != (rows, columns, len(_DIRS)):
        raise HydrologyCapabilityError("continuous MFD fractions must match routing shape")
    if not isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise HydrologyCapabilityError("cell_size_km must be finite and > 0")

    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    lake_index_by_id = {lake_feature_id(index): index for index in range(len(lake_candidates))}
    if len(lake_outlets) != len(lake_candidates):
        raise HydrologyCapabilityError("continuous routing requires exactly one outlet per accepted lake")
    outlet_by_id = {outlet.lake_id: outlet for outlet in lake_outlets}
    if set(outlet_by_id) != set(lake_index_by_id):
        raise HydrologyCapabilityError("lake outlet ids do not match accepted lakes")

    cell_count = rows * columns
    node_count = cell_count + len(lake_candidates)
    inactive = np.zeros(node_count, dtype=np.bool_)
    edges: list[list[tuple[int, float]]] = [[] for _ in range(node_count)]
    indegree = np.zeros(node_count, dtype=np.int32)
    initial = np.zeros(node_count, dtype=np.float64)
    cell_area = float(cell_size_km) * float(cell_size_km)
    outlet_receiver_to_lake = {
        outlet.receiver_cell: outlet.lake_id for outlet in lake_outlets
    }

    for row in range(rows):
        for column in range(columns):
            cell = (row, column)
            node = _flat_index(cell, columns)
            lake_id = lake_by_cell.get(cell)
            if lake_id is not None:
                inactive[node] = True
                continue
            initial[node] = cell_area
            combined: dict[int, float] = defaultdict(float)
            for receiver, fraction in _field_edges(field, cell):
                target_lake = lake_by_cell.get(receiver)
                # The chosen lake outlet receiver must not immediately route back into
                # the lake that just discharged into it; remove that return fraction and
                # renormalize remaining strictly-downstream flow below.
                source_lake = outlet_receiver_to_lake.get(cell)
                if target_lake is not None and target_lake == source_lake:
                    continue
                if target_lake is not None:
                    target = cell_count + lake_index_by_id[target_lake]
                else:
                    target = _flat_index(receiver, columns)
                combined[target] += fraction

            if combined:
                total = sum(combined.values())
                if total <= _EPS:
                    raise HydrologyCapabilityError("continuous outgoing fractions collapsed to zero")
                for target, fraction in sorted(combined.items()):
                    normalized = fraction / total
                    edges[node].append((target, normalized))
                    indegree[target] += 1
            elif not _is_edge(cell, shape):
                raise HydrologyCapabilityError("ordinary interior cell lost all continuous receivers")

    for index, candidate in enumerate(lake_candidates):
        lake_id = lake_feature_id(index)
        lake_node = cell_count + index
        initial[lake_node] = len(candidate.cells) * cell_area
        receiver = outlet_by_id[lake_id].receiver_cell
        target = _flat_index(receiver, columns)
        edges[lake_node].append((target, 1.0))
        indegree[target] += 1

    queue: list[int] = sorted(
        node for node in range(node_count) if not inactive[node] and indegree[node] == 0
    )
    accumulated = initial.copy()
    processed = 0
    while queue:
        node = queue.pop(0)
        processed += 1
        for target, fraction in edges[node]:
            accumulated[target] += accumulated[node] * fraction
            indegree[target] -= 1
            if indegree[target] == 0:
                # Stable insertion without depending on traversal order.
                insertion = 0
                while insertion < len(queue) and queue[insertion] < target:
                    insertion += 1
                queue.insert(insertion, target)

    active_count = int(np.count_nonzero(~inactive))
    if processed != active_count:
        raise HydrologyCapabilityError("continuous weighted routing graph contains a cycle")

    result = np.empty(shape, dtype=np.float64)
    for row in range(rows):
        for column in range(columns):
            cell = (row, column)
            lake_id = lake_by_cell.get(cell)
            if lake_id is None:
                result[cell] = accumulated[_flat_index(cell, columns)]
            else:
                result[cell] = accumulated[cell_count + lake_index_by_id[lake_id]]
    return result


def _dominant_channel_receiver_index(
    field: ContinuousRoutingField,
    accumulation: np.ndarray,
    channel_support: np.ndarray,
    *,
    lake_candidates: tuple[LakeCandidate, ...],
    lake_outlets: tuple[LakeOutlet, ...],
) -> np.ndarray:
    """Project diffuse MFD flux onto one deterministic receiver for channel topology."""
    shape = field.flow_angle_rad.shape
    if accumulation.shape != shape or channel_support.shape != shape:
        raise HydrologyCapabilityError("dominant channel projection arrays must share shape")

    rows, columns = shape
    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    outlet_receiver_to_lake = {
        outlet.receiver_cell: outlet.lake_id for outlet in lake_outlets
    }
    receiver_index = np.full(shape, -1, dtype=np.int32)

    for row in range(rows):
        for column in range(columns):
            cell = (row, column)
            if _is_edge(cell, shape) or cell in lake_by_cell:
                continue

            current_support = bool(channel_support[cell])
            source_lake = outlet_receiver_to_lake.get(cell)
            best_key: tuple[int, float, float, int] | None = None
            best_target: Cell | None = None

            for direction, fraction_value in enumerate(field.fractions[cell]):
                fraction = float(fraction_value)
                if fraction <= _EPS:
                    continue
                target = _neighbor(cell, direction, shape)
                if target is None:
                    continue
                target_lake = lake_by_cell.get(target)
                if source_lake is not None and target_lake == source_lake:
                    continue

                preferred = int(
                    target_lake is not None
                    or (current_support and bool(channel_support[target]))
                )
                transmitted_area = float(accumulation[cell]) * fraction
                target_area = float(accumulation[target])
                key = (preferred, transmitted_area, target_area, -direction)
                if best_key is None or key > best_key:
                    best_key = key
                    best_target = target

            if best_target is None:
                raise HydrologyCapabilityError(
                    f"ordinary interior cell ({row},{column}) lost dominant channel receiver"
                )
            receiver_index[cell] = np.int32(_flat_index(best_target, columns))

    return receiver_index


def _dominant_channel_area_km2(
    receiver_index: np.ndarray,
    *,
    cell_size_km: float,
    lake_candidates: tuple[LakeCandidate, ...],
) -> np.ndarray:
    """Accumulate unique upstream area on the single-receiver channel projection."""
    if receiver_index.ndim != 2:
        raise HydrologyCapabilityError("dominant receiver index must be a 2D array")
    shape = receiver_index.shape
    rows, columns = shape
    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    cell_count = rows * columns

    active = np.ones(cell_count, dtype=np.bool_)
    indegree = np.zeros(cell_count, dtype=np.int32)
    area = np.zeros(cell_count, dtype=np.float64)
    cell_area = float(cell_size_km) * float(cell_size_km)

    for row in range(rows):
        for column in range(columns):
            cell = (row, column)
            node = _flat_index(cell, columns)
            if cell in lake_by_cell:
                active[node] = False
                continue
            area[node] = cell_area
            target_index = int(receiver_index[cell])
            if target_index < 0:
                continue
            target = _cell_from_index(target_index, columns)
            if target in lake_by_cell:
                continue
            indegree[target_index] += 1

    queue = sorted(
        node for node in range(cell_count) if bool(active[node]) and int(indegree[node]) == 0
    )
    processed = 0
    while queue:
        node = queue.pop(0)
        processed += 1
        cell = _cell_from_index(node, columns)
        target_index = int(receiver_index[cell])
        if target_index < 0:
            continue
        target = _cell_from_index(target_index, columns)
        if target in lake_by_cell:
            continue
        area[target_index] += area[node]
        indegree[target_index] -= 1
        if indegree[target_index] == 0:
            insertion = 0
            while insertion < len(queue) and queue[insertion] < target_index:
                insertion += 1
            queue.insert(insertion, target_index)

    if processed != int(np.count_nonzero(active)):
        raise HydrologyCapabilityError("dominant channel projection contains a cycle")

    return area.reshape(shape)


def _mfd_incoming_fraction_sum(field: ContinuousRoutingField) -> np.ndarray:
    """Measure local MFD convergence as total fractional inflow from neighbours."""
    shape = field.flow_angle_rad.shape
    rows, columns = shape
    incoming = np.zeros(shape, dtype=np.float64)
    for row in range(rows):
        for column in range(columns):
            cell = (row, column)
            for target, fraction in _field_edges(field, cell):
                incoming[target] += float(fraction)
    return incoming


def _terrain_aware_initiation(
    field: ContinuousRoutingField,
    channel_area_km2: np.ndarray,
    *,
    stream_threshold_km2: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return convergence, area-slope score and normal-source eligibility."""
    if field.local_slope is None:
        raise HydrologyCapabilityError("terrain-aware initiation requires local_slope")
    if field.local_slope.shape != channel_area_km2.shape:
        raise HydrologyCapabilityError("local slope and channel area must share shape")

    convergence = _mfd_incoming_fraction_sum(field)
    slope = np.asarray(field.local_slope, dtype=np.float64)
    reference_slope = 0.05
    initiation_score = channel_area_km2 * (np.maximum(slope, 0.0) / reference_slope)
    eligible = (
        (initiation_score >= float(stream_threshold_km2))
        & (convergence > 1.0 + 1e-9)
    )
    return convergence, initiation_score, eligible


def _dominant_topological_order(
    receiver_index: np.ndarray,
    *,
    lake_candidates: tuple[LakeCandidate, ...],
) -> tuple[Cell, ...]:
    """Stable topological order for the single-downstream dominant graph."""
    shape = receiver_index.shape
    rows, columns = shape
    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    indegree = np.zeros(shape, dtype=np.int32)
    active_count = 0

    for row in range(rows):
        for column in range(columns):
            cell = (row, column)
            if cell in lake_by_cell:
                continue
            active_count += 1
            target_index = int(receiver_index[cell])
            if target_index < 0:
                continue
            target = _cell_from_index(target_index, columns)
            if target in lake_by_cell:
                continue
            indegree[target] += 1

    queue = sorted(
        (row, column)
        for row in range(rows)
        for column in range(columns)
        if (row, column) not in lake_by_cell and int(indegree[row, column]) == 0
    )
    order: list[Cell] = []
    while queue:
        cell = queue.pop(0)
        order.append(cell)
        target_index = int(receiver_index[cell])
        if target_index < 0:
            continue
        target = _cell_from_index(target_index, columns)
        if target in lake_by_cell:
            continue
        indegree[target] -= 1
        if indegree[target] == 0:
            insertion = 0
            while insertion < len(queue) and queue[insertion] < target:
                insertion += 1
            queue.insert(insertion, target)

    if len(order) != active_count:
        raise HydrologyCapabilityError("dominant channel projection contains a cycle")
    return tuple(order)


def _activate_channel_skeleton(
    receiver_index: np.ndarray,
    eligible: np.ndarray,
    *,
    lake_candidates: tuple[LakeCandidate, ...],
    lake_outlets: tuple[LakeOutlet, ...],
) -> tuple[np.ndarray, set[Cell], set[Cell]]:
    """Activate eligible headwaters once, then propagate merge-only channels downstream."""
    shape = receiver_index.shape
    rows, columns = shape
    if eligible.shape != shape:
        raise HydrologyCapabilityError("source eligibility must match dominant graph shape")
    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    outlet_receiver_cells = {outlet.receiver_cell for outlet in lake_outlets}
    order = _dominant_topological_order(
        receiver_index,
        lake_candidates=lake_candidates,
    )

    skeleton = np.zeros(shape, dtype=np.bool_)
    active_upstream = np.zeros(shape, dtype=np.int32)
    sources: set[Cell] = set()

    for cell in order:
        if cell in lake_by_cell:
            continue
        is_outlet_start = cell in outlet_receiver_cells
        has_active_upstream = int(active_upstream[cell]) > 0
        starts_here = (
            bool(eligible[cell])
            and not has_active_upstream
            and not is_outlet_start
            and not _is_edge(cell, shape)
        )
        is_active = has_active_upstream or is_outlet_start or starts_here
        if not is_active:
            continue

        skeleton[cell] = True
        if starts_here:
            sources.add(cell)

        target_index = int(receiver_index[cell])
        if target_index < 0:
            continue
        target = _cell_from_index(target_index, columns)
        if target in lake_by_cell:
            continue
        active_upstream[target] += 1

    skeleton_indegree = np.zeros(shape, dtype=np.int32)
    for row in range(rows):
        for column in range(columns):
            cell = (row, column)
            if not bool(skeleton[cell]):
                continue
            target_index = int(receiver_index[cell])
            if target_index < 0:
                continue
            target = _cell_from_index(target_index, columns)
            if bool(skeleton[target]):
                skeleton_indegree[target] += 1

    for outlet in lake_outlets:
        if bool(skeleton[outlet.receiver_cell]):
            skeleton_indegree[outlet.receiver_cell] += 1

    confluences = {
        (row, column)
        for row in range(rows)
        for column in range(columns)
        if bool(skeleton[row, column])
        and int(skeleton_indegree[row, column]) >= 2
        and (row, column) not in lake_by_cell
    }
    sources.difference_update(confluences)
    return skeleton, sources, confluences


def _build_channel_skeleton(
    plan: GenerationPlan,
    field: ContinuousRoutingField,
    accumulation: np.ndarray,
    channel_support: np.ndarray,
    lake_candidates: tuple[LakeCandidate, ...],
    lake_outlets: tuple[LakeOutlet, ...],
) -> _ChannelSkeleton:
    """Extract terrain-aware one-cell-wide channel topology from diffuse MFD transport."""
    shape = channel_support.shape
    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    receiver_index = _dominant_channel_receiver_index(
        field,
        accumulation,
        channel_support,
        lake_candidates=lake_candidates,
        lake_outlets=lake_outlets,
    )
    channel_area = _dominant_channel_area_km2(
        receiver_index,
        cell_size_km=plan.grid.cell_size_km,
        lake_candidates=lake_candidates,
    )

    convergence, initiation_score, eligible = _terrain_aware_initiation(
        field,
        channel_area,
        stream_threshold_km2=plan.hydrology.stream_threshold_km2,
    )
    eligible = eligible.copy()
    for cell in lake_by_cell:
        eligible[cell] = False

    skeleton, source_cells, confluence_cells = _activate_channel_skeleton(
        receiver_index,
        eligible,
        lake_candidates=lake_candidates,
        lake_outlets=lake_outlets,
    )

    return _ChannelSkeleton(
        receiver_index=receiver_index,
        channel_area_km2=channel_area,
        convergence=convergence,
        initiation_score_km2=initiation_score,
        mask=skeleton,
        sources=frozenset(source_cells),
        confluences=frozenset(confluence_cells),
    )


def _sample_vector(
    field: ContinuousRoutingField,
    adapter: GridAdapter,
    x_km: float,
    y_km: float,
) -> tuple[float, float] | None:
    cell_size = adapter.cell_size_km
    column_f = x_km / cell_size - 0.5
    row_f = (adapter.height_km - y_km) / cell_size - 0.5
    c0 = int(np.floor(column_f))
    r0 = int(np.floor(row_f))
    tx = column_f - c0
    ty = row_f - r0

    weighted_x = 0.0
    weighted_y = 0.0
    total = 0.0
    for dr, wy in ((0, 1.0 - ty), (1, ty)):
        for dc, wx in ((0, 1.0 - tx), (1, tx)):
            row = min(adapter.rows - 1, max(0, r0 + dr))
            column = min(adapter.columns - 1, max(0, c0 + dc))
            angle = float(field.flow_angle_rad[row, column])
            weight = max(0.0, wx * wy)
            if weight <= _EPS or not isfinite(angle):
                continue
            weighted_x += weight * cos(angle)
            weighted_y += weight * sin(angle)
            total += weight
    if total <= _EPS:
        return None
    length = hypot(weighted_x, weighted_y)
    if length <= _EPS:
        return None
    return weighted_x / length, weighted_y / length


def _boundary_intersection(
    x: float,
    y: float,
    dx: float,
    dy: float,
    adapter: GridAdapter,
) -> tuple[WorldPoint, BoundarySide]:
    candidates: list[tuple[float, WorldPoint, BoundarySide]] = []
    if dx > _EPS:
        t = (adapter.width_km - x) / dx
        yy = y + t * dy
        if t >= 0.0 and -_EPS <= yy <= adapter.height_km + _EPS:
            candidates.append((t, WorldPoint(x_km=adapter.width_km, y_km=min(adapter.height_km, max(0.0, yy))), BoundarySide.EAST))
    if dx < -_EPS:
        t = (0.0 - x) / dx
        yy = y + t * dy
        if t >= 0.0 and -_EPS <= yy <= adapter.height_km + _EPS:
            candidates.append((t, WorldPoint(x_km=0.0, y_km=min(adapter.height_km, max(0.0, yy))), BoundarySide.WEST))
    if dy > _EPS:
        t = (adapter.height_km - y) / dy
        xx = x + t * dx
        if t >= 0.0 and -_EPS <= xx <= adapter.width_km + _EPS:
            candidates.append((t, WorldPoint(x_km=min(adapter.width_km, max(0.0, xx)), y_km=adapter.height_km), BoundarySide.NORTH))
    if dy < -_EPS:
        t = (0.0 - y) / dy
        xx = x + t * dx
        if t >= 0.0 and -_EPS <= xx <= adapter.width_km + _EPS:
            candidates.append((t, WorldPoint(x_km=min(adapter.width_km, max(0.0, xx)), y_km=0.0), BoundarySide.SOUTH))
    if not candidates:
        raise HydrologyCapabilityError("continuous trace cannot intersect domain boundary")
    _, point, side = min(candidates, key=lambda item: (item[0], item[2].value))
    return point, side


def _lake_boundary_point(
    adapter: GridAdapter,
    start: tuple[float, float],
    end: tuple[float, float],
    lake_by_cell: dict[Cell, str],
) -> WorldPoint:
    ax, ay = start
    bx, by = end
    for _ in range(40):
        mx = (ax + bx) / 2.0
        my = (ay + by) / 2.0
        cell = adapter.containing_cell(
            min(adapter.width_km, max(0.0, mx)),
            min(adapter.height_km, max(0.0, my)),
        )
        if cell in lake_by_cell:
            bx, by = mx, my
        else:
            ax, ay = mx, my
    return WorldPoint(x_km=(ax + bx) / 2.0, y_km=(ay + by) / 2.0)


def _trace_continuous(
    *,
    adapter: GridAdapter,
    field: ContinuousRoutingField,
    accumulation: np.ndarray,
    start_position: WorldPoint,
    start_cell: Cell,
    confluence_cells: set[Cell],
    lake_by_cell: dict[Cell, str],
) -> _TraceResult:
    step = adapter.cell_size_km * 0.22
    max_steps = max(200, (adapter.rows + adapter.columns) * 40)
    points: list[WorldPoint] = [start_position]
    traversed: list[Cell] = [start_cell]
    x = float(start_position.x_km)
    y = float(start_position.y_km)
    cell = start_cell
    max_catchment = float(accumulation[cell])

    # Lake outlet starts exactly on a boundary between two cells. Nudge the numeric
    # integrator into the declared start cell without changing the serialized endpoint.
    center = adapter.cell_center(*start_cell)
    if hypot(center.x_km - x, center.y_km - y) > adapter.cell_size_km * 0.4:
        x = x + (center.x_km - x) * 1e-6
        y = y + (center.y_km - y) * 1e-6

    for _ in range(max_steps):
        if _is_edge(cell, (adapter.rows, adapter.columns)):
            vector = _sample_vector(field, adapter, x, y)
            if vector is None:
                center_point = adapter.cell_center(*cell)
                dx = center_point.x_km - x
                dy = center_point.y_km - y
                if abs(dx) + abs(dy) <= _EPS:
                    if cell[0] == 0:
                        dx, dy = 0.0, 1.0
                    elif cell[1] == adapter.columns - 1:
                        dx, dy = 1.0, 0.0
                    elif cell[0] == adapter.rows - 1:
                        dx, dy = 0.0, -1.0
                    else:
                        dx, dy = -1.0, 0.0
            else:
                dx, dy = vector
            boundary, side = _boundary_intersection(x, y, dx, dy, adapter)
            if points[-1] != boundary:
                points.append(boundary)
            return _TraceResult(
                points=tuple(points),
                terminal=_TraceTerminal(kind="domain_outlet", position=boundary, boundary_side=side),
                traversed_cells=tuple(dict.fromkeys(traversed)),
                catchment_area_km2=max_catchment,
            )

        vector = _sample_vector(field, adapter, x, y)
        if vector is None:
            raise HydrologyCapabilityError("continuous trace lost downstream vector inside domain")
        dx, dy = vector
        nx = x + dx * step
        ny = y + dy * step
        if nx < 0.0 or nx > adapter.width_km or ny < 0.0 or ny > adapter.height_km:
            boundary, side = _boundary_intersection(x, y, dx, dy, adapter)
            points.append(boundary)
            return _TraceResult(
                points=tuple(points),
                terminal=_TraceTerminal(kind="domain_outlet", position=boundary, boundary_side=side),
                traversed_cells=tuple(dict.fromkeys(traversed)),
                catchment_area_km2=max_catchment,
            )

        next_cell = adapter.containing_cell(nx, ny)
        target_lake = lake_by_cell.get(next_cell)
        if target_lake is not None and next_cell != start_cell:
            boundary = _lake_boundary_point(adapter, (x, y), (nx, ny), lake_by_cell)
            points.append(boundary)
            return _TraceResult(
                points=tuple(points),
                terminal=_TraceTerminal(
                    kind="lake_inflow",
                    position=boundary,
                    feature_id=target_lake,
                ),
                traversed_cells=tuple(dict.fromkeys(traversed)),
                catchment_area_km2=max_catchment,
            )

        if next_cell != start_cell and next_cell in confluence_cells:
            center_point = adapter.cell_center(*next_cell)
            target = WorldPoint(x_km=center_point.x_km, y_km=center_point.y_km)
            points.append(target)
            max_catchment = max(max_catchment, float(accumulation[next_cell]))
            traversed.append(next_cell)
            return _TraceResult(
                points=tuple(points),
                terminal=_TraceTerminal(
                    kind="confluence",
                    position=target,
                    anchor_cell=next_cell,
                ),
                traversed_cells=tuple(dict.fromkeys(traversed)),
                catchment_area_km2=max_catchment,
            )

        x, y = nx, ny
        if hypot(points[-1].x_km - x, points[-1].y_km - y) >= step * 0.9:
            points.append(WorldPoint(x_km=x, y_km=y))
        if next_cell != cell:
            traversed.append(next_cell)
            cell = next_cell
            max_catchment = max(max_catchment, float(accumulation[cell]))

    raise HydrologyCapabilityError("continuous river trace exceeded deterministic step budget")


def _node_sort_key(node: _NodeDescriptor) -> tuple[object, ...]:
    return (
        node.kind.value,
        node.position.x_km,
        node.position.y_km,
        node.boundary_side.value if node.boundary_side is not None else "",
        node.feature_id or "",
    )


def _outlet_position(adapter: GridAdapter, outlet: LakeOutlet) -> WorldPoint:
    lake_center = adapter.cell_center(*outlet.lake_cell)
    receiver_center = adapter.cell_center(*outlet.receiver_cell)
    return WorldPoint(
        x_km=(lake_center.x_km + receiver_center.x_km) / 2.0,
        y_km=(lake_center.y_km + receiver_center.y_km) / 2.0,
    )


def build_continuous_river_network(
    plan: GenerationPlan,
    field: ContinuousRoutingField,
    accumulation: np.ndarray,
    channel_support: np.ndarray,
    lake_candidates: tuple[LakeCandidate, ...],
    lake_outlets: tuple[LakeOutlet, ...],
) -> tuple[RiverNetwork, np.ndarray]:
    shape = (plan.grid.rows, plan.grid.columns)
    if accumulation.shape != shape or channel_support.shape != shape:
        raise HydrologyCapabilityError("continuous network arrays must match plan grid")
    if channel_support.dtype != np.dtype(np.bool_):
        raise HydrologyCapabilityError("channel support must use bool dtype")

    adapter = GridAdapter.from_plan(plan)
    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    skeleton = _build_channel_skeleton(
        plan,
        field,
        accumulation,
        channel_support,
        lake_candidates,
        lake_outlets,
    )
    source_cells = set(skeleton.sources)
    confluence_cells = set(skeleton.confluences)

    descriptors: dict[tuple[object, ...], _NodeDescriptor] = {}
    for cell in sorted(source_cells):
        point = adapter.cell_center(*cell)
        descriptor = _NodeDescriptor(
            key=("source", cell[0], cell[1]),
            kind=RiverNodeKind.SOURCE,
            position=WorldPoint(x_km=point.x_km, y_km=point.y_km),
            anchor_cell=cell,
        )
        descriptors[descriptor.key] = descriptor
    for cell in sorted(confluence_cells):
        point = adapter.cell_center(*cell)
        descriptor = _NodeDescriptor(
            key=("confluence", cell[0], cell[1]),
            kind=RiverNodeKind.CONFLUENCE,
            position=WorldPoint(x_km=point.x_km, y_km=point.y_km),
            anchor_cell=cell,
        )
        descriptors[descriptor.key] = descriptor
    for outlet in lake_outlets:
        descriptor = _NodeDescriptor(
            key=("lake_outlet", outlet.lake_id),
            kind=RiverNodeKind.LAKE_OUTLET,
            position=_outlet_position(adapter, outlet),
            feature_id=outlet.lake_id,
            anchor_cell=outlet.receiver_cell,
        )
        descriptors[descriptor.key] = descriptor

    starts = sorted(
        (descriptor for descriptor in descriptors.values() if descriptor.kind in {RiverNodeKind.SOURCE, RiverNodeKind.CONFLUENCE, RiverNodeKind.LAKE_OUTLET}),
        key=_node_sort_key,
    )
    trace_records: list[tuple[_NodeDescriptor, _NodeDescriptor, tuple[WorldPoint, ...], float, tuple[Cell, ...]]] = []

    for start in starts:
        assert start.anchor_cell is not None

        if start.kind is RiverNodeKind.LAKE_OUTLET and start.anchor_cell in confluence_cells:
            key = ("confluence", start.anchor_cell[0], start.anchor_cell[1])
            target = descriptors[key]
            points = (start.position, target.position)
            trace_records.append(
                (
                    start,
                    target,
                    points,
                    float(accumulation[start.anchor_cell]),
                    (start.anchor_cell,),
                )
            )
            continue

        trace = _trace_continuous(
            adapter=adapter,
            field=field,
            accumulation=accumulation,
            start_position=start.position,
            start_cell=start.anchor_cell,
            confluence_cells=confluence_cells - {start.anchor_cell},
            lake_by_cell=lake_by_cell,
        )
        terminal = trace.terminal
        if terminal.kind == "confluence":
            assert terminal.anchor_cell is not None
            key = ("confluence", terminal.anchor_cell[0], terminal.anchor_cell[1])
        elif terminal.kind == "lake_inflow":
            assert terminal.feature_id is not None
            key = (
                "lake_inflow",
                terminal.feature_id,
                round(terminal.position.x_km, 9),
                round(terminal.position.y_km, 9),
            )
            descriptors.setdefault(
                key,
                _NodeDescriptor(
                    key=key,
                    kind=RiverNodeKind.LAKE_INFLOW,
                    position=terminal.position,
                    feature_id=terminal.feature_id,
                ),
            )
        else:
            assert terminal.boundary_side is not None
            key = (
                "domain_outlet",
                terminal.boundary_side.value,
                round(terminal.position.x_km, 9),
                round(terminal.position.y_km, 9),
            )
            descriptors.setdefault(
                key,
                _NodeDescriptor(
                    key=key,
                    kind=RiverNodeKind.DOMAIN_OUTLET,
                    position=terminal.position,
                    boundary_side=terminal.boundary_side,
                ),
            )
        target = descriptors[key]
        if start.key == target.key:
            raise HydrologyCapabilityError("continuous river segment cannot terminate at its start node")
        trace_records.append((start, target, trace.points, trace.catchment_area_km2, trace.traversed_cells))

    ordered_descriptors = sorted(descriptors.values(), key=_node_sort_key)
    node_id_by_key = {
        descriptor.key: f"river-node-{index:04d}"
        for index, descriptor in enumerate(ordered_descriptors, start=1)
    }
    nodes = {
        node_id_by_key[descriptor.key]: RiverNode(
            kind=descriptor.kind,
            position=descriptor.position,
            boundary_side=descriptor.boundary_side,
            feature_id=descriptor.feature_id,
        )
        for descriptor in ordered_descriptors
    }

    trace_records.sort(
        key=lambda item: (
            node_id_by_key[item[0].key],
            node_id_by_key[item[1].key],
            tuple((point.x_km, point.y_km) for point in item[2]),
        )
    )
    segments = {
        f"river-segment-{index:04d}": RiverSegment(
            **{
                "from": node_id_by_key[start.key],
                "to": node_id_by_key[target.key],
            },
            centerline=points,
            properties=RiverSegmentProperties(catchment_area_km2=catchment),
        )
        for index, (start, target, points, catchment, _) in enumerate(trace_records, start=1)
    }

    stream_mask = np.zeros(shape, dtype=np.bool_)
    for _, _, _, _, cells in trace_records:
        for cell in cells:
            if cell not in lake_by_cell:
                stream_mask[cell] = True
    for cell in source_cells | confluence_cells:
        stream_mask[cell] = True
    for outlet in lake_outlets:
        stream_mask[outlet.receiver_cell] = True

    return RiverNetwork(nodes=nodes, segments=segments), stream_mask


def _legacy_direction_projection(field: ContinuousRoutingField) -> np.ndarray:
    """Compatibility-only D8 projection; never used as 0.2 routing authority."""
    shape = field.flow_angle_rad.shape
    rows, columns = shape
    result = np.full(shape, -1, dtype=np.int8)
    for row in range(rows):
        for column in range(columns):
            if _is_edge((row, column), shape):
                continue
            fractions = field.fractions[row, column]
            if float(np.sum(fractions)) <= _EPS:
                continue
            result[row, column] = np.int8(int(np.argmax(fractions)))
    return result

def generate_hydrology_v02(plan: GenerationPlan, terrain: TerrainState) -> HydrologyState:
    if plan.plan_version != "0.2":
        raise HydrologyCapabilityError("continuous hydrology requires GenerationPlan 0.2")
    elevation = terrain.elevation_m
    expected_shape = (plan.grid.rows, plan.grid.columns)
    if not isinstance(elevation, np.ndarray) or elevation.shape != expected_shape:
        raise HydrologyCapabilityError("terrain elevation shape must match plan grid")
    if not np.isfinite(elevation).all():
        raise HydrologyCapabilityError("terrain elevation must contain only finite values")

    surfaces = priority_flood_surfaces(elevation)
    field = continuous_routing_field(
        surfaces.routing_elevation_m,
        cell_size_km=plan.grid.cell_size_km,
    )
    lakes = extract_lake_candidates(
        elevation,
        surfaces.fill_elevation_m,
        cell_size_km=plan.grid.cell_size_km,
        lake_min_area_km2=plan.hydrology.lake_min_area_km2,
        lake_min_depth_m=plan.hydrology.lake_min_depth_m,
    )
    outlets = choose_lake_outlets(
        elevation,
        surfaces.routing_elevation_m,
        field,
        lakes,
    )
    accumulation = distributed_flow_accumulation_km2(
        field,
        cell_size_km=plan.grid.cell_size_km,
        lake_candidates=lakes,
        lake_outlets=outlets,
    )
    lake_by_cell = accepted_lake_cell_map(expected_shape, lakes)
    support = classify_stream_mask(
        accumulation,
        stream_threshold_km2=plan.hydrology.stream_threshold_km2,
    )
    if lake_by_cell:
        for cell in lake_by_cell:
            support[cell] = False

    lake_features = materialize_lake_features(plan, lakes)
    channel_skeleton = _build_channel_skeleton(
        plan,
        field,
        accumulation,
        support,
        lakes,
        outlets,
    )
    river_network, stream_mask = build_continuous_river_network(
        plan,
        field,
        accumulation,
        support,
        lakes,
        outlets,
    )
    validate_river_lake_references(river_network, lake_features)
    water_depth = build_water_depth_m(
        elevation,
        surfaces.fill_elevation_m,
        accumulation,
        stream_mask,
        lakes,
        stream_threshold_km2=plan.hydrology.stream_threshold_km2,
        river_depth_at_threshold_m=plan.hydrology.river_depth_at_threshold_m,
        river_depth_exponent=plan.hydrology.river_depth_exponent,
    )
    return HydrologyState(
        routing_elevation_m=surfaces.routing_elevation_m,
        fill_elevation_m=surfaces.fill_elevation_m,
        flow_direction=_legacy_direction_projection(field),
        flow_accumulation_km2=accumulation,
        stream_mask=stream_mask,
        lake_candidates=lakes,
        lake_features=lake_features,
        river_network=river_network,
        water_depth_m=water_depth,
        routing_mode="continuous",
        continuous_routing=field,
        channel_support_mask=support,
        channel_skeleton_mask=channel_skeleton.mask,
        channel_unique_area_km2=channel_skeleton.channel_area_km2,
        channel_convergence=channel_skeleton.convergence,
        channel_initiation_score_km2=channel_skeleton.initiation_score_km2,
        lake_outlets=outlets,
    )


def _network_invariants(network: RiverNetwork) -> bool:
    indegree = {node_id: 0 for node_id in network.nodes}
    outdegree = {node_id: 0 for node_id in network.nodes}
    adjacency: dict[str, list[str]] = defaultdict(list)
    for segment in network.segments.values():
        indegree[segment.to_node] += 1
        outdegree[segment.from_node] += 1
        adjacency[segment.from_node].append(segment.to_node)
        if len(segment.centerline) < 2:
            return False
        if segment.centerline[0] != network.nodes[segment.from_node].position:
            return False
        if segment.centerline[-1] != network.nodes[segment.to_node].position:
            return False

    for node_id, node in network.nodes.items():
        if node.kind is RiverNodeKind.SOURCE and indegree[node_id] != 0:
            return False
        if node.kind is RiverNodeKind.CONFLUENCE and indegree[node_id] < 2:
            return False
        if node.kind is RiverNodeKind.DOMAIN_OUTLET and outdegree[node_id] != 0:
            return False
        if node.kind not in {RiverNodeKind.DOMAIN_OUTLET, RiverNodeKind.LAKE_INFLOW} and outdegree[node_id] > 1:
            return False

    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(node_id: str) -> bool:
        if node_id in permanent:
            return True
        if node_id in temporary:
            return False
        temporary.add(node_id)
        for target in adjacency[node_id]:
            if not visit(target):
                return False
        temporary.remove(node_id)
        permanent.add(node_id)
        return True

    return all(visit(node_id) for node_id in network.nodes)


def validate_hydrology_v02(
    plan: GenerationPlan,
    terrain: TerrainState | None,
    hydrology: HydrologyState | None,
    *,
    attempt_index: int,
) -> ValidationResult:
    shape = (plan.grid.rows, plan.grid.columns)
    cell_area = plan.grid.cell_size_km * plan.grid.cell_size_km
    terrain_ok = (
        terrain is not None
        and isinstance(terrain.elevation_m, np.ndarray)
        and terrain.elevation_m.shape == shape
        and bool(np.isfinite(terrain.elevation_m).all())
    )
    state_ok = hydrology is not None and hydrology.routing_mode == "continuous"
    field = hydrology.continuous_routing if hydrology is not None else None
    field_shapes = False
    fractions_valid = False
    receivers_lower = False
    angles_valid = False
    if state_ok and field is not None:
        field_shapes = (
            isinstance(field.flow_angle_rad, np.ndarray)
            and field.flow_angle_rad.shape == shape
            and isinstance(field.fractions, np.ndarray)
            and field.fractions.shape == (shape[0], shape[1], len(_DIRS))
            and isinstance(field.local_slope, np.ndarray)
            and field.local_slope.shape == shape
        )
        if field_shapes:
            finite_fraction = bool(np.isfinite(field.fractions).all())
            nonnegative = bool(np.all(field.fractions >= 0.0))
            sums = np.sum(field.fractions, axis=2)
            edge = np.zeros(shape, dtype=np.bool_)
            edge[0, :] = edge[-1, :] = True
            edge[:, 0] = edge[:, -1] = True
            fractions_valid = (
                finite_fraction
                and nonnegative
                and bool(np.allclose(sums[~edge], 1.0, atol=1e-12, rtol=0.0))
                and bool(np.allclose(sums[edge], 0.0, atol=1e-12, rtol=0.0))
            )
            angles_valid = (
                bool(np.all((field.flow_angle_rad[~edge] >= 0.0) & (field.flow_angle_rad[~edge] < _TWO_PI)))
                and bool(np.isnan(field.flow_angle_rad[edge]).all())
            )
            receivers_lower = True
            if hydrology is not None:
                for row in range(shape[0]):
                    for column in range(shape[1]):
                        cell = (row, column)
                        for receiver, fraction in _field_edges(field, cell):
                            if fraction > _EPS and not hydrology.routing_elevation_m[receiver] < hydrology.routing_elevation_m[cell]:
                                receivers_lower = False
                                break
                        if not receivers_lower:
                            break
                    if not receivers_lower:
                        break

    accumulation_ok = False
    support_ok = False
    skeleton_ok = False
    lakes_ok = False
    network_ok = False
    water_ok = False
    if state_ok and hydrology is not None:
        accumulation_ok = (
            hydrology.flow_accumulation_km2.shape == shape
            and hydrology.flow_accumulation_km2.dtype == np.dtype(np.float64)
            and bool(np.isfinite(hydrology.flow_accumulation_km2).all())
            and bool(np.all(hydrology.flow_accumulation_km2 >= cell_area - 1e-10))
        )
        lake_by_cell = accepted_lake_cell_map(shape, hydrology.lake_candidates)
        if hydrology.channel_support_mask is not None and hydrology.channel_support_mask.shape == shape:
            expected_support = hydrology.flow_accumulation_km2 >= plan.hydrology.stream_threshold_km2
            for cell in lake_by_cell:
                expected_support[cell] = False
            support_ok = hydrology.channel_support_mask.dtype == np.dtype(np.bool_) and np.array_equal(hydrology.channel_support_mask, expected_support)
        if hydrology.channel_skeleton_mask is not None:
            diagnostic_arrays_ok = (
                hydrology.channel_unique_area_km2 is not None
                and hydrology.channel_unique_area_km2.shape == shape
                and np.isfinite(hydrology.channel_unique_area_km2).all()
                and hydrology.channel_convergence is not None
                and hydrology.channel_convergence.shape == shape
                and np.isfinite(hydrology.channel_convergence).all()
                and hydrology.channel_initiation_score_km2 is not None
                and hydrology.channel_initiation_score_km2.shape == shape
                and np.isfinite(hydrology.channel_initiation_score_km2).all()
            )
            skeleton_ok = (
                hydrology.channel_skeleton_mask.shape == shape
                and hydrology.channel_skeleton_mask.dtype == np.dtype(np.bool_)
                and all(not bool(hydrology.channel_skeleton_mask[cell]) for cell in lake_by_cell)
                and diagnostic_arrays_ok
            )
        lakes_ok = (
            len(hydrology.lake_outlets) == len(hydrology.lake_candidates)
            and len({outlet.lake_id for outlet in hydrology.lake_outlets}) == len(hydrology.lake_candidates)
        )
        network_ok = _network_invariants(hydrology.river_network)
        water_ok = (
            hydrology.water_depth_m.shape == shape
            and hydrology.water_depth_m.dtype == np.dtype(np.float32)
            and bool(np.isfinite(hydrology.water_depth_m).all())
            and bool(np.all(hydrology.water_depth_m >= 0.0))
        )

    results = (
        EngineInvariantResult(id="hydrology-v02-upstream-terrain-valid", passed=terrain_ok),
        EngineInvariantResult(id="hydrology-v02-continuous-state-exists", passed=state_ok),
        EngineInvariantResult(id="hydrology-v02-routing-field-shapes", passed=field_shapes),
        EngineInvariantResult(id="hydrology-v02-routing-fractions-valid", passed=fractions_valid),
        EngineInvariantResult(id="hydrology-v02-routing-angles-valid", passed=angles_valid),
        EngineInvariantResult(id="hydrology-v02-receivers-strictly-lower", passed=receivers_lower),
        EngineInvariantResult(id="hydrology-v02-distributed-accumulation-valid", passed=accumulation_ok),
        EngineInvariantResult(id="hydrology-v02-channel-support-threshold", passed=support_ok),
        EngineInvariantResult(id="hydrology-v02-channel-skeleton-valid", passed=skeleton_ok),
        EngineInvariantResult(id="hydrology-v02-single-lake-outlet", passed=lakes_ok),
        EngineInvariantResult(id="hydrology-v02-river-network-invariants", passed=network_ok),
        EngineInvariantResult(id="hydrology-v02-water-depth-valid", passed=water_ok),
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


__all__ = [
    "build_continuous_river_network",
    "choose_lake_outlets",
    "continuous_routing_field",
    "distributed_flow_accumulation_km2",
    "generate_hydrology_v02",
    "validate_hydrology_v02",
]
