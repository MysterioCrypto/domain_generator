from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SurfaceState:
    """Per-attempt runtime surface state; not a serialized root contract."""

    moisture: np.ndarray
    vegetation_density: np.ndarray
