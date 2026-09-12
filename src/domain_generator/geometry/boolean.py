from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry

from ..contracts.geometry import (
    AreaGeometry,
    CorridorGeometry,
    PointGeometry,
    RegionPolygon,
    RegionSet,
    WorldPoint,
)
from ..contracts.plan import CompiledRectangle

BUFFER_QUAD_SEGS = 8


@dataclass(frozen=True)
class BooleanGeometry:
    """Opaque internal wrapper that keeps Shapely objects out of serialized contracts."""

    _value: BaseGeometry


def _xy(point: WorldPoint | PointGeometry) -> tuple[float, float]:
    return float(point.x_km), float(point.y_km)


def backend_domain(width_km: float, height_km: float) -> BooleanGeometry:
    return BooleanGeometry(
        Polygon(
            (
                (0.0, 0.0),
                (float(width_km), 0.0),
                (float(width_km), float(height_km)),
                (0.0, float(height_km)),
            )
        )
    )


def backend_point(point: WorldPoint | PointGeometry) -> BooleanGeometry:
    return BooleanGeometry(Point(_xy(point)))


def backend_corridor(corridor: CorridorGeometry) -> BooleanGeometry:
    return BooleanGeometry(LineString(tuple(_xy(point) for point in corridor.centerline)))


def backend_area(area: AreaGeometry) -> BooleanGeometry:
    return BooleanGeometry(Polygon(tuple(_xy(point) for point in area.boundary)))


def backend_area_boundary(area: AreaGeometry) -> BooleanGeometry:
    coordinates = tuple(_xy(point) for point in area.boundary)
    return BooleanGeometry(LineString(coordinates + (coordinates[0],)))


def backend_rectangle(rectangle: CompiledRectangle) -> BooleanGeometry:
    return BooleanGeometry(
        Polygon(
            (
                (rectangle.min_x_km, rectangle.min_y_km),
                (rectangle.max_x_km, rectangle.min_y_km),
                (rectangle.max_x_km, rectangle.max_y_km),
                (rectangle.min_x_km, rectangle.max_y_km),
            )
        )
    )


def backend_region_set(region_set: RegionSet) -> BooleanGeometry:
    polygons = []
    for polygon in region_set.polygons:
        shell = tuple(_xy(point) for point in polygon.outer)
        holes = [tuple(_xy(point) for point in ring) for ring in polygon.holes]
        polygons.append(Polygon(shell, holes=holes))
    if not polygons:
        return BooleanGeometry(GeometryCollection())
    if len(polygons) == 1:
        return BooleanGeometry(polygons[0])
    return BooleanGeometry(MultiPolygon(polygons))


def intersect_geometry(left: BooleanGeometry, right: BooleanGeometry) -> BooleanGeometry:
    return BooleanGeometry(left._value.intersection(right._value))


def subtract_geometry(left: BooleanGeometry, right: BooleanGeometry) -> BooleanGeometry:
    return BooleanGeometry(left._value.difference(right._value))


def buffer_geometry(geometry: BooleanGeometry, distance_km: float) -> BooleanGeometry:
    if distance_km < 0.0:
        raise ValueError("buffer distance must be >= 0")
    return BooleanGeometry(
        geometry._value.buffer(
            float(distance_km),
            quad_segs=BUFFER_QUAD_SEGS,
            cap_style="round",
            join_style="round",
            single_sided=False,
        )
    )


def _normalize_zero(value: float) -> float:
    value = float(value)
    return 0.0 if value == 0.0 else value


def _open_ring_coordinates(coordinates) -> tuple[tuple[float, float], ...]:
    values = tuple(
        (_normalize_zero(x), _normalize_zero(y))
        for x, y, *rest in coordinates
    )
    if len(values) >= 2 and values[0] == values[-1]:
        values = values[:-1]
    return values


def _signed_area(ring: tuple[tuple[float, float], ...]) -> float:
    return 0.5 * sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1])
    )


def _rotate_ring_canonical(
    ring: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    if not ring:
        return ring
    minimum = min(ring)
    rotations = tuple(
        ring[index:] + ring[:index]
        for index, point in enumerate(ring)
        if point == minimum
    )
    return min(rotations)


def _canonical_ring(
    coordinates,
    *,
    ccw: bool,
) -> tuple[tuple[float, float], ...]:
    ring = _open_ring_coordinates(coordinates)
    if len(ring) < 3:
        raise ValueError("polygon ring must contain at least three points")
    signed_area = _signed_area(ring)
    if signed_area == 0.0:
        raise ValueError("polygon ring must have non-zero signed area")
    if (signed_area > 0.0) != ccw:
        ring = tuple(reversed(ring))
    return _rotate_ring_canonical(ring)


def _polygon_components(geometry: BaseGeometry) -> list[Polygon]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        result: list[Polygon] = []
        for part in geometry.geoms:
            result.extend(_polygon_components(part))
        return result
    # Line/point remnants from touching overlays have zero placement area.
    return []


def _canonical_polygon_data(
    polygon: Polygon,
) -> tuple[
    tuple[tuple[float, float], ...],
    tuple[tuple[tuple[float, float], ...], ...],
]:
    outer = _canonical_ring(polygon.exterior.coords, ccw=True)
    holes = tuple(
        sorted(
            _canonical_ring(interior.coords, ccw=False)
            for interior in polygon.interiors
        )
    )
    return outer, holes


def _world_ring(
    coordinates: tuple[tuple[float, float], ...],
) -> tuple[WorldPoint, ...]:
    return tuple(WorldPoint(x_km=x, y_km=y) for x, y in coordinates)


def to_region_set(geometry: BooleanGeometry) -> RegionSet:
    canonical = sorted(
        _canonical_polygon_data(polygon)
        for polygon in _polygon_components(geometry._value)
    )
    polygons = tuple(
        RegionPolygon(
            outer=_world_ring(outer),
            holes=tuple(_world_ring(hole) for hole in holes),
        )
        for outer, holes in canonical
    )
    return RegionSet(polygons=polygons)


def is_canonical_region_set(region_set: RegionSet) -> bool:
    try:
        return to_region_set(backend_region_set(region_set)) == region_set
    except (ValueError, TypeError):
        return False
