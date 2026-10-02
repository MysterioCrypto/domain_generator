from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SurfaceState:
    """Per-attempt runtime surface state; not a serialized root contract."""

    moisture: np.ndarray
    vegetation_density: np.ndarray
    annual_mean_temperature_c: np.ndarray | None = None
    annual_precipitation_mm: np.ndarray | None = None
    monthly_mean_temperature_c: np.ndarray | None = None
    monthly_precipitation_mm: np.ndarray | None = None
    climate_regime_koppen_geiger: np.ndarray | None = None
