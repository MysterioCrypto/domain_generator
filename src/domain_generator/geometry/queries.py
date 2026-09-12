from __future__ import annotations

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
