from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from ..contracts.geometry import AreaGeometry, PointGeometry
from ..contracts.plan import GenerationPlan
from ..geometry import backend_area, intersection_area_km2
from ..grid import GridAdapter
from ..layout.area import distance_point_area_boundary, point_in_area


@dataclass(frozen=True, slots=True)
class FlattenSpec:
    feature_id: str
    geometry: AreaGeometry
    target_elevation_m: float
    blend_width_km: float

    def __post_init__(self) -> None:
        if not self.feature_id:
            raise ValueError("flatten feature_id must be non-empty")
        if not isfinite(self.target_elevation_m):
            raise ValueError("flatten target_elevation_m must be finite")
        if not isfinite(self.blend_width_km) or self.blend_width_km < 0.0:
            raise ValueError("flatten blend_width_km must be finite and >= 0")


def flatten_weight_at(
    point: PointGeometry,
    area: AreaGeometry,
    *,
    blend_width_km: float,
) -> float:
    """Return shaping weight in [0,1], with transition entirely inside the area."""
    if not point_in_area(point, area):
        return 0.0

    distance = distance_point_area_boundary(point, area)
    # The boundary itself remains unchanged even for zero-width flattening.
    if distance <= 0.0:
        return 0.0
    if blend_width_km == 0.0:
        return 1.0
    weight = distance / blend_width_km
    if weight <= 0.0:
        return 0.0
    if weight >= 1.0:
        return 1.0
    return weight


def flatten_conflicts(specs: tuple[FlattenSpec, ...]) -> tuple[tuple[str, str], ...]:
    """Return sorted pairs whose polygon interiors overlap with positive area."""
    conflicts: list[tuple[str, str]] = []
    ordered = tuple(sorted(specs, key=lambda item: item.feature_id))
    for index, left in enumerate(ordered):
        left_backend = backend_area(left.geometry)
        for right in ordered[index + 1 :]:
            overlap = intersection_area_km2(left_backend, backend_area(right.geometry))
            if overlap > 0.0:
                conflicts.append((left.feature_id, right.feature_id))
    return tuple(conflicts)


def apply_flatten(
    plan: GenerationPlan,
    structural_elevation: np.ndarray,
    spec: FlattenSpec,
) -> np.ndarray:
    """Apply one flatten against an immutable structural snapshot and return a copy."""
    if structural_elevation.shape != (plan.grid.rows, plan.grid.columns):
        raise ValueError("structural elevation shape does not match plan grid")

    result = np.array(structural_elevation, dtype=np.float64, copy=True)
    adapter = GridAdapter.from_plan(plan)
    for row in range(plan.grid.rows):
        for column in range(plan.grid.columns):
            point = adapter.cell_center(row, column)
            weight = flatten_weight_at(
                point,
                spec.geometry,
                blend_width_km=spec.blend_width_km,
            )
            if weight == 0.0:
                continue
            original = float(structural_elevation[row, column])
            result[row, column] = (
                original * (1.0 - weight)
                + spec.target_elevation_m * weight
            )
    return result


def compose_nonoverlapping_flatten(
    plan: GenerationPlan,
    structural_elevation: np.ndarray,
    specs: tuple[FlattenSpec, ...],
) -> np.ndarray:
    """Compose disjoint flatten operators, each reading the same structural snapshot."""
    conflicts = flatten_conflicts(specs)
    if conflicts:
        # Caller turns this attempt-level condition into validation failure.
        return np.array(structural_elevation, dtype=np.float64, copy=True)

    structural = np.array(structural_elevation, dtype=np.float64, copy=False)
    result = np.array(structural, dtype=np.float64, copy=True)
    for spec in sorted(specs, key=lambda item: item.feature_id):
        shaped = apply_flatten(plan, structural, spec)
        # Regions are guaranteed to have no positive-area overlap, so replacing changed
        # cells cannot introduce sequential operator semantics.
        changed = shaped != structural
        result[changed] = shaped[changed]
    return result
