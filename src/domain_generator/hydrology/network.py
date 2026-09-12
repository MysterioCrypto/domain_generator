from __future__ import annotations

from dataclasses import dataclass

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
from ..grid import GridAdapter
from .routing import D8_DIRECTIONS, HydrologyCapabilityError
from .state import LakeCandidate
from .water import accepted_lake_cell_map


Cell = tuple[int, int]


@dataclass(frozen=True, slots=True)
class _NodeDescriptor:
    key: tuple[object, ...]
    kind: RiverNodeKind
    position: WorldPoint
    boundary_side: BoundarySide | None = None
    feature_id: str | None = None


def _world_point(adapter: GridAdapter, cell: Cell) -> WorldPoint:
    point = adapter.cell_center(*cell)
    return WorldPoint(x_km=point.x_km, y_km=point.y_km)


def _midpoint(adapter: GridAdapter, first: Cell, second: Cell) -> WorldPoint:
    a = adapter.cell_center(*first)
    b = adapter.cell_center(*second)
    return WorldPoint(x_km=(a.x_km + b.x_km) / 2.0, y_km=(a.y_km + b.y_km) / 2.0)


def _receiver(flow_direction: np.ndarray, cell: Cell) -> Cell | None:
    row, column = cell
    code = int(flow_direction[cell])
    if code == -1:
        return None
    if not 0 <= code < len(D8_DIRECTIONS):
        raise HydrologyCapabilityError("flow_direction contains invalid D8 code")
    delta_row, delta_column, _ = D8_DIRECTIONS[code]
    receiver = (row + delta_row, column + delta_column)
    rows, columns = flow_direction.shape
    if not (0 <= receiver[0] < rows and 0 <= receiver[1] < columns):
        raise HydrologyCapabilityError("non-outlet D8 receiver is outside domain")
    return receiver


def _domain_outlet_descriptor(adapter: GridAdapter, cell: Cell) -> _NodeDescriptor:
    row, column = cell
    center = adapter.cell_center(row, column)
    if row == 0:
        side = BoundarySide.NORTH
        position = WorldPoint(x_km=center.x_km, y_km=adapter.height_km)
    elif column == adapter.columns - 1:
        side = BoundarySide.EAST
        position = WorldPoint(x_km=adapter.width_km, y_km=center.y_km)
    elif row == adapter.rows - 1:
        side = BoundarySide.SOUTH
        position = WorldPoint(x_km=center.x_km, y_km=0.0)
    elif column == 0:
        side = BoundarySide.WEST
        position = WorldPoint(x_km=0.0, y_km=center.y_km)
    else:
        raise HydrologyCapabilityError("domain outlet can only originate from an edge cell")
    return _NodeDescriptor(
        key=("domain_outlet", row, column, side.value),
        kind=RiverNodeKind.DOMAIN_OUTLET,
        position=position,
        boundary_side=side,
    )


def _node_sort_key(node: _NodeDescriptor) -> tuple[object, ...]:
    return (
        node.kind.value,
        node.position.x_km,
        node.position.y_km,
        node.boundary_side.value if node.boundary_side is not None else "",
        node.feature_id or "",
    )


