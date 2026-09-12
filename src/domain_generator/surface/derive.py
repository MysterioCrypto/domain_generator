from __future__ import annotations

from math import atan, degrees, exp, inf, isfinite, sqrt

import numpy as np

from ..fields.noise import value_noise_2d
from ..grid import GridAdapter
from ..pipeline.rng import RngFactory, RngStage


class SurfaceCapabilityError(RuntimeError):
    """Surface Core 0.1 cannot evaluate the supplied upstream state or recipe."""


def _distance_transform_1d(values: np.ndarray) -> np.ndarray:
    """Exact squared Euclidean distance transform for one 1D sampled axis."""
    if not isinstance(values, np.ndarray) or values.ndim != 1:
        raise SurfaceCapabilityError("distance-transform input must be a 1D numpy array")
    if values.dtype != np.dtype(np.float64):
        values = values.astype(np.float64, copy=False)

    finite_indices = np.flatnonzero(np.isfinite(values))
    result = np.full(values.shape, np.inf, dtype=np.float64)
    if finite_indices.size == 0:
        return result

    n = values.shape[0]
    vertices = np.empty(n, dtype=np.int64)
    boundaries = np.empty(n + 1, dtype=np.float64)

    k = 0
    first = int(finite_indices[0])
    vertices[0] = first
    boundaries[0] = -inf
    boundaries[1] = inf

    for raw_q in finite_indices[1:]:
        q = int(raw_q)
        while True:
            vk = int(vertices[k])
            numerator = (values[q] + q * q) - (values[vk] + vk * vk)
            denominator = 2.0 * (q - vk)
            separation = numerator / denominator
            if separation > boundaries[k] or k == 0:
                break
            k -= 1
        if k == 0:
            vk = int(vertices[k])
            numerator = (values[q] + q * q) - (values[vk] + vk * vk)
            denominator = 2.0 * (q - vk)
            separation = numerator / denominator
        k += 1
        vertices[k] = q
        boundaries[k] = separation
        boundaries[k + 1] = inf

    active = 0
    for q in range(n):
        while active < k and boundaries[active + 1] < q:
            active += 1
        source = int(vertices[active])
        result[q] = (q - source) ** 2 + values[source]
    return result


def distance_to_water_km(water_mask: np.ndarray, *, cell_size_km: float) -> np.ndarray:
    """Exact center-to-center Euclidean distance to nearest water cell in km."""
    if not isinstance(water_mask, np.ndarray) or water_mask.ndim != 2:
        raise SurfaceCapabilityError("water_mask must be a 2D numpy array")
    if water_mask.dtype != np.dtype(np.bool_):
        raise SurfaceCapabilityError("water_mask must use bool dtype")
    if not isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise SurfaceCapabilityError("cell_size_km must be finite and > 0")

    rows, columns = water_mask.shape
    if not bool(water_mask.any()):
        return np.full((rows, columns), np.inf, dtype=np.float64)

    base = np.where(water_mask, 0.0, np.inf).astype(np.float64, copy=False)
    horizontal = np.empty_like(base)
    for row in range(rows):
        horizontal[row, :] = _distance_transform_1d(base[row, :])

    squared_cells = np.empty_like(base)
    for column in range(columns):
        squared_cells[:, column] = _distance_transform_1d(horizontal[:, column])

    return np.sqrt(squared_cells) * float(cell_size_km)


def slope_degrees(elevation_m: np.ndarray, *, cell_size_km: float) -> np.ndarray:
    """Maximum local 8-neighbor slope angle at every grid cell."""
    if not isinstance(elevation_m, np.ndarray) or elevation_m.ndim != 2:
        raise SurfaceCapabilityError("elevation_m must be a 2D numpy array")
    if not np.isfinite(elevation_m).all():
        raise SurfaceCapabilityError("elevation_m must contain only finite values")
    if not isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise SurfaceCapabilityError("cell_size_km must be finite and > 0")

    elevation = elevation_m.astype(np.float64, copy=False)
    rows, columns = elevation.shape
    result = np.zeros((rows, columns), dtype=np.float64)
    orthogonal_run_m = float(cell_size_km) * 1000.0
    diagonal_run_m = orthogonal_run_m * sqrt(2.0)
    directions = (
        (-1, 0, orthogonal_run_m),
        (-1, 1, diagonal_run_m),
        (0, 1, orthogonal_run_m),
        (1, 1, diagonal_run_m),
        (1, 0, orthogonal_run_m),
        (1, -1, diagonal_run_m),
        (0, -1, orthogonal_run_m),
        (-1, -1, diagonal_run_m),
    )

    for row in range(rows):
        for column in range(columns):
            current = float(elevation[row, column])
            max_gradient = 0.0
            for delta_row, delta_column, run_m in directions:
                neighbor_row = row + delta_row
                neighbor_column = column + delta_column
                if not (0 <= neighbor_row < rows and 0 <= neighbor_column < columns):
                    continue
                rise_m = abs(float(elevation[neighbor_row, neighbor_column]) - current)
                gradient = rise_m / run_m
                if gradient > max_gradient:
                    max_gradient = gradient
            result[row, column] = degrees(atan(max_gradient))
    return result


