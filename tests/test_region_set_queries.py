from domain_generator.contracts.geometry import PointGeometry, RegionPolygon, RegionSet, WorldPoint
from domain_generator.geometry import region_set_covers_point


def test_region_set_covers_outer_and_hole_boundaries_but_not_hole_interior() -> None:
    region = RegionSet(
        polygons=(
            RegionPolygon(
                outer=(
                    WorldPoint(x_km=0.0, y_km=0.0),
                    WorldPoint(x_km=4.0, y_km=0.0),
                    WorldPoint(x_km=4.0, y_km=4.0),
                    WorldPoint(x_km=0.0, y_km=4.0),
                ),
                holes=(
                    (
                        WorldPoint(x_km=1.0, y_km=1.0),
                        WorldPoint(x_km=1.0, y_km=3.0),
                        WorldPoint(x_km=3.0, y_km=3.0),
                        WorldPoint(x_km=3.0, y_km=1.0),
                    ),
                ),
            ),
        )
    )

    assert region_set_covers_point(region, PointGeometry(x_km=0.0, y_km=2.0)) is True
    assert region_set_covers_point(region, PointGeometry(x_km=0.5, y_km=0.5)) is True
    assert region_set_covers_point(region, PointGeometry(x_km=2.0, y_km=2.0)) is False
    assert region_set_covers_point(region, PointGeometry(x_km=1.0, y_km=2.0)) is True
