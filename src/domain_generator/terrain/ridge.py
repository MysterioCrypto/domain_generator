from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite, sqrt

from ..contracts.geometry import BandGeometry
from ..fields.noise import value_noise_2d
from ..pipeline.rng import RngFactory, RngStage


@dataclass(frozen=True, slots=True)
class _Segment:
    ax: float
    ay: float
    dx: float
    dy: float
    length: float
    length_sq: float
    prefix_length: float


@dataclass(frozen=True, slots=True)
class PreparedBand:
    geometry: BandGeometry
    segments: tuple[_Segment, ...]
    total_length: float


def prepare_band(band: BandGeometry) -> PreparedBand:
    segments: list[_Segment] = []
    prefix = 0.0
    for left, right in zip(band.centerline, band.centerline[1:]):
        ax = float(left.x_km)
        ay = float(left.y_km)
        dx = float(right.x_km) - ax
        dy = float(right.y_km) - ay
        length = hypot(dx, dy)
        if length > 0.0:
            segments.append(
                _Segment(
                    ax=ax,
                    ay=ay,
                    dx=dx,
                    dy=dy,
                    length=length,
                    length_sq=length * length,
                    prefix_length=prefix,
                )
            )
        prefix += length

    if not isfinite(prefix) or prefix <= 0.0 or not segments:
        raise ValueError("band centerline must have positive finite total arc length")
    return PreparedBand(
        geometry=band,
        segments=tuple(segments),
        total_length=prefix,
    )


def nearest_centerline_distance_and_t(
    prepared: PreparedBand,
    *,
    x_km: float,
    y_km: float,
) -> tuple[float, float]:
    """Return Euclidean distance to polyline and normalized total arc-length t."""
    x = float(x_km)
    y = float(y_km)
    best_distance_sq: float | None = None
    best_arc = 0.0

    for segment in prepared.segments:
        px = x - segment.ax
        py = y - segment.ay
        scalar = (px * segment.dx + py * segment.dy) / segment.length_sq
        if scalar < 0.0:
            scalar = 0.0
        elif scalar > 1.0:
            scalar = 1.0

        qx = segment.ax + scalar * segment.dx
        qy = segment.ay + scalar * segment.dy
        ddx = x - qx
        ddy = y - qy
        distance_sq = ddx * ddx + ddy * ddy

        if best_distance_sq is None or distance_sq < best_distance_sq:
            best_distance_sq = distance_sq
            best_arc = segment.prefix_length + scalar * segment.length

    if best_distance_sq is None:
        raise ValueError("prepared band has no non-zero-length segments")
    t = best_arc / prepared.total_length
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    return sqrt(best_distance_sq), t


def width_at(band: BandGeometry, t: float) -> float:
    value = float(t)
    samples = band.width_profile
    if value <= float(samples[0].t):
        return float(samples[0].width_km)
    if value >= float(samples[-1].t):
        return float(samples[-1].width_km)

    for left, right in zip(samples, samples[1:]):
        left_t = float(left.t)
        right_t = float(right.t)
        if value <= right_t:
            alpha = (value - left_t) / (right_t - left_t)
            width = float(left.width_km) + (
                float(right.width_km) - float(left.width_km)
            ) * alpha
            if not isfinite(width) or width <= 0.0:
                raise ValueError("band width interpolation produced invalid width")
            return width

    raise ValueError("band width interpolation failed to bracket t")


def ridge_contribution_at(
    prepared: PreparedBand,
    *,
    x_km: float,
    y_km: float,
    height_m: float,
    profile_power: float,
    roughness: float,
    roughness_scale_km: float,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> float:
    distance, t = nearest_centerline_distance_and_t(
        prepared,
        x_km=x_km,
        y_km=y_km,
    )
    width = width_at(prepared.geometry, t)
    half_width = width * 0.5
    if not isfinite(half_width) or half_width <= 0.0:
        raise ValueError("ridge local half-width must be finite and > 0")

    u = distance / half_width
    if roughness != 0.0:
        noise = value_noise_2d(
            x_km=x_km,
            y_km=y_km,
            scale_km=roughness_scale_km,
            rng_factory=rng_factory,
            attempt_index=attempt_index,
            stage=RngStage.TERRAIN,
            scope=("feature", feature_id, "ridge-noise"),
            purpose="value",
        )
        denominator = 1.0 + roughness * 0.35 * noise
        u = u / denominator

    if u > 1.0:
        return 0.0
    if u < 0.0:
        u = 0.0
    return height_m * ((1.0 - u) ** profile_power)
