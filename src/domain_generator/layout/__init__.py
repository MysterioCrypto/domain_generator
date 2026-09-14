from . import geometry as _geometry
from .geometry import (
    GEOMETRY_EPSILON_KM,
    LayoutCapabilityError,
    geometry_layout_stage,
    validate_geometry_layout,
)
from .v02 import generate_geometry_layout, smooth_band_centerline, smooth_band_geometry

# Keep legacy modules that import ``layout.geometry.generate_geometry_layout``
# coherent with the 0.2 dispatcher. The wrapper itself keeps a stable reference
# to the original 0.1 implementation.
_geometry.generate_geometry_layout = generate_geometry_layout

from .point import generate_point_layout, point_layout_stage, validate_point_layout
from .reservations import (
    ReservationCapabilityError,
    generate_layout,
    layout_stage,
    materialize_placement_reservations,
    validate_layout,
)

__all__ = [
    "GEOMETRY_EPSILON_KM",
    "LayoutCapabilityError",
    "ReservationCapabilityError",
    "generate_geometry_layout",
    "geometry_layout_stage",
    "validate_geometry_layout",
    "generate_point_layout",
    "point_layout_stage",
    "validate_point_layout",
    "generate_layout",
    "layout_stage",
    "materialize_placement_reservations",
    "validate_layout",
    "smooth_band_centerline",
    "smooth_band_geometry",
]
