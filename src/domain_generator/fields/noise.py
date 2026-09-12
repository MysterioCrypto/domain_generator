from __future__ import annotations

from math import floor, isfinite

from ..pipeline.rng import RngFactory, RngKey, RngStage


def _smoothstep(value: float) -> float:
    return value * value * (3.0 - 2.0 * value)


def _lerp(left: float, right: float, amount: float) -> float:
    return left + (right - left) * amount


def _node_value(
    *,
    rng_factory: RngFactory,
    attempt_index: int,
    stage: RngStage,
    scope: tuple[str, ...],
    purpose: str,
    i: int,
    j: int,
) -> float:
    stream = rng_factory.stream(
        RngKey(
            attempt_index=attempt_index,
            stage=stage,
            scope=scope + ("node", str(i), str(j)),
            purpose=purpose,
        )
    )
    return 2.0 * stream.uniform01() - 1.0


def value_noise_2d(
    *,
    x_km: float,
    y_km: float,
    scale_km: float,
    rng_factory: RngFactory,
    attempt_index: int,
    stage: RngStage,
    scope: tuple[str, ...],
    purpose: str = "value",
) -> float:
    """Evaluate deterministic smooth value noise at one world-space point."""
    x = float(x_km)
    y = float(y_km)
    scale = float(scale_km)
    if not isfinite(x) or not isfinite(y):
        raise ValueError("world-space noise coordinates must be finite")
    if not isfinite(scale) or scale <= 0.0:
        raise ValueError("world-space noise scale_km must be finite and > 0")
    if not scope:
        raise ValueError("world-space noise scope must be non-empty")
    if not purpose:
        raise ValueError("world-space noise purpose must be non-empty")

    gx = x / scale
    gy = y / scale
    i0 = floor(gx)
    j0 = floor(gy)
    i1 = i0 + 1
    j1 = j0 + 1
    fx = gx - i0
    fy = gy - j0
    sx = _smoothstep(fx)
    sy = _smoothstep(fy)

    common = dict(
        rng_factory=rng_factory,
        attempt_index=attempt_index,
        stage=stage,
        scope=scope,
        purpose=purpose,
    )
    v00 = _node_value(i=i0, j=j0, **common)
    v10 = _node_value(i=i1, j=j0, **common)
    v01 = _node_value(i=i0, j=j1, **common)
    v11 = _node_value(i=i1, j=j1, **common)

    low = _lerp(v00, v10, sx)
    high = _lerp(v01, v11, sx)
    return _lerp(low, high, sy)
