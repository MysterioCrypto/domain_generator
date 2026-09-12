from __future__ import annotations

import numpy as np

from .routing import D8_DIRECTIONS, HydrologyCapabilityError
from .state import LakeCandidate


def classify_stream_mask(
    flow_accumulation_km2: np.ndarray,
    *,
    stream_threshold_km2: float,
) -> np.ndarray:
    if not isinstance(flow_accumulation_km2, np.ndarray) or flow_accumulation_km2.ndim != 2:
        raise HydrologyCapabilityError("flow_accumulation_km2 must be a 2D numpy array")
    if not np.isfinite(flow_accumulation_km2).all():
        raise HydrologyCapabilityError("flow_accumulation_km2 must contain only finite values")
    if not np.isfinite(stream_threshold_km2) or stream_threshold_km2 <= 0.0:
        raise HydrologyCapabilityError("stream_threshold_km2 must be finite and > 0")
    return (flow_accumulation_km2 >= float(stream_threshold_km2)).astype(np.bool_, copy=False)


def _component_from(
    depression_mask: np.ndarray,
    visited: np.ndarray,
    start: tuple[int, int],
) -> tuple[tuple[int, int], ...]:
    rows, columns = depression_mask.shape
    stack = [start]
    visited[start] = True
    cells: list[tuple[int, int]] = []

    while stack:
        row, column = stack.pop()
        cells.append((row, column))
        for delta_row, delta_column, _ in D8_DIRECTIONS:
            neighbor_row = row + delta_row
            neighbor_column = column + delta_column
            if not (0 <= neighbor_row < rows and 0 <= neighbor_column < columns):
                continue
            if visited[neighbor_row, neighbor_column]:
                continue
            if not depression_mask[neighbor_row, neighbor_column]:
                continue
            visited[neighbor_row, neighbor_column] = True
            stack.append((neighbor_row, neighbor_column))

    return tuple(sorted(cells))


def extract_lake_candidates(
    terrain_elevation_m: np.ndarray,
    fill_elevation_m: np.ndarray,
    *,
    cell_size_km: float,
    lake_min_area_km2: float,
    lake_min_depth_m: float,
) -> tuple[LakeCandidate, ...]:
    if not isinstance(terrain_elevation_m, np.ndarray) or terrain_elevation_m.ndim != 2:
        raise HydrologyCapabilityError("terrain_elevation_m must be a 2D numpy array")
    if not isinstance(fill_elevation_m, np.ndarray) or fill_elevation_m.shape != terrain_elevation_m.shape:
        raise HydrologyCapabilityError("fill_elevation_m must match terrain shape")
    if not np.isfinite(terrain_elevation_m).all() or not np.isfinite(fill_elevation_m).all():
        raise HydrologyCapabilityError("terrain/fill elevations must contain only finite values")
    if not np.isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise HydrologyCapabilityError("cell_size_km must be finite and > 0")
    if not np.isfinite(lake_min_area_km2) or lake_min_area_km2 <= 0.0:
        raise HydrologyCapabilityError("lake_min_area_km2 must be finite and > 0")
    if not np.isfinite(lake_min_depth_m) or lake_min_depth_m <= 0.0:
        raise HydrologyCapabilityError("lake_min_depth_m must be finite and > 0")

    terrain = terrain_elevation_m.astype(np.float64, copy=False)
    fill = fill_elevation_m.astype(np.float64, copy=False)
    if not bool(np.all(fill >= terrain)):
        raise HydrologyCapabilityError("fill elevation must not fall below terrain")

    depth = fill - terrain
    depression_mask = depth > 0.0
    visited = np.zeros(depression_mask.shape, dtype=np.bool_)
    cell_area_km2 = float(cell_size_km) * float(cell_size_km)
    candidates: list[LakeCandidate] = []

    rows, columns = depression_mask.shape
    for row in range(rows):
        for column in range(columns):
            if not depression_mask[row, column] or visited[row, column]:
                continue
            cells = _component_from(depression_mask, visited, (row, column))
            surface = float(fill[cells[0]])
            if any(float(fill[cell]) != surface for cell in cells):
                raise HydrologyCapabilityError(
                    "connected depression component contains multiple physical fill elevations"
                )

            area_km2 = len(cells) * cell_area_km2
            max_depth_m = max(float(depth[cell]) for cell in cells)
            if area_km2 < lake_min_area_km2 or max_depth_m < lake_min_depth_m:
                continue

            candidates.append(
                LakeCandidate(
                    cells=cells,
                    area_km2=area_km2,
                    max_depth_m=max_depth_m,
                    surface_elevation_m=surface,
                )
            )

    candidates.sort(key=lambda candidate: candidate.cells[0])
    return tuple(candidates)
