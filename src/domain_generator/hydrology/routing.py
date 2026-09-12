from __future__ import annotations

from heapq import heappop, heappush
from math import inf, sqrt

import numpy as np


class HydrologyCapabilityError(RuntimeError):
    """A valid upstream terrain state cannot be routed by hydrology Core 0.1."""


D8_DIRECTIONS: tuple[tuple[int, int, float], ...] = (
    (-1, 0, 1.0),
    (-1, 1, sqrt(2.0)),
    (0, 1, 1.0),
    (1, 1, sqrt(2.0)),
    (1, 0, 1.0),
    (1, -1, sqrt(2.0)),
    (0, -1, 1.0),
    (-1, -1, sqrt(2.0)),
)


def _require_2d_finite(name: str, values: np.ndarray) -> None:
    if not isinstance(values, np.ndarray):
        raise HydrologyCapabilityError(f"{name} must be a numpy array")
    if values.ndim != 2 or values.shape[0] < 1 or values.shape[1] < 1:
        raise HydrologyCapabilityError(f"{name} must be a non-empty 2D array")
    if not np.isfinite(values).all():
        raise HydrologyCapabilityError(f"{name} must contain only finite values")


def _is_edge(row: int, column: int, rows: int, columns: int) -> bool:
    return row == 0 or column == 0 or row == rows - 1 or column == columns - 1


def priority_flood_routing_surface(elevation_m: np.ndarray) -> np.ndarray:
    """Return float64 depression-conditioned routing surface without mutating input."""
    _require_2d_finite("elevation_m", elevation_m)
    terrain = elevation_m.astype(np.float64, copy=False)
    rows, columns = terrain.shape
    routing = np.empty((rows, columns), dtype=np.float64)
    visited = np.zeros((rows, columns), dtype=np.bool_)
    heap: list[tuple[float, int, int]] = []

    for row in range(rows):
        for column in range(columns):
            if not _is_edge(row, column, rows, columns) or visited[row, column]:
                continue
            value = float(terrain[row, column])
            routing[row, column] = value
            visited[row, column] = True
            heappush(heap, (value, row, column))

    while heap:
        current_height, row, column = heappop(heap)
        for delta_row, delta_column, _ in D8_DIRECTIONS:
            neighbor_row = row + delta_row
            neighbor_column = column + delta_column
            if not (0 <= neighbor_row < rows and 0 <= neighbor_column < columns):
                continue
            if visited[neighbor_row, neighbor_column]:
                continue

            original = float(terrain[neighbor_row, neighbor_column])
            if original > current_height:
                routed = original
            else:
                routed = float(np.nextafter(current_height, inf))

            routing[neighbor_row, neighbor_column] = routed
            visited[neighbor_row, neighbor_column] = True
            heappush(heap, (routed, neighbor_row, neighbor_column))

    if not bool(visited.all()):
        raise HydrologyCapabilityError("Priority-Flood did not visit every terrain cell")
    return routing


def d8_flow_direction(routing_elevation_m: np.ndarray, *, cell_size_km: float) -> np.ndarray:
    """Compute canonical D8 receiver code, with every domain-edge cell as outlet (-1)."""
    _require_2d_finite("routing_elevation_m", routing_elevation_m)
    if not np.isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise HydrologyCapabilityError("cell_size_km must be finite and > 0")

    rows, columns = routing_elevation_m.shape
    result = np.full((rows, columns), -1, dtype=np.int8)

    for row in range(rows):
        for column in range(columns):
            if _is_edge(row, column, rows, columns):
                continue

            current = float(routing_elevation_m[row, column])
            best_direction = -1
            best_slope = 0.0

            for direction, (delta_row, delta_column, distance_factor) in enumerate(D8_DIRECTIONS):
                neighbor_row = row + delta_row
                neighbor_column = column + delta_column
                neighbor = float(routing_elevation_m[neighbor_row, neighbor_column])
                if neighbor >= current:
                    continue
                slope = (current - neighbor) / (cell_size_km * distance_factor)
                if slope > best_slope:
                    best_slope = slope
                    best_direction = direction

            if best_direction < 0:
                raise HydrologyCapabilityError(
                    f"conditioned interior cell ({row},{column}) has no strictly lower D8 receiver"
                )
            result[row, column] = np.int8(best_direction)

    return result


def flow_accumulation_km2(
    routing_elevation_m: np.ndarray,
    flow_direction: np.ndarray,
    *,
    cell_size_km: float,
) -> np.ndarray:
    """Accumulate exact upstream cell counts, then convert once to physical catchment area."""
    _require_2d_finite("routing_elevation_m", routing_elevation_m)
    if not isinstance(flow_direction, np.ndarray) or flow_direction.shape != routing_elevation_m.shape:
        raise HydrologyCapabilityError("flow_direction must be an array matching routing surface shape")
    if flow_direction.dtype != np.dtype(np.int8):
        raise HydrologyCapabilityError("flow_direction must use int8 dtype")
    if not np.isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise HydrologyCapabilityError("cell_size_km must be finite and > 0")

    rows, columns = routing_elevation_m.shape
    counts = np.ones((rows, columns), dtype=np.int64)
    ordered_cells = sorted(
        ((row, column) for row in range(rows) for column in range(columns)),
        key=lambda rc: (-float(routing_elevation_m[rc]), rc[0], rc[1]),
    )

    for row, column in ordered_cells:
        direction = int(flow_direction[row, column])
        if direction == -1:
            continue
        if not 0 <= direction < len(D8_DIRECTIONS):
            raise HydrologyCapabilityError("flow_direction contains invalid D8 code")
        delta_row, delta_column, _ = D8_DIRECTIONS[direction]
        receiver_row = row + delta_row
        receiver_column = column + delta_column
        if not (0 <= receiver_row < rows and 0 <= receiver_column < columns):
            raise HydrologyCapabilityError("flow_direction points outside domain from non-outlet cell")
        if not routing_elevation_m[receiver_row, receiver_column] < routing_elevation_m[row, column]:
            raise HydrologyCapabilityError("flow receiver must be strictly lower on routing surface")
        counts[receiver_row, receiver_column] += counts[row, column]

    cell_area_km2 = float(cell_size_km) * float(cell_size_km)
    return counts.astype(np.float64) * cell_area_km2
