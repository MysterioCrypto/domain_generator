from __future__ import annotations

from domain_generator.contracts.geometry import RegionPolygon, RegionSet, WorldPoint
from domain_generator.geometry import (
    backend_domain,
    backend_region_set,
    buffer_geometry,
    backend_point,
    intersect_geometry,
    subtract_geometry,
    to_region_set,
)
from domain_generator.contracts.geometry import PointGeometry


def signed_area(points: tuple[WorldPoint, ...]) -> float:
    return 0.5 * sum(
        left.x_km * right.y_km - right.x_km * left.y_km
        for left, right in zip(points, points[1:] + points[:1])
    )


def test_domain_canonicalizes_to_ccw_ring_with_lexicographic_start() -> None:
    region = to_region_set(backend_domain(100.0, 80.0))

    assert len(region.polygons) == 1
    polygon = region.polygons[0]
    assert polygon.outer[0] == WorldPoint(x_km=0.0, y_km=0.0)
    assert signed_area(polygon.outer) > 0.0
    assert polygon.holes == ()


def test_difference_canonicalizes_hole_clockwise() -> None:
    domain = backend_domain(100.0, 80.0)
    forbidden = buffer_geometry(
        backend_point(PointGeometry(x_km=50.0, y_km=40.0)),
        5.0,
    )

    region = to_region_set(subtract_geometry(domain, forbidden))

    assert len(region.polygons) == 1
    polygon = region.polygons[0]
    assert len(polygon.holes) == 1
    assert signed_area(polygon.outer) > 0.0
    assert signed_area(polygon.holes[0]) < 0.0
    assert polygon.holes[0][0] == min(polygon.holes[0], key=lambda p: (p.x_km, p.y_km))


def test_region_set_round_trip_is_canonical_and_stable() -> None:
    raw = RegionSet(
        polygons=(
            RegionPolygon(
                outer=(
                    WorldPoint(x_km=10.0, y_km=10.0),
                    WorldPoint(x_km=0.0, y_km=10.0),
                    WorldPoint(x_km=0.0, y_km=0.0),
                    WorldPoint(x_km=10.0, y_km=0.0),
                ),
            ),
        )
    )

    first = to_region_set(backend_region_set(raw))
    second = to_region_set(backend_region_set(first))

    assert first == second
    assert first.polygons[0].outer[0] == WorldPoint(x_km=0.0, y_km=0.0)
    assert signed_area(first.polygons[0].outer) > 0.0


def test_intersection_can_be_empty_region_set() -> None:
    left = buffer_geometry(
        backend_point(PointGeometry(x_km=10.0, y_km=10.0)),
        1.0,
    )
    right = buffer_geometry(
        backend_point(PointGeometry(x_km=90.0, y_km=70.0)),
        1.0,
    )

    result = to_region_set(intersect_geometry(left, right))

    assert result.polygons == ()
