from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class LakeCandidate:
    """One threshold-qualified connected depression in runtime grid coordinates."""

    cells: tuple[tuple[int, int], ...]
    area_km2: float
    max_depth_m: float
    surface_elevation_m: float


@dataclass(frozen=True, slots=True)
class HydrologyState:
    """Per-attempt runtime hydrology state; not a serialized contract."""

    routing_elevation_m: np.ndarray
    fill_elevation_m: np.ndarray
    flow_direction: np.ndarray
    flow_accumulation_km2: np.ndarray
    stream_mask: np.ndarray
    lake_candidates: tuple[LakeCandidate, ...]
