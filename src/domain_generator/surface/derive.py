from __future__ import annotations

from dataclasses import dataclass
from math import atan, cos, degrees, exp, floor, inf, isfinite, radians, sin, sqrt

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


def moisture_potential_field(
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
    """Return unclamped float64 moisture potential before feature biases."""
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
            result[row, column] = moisture_base + water_term + moisture_noise_amplitude * noise
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
    """Compatibility helper for base-only canonical moisture semantics."""
    result = np.clip(
        moisture_potential_field(
            adapter=adapter,
            water_depth_m=water_depth_m,
            moisture_base=moisture_base,
            water_moisture_boost=water_moisture_boost,
            water_moisture_decay_km=water_moisture_decay_km,
            moisture_noise_amplitude=moisture_noise_amplitude,
            moisture_noise_scale_km=moisture_noise_scale_km,
            rng_factory=rng_factory,
            attempt_index=attempt_index,
        ),
        0.0,
        1.0,
    )
    result[water_depth_m > 0.0] = 1.0
    return result


def vegetation_potential_field(
    *,
    moisture: np.ndarray,
    slope_deg: np.ndarray,
    vegetation_slope_zero_deg: float,
) -> np.ndarray:
    """Return unclamped terrestrial vegetation potential before feature biases."""
    if not isinstance(moisture, np.ndarray) or moisture.ndim != 2:
        raise SurfaceCapabilityError("moisture must be a 2D numpy array")
    if not isinstance(slope_deg, np.ndarray) or slope_deg.shape != moisture.shape:
        raise SurfaceCapabilityError("slope_deg must match moisture shape")
    if not np.isfinite(moisture).all() or not np.isfinite(slope_deg).all():
        raise SurfaceCapabilityError("moisture and slope must be finite")
    if not isfinite(vegetation_slope_zero_deg) or not 0.0 < vegetation_slope_zero_deg <= 90.0:
        raise SurfaceCapabilityError("vegetation_slope_zero_deg must be finite and in (0, 90]")

    slope_factor = np.clip(
        1.0 - slope_deg.astype(np.float64, copy=False) / vegetation_slope_zero_deg,
        0.0,
        1.0,
    )
    return moisture.astype(np.float64, copy=False) * slope_factor


def vegetation_density_field(
    *,
    moisture: np.ndarray,
    slope_deg: np.ndarray,
    water_depth_m: np.ndarray,
    vegetation_slope_zero_deg: float,
) -> np.ndarray:
    """Compatibility helper for base-only canonical vegetation semantics."""
    if not isinstance(water_depth_m, np.ndarray) or water_depth_m.shape != moisture.shape:
        raise SurfaceCapabilityError("water_depth_m must match moisture shape")
    vegetation = np.clip(
        vegetation_potential_field(
            moisture=moisture,
            slope_deg=slope_deg,
            vegetation_slope_zero_deg=vegetation_slope_zero_deg,
        ),
        0.0,
        1.0,
    )
    vegetation[water_depth_m > 0.0] = 0.0
    return vegetation



_ENVIRONMENTAL_LAPSE_RATE_C_PER_KM = 6.5
_OROGRAPHIC_SAMPLES_PER_SCALE = 8
_OROGRAPHIC_HORIZON_SCALES = 4


def _sample_cell_centered_bilinear(
    field: np.ndarray,
    adapter: GridAdapter,
    x_km: float,
    y_km: float,
) -> float:
    if not 0.0 <= x_km <= adapter.width_km or not 0.0 <= y_km <= adapter.height_km:
        raise SurfaceCapabilityError("bilinear sample point lies outside domain")

    column_f = x_km / adapter.cell_size_km - 0.5
    row_f = (adapter.height_km - y_km) / adapter.cell_size_km - 0.5
    c0 = floor(column_f)
    r0 = floor(row_f)
    tx = column_f - c0
    ty = row_f - r0

    value = 0.0
    total = 0.0
    for delta_row, weight_y in ((0, 1.0 - ty), (1, ty)):
        for delta_column, weight_x in ((0, 1.0 - tx), (1, tx)):
            row = min(adapter.rows - 1, max(0, r0 + delta_row))
            column = min(adapter.columns - 1, max(0, c0 + delta_column))
            weight = max(0.0, weight_x * weight_y)
            value += weight * float(field[row, column])
            total += weight
    if total <= 0.0:
        raise SurfaceCapabilityError("bilinear climate sampling collapsed to zero weight")
    return value / total


def annual_mean_temperature_field(
    *,
    adapter: GridAdapter,
    elevation_m: np.ndarray,
    mean_temperature_c: float,
    north_minus_south_temperature_c: float,
    temperature_noise_amplitude_c: float,
    climate_noise_scale_km: float,
    rng_factory: RngFactory,
    attempt_index: int,
) -> np.ndarray:
    """Return annual mean air temperature in degrees Celsius as float64."""
    expected_shape = (adapter.rows, adapter.columns)
    if not isinstance(elevation_m, np.ndarray) or elevation_m.shape != expected_shape:
        raise SurfaceCapabilityError("elevation_m must match grid shape")
    if not bool(np.isfinite(elevation_m).all()):
        raise SurfaceCapabilityError("elevation_m must be finite")
    for name, value in (
        ("mean_temperature_c", mean_temperature_c),
        ("north_minus_south_temperature_c", north_minus_south_temperature_c),
        ("temperature_noise_amplitude_c", temperature_noise_amplitude_c),
        ("climate_noise_scale_km", climate_noise_scale_km),
    ):
        if not isfinite(value):
            raise SurfaceCapabilityError(f"{name} must be finite")
    if temperature_noise_amplitude_c < 0.0:
        raise SurfaceCapabilityError("temperature_noise_amplitude_c must be >= 0")
    if climate_noise_scale_km <= 0.0:
        raise SurfaceCapabilityError("climate_noise_scale_km must be > 0")

    elevation64 = elevation_m.astype(np.float64, copy=False)
    mean_elevation_m = float(np.mean(elevation64))
    result = np.empty(expected_shape, dtype=np.float64)

    for row in range(adapter.rows):
        for column in range(adapter.columns):
            point = adapter.cell_center(row, column)
            y_norm = point.y_km / adapter.height_km
            macro = mean_temperature_c + north_minus_south_temperature_c * (y_norm - 0.5)
            lapse = -_ENVIRONMENTAL_LAPSE_RATE_C_PER_KM * (
                (float(elevation64[row, column]) - mean_elevation_m) / 1000.0
            )
            noise = value_noise_2d(
                x_km=point.x_km,
                y_km=point.y_km,
                scale_km=climate_noise_scale_km,
                rng_factory=rng_factory,
                attempt_index=attempt_index,
                stage=RngStage.SURFACE,
                scope=("field", "climate", "temperature"),
                purpose="value",
            )
            result[row, column] = macro + lapse + temperature_noise_amplitude_c * noise
    return result


def _upwind_reference_elevation_m(
    *,
    adapter: GridAdapter,
    elevation_m: np.ndarray,
    x_km: float,
    y_km: float,
    transport_dx: float,
    transport_dy: float,
    orographic_scale_km: float,
) -> float:
    step_km = orographic_scale_km / float(_OROGRAPHIC_SAMPLES_PER_SCALE)
    sample_count = _OROGRAPHIC_SAMPLES_PER_SCALE * _OROGRAPHIC_HORIZON_SCALES
    weighted = 0.0
    total_weight = 0.0

    for index in range(1, sample_count + 1):
        distance_km = step_km * float(index)
        sample_x = x_km - transport_dx * distance_km
        sample_y = y_km - transport_dy * distance_km
        if not (0.0 <= sample_x <= adapter.width_km and 0.0 <= sample_y <= adapter.height_km):
            break
        weight = exp(-distance_km / orographic_scale_km)
        weighted += weight * _sample_cell_centered_bilinear(
            elevation_m,
            adapter,
            sample_x,
            sample_y,
        )
        total_weight += weight

    if total_weight <= 0.0:
        return _sample_cell_centered_bilinear(elevation_m, adapter, x_km, y_km)
    return weighted / total_weight


def annual_precipitation_field(
    *,
    adapter: GridAdapter,
    elevation_m: np.ndarray,
    water_depth_m: np.ndarray,
    mean_annual_precipitation_mm: float,
    moisture_transport_bearing_deg: float,
    orographic_scale_km: float,
    orographic_strength: float,
    precipitation_noise_log_amplitude: float,
    climate_noise_scale_km: float,
    rng_factory: RngFactory,
    attempt_index: int,
) -> np.ndarray:
    """Return annual precipitation in mm/year as a deterministic float64 field."""
    expected_shape = (adapter.rows, adapter.columns)
    if not isinstance(elevation_m, np.ndarray) or elevation_m.shape != expected_shape:
        raise SurfaceCapabilityError("elevation_m must match grid shape")
    if not isinstance(water_depth_m, np.ndarray) or water_depth_m.shape != expected_shape:
        raise SurfaceCapabilityError("water_depth_m must match grid shape")
    if not bool(np.isfinite(elevation_m).all()) or not bool(np.isfinite(water_depth_m).all()):
        raise SurfaceCapabilityError("climate upstream fields must be finite")
    if bool(np.any(water_depth_m < 0.0)):
        raise SurfaceCapabilityError("water_depth_m must be non-negative")
    if not isfinite(mean_annual_precipitation_mm) or mean_annual_precipitation_mm <= 0.0:
        raise SurfaceCapabilityError("mean_annual_precipitation_mm must be finite and > 0")
    if (
        not isfinite(moisture_transport_bearing_deg)
        or not 0.0 <= moisture_transport_bearing_deg < 360.0
    ):
        raise SurfaceCapabilityError("moisture_transport_bearing_deg must be in [0, 360)")
    if not isfinite(orographic_scale_km) or orographic_scale_km <= 0.0:
        raise SurfaceCapabilityError("orographic_scale_km must be finite and > 0")
    if not isfinite(orographic_strength) or orographic_strength < 0.0:
        raise SurfaceCapabilityError("orographic_strength must be finite and >= 0")
    if (
        not isfinite(precipitation_noise_log_amplitude)
        or precipitation_noise_log_amplitude < 0.0
    ):
        raise SurfaceCapabilityError(
            "precipitation_noise_log_amplitude must be finite and >= 0"
        )
    if not isfinite(climate_noise_scale_km) or climate_noise_scale_km <= 0.0:
        raise SurfaceCapabilityError("climate_noise_scale_km must be finite and > 0")

    bearing = radians(moisture_transport_bearing_deg)
    transport_dx = sin(bearing)
    transport_dy = cos(bearing)
    elevation64 = elevation_m.astype(np.float64, copy=False)
    log_weight = np.empty(expected_shape, dtype=np.float64)

    for row in range(adapter.rows):
        for column in range(adapter.columns):
            point = adapter.cell_center(row, column)
            upwind = _upwind_reference_elevation_m(
                adapter=adapter,
                elevation_m=elevation64,
                x_km=point.x_km,
                y_km=point.y_km,
                transport_dx=transport_dx,
                transport_dy=transport_dy,
                orographic_scale_km=orographic_scale_km,
            )
            relative_relief_km = (float(elevation64[row, column]) - upwind) / 1000.0
            noise = value_noise_2d(
                x_km=point.x_km,
                y_km=point.y_km,
                scale_km=climate_noise_scale_km,
                rng_factory=rng_factory,
                attempt_index=attempt_index,
                stage=RngStage.SURFACE,
                scope=("field", "climate", "precipitation"),
                purpose="value",
            )
            log_weight[row, column] = (
                orographic_strength * relative_relief_km
                + precipitation_noise_log_amplitude * noise
            )

    land_mask = water_depth_m <= 0.0
    normalization_mask = land_mask if bool(land_mask.any()) else np.ones(expected_shape, dtype=np.bool_)
    reference_max = float(np.max(log_weight[normalization_mask]))
    raw_weight = np.exp(log_weight - reference_max)
    mean_weight = float(np.mean(raw_weight[normalization_mask]))
    if not isfinite(mean_weight) or mean_weight <= 0.0:
        raise SurfaceCapabilityError("precipitation normalization collapsed")
    result = mean_annual_precipitation_mm * raw_weight / mean_weight
    if not bool(np.isfinite(result).all()) or bool(np.any(result <= 0.0)):
        raise SurfaceCapabilityError("annual precipitation must be finite and positive")
    return result



_HOLDRIDGE_PET_MM_PER_C = 58.93


@dataclass(frozen=True, slots=True)
class EffectiveMoistureComponents:
    climatic_wetness: np.ndarray
    water_proximity_signal: np.ndarray
    catchment_signal: np.ndarray
    climate_gated_catchment: np.ndarray
    local_hydrology: np.ndarray
    pre_slope_moisture: np.ndarray
    slope_retention: np.ndarray
    effective_moisture: np.ndarray


def effective_surface_moisture_components(
    *,
    adapter: GridAdapter,
    annual_mean_temperature_c: np.ndarray,
    annual_precipitation_mm: np.ndarray,
    flow_accumulation_km2: np.ndarray,
    water_depth_m: np.ndarray,
    slope_deg: np.ndarray,
    stream_threshold_km2: float,
    water_moisture_boost: float,
    water_moisture_decay_km: float,
) -> EffectiveMoistureComponents:
    """Build deterministic Core 0.2 effective-moisture components as float64 arrays."""
    expected_shape = (adapter.rows, adapter.columns)
    fields = (
        ("annual_mean_temperature_c", annual_mean_temperature_c),
        ("annual_precipitation_mm", annual_precipitation_mm),
        ("flow_accumulation_km2", flow_accumulation_km2),
        ("water_depth_m", water_depth_m),
        ("slope_deg", slope_deg),
    )
    for name, field in fields:
        if not isinstance(field, np.ndarray) or field.shape != expected_shape:
            raise SurfaceCapabilityError(f"{name} must match grid shape")
        if not bool(np.isfinite(field).all()):
            raise SurfaceCapabilityError(f"{name} must be finite")

    if bool(np.any(annual_precipitation_mm <= 0.0)):
        raise SurfaceCapabilityError("annual_precipitation_mm must be positive")
    if bool(np.any(flow_accumulation_km2 < 0.0)):
        raise SurfaceCapabilityError("flow_accumulation_km2 must be non-negative")
    if bool(np.any(water_depth_m < 0.0)):
        raise SurfaceCapabilityError("water_depth_m must be non-negative")
    if bool(np.any(slope_deg < 0.0)) or bool(np.any(slope_deg > 90.0)):
        raise SurfaceCapabilityError("slope_deg must be in [0, 90]")
    if not isfinite(stream_threshold_km2) or stream_threshold_km2 <= 0.0:
        raise SurfaceCapabilityError("stream_threshold_km2 must be finite and > 0")
    if (
        not isfinite(water_moisture_boost)
        or water_moisture_boost < 0.0
        or water_moisture_boost > 1.0
    ):
        raise SurfaceCapabilityError("water_moisture_boost must be finite and in [0, 1]")
    if not isfinite(water_moisture_decay_km) or water_moisture_decay_km <= 0.0:
        raise SurfaceCapabilityError("water_moisture_decay_km must be finite and > 0")

    temperature = annual_mean_temperature_c.astype(np.float64, copy=False)
    precipitation = annual_precipitation_mm.astype(np.float64, copy=False)
    accumulation = flow_accumulation_km2.astype(np.float64, copy=False)
    slope = slope_deg.astype(np.float64, copy=False)

    biotemperature = np.clip(temperature, 0.0, 30.0)
    pet_proxy_mm = _HOLDRIDGE_PET_MM_PER_C * biotemperature
    climatic_wetness = precipitation / (precipitation + pet_proxy_mm)
    climatic_wetness = np.clip(climatic_wetness, 0.0, 1.0)

    water_mask = water_depth_m > 0.0
    distance = distance_to_water_km(
        water_mask.astype(np.bool_, copy=False),
        cell_size_km=adapter.cell_size_km,
    )
    if bool(water_mask.any()):
        water_proximity = water_moisture_boost * np.exp(
            -distance / float(water_moisture_decay_km)
        )
    else:
        water_proximity = np.zeros(expected_shape, dtype=np.float64)

    catchment_signal = accumulation / (
        accumulation + float(stream_threshold_km2)
    )
    catchment_signal = np.clip(catchment_signal, 0.0, 1.0)
    climate_gated_catchment = climatic_wetness * catchment_signal
    local_hydrology = np.maximum(water_proximity, climate_gated_catchment)

    pre_slope = climatic_wetness + (1.0 - climatic_wetness) * local_hydrology
    slope_retention = np.square(np.cos(np.radians(slope)))
    effective = np.clip(pre_slope * slope_retention, 0.0, 1.0)
    effective[water_mask] = 1.0

    return EffectiveMoistureComponents(
        climatic_wetness=climatic_wetness,
        water_proximity_signal=water_proximity,
        catchment_signal=catchment_signal,
        climate_gated_catchment=climate_gated_catchment,
        local_hydrology=local_hydrology,
        pre_slope_moisture=pre_slope,
        slope_retention=slope_retention,
        effective_moisture=effective,
    )


_MIAMI_TEMP_INTERCEPT = 1.315
_MIAMI_TEMP_SLOPE_PER_C = 0.119
_MIAMI_TEMP_REFERENCE_C = 30.0


@dataclass(frozen=True, slots=True)
class VegetationComponents:
    thermal_suitability: np.ndarray
    vegetation_potential: np.ndarray


def climate_aware_vegetation_components(
    *,
    moisture: np.ndarray,
    annual_mean_temperature_c: np.ndarray,
) -> VegetationComponents:
    """Build deterministic Core 0.2 climate-aware vegetation components."""
    if not isinstance(moisture, np.ndarray) or moisture.ndim != 2:
        raise SurfaceCapabilityError("moisture must be a 2D numpy array")
    if (
        not isinstance(annual_mean_temperature_c, np.ndarray)
        or annual_mean_temperature_c.shape != moisture.shape
    ):
        raise SurfaceCapabilityError(
            "annual_mean_temperature_c must match moisture shape"
        )
    if not bool(np.isfinite(moisture).all()):
        raise SurfaceCapabilityError("moisture must be finite")
    if not bool(np.isfinite(annual_mean_temperature_c).all()):
        raise SurfaceCapabilityError("annual_mean_temperature_c must be finite")
    if bool(np.any(moisture < 0.0)) or bool(np.any(moisture > 1.0)):
        raise SurfaceCapabilityError("moisture must be in [0, 1]")

    temperature = annual_mean_temperature_c.astype(np.float64, copy=False)
    temperature_for_response = np.minimum(
        temperature,
        _MIAMI_TEMP_REFERENCE_C,
    )

    exponent = np.clip(
        _MIAMI_TEMP_INTERCEPT
        - _MIAMI_TEMP_SLOPE_PER_C * temperature_for_response,
        -700.0,
        700.0,
    )
    response = 1.0 / (1.0 + np.exp(exponent))

    reference_exponent = (
        _MIAMI_TEMP_INTERCEPT
        - _MIAMI_TEMP_SLOPE_PER_C * _MIAMI_TEMP_REFERENCE_C
    )
    reference_response = 1.0 / (1.0 + exp(reference_exponent))

    thermal_suitability = np.clip(response / reference_response, 0.0, 1.0)
    vegetation_potential = np.clip(
        moisture.astype(np.float64, copy=False) * thermal_suitability,
        0.0,
        1.0,
    )

    return VegetationComponents(
        thermal_suitability=thermal_suitability,
        vegetation_potential=vegetation_potential,
    )
