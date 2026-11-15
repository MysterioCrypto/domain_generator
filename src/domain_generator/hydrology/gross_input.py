from __future__ import annotations

"""H13-A: weighted gross precipitation accounting, not actual runoff or discharge."""

from bisect import insort
from collections import defaultdict
from dataclasses import dataclass
from math import fsum, isfinite

import numpy as np

from .continuous import _field_edges
from .ids import lake_feature_id
from .marine import accepted_marine_cell_map
from .routing import HydrologyCapabilityError
from .state import ContinuousRoutingField, LakeCandidate, LakeOutlet, MarineCandidate
from .water import accepted_lake_cell_map


@dataclass(frozen=True, slots=True)
class GrossPrecipitationAccounting:
    gross_upstream_precipitation_m3_per_year: np.ndarray
    source_total_m3_per_year: float
    land_edge_terminal_m3_per_year: float
    marine_terminal_by_id_m3_per_year: dict[str, float]

    @property
    def terminal_total_m3_per_year(self) -> float:
        return fsum((self.land_edge_terminal_m3_per_year, *self.marine_terminal_by_id_m3_per_year.values()))

    @property
    def balance_error_m3_per_year(self) -> float:
        return self.source_total_m3_per_year - self.terminal_total_m3_per_year


def accumulate_gross_precipitation_input(
    field: ContinuousRoutingField,
    annual_precipitation_mm: np.ndarray,
    *,
    cell_size_km: float,
    lake_candidates: tuple[LakeCandidate, ...] = (),
    lake_outlets: tuple[LakeOutlet, ...] = (),
    marine_mask: np.ndarray | None = None,
    marine_candidates: tuple[MarineCandidate, ...] = (),
) -> GrossPrecipitationAccounting:
    """Allocate *gross* upstream source volumes on accepted MFD/lake topology.

    The ledger is a mathematical no-loss allocation: it represents neither
    physically delivered channel water nor catchment runoff. Marine cells
    contribute no source and absorb land contributions at their first entry.
    """
    if not isinstance(field.fractions, np.ndarray) or field.fractions.ndim != 3:
        raise HydrologyCapabilityError("H13 requires accepted 3D MFD fractions")
    shape = field.flow_angle_rad.shape
    rows, columns = shape
    if field.fractions.shape != (rows, columns, 8):
        raise HydrologyCapabilityError("H13 MFD fractions/grid mismatch")
    if not isinstance(annual_precipitation_mm, np.ndarray) or annual_precipitation_mm.shape != shape:
        raise HydrologyCapabilityError("H13 annual precipitation must match routing grid")
    if not np.issubdtype(annual_precipitation_mm.dtype, np.floating):
        raise HydrologyCapabilityError("H13 precipitation must have floating dtype")
    if not np.isfinite(annual_precipitation_mm).all() or np.any(annual_precipitation_mm < 0.0):
        raise HydrologyCapabilityError("H13 precipitation must be finite and nonnegative")
    if not isfinite(cell_size_km) or cell_size_km <= 0.0:
        raise HydrologyCapabilityError("H13 cell size must be positive and finite")

    if marine_mask is None:
        marine = np.zeros(shape, dtype=np.bool_)
        if marine_candidates:
            raise HydrologyCapabilityError("H13 marine candidates require marine mask")
    else:
        if not isinstance(marine_mask, np.ndarray) or marine_mask.shape != shape or marine_mask.dtype != np.dtype(np.bool_):
            raise HydrologyCapabilityError("H13 marine mask must be bool grid")
        marine = marine_mask
    marine_by_cell = accepted_marine_cell_map(shape, marine_candidates)
    if set(marine_by_cell) != set(map(tuple, np.argwhere(marine))):
        raise HydrologyCapabilityError("H13 marine mask and component cells mismatch")

    lake_by_cell = accepted_lake_cell_map(shape, lake_candidates)
    if any(marine[cell] for cell in lake_by_cell):
        raise HydrologyCapabilityError("H13 inland lakes must not overlap marine")
    lake_index_by_id = {lake_feature_id(i): i for i in range(len(lake_candidates))}
    outlet_by_id = {item.lake_id: item for item in lake_outlets}
    if len(lake_outlets) != len(lake_candidates) or set(outlet_by_id) != set(lake_index_by_id):
        raise HydrologyCapabilityError("H13 requires exactly one accepted outlet per lake")
    for outlet in lake_outlets:
        if outlet.receiver_cell in lake_by_cell:
            raise HydrologyCapabilityError("H13 lake receiver must be outside accepted lake support")

    count = rows * columns
    nodes = count + len(lake_candidates)
    initial = np.zeros(nodes, dtype=np.float64)
    inactive = np.zeros(nodes, dtype=np.bool_)
    indegree = np.zeros(nodes, dtype=np.int32)
    edges: list[list[tuple[int, float]]] = [[] for _ in range(nodes)]
    marine_edges: list[list[tuple[str, float]]] = [[] for _ in range(nodes)]
    cell_volume_factor = (float(cell_size_km) ** 2) * 1000.0
    rain = annual_precipitation_mm.astype(np.float64, copy=False)
    reverse_lake_outlets = {o.receiver_cell: o.lake_id for o in lake_outlets}
    marine_ids = tuple(sorted(set(marine_by_cell.values())))
    marine_to_negative = {name: -(index + 1) for index, name in enumerate(marine_ids)}
    negative_to_marine = {value: name for name, value in marine_to_negative.items()}

    for row in range(rows):
        for col in range(columns):
            cell = (row, col)
            node = row * columns + col
            if marine[cell] or cell in lake_by_cell:
                inactive[node] = True
                continue
            initial[node] = rain[cell] * cell_volume_factor
            combined: dict[int, float] = defaultdict(float)
            for receiver, fraction in _field_edges(field, cell):
                target_lake = lake_by_cell.get(receiver)
                if target_lake is not None and reverse_lake_outlets.get(cell) == target_lake:
                    # Follow the accepted lake-outlet return-link suppression.
                    continue
                if receiver in marine_by_cell:
                    target = marine_to_negative[marine_by_cell[receiver]]
                elif target_lake is not None:
                    target = count + lake_index_by_id[target_lake]
                else:
                    target = receiver[0] * columns + receiver[1]
                combined[target] += fraction
            if combined:
                total = fsum(combined.values())
                if total <= 1e-12:
                    raise HydrologyCapabilityError("H13 outgoing fractions collapsed to zero")
                for target, fraction in sorted(combined.items()):
                    weight = fraction / total
                    if target < 0:
                        marine_edges[node].append((negative_to_marine[target], weight))
                    else:
                        edges[node].append((target, weight))
                        indegree[target] += 1
            elif 0 < row < rows - 1 and 0 < col < columns - 1:
                raise HydrologyCapabilityError("H13 interior nonmarine cell lost receivers")

    for index, candidate in enumerate(lake_candidates):
        node = count + index
        initial[node] = fsum(rain[cell] * cell_volume_factor for cell in candidate.cells)
        receiver = outlet_by_id[lake_feature_id(index)].receiver_cell
        if receiver in marine_by_cell:
            marine_edges[node].append((marine_by_cell[receiver], 1.0))
        else:
            target = receiver[0] * columns + receiver[1]
            if inactive[target]:
                raise HydrologyCapabilityError("H13 lake outlet targets inactive cell")
            edges[node].append((target, 1.0))
            indegree[target] += 1

    queue = [i for i in range(nodes) if not inactive[i] and indegree[i] == 0]
    accumulated = initial.copy()
    processed = 0
    land_terminal = 0.0
    marine_ledger = {key: 0.0 for key in marine_ids}
    while queue:
        node = queue.pop(0)
        processed += 1
        volume = accumulated[node]
        if not edges[node] and not marine_edges[node]:
            land_terminal += volume
        for marine_id, weight in marine_edges[node]:
            marine_ledger[marine_id] += volume * weight
        for receiver, weight in edges[node]:
            accumulated[receiver] += volume * weight
            indegree[receiver] -= 1
            if indegree[receiver] == 0:
                insort(queue, receiver)
    if processed != int(np.count_nonzero(~inactive)):
        raise HydrologyCapabilityError("H13 accepted MFD/lake traversal contains a cycle")
    if not np.isfinite(accumulated).all():
        raise HydrologyCapabilityError("H13 accumulation became nonfinite")

    raster = np.zeros(shape, dtype=np.float64)
    for row in range(rows):
        for col in range(columns):
            cell = (row, col)
            if marine[cell]:
                continue
            lake_id = lake_by_cell.get(cell)
            node = count + lake_index_by_id[lake_id] if lake_id is not None else row * columns + col
            raster[cell] = accumulated[node]
    source_total = fsum(initial)
    terminal_total = fsum((land_terminal, *marine_ledger.values()))
    if not isfinite(source_total) or not isfinite(terminal_total):
        raise HydrologyCapabilityError("H13 ledger became nonfinite")
    return GrossPrecipitationAccounting(
        gross_upstream_precipitation_m3_per_year=raster,
        source_total_m3_per_year=source_total,
        land_edge_terminal_m3_per_year=land_terminal,
        marine_terminal_by_id_m3_per_year=marine_ledger,
    )
