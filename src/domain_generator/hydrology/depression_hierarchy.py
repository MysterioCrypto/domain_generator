from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from .routing import D8_DIRECTIONS, HydrologyCapabilityError
from .state import Cell, LakeCandidate


@dataclass(frozen=True, slots=True)
class DepressionHierarchyNode:
    id: str
    parent_id: str | None
    child_ids: tuple[str, ...]
    minimum_cell: Cell
    minimum_elevation_m: float
    birth_elevation_m: float
    spill_elevation_m: float
    relief_to_spill_m: float
    cells_at_spill: tuple[Cell, ...]
    area_at_spill_km2: float
    storage_to_spill_proxy_km3: float
    threshold_significant: bool


@dataclass(frozen=True, slots=True)
class DepressionHierarchy:
    root_id: str
    nodes: tuple[DepressionHierarchyNode, ...]

    def node_map(self) -> dict[str, DepressionHierarchyNode]:
        return {node.id: node for node in self.nodes}

    def leaf_nodes(self) -> tuple[DepressionHierarchyNode, ...]:
        return tuple(node for node in self.nodes if not node.child_ids)


def _components(active: set[Cell]) -> tuple[tuple[Cell, ...], ...]:
    visited: set[Cell] = set()
    result: list[tuple[Cell, ...]] = []
    for start in sorted(active):
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        cells: list[Cell] = []
        while stack:
            cell = stack.pop()
            cells.append(cell)
            row, column = cell
            for delta_row, delta_column, _ in D8_DIRECTIONS:
                neighbor = (row + delta_row, column + delta_column)
                if neighbor in active and neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        result.append(tuple(sorted(cells)))
    result.sort(key=lambda cells: cells[0])
    return tuple(result)


def _storage_proxy_km3(
    terrain_elevation_m: np.ndarray,
    cells: tuple[Cell, ...],
    spill_elevation_m: float,
    *,
    cell_area_km2: float,
) -> float:
    depth_sum_m = sum(
        max(float(spill_elevation_m) - float(terrain_elevation_m[cell]), 0.0)
        for cell in cells
    )
    return float(depth_sum_m * cell_area_km2 / 1000.0)


