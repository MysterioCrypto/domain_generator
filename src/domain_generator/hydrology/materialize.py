from __future__ import annotations

from math import floor, isclose

import numpy as np
from shapely import union_all
from shapely.geometry import box

from ..contracts.data import GeneratedFeatureSource, HydroFeature, LakeProperties, RiverNetwork
from ..contracts.geometry import AreaGeometry, WorldPoint
from ..contracts.plan import GenerationPlan
from ..geometry import (
    BooleanGeometry,
    backend_area,
    geometry_area_km2,
    is_canonical_region_set,
    to_region_set,
    union_geometry,
)
from ..grid import GridAdapter
from .ids import lake_feature_id
from .routing import HydrologyCapabilityError
from .state import LakeCandidate
from .water import accepted_lake_cell_map


def _cell_square(adapter: GridAdapter, row: int, column: int) -> AreaGeometry:
    if not 0 <= row < adapter.rows or not 0 <= column < adapter.columns:
        raise HydrologyCapabilityError("lake candidate cell is outside grid")
    s = adapter.cell_size_km
    x_min = column * s
    x_max = (column + 1) * s
    y_max = adapter.height_km - row * s
    y_min = adapter.height_km - (row + 1) * s
    return AreaGeometry(
        boundary=(
            WorldPoint(x_km=x_min, y_km=y_min),
            WorldPoint(x_km=x_max, y_km=y_min),
            WorldPoint(x_km=x_max, y_km=y_max),
            WorldPoint(x_km=x_min, y_km=y_max),
        )
    )


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
        raise HydrologyCapabilityError("bilinear terrain sampling collapsed to zero weight")
    return value / total


def refined_lake_region_set(
    plan: GenerationPlan,
    candidate: LakeCandidate,
    terrain_elevation_m: np.ndarray,
    *,
    subdivision: int = 4,
):
    """Reconstruct a deterministic sub-cell shoreline inside one routing basin."""
    if isinstance(subdivision, bool) or not isinstance(subdivision, int) or subdivision < 2:
        raise HydrologyCapabilityError("shoreline subdivision must be an integer >= 2")
    adapter = GridAdapter.from_plan(plan)
    expected_shape = (adapter.rows, adapter.columns)
    if not isinstance(terrain_elevation_m, np.ndarray) or terrain_elevation_m.shape != expected_shape:
        raise HydrologyCapabilityError("terrain elevation must match plan grid")
    if not np.isfinite(terrain_elevation_m).all():
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
                if elevation < float(candidate.surface_elevation_m):
                    wet_boxes.append(box(sx0, sy0, sx1, sy1))

    if not wet_boxes:
        raise HydrologyCapabilityError("refined lake shoreline produced no wet sub-cells")

    region_set = to_region_set(BooleanGeometry(union_all(wet_boxes)))
    if len(region_set.polygons) != 1:
        raise HydrologyCapabilityError(
            "refined lake shoreline fragmented into disconnected polygons"
        )
    if not is_canonical_region_set(region_set):
        raise HydrologyCapabilityError("refined lake shoreline is not canonical")

    refined_area = geometry_area_km2(backend_region_set(region_set))
    if not (0.0 < refined_area <= float(candidate.area_km2) + 1e-12):
        raise HydrologyCapabilityError(
            "refined lake area must be positive and contained in routing basin"
        )
    return region_set


def materialize_lake_features(
    plan: GenerationPlan,
    lake_candidates: tuple[LakeCandidate, ...],
    *,
    terrain_elevation_m: np.ndarray | None = None,
    shoreline_subdivision: int = 4,
) -> dict[str, HydroFeature]:
    adapter = GridAdapter.from_plan(plan)
    shape = (plan.grid.rows, plan.grid.columns)
    accepted_lake_cell_map(shape, lake_candidates)

    result: dict[str, HydroFeature] = {}
    for index, candidate in enumerate(lake_candidates):
        if not candidate.cells:
            raise HydrologyCapabilityError("lake candidate must contain at least one cell")

        if terrain_elevation_m is None:
            geometry = None
            for row, column in sorted(candidate.cells):
                cell_geometry = backend_area(_cell_square(adapter, row, column))
                geometry = cell_geometry if geometry is None else union_geometry(geometry, cell_geometry)
            if geometry is None:
                raise HydrologyCapabilityError("lake candidate produced empty geometry")
            region_set = to_region_set(geometry)
            geometry_area = geometry_area_km2(geometry)
            if not isclose(
                geometry_area,
                float(candidate.area_km2),
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise HydrologyCapabilityError("lake geometry area does not match candidate area")
        else:
            region_set = refined_lake_region_set(
                plan,
                candidate,
                terrain_elevation_m,
                subdivision=shoreline_subdivision,
            )
            geometry_area = geometry_area_km2(backend_region_set(region_set))

        if not region_set.polygons:
            raise HydrologyCapabilityError("lake candidate produced empty polygonal geometry")
        if not is_canonical_region_set(region_set):
            raise HydrologyCapabilityError("lake geometry is not canonical RegionSet")

        feature_id = lake_feature_id(index)
        if feature_id in result:
            raise HydrologyCapabilityError("duplicate lake feature id")
        try:
            result[feature_id] = HydroFeature(
                source=GeneratedFeatureSource(system="hydrology"),
                geometry=region_set,
                properties=LakeProperties(
                    area_km2=float(geometry_area),
                    surface_elevation_m=float(candidate.surface_elevation_m),
                    max_depth_m=float(candidate.max_depth_m),
                ),
            )
        except ValueError as exc:
            raise HydrologyCapabilityError("lake candidate properties are invalid") from exc

    return result


def validate_river_lake_references(
    river_network: RiverNetwork,
    lake_features: dict[str, HydroFeature],
) -> None:
    for node in river_network.nodes.values():
        if node.feature_id is not None and node.feature_id not in lake_features:
            raise HydrologyCapabilityError(
                f"river node references unknown materialized lake {node.feature_id!r}"
            )
