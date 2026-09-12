from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class HydrologyState:
    """Per-attempt runtime hydrology routing state; not a serialized contract."""

    routing_elevation_m: np.ndarray
    flow_direction: np.ndarray
    flow_accumulation_km2: np.ndarray
