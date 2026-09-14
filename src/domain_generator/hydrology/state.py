from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..contracts.data import HydroFeature, RiverNetwork


Cell = tuple[int, int]


@dataclass(frozen=True, slots=True)
class LakeCandidate:
    """One threshold-qualified connected depression in runtime grid coordinates."""

    cells: tuple[Cell, ...]
    area_km2: float
    max_depth_m: float
    surface_elevation_m: float


@dataclass(frozen=True, slots=True)
class LakeOutlet:
    """One canonical physical spill transition for an accepted lake."""

    lake_id: str
    lake_cell: Cell
    receiver_cell: Cell
    saddle_elevation_m: float


@dataclass(frozen=True, slots=True)
class ContinuousRoutingField:
    """Internal Core 0.2 weighted drainage field.

    Receiver arrays contain flattened row-major cell indices or -1. Fractions are
    float64 and sum to one for ordinary routable cells. ``flow_angle_rad`` is a
    world-space angle measured counter-clockwise from +x/east in [0, 2π), with NaN
    on cells that have no in-domain downstream direction.
    """

    flow_angle_rad: np.ndarray
    receiver_a: np.ndarray
    receiver_b: np.ndarray
    fraction_a: np.ndarray
    fraction_b: np.ndarray


@dataclass(frozen=True, slots=True)
class HydrologyState:
    """Per-attempt runtime hydrology state; not a serialized contract."""

    routing_elevation_m: np.ndarray
    fill_elevation_m: np.ndarray
    flow_direction: np.ndarray
    flow_accumulation_km2: np.ndarray
    stream_mask: np.ndarray
    lake_candidates: tuple[LakeCandidate, ...]
    river_network: RiverNetwork
    water_depth_m: np.ndarray
    lake_features: dict[str, HydroFeature] = field(default_factory=dict)

    # Core 0.2 diagnostics/semantic routing. Defaults preserve 0.1 constructors and
    # exact historical acceptance fixtures. ``flow_direction`` above remains the
    # legacy compatibility field and is not authoritative when routing_mode is
    # ``continuous``.
    routing_mode: str = "d8"
    continuous_routing: ContinuousRoutingField | None = None
    channel_support_mask: np.ndarray | None = None
    lake_outlets: tuple[LakeOutlet, ...] = ()
