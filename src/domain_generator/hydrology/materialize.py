from __future__ import annotations

from math import isclose

from ..contracts.data import GeneratedFeatureSource, HydroFeature, LakeProperties, RiverNetwork
from ..contracts.geometry import AreaGeometry, WorldPoint
from ..contracts.plan import GenerationPlan
from ..geometry import (
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


def materialize_lake_features(
    plan: GenerationPlan,
    lake_candidates: tuple[LakeCandidate, ...],
) -> dict[str, HydroFeature]:
    adapter = GridAdapter.from_plan(plan)
    shape = (plan.grid.rows, plan.grid.columns)
    accepted_lake_cell_map(shape, lake_candidates)

    result: dict[str, HydroFeature] = {}
    for index, candidate in enumerate(lake_candidates):
        if not candidate.cells:
            raise HydrologyCapabilityError("lake candidate must contain at least one cell")

        geometry = None
        for row, column in sorted(candidate.cells):
            cell_geometry = backend_area(_cell_square(adapter, row, column))
            geometry = cell_geometry if geometry is None else union_geometry(geometry, cell_geometry)
        if geometry is None:
            raise HydrologyCapabilityError("lake candidate produced empty geometry")

        region_set = to_region_set(geometry)
        if not region_set.polygons:
            raise HydrologyCapabilityError("lake candidate produced empty polygonal geometry")
        if not is_canonical_region_set(region_set):
            raise HydrologyCapabilityError("lake geometry is not canonical RegionSet")

        geometry_area = geometry_area_km2(geometry)
        if not isclose(
            geometry_area,
            float(candidate.area_km2),
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise HydrologyCapabilityError("lake geometry area does not match candidate area")

        feature_id = lake_feature_id(index)
        if feature_id in result:
            raise HydrologyCapabilityError("duplicate lake feature id")
        try:
            result[feature_id] = HydroFeature(
                source=GeneratedFeatureSource(system="hydrology"),
                geometry=region_set,
                properties=LakeProperties(
                    area_km2=float(candidate.area_km2),
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
