from __future__ import annotations

from ..contracts.geometry import BandGeometry, WorldPoint
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import GenerationPlan
from ..pipeline.rng import RngFactory
from .geometry import generate_geometry_layout as _generate_geometry_layout_v01


_CHAIKIN_ITERATIONS = 2


def _chaikin_once(points: tuple[WorldPoint, ...]) -> tuple[WorldPoint, ...]:
    if len(points) <= 2:
        return points
    result: list[WorldPoint] = [points[0]]
    for left, right in zip(points, points[1:]):
        q = WorldPoint(
            x_km=0.75 * left.x_km + 0.25 * right.x_km,
            y_km=0.75 * left.y_km + 0.25 * right.y_km,
        )
        r = WorldPoint(
            x_km=0.25 * left.x_km + 0.75 * right.x_km,
            y_km=0.25 * left.y_km + 0.75 * right.y_km,
        )
        if q != result[-1]:
            result.append(q)
        if r != result[-1]:
            result.append(r)
    if points[-1] != result[-1]:
        result.append(points[-1])
    return tuple(result)


def smooth_band_centerline(points: tuple[WorldPoint, ...]) -> tuple[WorldPoint, ...]:
    """Endpoint-preserving deterministic Chaikin smoothing independent of raster resolution."""
    smoothed = points
    for _ in range(_CHAIKIN_ITERATIONS):
        smoothed = _chaikin_once(smoothed)
    return smoothed


def smooth_band_geometry(band: BandGeometry) -> BandGeometry:
    return band.model_copy(update={"centerline": smooth_band_centerline(band.centerline)})


def generate_geometry_layout(
    plan: GenerationPlan,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> LayoutCandidate:
    candidate = _generate_geometry_layout_v01(
        plan,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    if plan.plan_version != "0.2":
        return candidate

    geometries = dict(candidate.geometry_realizations)
    for feature_id, geometry in sorted(geometries.items()):
        if isinstance(geometry, BandGeometry):
            geometries[feature_id] = smooth_band_geometry(geometry)
    return candidate.model_copy(update={"geometry_realizations": geometries})


__all__ = ["generate_geometry_layout", "smooth_band_centerline", "smooth_band_geometry"]
