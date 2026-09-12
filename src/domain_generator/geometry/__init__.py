import shapely

EXPECTED_SHAPELY_VERSION = "2.1.2"
EXPECTED_GEOS_VERSION = "3.13.1"

if shapely.__version__ != EXPECTED_SHAPELY_VERSION:
    raise RuntimeError(
        "unsupported Shapely version for deterministic Core 0.1 boolean geometry: "
        f"expected {EXPECTED_SHAPELY_VERSION}, got {shapely.__version__}"
    )
if shapely.geos_version_string != EXPECTED_GEOS_VERSION:
    raise RuntimeError(
        "unsupported GEOS version for deterministic Core 0.1 boolean geometry: "
        f"expected {EXPECTED_GEOS_VERSION}, got {shapely.geos_version_string}"
    )

from .boolean import (
    BUFFER_QUAD_SEGS,
    BooleanGeometry,
    backend_area,
    backend_area_boundary,
    backend_corridor,
    backend_domain,
    backend_point,
    backend_rectangle,
    backend_region_set,
    buffer_geometry,
    intersect_geometry,
    is_canonical_region_set,
    subtract_geometry,
    to_region_set,
)

__all__ = [
    "EXPECTED_SHAPELY_VERSION",
    "EXPECTED_GEOS_VERSION",
    "BUFFER_QUAD_SEGS",
    "BooleanGeometry",
    "backend_area",
    "backend_area_boundary",
    "backend_corridor",
    "backend_domain",
    "backend_point",
    "backend_rectangle",
    "backend_region_set",
    "buffer_geometry",
    "intersect_geometry",
    "is_canonical_region_set",
    "subtract_geometry",
    "to_region_set",
]
