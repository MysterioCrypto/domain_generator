from __future__ import annotations

from math import floor

import numpy as np
from shapely import union_all
from shapely.geometry import box

from ..contracts.data import GeneratedFeatureSource, MarineFeature, MarineProperties
from ..contracts.geometry import WorldPoint
from ..contracts.plan import GenerationPlan
from ..geometry import BooleanGeometry, backend_region_set, geometry_area_km2, is_canonical_region_set, to_region_set
from ..grid import GridAdapter
from .ids import marine_feature_id
from .routing import HydrologyCapabilityError
from .state import MarineCandidate


Cell = tuple[int, int]
_FOUR_NEIGHBORS: tuple[tuple[int, int], ...] = (
    (-1, 0),
    (0, 1),
    (1, 0),
    (0, -1),
)


def _is_edge(cell: Cell, shape: tuple[int, int]) -> bool:
    row, column = cell
    rows, columns = shape
    return row == 0 or column == 0 or row == rows - 1 or column == columns - 1


def classify_marine_components(
    terrain_elevation_m: np.ndarray,
    *,
    sea_level_m: float,
    cell_size_km: float,
) -> tuple[np.ndarray, tuple[MarineCandidate, ...]]:
    """Classify boundary-connected below-sea terrain using fixed 4-neighbour connectivity."""
    if not isinstance(terrain_elevation_m, np.ndarray) or terrain_elevation_m.ndim != 2:
        raise HydrologyCapabilityError("terrain_elevation_m must be a 2D numpy array")
    if not bool(np.isfinite(terrain_elevation_m).all()):
        raise HydrologyCapabilityError("terrain_elevation_m must be finite")
    if not np.isfinite(sea_level_m):
        raise HydrologyCapabilityError("sea_level_m must be finite")
    if not np.isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise HydrologyCapabilityError("cell_size_km must be finite and > 0")

    terrain = terrain_elevation_m.astype(np.float64, copy=False)
    below = terrain < float(sea_level_m)
    visited = np.zeros(below.shape, dtype=np.bool_)
    marine = np.zeros(below.shape, dtype=np.bool_)
    candidates: list[MarineCandidate] = []
    rows, columns = below.shape
    cell_area = float(cell_size_km) * float(cell_size_km)

    for row in range(rows):
        for column in range(columns):
            start = (row, column)
            if not bool(below[start]) or bool(visited[start]):
                continue

            stack = [start]
            visited[start] = True
            cells: list[Cell] = []
            touches_boundary = False

            while stack:
                cell = stack.pop()
                cells.append(cell)
                if _is_edge(cell, below.shape):
                    touches_boundary = True

                cr, cc = cell
                for dr, dc in _FOUR_NEIGHBORS:
                    nr, nc = cr + dr, cc + dc
                    if not (0 <= nr < rows and 0 <= nc < columns):
                        continue
                    target = (nr, nc)
                    if bool(visited[target]) or not bool(below[target]):
                        continue
                    visited[target] = True
                    stack.append(target)

            if not touches_boundary:
                continue

            ordered = tuple(sorted(cells))
            for cell in ordered:
                marine[cell] = True
            max_depth = max(float(sea_level_m) - float(terrain[cell]) for cell in ordered)
            candidates.append(
                MarineCandidate(
                    cells=ordered,
                    raster_area_km2=len(ordered) * cell_area,
                    sea_level_m=float(sea_level_m),
                    max_depth_m=max_depth,
                )
            )

    candidates.sort(
        key=lambda candidate: (
            candidate.cells[0][0],
            candidate.cells[0][1],
            len(candidate.cells),
            candidate.cells,
        )
    )
    return marine, tuple(candidates)


def accepted_marine_cell_map(
    shape: tuple[int, int],
    marine_candidates: tuple[MarineCandidate, ...],
) -> dict[Cell, str]:
    rows, columns = shape
    mapping: dict[Cell, str] = {}
    for index, candidate in enumerate(marine_candidates):
        feature_id = marine_feature_id(index)
        for cell in candidate.cells:
            row, column = cell
            if not (0 <= row < rows and 0 <= column < columns):
                raise HydrologyCapabilityError("marine candidate cell is outside grid")
            if cell in mapping:
                raise HydrologyCapabilityError("marine candidates overlap")
            mapping[cell] = feature_id
    return mapping