def build_nested_depression_hierarchy(
    terrain_elevation_m: np.ndarray,
    candidate: LakeCandidate,
    *,
    cell_size_km: float,
    lake_min_area_km2: float,
    lake_min_depth_m: float,
) -> DepressionHierarchy:
    """Build a deterministic level-set merge tree inside one accepted routing lake."""
    if not isinstance(terrain_elevation_m, np.ndarray) or terrain_elevation_m.ndim != 2:
        raise HydrologyCapabilityError("terrain_elevation_m must be a 2D numpy array")
    if not bool(np.isfinite(terrain_elevation_m).all()):
        raise HydrologyCapabilityError("terrain_elevation_m must be finite")
    if not isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise HydrologyCapabilityError("cell_size_km must be finite and > 0")
    if not isfinite(lake_min_area_km2) or lake_min_area_km2 <= 0.0:
        raise HydrologyCapabilityError("lake_min_area_km2 must be finite and > 0")
    if not isfinite(lake_min_depth_m) or lake_min_depth_m <= 0.0:
        raise HydrologyCapabilityError("lake_min_depth_m must be finite and > 0")
    if not candidate.cells:
        raise HydrologyCapabilityError("lake candidate must contain cells")

    rows, columns = terrain_elevation_m.shape
    basin = tuple(sorted(candidate.cells))
    basin_set = set(basin)
    for row, column in basin:
        if not (0 <= row < rows and 0 <= column < columns):
            raise HydrologyCapabilityError("lake candidate cell lies outside terrain")
        if not float(terrain_elevation_m[row, column]) < float(candidate.surface_elevation_m):
            raise HydrologyCapabilityError(
                "routing lake cell must lie below accepted spill/surface elevation"
            )

    # The accepted routing basin itself must be one 8-connected component.
    if _components(set(basin)) != (basin,):
        raise HydrologyCapabilityError("accepted routing lake basin must be 8-connected")

    cell_area_km2 = float(cell_size_km) * float(cell_size_km)
    by_level: dict[float, list[Cell]] = {}
    for cell in basin:
        by_level.setdefault(float(terrain_elevation_m[cell]), []).append(cell)

    active: set[Cell] = set()
    previous_components: tuple[tuple[Cell, ...], ...] = ()
    previous_node_by_component: dict[tuple[Cell, ...], str] = {}

    builders: dict[str, dict[str, object]] = {}
    next_id = 1

    def new_node(
        *,
        child_ids: tuple[str, ...],
        minimum_cell: Cell,
        minimum_elevation_m: float,
        birth_elevation_m: float,
    ) -> str:
        nonlocal next_id
        node_id = f"depression-node-{next_id:04d}"
        next_id += 1
        builders[node_id] = {
            "id": node_id,
            "parent_id": None,
            "child_ids": child_ids,
            "minimum_cell": minimum_cell,
            "minimum_elevation_m": float(minimum_elevation_m),
            "birth_elevation_m": float(birth_elevation_m),
            "spill_elevation_m": None,
            "cells_at_spill": None,
        }
        for child_id in child_ids:
            if builders[child_id]["parent_id"] is not None:
                raise HydrologyCapabilityError("depression hierarchy child already has parent")
            builders[child_id]["parent_id"] = node_id
        return node_id

    def finalize_node(node_id: str, spill: float, cells: tuple[Cell, ...]) -> None:
        builder = builders[node_id]
        if builder["spill_elevation_m"] is not None:
            raise HydrologyCapabilityError("depression hierarchy node finalized twice")
        builder["spill_elevation_m"] = float(spill)
        builder["cells_at_spill"] = tuple(sorted(cells))

    for level in sorted(by_level):
        active.update(by_level[level])
        current_components = _components(active)

        previous_owner: dict[Cell, tuple[Cell, ...]] = {}
        for component in previous_components:
            for cell in component:
                previous_owner[cell] = component

        current_node_by_component: dict[tuple[Cell, ...], str] = {}
        for component in current_components:
            previous = {
                previous_owner[cell]
                for cell in component
                if cell in previous_owner
            }
            previous_sorted = tuple(sorted(previous, key=lambda cells: cells[0]))

            if not previous_sorted:
                minimum_cell = min(
                    component,
                    key=lambda cell: (float(terrain_elevation_m[cell]), cell[0], cell[1]),
                )
                node_id = new_node(
                    child_ids=(),
                    minimum_cell=minimum_cell,
                    minimum_elevation_m=float(terrain_elevation_m[minimum_cell]),
                    birth_elevation_m=float(terrain_elevation_m[minimum_cell]),
                )
            elif len(previous_sorted) == 1:
                node_id = previous_node_by_component[previous_sorted[0]]
            else:
                child_ids = tuple(
                    sorted(previous_node_by_component[prev] for prev in previous_sorted)
                )
                for prev in previous_sorted:
                    finalize_node(
                        previous_node_by_component[prev],
                        float(level),
                        prev,
                    )
                minimum_cell = min(
                    (builders[child_id]["minimum_cell"] for child_id in child_ids),
                    key=lambda cell: (float(terrain_elevation_m[cell]), cell[0], cell[1]),
                )
                node_id = new_node(
                    child_ids=child_ids,
                    minimum_cell=minimum_cell,
                    minimum_elevation_m=float(terrain_elevation_m[minimum_cell]),
                    birth_elevation_m=float(level),
                )
            current_node_by_component[component] = node_id

        previous_components = current_components
        previous_node_by_component = current_node_by_component

    if len(previous_components) != 1:
        raise HydrologyCapabilityError("nested depression sweep did not converge to one root")
    root_component = previous_components[0]
    if root_component != basin:
        raise HydrologyCapabilityError("nested depression root does not cover routing basin")
    root_id = previous_node_by_component[root_component]
    finalize_node(root_id, float(candidate.surface_elevation_m), basin)

    nodes: list[DepressionHierarchyNode] = []
    for node_id in sorted(builders):
        builder = builders[node_id]
        spill = builder["spill_elevation_m"]
        cells = builder["cells_at_spill"]
        if spill is None or cells is None:
            raise HydrologyCapabilityError("nested depression node was not finalized")
        cells_tuple = tuple(cells)
        minimum_elevation = float(builder["minimum_elevation_m"])
        relief = float(spill) - minimum_elevation
        area = len(cells_tuple) * cell_area_km2
        storage = _storage_proxy_km3(
            terrain_elevation_m,
            cells_tuple,
            float(spill),
            cell_area_km2=cell_area_km2,
        )
        significant = area >= float(lake_min_area_km2) and relief >= float(lake_min_depth_m)
        nodes.append(
            DepressionHierarchyNode(
                id=node_id,
                parent_id=builder["parent_id"],
                child_ids=tuple(builder["child_ids"]),
                minimum_cell=builder["minimum_cell"],
                minimum_elevation_m=minimum_elevation,
                birth_elevation_m=float(builder["birth_elevation_m"]),
                spill_elevation_m=float(spill),
                relief_to_spill_m=relief,
                cells_at_spill=cells_tuple,
                area_at_spill_km2=area,
                storage_to_spill_proxy_km3=storage,
                threshold_significant=bool(significant),
            )
        )

    node_map = {node.id: node for node in nodes}
    if root_id not in node_map:
        raise HydrologyCapabilityError("nested depression hierarchy root is missing")
    if node_map[root_id].parent_id is not None:
        raise HydrologyCapabilityError("nested depression root cannot have a parent")
    if node_map[root_id].cells_at_spill != basin:
        raise HydrologyCapabilityError("nested depression root cells must equal routing basin")

    # Guard tree structure and monotonic child -> parent semantics.
    for node in nodes:
        for child_id in node.child_ids:
            child = node_map[child_id]
            if child.parent_id != node.id:
                raise HydrologyCapabilityError("nested depression parent/child mismatch")
            if node.spill_elevation_m + 1e-12 < child.spill_elevation_m:
                raise HydrologyCapabilityError("parent spill level must not be below child spill")
            if node.area_at_spill_km2 + 1e-12 < child.area_at_spill_km2:
                raise HydrologyCapabilityError("parent area must not be below child area")
        if any(cell not in basin_set for cell in node.cells_at_spill):
            raise HydrologyCapabilityError("nested depression node escaped routing basin")

    return DepressionHierarchy(root_id=root_id, nodes=tuple(nodes))


__all__ = [
    "DepressionHierarchy",
    "DepressionHierarchyNode",
    "build_nested_depression_hierarchy",
]
