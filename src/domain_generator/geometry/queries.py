from __future__ import annotations

from shapely.geometry import Point

from ..contracts.geometry import PointGeometry, RegionSet, WorldPoint
from .boolean import backend_point, backend_region_set


def region_set_covers_point(
    region_set: RegionSet,
    point: PointGeometry | WorldPoint,
) -> bool:
    """Return whether a canonical polygonal RegionSet contains or touches a point."""
    region = backend_region_set(region_set)
    target = backend_point(point)
    return bool(region._value.covers(target._value))



def region_set_nearest_boundary_point(
    region_set: RegionSet,
    point: PointGeometry | WorldPoint,
) -> WorldPoint:
    """Project a point to the nearest point on a non-empty RegionSet boundary."""
    region = backend_region_set(region_set)
    if region._value.is_empty:
        raise ValueError("cannot project to empty RegionSet boundary")
    target = Point(float(point.x_km), float(point.y_km))
    boundary = region._value.boundary
    if boundary.is_empty:
        raise ValueError("RegionSet boundary is empty")
    distance = boundary.project(target)
    projected = boundary.interpolate(distance)
    return WorldPoint(x_km=float(projected.x), y_km=float(projected.y))


def region_set_boundary_distance_km(
    region_set: RegionSet,
    point: PointGeometry | WorldPoint,
) -> float:
    """Return Euclidean distance from a point to the RegionSet boundary."""
    region = backend_region_set(region_set)
    if region._value.is_empty:
        raise ValueError("cannot measure empty RegionSet boundary")
    target = Point(float(point.x_km), float(point.y_km))
    return float(region._value.boundary.distance(target))
