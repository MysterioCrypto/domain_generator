from __future__ import annotations

import numpy as np

from .ids import lake_feature_id
from .routing import HydrologyCapabilityError
from .state import LakeCandidate


def accepted_lake_cell_map(
    shape: tuple[int, int],
    lake_candidates: tuple[LakeCandidate, ...],
) -> dict[tuple[int, int], str]:
    rows, columns = shape
    mapping: dict[tuple[int, int], str] = {}
    for index, candidate in enumerate(lake_candidates):
        lake_id = lake_feature_id(index)
        for cell in candidate.cells:
            row, column = cell
            if not (0 <= row < rows and 0 <= column < columns):
                raise HydrologyCapabilityError("lake candidate cell is outside grid")
            if cell in mapping:
                raise HydrologyCapabilityError("accepted lake candidates overlap")
            mapping[cell] = lake_id
    return mapping


def river_depth_proxy_m(
    catchment_area_km2: float,
    *,
    stream_threshold_km2: float,
    river_depth_at_threshold_m: float,
    river_depth_exponent: float,
) -> float:
    values = (
        catchment_area_km2,
        stream_threshold_km2,
        river_depth_at_threshold_m,
        river_depth_exponent,
    )
    if not all(np.isfinite(value) for value in values):
        raise HydrologyCapabilityError("river depth proxy inputs must be finite")
    if stream_threshold_km2 <= 0.0:
        raise HydrologyCapabilityError("stream_threshold_km2 must be > 0")
    if river_depth_at_threshold_m <= 0.0:
        raise HydrologyCapabilityError("river_depth_at_threshold_m must be > 0")
    if river_depth_exponent < 0.0:
        raise HydrologyCapabilityError("river_depth_exponent must be >= 0")
    if catchment_area_km2 < stream_threshold_km2:
        raise HydrologyCapabilityError("river depth proxy requires stream catchment >= threshold")
    return float(
        river_depth_at_threshold_m
        * (catchment_area_km2 / stream_threshold_km2) ** river_depth_exponent
    )


def build_water_depth_m(
    terrain_elevation_m: np.ndarray,
    fill_elevation_m: np.ndarray,
    flow_accumulation_km2: np.ndarray,
    stream_mask: np.ndarray,
    lake_candidates: tuple[LakeCandidate, ...],
    *,
    stream_threshold_km2: float,
    river_depth_at_threshold_m: float,
    river_depth_exponent: float,
) -> np.ndarray:
    if not isinstance(terrain_elevation_m, np.ndarray) or terrain_elevation_m.ndim != 2:
        raise HydrologyCapabilityError("terrain_elevation_m must be a 2D numpy array")
    shape = terrain_elevation_m.shape
    for name, array in (
        ("fill_elevation_m", fill_elevation_m),
        ("flow_accumulation_km2", flow_accumulation_km2),
        ("stream_mask", stream_mask),
    ):
        if not isinstance(array, np.ndarray) or array.shape != shape:
            raise HydrologyCapabilityError(f"{name} must match terrain shape")
    if stream_mask.dtype != np.dtype(np.bool_):
        raise HydrologyCapabilityError("stream_mask must use bool dtype")
    if not np.isfinite(terrain_elevation_m).all():
        raise HydrologyCapabilityError("terrain elevation must be finite")
    if not np.isfinite(fill_elevation_m).all():
        raise HydrologyCapabilityError("fill elevation must be finite")
    if not np.isfinite(flow_accumulation_km2).all():
        raise HydrologyCapabilityError("flow accumulation must be finite")

    terrain = terrain_elevation_m.astype(np.float64, copy=False)
    fill = fill_elevation_m.astype(np.float64, copy=False)
    if not bool(np.all(fill >= terrain)):
        raise HydrologyCapabilityError("fill elevation must not fall below terrain")

    lake_cells = accepted_lake_cell_map(shape, lake_candidates)
    result = np.zeros(shape, dtype=np.float64)

    for row in range(shape[0]):
        for column in range(shape[1]):
            cell = (row, column)
            if cell in lake_cells:
                result[cell] = float(fill[cell] - terrain[cell])
                continue
            if bool(stream_mask[cell]):
                result[cell] = river_depth_proxy_m(
                    float(flow_accumulation_km2[cell]),
                    stream_threshold_km2=stream_threshold_km2,
                    river_depth_at_threshold_m=river_depth_at_threshold_m,
                    river_depth_exponent=river_depth_exponent,
                )

    if not np.isfinite(result).all() or bool(np.any(result < 0.0)):
        raise HydrologyCapabilityError("water depth must be finite and non-negative")
    return result.astype(np.float32)