def _sample_terrain_bilinear(
    terrain_elevation_m: np.ndarray,
    adapter: GridAdapter,
    x_km: float,
    y_km: float,
) -> float:
    column_f = x_km / adapter.cell_size_km - 0.5
    row_f = (adapter.height_km - y_km) / adapter.cell_size_km - 0.5
    c0 = floor(column_f)
    r0 = floor(row_f)
    tx = column_f - c0
    ty = row_f - r0

    value = 0.0
    total = 0.0
    for dr, wy in ((0, 1.0 - ty), (1, ty)):
        for dc, wx in ((0, 1.0 - tx), (1, tx)):
            row = min(adapter.rows - 1, max(0, r0 + dr))
            column = min(adapter.columns - 1, max(0, c0 + dc))
            weight = max(0.0, wx * wy)
            value += weight * float(terrain_elevation_m[row, column])
            total += weight
    if total <= 0.0:
        raise HydrologyCapabilityError("bilinear marine terrain sampling collapsed")
    return value / total


def refined_marine_region_set(
    plan: GenerationPlan,
    candidate: MarineCandidate,
    terrain_elevation_m: np.ndarray,
    *,
    subdivision: int = 4,
):
    """Reconstruct deterministic sub-cell marine geometry inside raster marine support."""
    if isinstance(subdivision, bool) or not isinstance(subdivision, int) or subdivision < 2:
        raise HydrologyCapabilityError("marine subdivision must be an integer >= 2")

    adapter = GridAdapter.from_plan(plan)
    expected_shape = (adapter.rows, adapter.columns)
    if (
        not isinstance(terrain_elevation_m, np.ndarray)
        or terrain_elevation_m.shape != expected_shape
    ):
        raise HydrologyCapabilityError("terrain elevation must match plan grid")
    if not bool(np.isfinite(terrain_elevation_m).all()):
        raise HydrologyCapabilityError("terrain elevation must be finite")

    subcell = adapter.cell_size_km / float(subdivision)
    wet_boxes = []
    for row, column in sorted(candidate.cells):
        x_min = column * adapter.cell_size_km
        y_min = adapter.height_km - (row + 1) * adapter.cell_size_km
        for sub_row in range(subdivision):
            for sub_column in range(subdivision):
                sx0 = x_min + sub_column * subcell
                sy0 = y_min + sub_row * subcell
                sx1 = sx0 + subcell
                sy1 = sy0 + subcell
                sample_x = (sx0 + sx1) / 2.0
                sample_y = (sy0 + sy1) / 2.0
                elevation = _sample_terrain_bilinear(
                    terrain_elevation_m,
                    adapter,
                    sample_x,
                    sample_y,
                )
                if elevation < float(candidate.sea_level_m):
                    wet_boxes.append(box(sx0, sy0, sx1, sy1))

    if not wet_boxes:
        raise HydrologyCapabilityError("refined marine coastline produced no wet sub-cells")

    region_set = to_region_set(BooleanGeometry(union_all(wet_boxes)))
    if not region_set.polygons:
        raise HydrologyCapabilityError("refined marine geometry is empty")
    if not is_canonical_region_set(region_set):
        raise HydrologyCapabilityError("refined marine geometry is not canonical")

    geometry = backend_region_set(region_set)
    refined_area = geometry_area_km2(geometry)
    if not (0.0 < refined_area <= float(candidate.raster_area_km2) + 1e-12):
        raise HydrologyCapabilityError(
            "refined marine area must be positive and contained in raster support"
        )

    domain_boundary = box(
        0.0,
        0.0,
        adapter.width_km,
        adapter.height_km,
    ).boundary
    for polygon in geometry._value.geoms if hasattr(geometry._value, "geoms") else (geometry._value,):
        if polygon.is_empty:
            continue
        if not polygon.intersects(domain_boundary):
            raise HydrologyCapabilityError(
                "refined marine polygon lost required domain-boundary connection"
            )

    return region_set


def materialize_marine_features(
    plan: GenerationPlan,
    marine_candidates: tuple[MarineCandidate, ...],
    terrain_elevation_m: np.ndarray,
    *,
    subdivision: int = 4,
) -> dict[str, MarineFeature]:
    result: dict[str, MarineFeature] = {}
    for index, candidate in enumerate(marine_candidates):
        feature_id = marine_feature_id(index)
        region_set = refined_marine_region_set(
            plan,
            candidate,
            terrain_elevation_m,
            subdivision=subdivision,
        )
        area = geometry_area_km2(backend_region_set(region_set))
        result[feature_id] = MarineFeature(
            source=GeneratedFeatureSource(system="hydrology"),
            geometry=region_set,
            properties=MarineProperties(
                area_km2=area,
                sea_level_m=float(candidate.sea_level_m),
                max_depth_m=float(candidate.max_depth_m),
            ),
        )
    return result


__all__ = [
    "accepted_marine_cell_map",
    "classify_marine_components",
    "materialize_marine_features",
    "refined_marine_region_set",
]