def build_river_network(
    plan: GenerationPlan,
    flow_direction: np.ndarray,
    flow_accumulation_km2: np.ndarray,
    stream_mask: np.ndarray,
    lake_candidates: tuple[LakeCandidate, ...],
) -> RiverNetwork:
    shape = (plan.grid.rows, plan.grid.columns)
    for name, array in (
        ("flow_direction", flow_direction),
        ("flow_accumulation_km2", flow_accumulation_km2),
        ("stream_mask", stream_mask),
    ):
        if not isinstance(array, np.ndarray) or array.shape != shape:
            raise HydrologyCapabilityError(f"{name} must match plan grid")
    if flow_direction.dtype != np.dtype(np.int8):
        raise HydrologyCapabilityError("flow_direction must use int8 dtype")
    if stream_mask.dtype != np.dtype(np.bool_):
        raise HydrologyCapabilityError("stream_mask must use bool dtype")
    if not np.isfinite(flow_accumulation_km2).all():
        raise HydrologyCapabilityError("flow accumulation must be finite")

    adapter = GridAdapter.from_plan(plan)
    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    outside_stream_cells: tuple[Cell, ...] = tuple(
        (row, column)
        for row in range(shape[0])
        for column in range(shape[1])
        if bool(stream_mask[row, column]) and (row, column) not in lake_by_cell
    )
    outside_stream_set = set(outside_stream_cells)

    ordinary_indegree = {cell: 0 for cell in outside_stream_cells}
    for cell in outside_stream_cells:
        receiver = _receiver(flow_direction, cell)
        if receiver is None or receiver in lake_by_cell:
            continue
        if receiver not in outside_stream_set:
            raise HydrologyCapabilityError("stream cell drains to non-stream cell outside accepted lake")
        ordinary_indegree[receiver] += 1

    # descriptor, last lake cell before exit, first outside receiver
    lake_outlets: list[tuple[_NodeDescriptor, Cell, Cell]] = []
    lake_outlet_count_by_receiver = {cell: 0 for cell in outside_stream_cells}
    for index, candidate in enumerate(lake_candidates, start=1):
        lake_id = f"lake-{index:04d}"
        candidate_cells = set(candidate.cells)
        for cell in candidate.cells:
            receiver = _receiver(flow_direction, cell)
            if receiver is None or receiver in candidate_cells:
                continue
            if receiver not in outside_stream_set:
                continue
            descriptor = _NodeDescriptor(
                key=("lake_outlet", lake_id, cell[0], cell[1], receiver[0], receiver[1]),
                kind=RiverNodeKind.LAKE_OUTLET,
                position=_midpoint(adapter, cell, receiver),
                feature_id=lake_id,
            )
            lake_outlets.append((descriptor, cell, receiver))
            lake_outlet_count_by_receiver[receiver] += 1

    effective_indegree = {
        cell: ordinary_indegree[cell] + lake_outlet_count_by_receiver[cell]
        for cell in outside_stream_cells
    }

    cell_nodes: dict[Cell, _NodeDescriptor] = {}
    for cell in outside_stream_cells:
        indegree = effective_indegree[cell]
        if indegree == 0:
            kind = RiverNodeKind.SOURCE
        elif indegree >= 2:
            kind = RiverNodeKind.CONFLUENCE
        else:
            continue
        cell_nodes[cell] = _NodeDescriptor(
            key=("cell", kind.value, cell[0], cell[1]),
            kind=kind,
            position=_world_point(adapter, cell),
        )

    terminal_nodes: dict[tuple[object, ...], _NodeDescriptor] = {}
    outgoing_terminal: dict[Cell, _NodeDescriptor] = {}
    outgoing_cell: dict[Cell, Cell] = {}

    for cell in outside_stream_cells:
        receiver = _receiver(flow_direction, cell)
        if receiver is None:
            terminal = _domain_outlet_descriptor(adapter, cell)
            terminal_nodes[terminal.key] = terminal
            outgoing_terminal[cell] = terminal
            continue
        if receiver in lake_by_cell:
            lake_id = lake_by_cell[receiver]
            terminal = _NodeDescriptor(
                key=("lake_inflow", lake_id, cell[0], cell[1], receiver[0], receiver[1]),
                kind=RiverNodeKind.LAKE_INFLOW,
                position=_midpoint(adapter, cell, receiver),
                feature_id=lake_id,
            )
            terminal_nodes[terminal.key] = terminal
            outgoing_terminal[cell] = terminal
            continue
        if receiver not in outside_stream_set:
            raise HydrologyCapabilityError("visible stream path leaves stream mask without lake/outlet")
        outgoing_cell[cell] = receiver

    all_descriptors: dict[tuple[object, ...], _NodeDescriptor] = {
        descriptor.key: descriptor for descriptor in cell_nodes.values()
    }
    all_descriptors.update(terminal_nodes)
    for descriptor, _, _ in lake_outlets:
        all_descriptors[descriptor.key] = descriptor

    ordered_descriptors = sorted(all_descriptors.values(), key=_node_sort_key)
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

    segment_records: list[tuple[str, str, tuple[WorldPoint, ...], float]] = []

    def follow_from_cell(start_descriptor: _NodeDescriptor, start_cell: Cell) -> None:
        points: list[WorldPoint] = [start_descriptor.position]
        current = start_cell
        if points[-1] != _world_point(adapter, current):
            points.append(_world_point(adapter, current))

        visited: set[Cell] = set()
        while True:
            if current in visited:
                raise HydrologyCapabilityError("visible river traversal encountered a cycle")
            visited.add(current)

            terminal = outgoing_terminal.get(current)
            if terminal is not None:
                points.append(terminal.position)
                segment_records.append(
                    (
                        node_id_by_key[start_descriptor.key],
                        node_id_by_key[terminal.key],
                        tuple(points),
                        float(flow_accumulation_km2[current]),
                    )
                )
                return

            receiver = outgoing_cell.get(current)
            if receiver is None:
                raise HydrologyCapabilityError("non-terminal visible stream cell has no successor")

            downstream_node = cell_nodes.get(receiver)
            if downstream_node is not None:
                points.append(downstream_node.position)
                segment_records.append(
                    (
                        node_id_by_key[start_descriptor.key],
                        node_id_by_key[downstream_node.key],
                        tuple(points),
                        float(flow_accumulation_km2[current]),
                    )
                )
                return

            points.append(_world_point(adapter, receiver))
            current = receiver

    for cell, descriptor in sorted(cell_nodes.items()):
        follow_from_cell(descriptor, cell)

    for descriptor, outlet_cell, receiver in sorted(
        lake_outlets,
        key=lambda item: _node_sort_key(item[0]),
    ):
        downstream_node = cell_nodes.get(receiver)
        if downstream_node is not None:
            # The confluence-cell accumulation already includes all branches.
            # Preserve the catchment carried specifically by this lake branch.
            segment_records.append(
                (
                    node_id_by_key[descriptor.key],
                    node_id_by_key[downstream_node.key],
                    (descriptor.position, downstream_node.position),
                    float(flow_accumulation_km2[outlet_cell]),
                )
            )
        else:
            follow_from_cell(descriptor, receiver)

    segment_records.sort(
        key=lambda item: (
            item[0],
            item[1],
            tuple((point.x_km, point.y_km) for point in item[2]),
        )
    )
    segments = {
        f"river-segment-{index:04d}": RiverSegment(
            **{"from": from_node, "to": to_node},
            centerline=centerline,
            properties=RiverSegmentProperties(catchment_area_km2=catchment),
        )
        for index, (from_node, to_node, centerline, catchment) in enumerate(
            segment_records,
            start=1,
        )
    }
    return RiverNetwork(nodes=nodes, segments=segments)
