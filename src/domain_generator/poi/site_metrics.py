from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite

import numpy as np

from ..contracts.geometry import PointGeometry
from ..contracts.plan import GenerationPlan
from ..grid import GridAdapter
from ..hydrology.state import HydrologyState
from ..surface.derive import distance_to_water_km, slope_degrees
from ..surface.state import SurfaceState
from ..terrain.state import TerrainState


SITE_METRIC_IDS: tuple[str, ...] = (
    "slope_mean",
    "water_fraction",
    "elevation_mean",
    "local_relief",
    "relative_elevation",
    "moisture_mean",
    "vegetation_density_mean",
    "distance_to_water",
)


class SiteMetricCapabilityError(RuntimeError):
    """Site-metric Core 0.1 cannot evaluate the supplied runtime state."""


@dataclass(frozen=True, slots=True)
class SiteMetricContext:
    """Attempt-global upstream fields used to evaluate many candidate sites."""

    adapter: GridAdapter
    elevation_m: np.ndarray
    water_depth_m: np.ndarray
    moisture: np.ndarray
    vegetation_density: np.ndarray
    slope_deg: np.ndarray
    distance_to_water_km: np.ndarray

    @classmethod
    def from_states(
        cls,
        plan: GenerationPlan,
        terrain: TerrainState,
        hydrology: HydrologyState,
        surface: SurfaceState,
    ) -> "SiteMetricContext":
        adapter = GridAdapter.from_plan(plan)
        expected_shape = (adapter.rows, adapter.columns)

        elevation = _require_field(
            "elevation_m",
            terrain.elevation_m,
            expected_shape=expected_shape,
            non_negative=False,
            normalized=False,
        )
        water_depth = _require_field(
            "water_depth_m",
            hydrology.water_depth_m,
            expected_shape=expected_shape,
            non_negative=True,
            normalized=False,
        )
        moisture = _require_field(
            "moisture",
            surface.moisture,
            expected_shape=expected_shape,
            non_negative=True,
            normalized=True,
        )
        vegetation = _require_field(
            "vegetation_density",
            surface.vegetation_density,
            expected_shape=expected_shape,
            non_negative=True,
            normalized=True,
        )

        slope = slope_degrees(elevation, cell_size_km=adapter.cell_size_km)
        water_mask = (water_depth > 0.0).astype(np.bool_, copy=False)
        water_distance = distance_to_water_km(
            water_mask,
            cell_size_km=adapter.cell_size_km,
        )

        return cls(
            adapter=adapter,
            elevation_m=elevation,
            water_depth_m=water_depth,
            moisture=moisture,
            vegetation_density=vegetation,
            slope_deg=slope,
            distance_to_water_km=water_distance,
        )


def _require_field(
    name: str,
    array: np.ndarray,
    *,
    expected_shape: tuple[int, int],
    non_negative: bool,
    normalized: bool,
) -> np.ndarray:
    if not isinstance(array, np.ndarray) or array.ndim != 2 or array.shape != expected_shape:
        raise SiteMetricCapabilityError(f"{name} must be a 2D array matching plan grid")
    if not np.isfinite(array).all():
        raise SiteMetricCapabilityError(f"{name} must contain only finite values")
    if non_negative and bool(np.any(array < 0.0)):
        raise SiteMetricCapabilityError(f"{name} must be non-negative")
    if normalized and bool(np.any(array > 1.0)):
        raise SiteMetricCapabilityError(f"{name} must be in [0, 1]")
    return array


def _validate_candidate(adapter: GridAdapter, candidate: PointGeometry) -> tuple[int, int]:
    try:
        return adapter.containing_cell(candidate.x_km, candidate.y_km)
    except (TypeError, ValueError) as exc:
        raise SiteMetricCapabilityError("candidate point must be finite and inside/on domain") from exc


def footprint_cells(
    adapter: GridAdapter,
    candidate: PointGeometry,
    footprint_radius_km: float,
) -> tuple[tuple[int, int], ...]:
    """Return canonical raster support cells for one world-space candidate footprint."""
    containing = _validate_candidate(adapter, candidate)
    if isinstance(footprint_radius_km, bool) or not isfinite(float(footprint_radius_km)):
        raise SiteMetricCapabilityError("footprint_radius_km must be finite and >= 0")
    radius = float(footprint_radius_km)
    if radius < 0.0:
        raise SiteMetricCapabilityError("footprint_radius_km must be finite and >= 0")
    if radius == 0.0:
        return (containing,)

    span = int(ceil(radius / adapter.cell_size_km)) + 1
    base_row, base_column = containing
    min_row = max(0, base_row - span)
    max_row = min(adapter.rows - 1, base_row + span)
    min_column = max(0, base_column - span)
    max_column = min(adapter.columns - 1, base_column + span)
    radius_squared = radius * radius

    cells: list[tuple[int, int]] = []
    for row in range(min_row, max_row + 1):
        for column in range(min_column, max_column + 1):
            center = adapter.cell_center(row, column)
            dx = center.x_km - candidate.x_km
            dy = center.y_km - candidate.y_km
            if dx * dx + dy * dy <= radius_squared:
                cells.append((row, column))

    if not cells:
        return (containing,)
    return tuple(cells)


def evaluate_site_metrics(
    context: SiteMetricContext,
    candidate: PointGeometry,
    footprint_radius_km: float,
) -> dict[str, float]:
    """Evaluate the complete Core 0.1 site metric registry for one candidate."""
    cells = footprint_cells(context.adapter, candidate, footprint_radius_km)
    containing = _validate_candidate(context.adapter, candidate)

    elevations = np.asarray(
        [context.elevation_m[cell] for cell in cells],
        dtype=np.float64,
    )
    slopes = np.asarray(
        [context.slope_deg[cell] for cell in cells],
        dtype=np.float64,
    )
    water = np.asarray(
        [context.water_depth_m[cell] > 0.0 for cell in cells],
        dtype=np.bool_,
    )
    moisture = np.asarray(
        [context.moisture[cell] for cell in cells],
        dtype=np.float64,
    )
    vegetation = np.asarray(
        [context.vegetation_density[cell] for cell in cells],
        dtype=np.float64,
    )
    water_distance = np.asarray(
        [context.distance_to_water_km[cell] for cell in cells],
        dtype=np.float64,
    )

    elevation_mean = float(np.mean(elevations, dtype=np.float64))
    containing_elevation = float(context.elevation_m[containing])

    values = {
        "slope_mean": float(np.mean(slopes, dtype=np.float64)),
        "water_fraction": float(np.count_nonzero(water) / len(cells)),
        "elevation_mean": elevation_mean,
        "local_relief": float(np.max(elevations) - np.min(elevations)),
        "relative_elevation": containing_elevation - elevation_mean,
        "moisture_mean": float(np.mean(moisture, dtype=np.float64)),
        "vegetation_density_mean": float(np.mean(vegetation, dtype=np.float64)),
        "distance_to_water": float(np.min(water_distance)),
    }
    return {metric_id: values[metric_id] for metric_id in SITE_METRIC_IDS}
