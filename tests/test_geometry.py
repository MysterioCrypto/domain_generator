import pytest
from pydantic import TypeAdapter, ValidationError

from domain_generator.contracts.geometry import Geometry, RegionSet


GEOMETRY_ADAPTER = TypeAdapter(Geometry)


def test_band_geometry_parses_and_is_immutable() -> None:
    band = GEOMETRY_ADAPTER.validate_python(
        {
            "type": "band",
            "centerline": [
                {"x_km": 1.0, "y_km": 2.0},
                {"x_km": 3.0, "y_km": 4.0},
            ],
            "width_profile": [
                {"t": 0.0, "width_km": 10.0},
                {"t": 1.0, "width_km": 20.0},
            ],
        }
    )
    assert band.width_profile[1].width_km == 20.0
    with pytest.raises(ValidationError):
        band.width_profile[0].width_km = 12.0


def test_band_requires_strictly_increasing_profile() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        GEOMETRY_ADAPTER.validate_python(
            {
                "type": "band",
                "centerline": [
                    {"x_km": 1.0, "y_km": 2.0},
                    {"x_km": 3.0, "y_km": 4.0},
                ],
                "width_profile": [
                    {"t": 0.0, "width_km": 10.0},
                    {"t": 0.5, "width_km": 15.0},
                    {"t": 0.5, "width_km": 20.0},
                    {"t": 1.0, "width_km": 20.0},
                ],
            }
        )


def test_empty_region_set_is_structurally_valid() -> None:
    region = RegionSet.model_validate({"type": "region_set", "polygons": []})
    assert region.polygons == ()