def moisture_field(
    *,
    adapter: GridAdapter,
    water_depth_m: np.ndarray,
    moisture_base: float,
    water_moisture_boost: float,
    water_moisture_decay_km: float,
    moisture_noise_amplitude: float,
    moisture_noise_scale_km: float,
    rng_factory: RngFactory,
    attempt_index: int,
) -> np.ndarray:
    expected_shape = (adapter.rows, adapter.columns)
    if not isinstance(water_depth_m, np.ndarray) or water_depth_m.shape != expected_shape:
        raise SurfaceCapabilityError("water_depth_m must match grid shape")
    if not np.isfinite(water_depth_m).all() or bool(np.any(water_depth_m < 0.0)):
        raise SurfaceCapabilityError("water_depth_m must be finite and non-negative")
    for name, value in (
        ("moisture_base", moisture_base),
        ("water_moisture_boost", water_moisture_boost),
        ("moisture_noise_amplitude", moisture_noise_amplitude),
    ):
        if not isfinite(value) or value < 0.0 or value > 1.0:
            raise SurfaceCapabilityError(f"{name} must be finite and in [0, 1]")
    for name, value in (
        ("water_moisture_decay_km", water_moisture_decay_km),
        ("moisture_noise_scale_km", moisture_noise_scale_km),
    ):
        if not isfinite(value) or value <= 0.0:
            raise SurfaceCapabilityError(f"{name} must be finite and > 0")

    water_mask = (water_depth_m > 0.0).astype(np.bool_, copy=False)
    distance = distance_to_water_km(water_mask, cell_size_km=adapter.cell_size_km)
    result = np.empty(expected_shape, dtype=np.float64)
    has_water = bool(water_mask.any())

    for row in range(adapter.rows):
        for column in range(adapter.columns):
            if bool(water_mask[row, column]):
                result[row, column] = 1.0
                continue

            point = adapter.cell_center(row, column)
            noise = value_noise_2d(
                x_km=point.x_km,
                y_km=point.y_km,
                scale_km=moisture_noise_scale_km,
                rng_factory=rng_factory,
                attempt_index=attempt_index,
                stage=RngStage.SURFACE,
                scope=("field", "moisture", "environmental-noise"),
                purpose="value",
            )
            water_term = 0.0
            if has_water:
                water_term = water_moisture_boost * exp(
                    -float(distance[row, column]) / water_moisture_decay_km
                )
            raw = moisture_base + water_term + moisture_noise_amplitude * noise
            result[row, column] = min(1.0, max(0.0, raw))
    return result


def vegetation_density_field(
    *,
    moisture: np.ndarray,
    slope_deg: np.ndarray,
    water_depth_m: np.ndarray,
    vegetation_slope_zero_deg: float,
) -> np.ndarray:
    if not isinstance(moisture, np.ndarray) or moisture.ndim != 2:
        raise SurfaceCapabilityError("moisture must be a 2D numpy array")
    if not isinstance(slope_deg, np.ndarray) or slope_deg.shape != moisture.shape:
        raise SurfaceCapabilityError("slope_deg must match moisture shape")
    if not isinstance(water_depth_m, np.ndarray) or water_depth_m.shape != moisture.shape:
        raise SurfaceCapabilityError("water_depth_m must match moisture shape")
    if not np.isfinite(moisture).all() or not np.isfinite(slope_deg).all():
        raise SurfaceCapabilityError("moisture and slope must be finite")
    if not isfinite(vegetation_slope_zero_deg) or not 0.0 < vegetation_slope_zero_deg <= 90.0:
        raise SurfaceCapabilityError("vegetation_slope_zero_deg must be finite and in (0, 90]")

    slope_factor = np.clip(
        1.0 - slope_deg.astype(np.float64, copy=False) / vegetation_slope_zero_deg,
        0.0,
        1.0,
    )
    vegetation = moisture.astype(np.float64, copy=False) * slope_factor
    vegetation[water_depth_m > 0.0] = 0.0
    return vegetation
