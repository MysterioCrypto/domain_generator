from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class TerrainState:
    """Per-attempt runtime terrain state; not a serialized contract."""

    elevation_m: np.ndarray
