from __future__ import annotations

import numpy as np

from ..contracts.plan import GenerationPlan
from ..fields.noise import value_noise_2d
from ..grid import GridAdapter
from ..pipeline.rng import RngFactory, RngStage


class TerrainBaseCapabilityError(RuntimeError):
    """Base elevation synthesis cannot execute the supplied terrain plan."""


def synthesize_base_elevation(
    plan: GenerationPlan,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> np.ndarray:
    """Return canonical grid-sampled base elevation before terrain features."""
    shape = (plan.grid.rows, plan.grid.columns)
    if plan.plan_version == "0.1":
        return np.zeros(shape, dtype=np.float32)
    if plan.terrain is None:
        raise TerrainBaseCapabilityError("GenerationPlan 0.2 requires terrain plan")

    adapter = GridAdapter.from_plan(plan)
    result = np.full(shape, float(plan.terrain.base_elevation_m), dtype=np.float64)

    # Canonical id order makes sibling JSON order irrelevant to floating-point
    # accumulation and RNG identity.
    for layer in sorted(plan.terrain.noise_layers, key=lambda item: item.id):
        amplitude = float(layer.amplitude_m)
        if amplitude == 0.0:
            continue
        for row in range(adapter.rows):
            for column in range(adapter.columns):
                point = adapter.cell_center(row, column)
                noise = value_noise_2d(
                    x_km=point.x_km,
                    y_km=point.y_km,
                    scale_km=float(layer.scale_km),
                    rng_factory=rng_factory,
                    attempt_index=attempt_index,
                    stage=RngStage.TERRAIN,
                    scope=("field", "base-elevation", "layer", layer.id),
                    purpose="value",
                )
                result[row, column] += amplitude * noise

    if not np.isfinite(result).all():
        raise TerrainBaseCapabilityError("base elevation synthesis produced non-finite values")
    return result.astype(np.float32)


__all__ = ["TerrainBaseCapabilityError", "synthesize_base_elevation"]
