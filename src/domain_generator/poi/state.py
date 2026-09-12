from __future__ import annotations

from dataclasses import dataclass

from ..contracts.geometry import PointGeometry


@dataclass(frozen=True, slots=True)
class PlacementState:
    """Runtime final point placements for deferred Core 0.1 POI features."""

    final_points: dict[str, PointGeometry]
