from __future__ import annotations

"""P2-B2.2: bounded source-boundary MFD/lake routing experiment, NOT canonical water.

A8/D8 is a coarse GEO REFERENCE. Its basin area is never automatically injected
as a local water contribution. Explicit external-area assumptions must be
provided by an operator, keyed to an identified boundary-entry candidate.

The area flow is hydrological topology support in km², NOT discharge in m³/s,
precipitation, perennial water, groundwater or a real filled lake.
"""

import argparse
import heapq
import json
from math import cos, pi, radians
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.continuous import (
    choose_lake_outlets, continuous_routing_field, distributed_flow_accumulation_km2,
)
from domain_generator.hydrology.ids import lake_feature_id
from domain_generator.hydrology.routing import HydrologyCapabilityError, priority_flood_surfaces
from domain_generator.hydrology.state import ContinuousRoutingField, LakeCandidate, LakeOutlet


DIRS = ((0, 1), (-1, 1), (-1, 0), (-1, -1),
        (0, -1), (1, -1), (1, 0), (1, 1))


class BoundaryIntegrationError(ValueError):
    pass


def _edge_mask(shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    out[0] = out[-1] = True
    out[:, 0] = out[:, -1] = True
    return out


def source_inlet_candidates(
    macro: dict[str, np.ndarray], child: dict[str, np.ndarray],
    manifest: dict,
) -> list[dict]:
    """Old D8 link crossings from OUTSIDE to INSIDE the CHILD box.

    This merely proposes WHERE a boundary inlet may be. Macro catchment area is
    an explicitly unsafe, potentially non-external-only hint.
    """
    needed = ("latitude_deg_north_first", "longitude_deg_west_to_east",
              "source_river_mask_D8", "local_downstream_index",
              "source_catchment_km2_D8")
    if not all(k in macro for k in needed):
        raise BoundaryIntegrationError("macro source lacks aligned A8 D8 reference fields")
    lat = np.asarray(macro[needed[0]], dtype=float)
    lon = np.asarray(macro[needed[1]], dtype=float)
    river = np.asarray(macro[needed[2]], dtype=bool)
    receiver = np.asarray(macro[needed[3]])
    catchment = np.asarray(macro[needed[4]], dtype=float)
    if lat.ndim != 1 or lon.ndim != 1 or min(len(lat), len(lon)) < 3:
        raise BoundaryIntegrationError("invalid macro geographic axes")
    shape = (len(lat), len(lon))
    if any(a.shape != shape for a in (river, receiver, catchment)):
        raise BoundaryIntegrationError("macro D8 reference arrays differ in shape")
    if not np.issubdtype(receiver.dtype, np.integer):
        raise BoundaryIntegrationError("macro D8 receivers must be flattened integer indexes")
    if np.any(receiver < -1) or np.any(receiver >= river.size):
        raise BoundaryIntegrationError("macro D8 receiver out of range")
    if not np.isfinite(catchment).all():
        raise BoundaryIntegrationError("macro source catchment contains nonfinite values")
    lon0 = float(manifest["center_lat_lon_deg"][1])
    lat0 = float(manifest["center_lat_lon_deg"][0])
    radius = float(manifest["planet_radius_km"])
    if not np.isfinite(radius) or radius <= 0 or abs(lat0) >= 80:
        raise BoundaryIntegrationError("non-Earth planet radius/latitude invalid")
    km_deg = pi * radius / 180
    xx = (lon - lon0) * km_deg * cos(radians(lat0))
    yy = (lat - lat0) * km_deg
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    if min(east.size, north.size) < 5:
        raise BoundaryIntegrationError("child grid too small for interior inflow anchors")
    x_min, x_max = float(east[0]), float(east[-1])
    y_min, y_max = float(north[-1]), float(north[0])
    rows, cols = shape
    proposals: list[dict] = []
    for r, c in np.argwhere(river & (receiver >= 0)):
        target = int(receiver[r, c])
        tr, tc = divmod(target, cols)
        x0, y0 = float(xx[c]), float(yy[r])
        x1, y1 = float(xx[tc]), float(yy[tr])
        a_inside = x_min <= x0 <= x_max and y_min <= y0 <= y_max
        b_inside = x_min <= x1 <= x_max and y_min <= y1 <= y_max
        if a_inside or not b_inside:
            continue
        intersections = []
        for side, dim, border in (
            ("west", 0, x_min), ("east", 0, x_max),
            ("south", 1, y_min), ("north", 1, y_max),
        ):
            start, end = ((x0, x1) if dim == 0 else (y0, y1))
            if abs(end - start) < 1e-12:
                continue
            t = (border - start) / (end - start)
            if t < 0 or t > 1:
                continue
            hit_x = x0 + t * (x1 - x0)
            hit_y = y0 + t * (y1 - y0)
            if (x_min - 1e-8 <= hit_x <= x_max + 1e-8
                    and y_min - 1e-8 <= hit_y <= y_max + 1e-8):
                intersections.append((t, side, hit_x, hit_y))
        if len(intersections) != 1:
            # Tangency/corner ambiguity is not silently resolved.
            continue
        _, side, hit_x, hit_y = intersections[0]
        if side in ("north", "south"):
            rr = 1 if side == "north" else len(north) - 2
            cc = int(np.argmin(abs(east[1:-1] - hit_x))) + 1
        else:
            cc = 1 if side == "west" else len(east) - 2
            rr = int(np.argmin(abs(north[1:-1] - hit_y))) + 1
        key = f"A8-r{r:04d}-c{c:04d}-to-r{tr:04d}-c{tc:04d}"
        proposals.append({
            "key": key, "side": side, "suggested_child_row_col": [rr, cc],
            "crossing_east_north_km": [round(hit_x, 5), round(hit_y, 5)],
            "a8_upstream_catchment_km2_UNSAFE_HINT": float(catchment[r, c]),
            "source_link_macro_cells": [[int(r), int(c)], [tr, tc]],
            "is_verified_external_only_area": False,
            "can_auto_inject_area": False,
            "reason": "A8 D8 catchment may include inside-crop or re-entering area, and the 0.3-degree line does not locate a fine-grid river",
        })
    return sorted(proposals, key=lambda x: x["key"])


def validate_declared_inlets(
    config: dict | None, candidates: list[dict], shape: tuple[int, int],
) -> tuple[tuple[tuple[int, int, float], ...], dict]:
    """Fail closed. Only explicit positive external-area scenarios are injected."""
    if config is None:
        return (), {"status": "NO_EXTERNAL_INFLOW_ASSUMED",
                    "declared_count": 0, "injected_external_area_km2": 0.0}
    if config.get("schema") != "P2_B2_2_EXPLICIT_A8_INFLOW_SCENARIO":
        raise BoundaryIntegrationError("explicit A8 inflow scenario schema required")
    entries = config.get("inflows")
    if not isinstance(entries, list):
        raise BoundaryIntegrationError("inflows must be a list")
    by_key = {p["key"]: p for p in candidates}
    if len(by_key) != len(candidates):
        raise BoundaryIntegrationError("duplicate A8 crossing reference keys")
    used: set[str] = set()
    out = []
    for e in entries:
        if not isinstance(e, dict):
            raise BoundaryIntegrationError("every explicit inflow must be an object")
        key = e.get("source_link_key")
        if not isinstance(key, str) or key not in by_key or key in used:
            raise BoundaryIntegrationError("inflow key absent from A8 candidates or duplicate")
        if e.get("area_semantics") != "EXTERNAL_ONLY_AREA_EXCLUDING_CHILD":
            raise BoundaryIntegrationError(
                "explicit confirmation that contribution excludes child area is required"
            )
        if not isinstance(e.get("operator_note"), str) or not e["operator_note"].strip():
            raise BoundaryIntegrationError("external input requires provenance/operator note")
        value = e.get("external_area_km2")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise BoundaryIntegrationError("explicit area must be finite and positive")
        value = float(value)
        if not np.isfinite(value) or value <= 0:
            raise BoundaryIntegrationError("external area must be finite and positive")
        row, col = by_key[key]["suggested_child_row_col"]
        if not (0 < row < shape[0] - 1 and 0 < col < shape[1] - 1):
            raise BoundaryIntegrationError("cannot inject onto terminal domain edge")
        used.add(key)
        out.append((row, col, value))
    return tuple(out), {
        "status": "EXPLICIT_UNVALIDATED_SCENARIO_NOT_PHYSICAL_DISCHARGE",
        "declared_count": len(out),
        "injected_external_area_km2": float(sum(v for _, _, v in out)),
        "source_keys": sorted(used),
        "warning": "area assumptions were explicitly provided, not measured or inferred from A8 Q",
    }


def accumulate_mfd_with_lake_nodes(
    field: ContinuousRoutingField, *,
    cell_size_km: float,
    lakes: tuple[LakeCandidate, ...] = (),
    outlets: tuple[LakeOutlet, ...] = (),
    external_inflows: tuple[tuple[int, int, float], ...] = (),
) -> tuple[np.ndarray, dict]:
    """O((N+E)logN) Kahn accumulation with Core-compatible lake supernodes.

    A separate implementation so the normative Core remains unmodified. Small
    synthetic examples MUST match its unmodified supernode accumulation.
    """
    f = np.asarray(field.fractions, dtype=np.float64)
    if f.ndim != 3 or f.shape[2] != 8 or not np.isfinite(f).all() or np.any(f < 0):
        raise BoundaryIntegrationError("invalid accepted Core 8-neighbour fractions")
    rows, cols, _ = f.shape
    if min(rows, cols) < 3 or not np.isfinite(cell_size_km) or cell_size_km <= 0:
        raise BoundaryIntegrationError("invalid grid or cell spacing")
    perimeter = _edge_mask((rows, cols))
    sumf = f.sum(axis=2)
    if np.max(abs(sumf[~perimeter] - 1)) > 1e-9 or np.max(abs(sumf[perimeter])) > 1e-12:
        raise BoundaryIntegrationError("nonconservative Core MFD fractions")
    if len(outlets) != len(lakes):
        raise BoundaryIntegrationError("must provide exactly one outlet per candidate lake")
    lake_index: dict[tuple[int, int], int] = {}
    for index, basin in enumerate(lakes):
        for r, c in basin.cells:
            if (r, c) in lake_index or not(0 <= r < rows and 0 <= c < cols):
                raise BoundaryIntegrationError("overlapping/outside lake candidate")
            if perimeter[r, c]:
                raise BoundaryIntegrationError("lake may not cross domain edge")
            lake_index[(r, c)] = index
    num_cells = rows * cols
    node_count = num_cells + len(lakes)
    lake_ids = [lake_feature_id(i) for i in range(len(lakes))]
    outlets_by_id = {o.lake_id: o for o in outlets}
    if set(outlets_by_id) != set(lake_ids):
        raise BoundaryIntegrationError("outlets must match Core lake IDs")
    for o in outlets:
        if o.lake_cell not in lake_index:
            raise BoundaryIntegrationError("spill's lake cell not in candidate")
        if o.receiver_cell in lake_index:
            raise BoundaryIntegrationError("spill receiver must be outside lake candidates")
    out_of_lake_receiver = {o.receiver_cell: lake_index[o.lake_cell] for o in outlets}
    weights = np.full(node_count, cell_size_km**2, dtype=np.float64)
    for r, c in lake_index:
        weights[r * cols + c] = 0
    weights[num_cells:] = [len(lake.cells) * cell_size_km**2 for lake in lakes]
    injected = 0.0
    for r, c, area in external_inflows:
        if not (isinstance(r, int) and isinstance(c, int)
                and 0 < r < rows - 1 and 0 < c < cols - 1
                and np.isfinite(area) and area > 0):
            raise BoundaryIntegrationError("inlet must be a positive, interior area")
        index = num_cells + lake_index[(r, c)] if (r, c) in lake_index else r * cols + c
        weights[index] += area
        injected += area

    indegree = np.zeros(node_count, dtype=np.int32)
    edges: list[list[tuple[int, float]]] = [[] for _ in range(node_count)]
    # Ordinary interior Core cells; a lake component is represented solely by
    # its extra supernode and receives flow from adjacent ordinary cells.
    for r in range(rows):
        for c in range(cols):
            if (r, c) in lake_index:
                continue
            node = r * cols + c
            if perimeter[r, c]:
                continue
            connected: dict[int, float] = {}
            for k, (dr, dc) in enumerate(DIRS):
                weight = float(f[r, c, k])
                if weight <= 0:
                    continue
                tr, tc = r + dr, c + dc
                target_lake = lake_index.get((tr, tc))
                if (r, c) in out_of_lake_receiver and target_lake == out_of_lake_receiver[(r, c)]:
                    continue  # Core's no-return-to-own-lake rule
                to = num_cells + target_lake if target_lake is not None else tr * cols + tc
                connected[to] = connected.get(to, 0.0) + weight
            if not connected:
                raise BoundaryIntegrationError("ordinary interior MFD cell has no receiver")
            total = sum(connected.values())
            for dest, amount in sorted(connected.items()):
                edges[node].append((dest, amount / total))
                indegree[dest] += 1
    for index, lake_id in enumerate(lake_ids):
        target = outlets_by_id[lake_id].receiver_cell
        to = target[0] * cols + target[1]
        edges[num_cells + index].append((to, 1.0))
        indegree[to] += 1

    inactive = np.zeros(node_count, dtype=bool)
    for r, c in lake_index:
        inactive[r * cols + c] = True
    queue = [int(i) for i in np.flatnonzero((indegree == 0) & ~inactive)]
    heapq.heapify(queue)
    processed = 0
    while queue:
        node = heapq.heappop(queue)
        processed += 1
        for nxt, fraction in edges[node]:
            weights[nxt] += weights[node] * fraction
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(queue, nxt)
    if processed != int(np.count_nonzero(~inactive)):
        raise BoundaryIntegrationError("lake + MFD graph cycle / unresolved inflow")

    area = weights[:num_cells].reshape(rows, cols).copy()
    for cell, index in lake_index.items():
        area[cell] = weights[num_cells + index]
    source_area = num_cells * cell_size_km**2
    total_out = float(np.sum(area[perimeter]))
    error = total_out - source_area - injected
    if abs(error) > 1e-8 * (source_area + injected):
        raise BoundaryIntegrationError(f"area conservation failed by {error:.8g} km2")
    return area, {
        "local_source_area_km2": float(source_area),
        "explicit_external_area_km2": float(injected),
        "boundary_terminal_area_km2": total_out,
        "balance_error_km2": error,
        "lake_supernode_count": len(lakes),
        "mfd_node_count": num_cells,
        "is_discharge": False,
        "assumption": "Core-compatible MFD topology, external areas operator-supplied only",
    }


def analyze_boundary(
    child: dict[str, np.ndarray], macro: dict[str, np.ndarray],
    manifest: dict, *, inflow_config: dict | None = None,
    lake_min_area_km2: float = 16.0,
    lake_min_depth_m: float = 10.0,
    max_lake_supernodes: int = 12,
) -> tuple[dict[str, np.ndarray], dict]:
    """Run candidate MFD+lake geometry with explicit optional inflows.

    Candidate lakes here are strictly ROUTING SCENARIO supernodes, never actual
    water bodies. Error/ambiguity fails closed to no accepted lake network.
    """
    elevation = np.asarray(child["child_elevation_m"], dtype=float)
    land = np.asarray(child["land_mask"], dtype=bool)
    if elevation.ndim != 2 or not np.isfinite(elevation).all() or elevation.shape != land.shape:
        raise BoundaryIntegrationError("invalid child DEM/land")
    if not np.all(land):
        raise BoundaryIntegrationError("inland-only P2-B2.2; marine H12 must be separate")
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    if not(elevation.shape == (len(north), len(east))
           and np.all(np.diff(east) > 0) and np.all(np.diff(north) < 0)):
        raise BoundaryIntegrationError("invalid child north-first axes")
    spacing = float(np.median(np.diff(east)))
    if (spacing <= 0 or not np.allclose(np.diff(east), spacing, rtol=1e-7)
            or not np.allclose(-np.diff(north), spacing, rtol=1e-7)):
        raise BoundaryIntegrationError("child must have uniform square cells")
    if (not np.isfinite(lake_min_area_km2) or lake_min_area_km2 <= 0
            or not np.isfinite(lake_min_depth_m) or lake_min_depth_m <= 0
            or not isinstance(max_lake_supernodes, int) or max_lake_supernodes < 0):
        raise BoundaryIntegrationError("lake scenario thresholds/limit invalid")
    proposals = source_inlet_candidates(macro, child, manifest)
    inlets, inflow_ledger = validate_declared_inlets(
        inflow_config, proposals, elevation.shape
    )
    surfaces = priority_flood_surfaces(elevation)
    field = continuous_routing_field(surfaces.routing_elevation_m, cell_size_km=spacing)
    candidates = extract_lake_candidates(
        elevation, surfaces.fill_elevation_m, cell_size_km=spacing,
        lake_min_area_km2=lake_min_area_km2,
        lake_min_depth_m=lake_min_depth_m,
    )
    status = "NO_LAKES_QUALIFIED"
    chosen: tuple[LakeCandidate, ...] = ()
    outlets: tuple[LakeOutlet, ...] = ()
    if candidates:
        if len(candidates) > max_lake_supernodes:
            status = "UNRESOLVED_TOO_MANY_GEOMETRIC_LAKE_CANDIDATES"
        else:
            try:
                outlets = choose_lake_outlets(
                    elevation, surfaces.routing_elevation_m, field, candidates
                )
                chosen = candidates
                status = "GEOMETRIC_CANDIDATE_LAKE_SUPERNODES_NOT_PHYSICAL_LAKES"
            except HydrologyCapabilityError as exc:
                status = "UNRESOLVED_SPILL_TOPOLOGY: " + str(exc)
    # On unresolved lakes, do not claim a credible routed network. The
    # no-lake run is still a DEM-derived diagnostic and flagged accordingly.
    area, balance = accumulate_mfd_with_lake_nodes(
        field, cell_size_km=spacing, lakes=chosen,
        outlets=outlets, external_inflows=inlets
    )
    lake_ids = np.zeros(elevation.shape, dtype=np.int32)
    for i, lake in enumerate(chosen, 1):
        for cell in lake.cells:
            lake_ids[cell] = i
    return {
        "mfd_contributing_area_with_explicit_inflows_km2": area,
        "geometric_lake_supernode_ids": lake_ids,
        "preliminary_required_fill_m": np.maximum(
            0, surfaces.fill_elevation_m - elevation
        ),
    }, {
        "status": "P2_B2_2_BOUNDARY_SCENARIO_NOT_FINAL_RIVERS",
        "boundary_source_A8_D8_candidates": proposals,
        "source_A8_D8_candidate_count": len(proposals),
        "external_inflow": inflow_ledger,
        "lake_topology": {
            "status": status,
            "qualified_geometric_basins": len(candidates),
            "routed_proxy_supernodes": len(chosen),
            "actual_water_lakes_inferred": False,
        },
        "area_mass_ledger": balance,
        "river_network_consistency_with_macro": "NOT YET VALIDATED",
        "explicit_disclaimer": "AREA km2 is NOT Q m3/s, water volume, annual precipitation, or proof of flowing rivers",
    }


def render_boundary(
    child: dict[str, np.ndarray], fields: dict[str, np.ndarray],
    report: dict, filename: Path,
) -> None:
    east = np.asarray(child["east_km"])
    north = np.asarray(child["north_km_north_first"])
    extent = [float(east[0]), float(east[-1]),
              float(north[-1]), float(north[0])]
    dem = child["child_elevation_m"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8), layout="constrained")
    v = np.ma.masked_where(np.asarray(dem) < 0, dem)
    axes[0].imshow(v, extent=extent, cmap="terrain", origin="upper")
    axes[0].set_title("New modeled child relief, NOT measured")
    a = fields["mfd_contributing_area_with_explicit_inflows_km2"]
    img = axes[1].imshow(np.log10(np.maximum(a, 1)), extent=extent,
                         cmap="Blues", origin="upper")
    axes[1].set_title("Core-compatible MFD+lake topology; area km² (NOT Q)")
    fig.colorbar(img, ax=axes[1], shrink=.6)
    axes[2].imshow(v, extent=extent, cmap="terrain", origin="upper")
    ids = fields["geometric_lake_supernode_ids"]
    if np.any(ids):
        axes[2].contourf(east, north, (ids > 0).astype(int),
                         levels=[.5, 1.5], colors=["#bf4c93"], alpha=.7)
    for p in report["boundary_source_A8_D8_candidates"]:
        cx, cy = p["crossing_east_north_km"]
        axes[2].plot(cx, cy, "o", color="#f7aa22", markersize=6)
    axes[2].set_title("Orange: coarse A8 INLETS (area NOT auto-injected); pink: candidate proxy lakes")
    for ax in axes:
        ax.set(xlabel="east km", ylabel="north km", aspect="equal")
        ax.grid(alpha=.13)
    fig.suptitle("P2-B2.2 SOURCE BOUNDARY SCENARIO — NOT accepted rivers or permanent lakes")
    fig.savefig(filename, dpi=130)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child-npz", type=Path, required=True)
    parser.add_argument("--child-manifest", type=Path, required=True)
    parser.add_argument("--macro-npz", type=Path, required=True)
    parser.add_argument("--inflows-json", type=Path)
    parser.add_argument("--lake-min-area-km2", type=float, default=16)
    parser.add_argument("--lake-min-depth-m", type=float, default=10)
    parser.add_argument("--max-lake-supernodes", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with np.load(args.child_npz, allow_pickle=False) as z:
        child = {name: z[name].copy() for name in z.files}
    with np.load(args.macro_npz, allow_pickle=False) as z:
        macro = {name: z[name].copy() for name in z.files}
    manifest = json.loads(args.child_manifest.read_text(encoding="utf-8"))
    if (manifest.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or manifest.get("is_accepted_Core_DomainData") is not False):
        raise BoundaryIntegrationError("requires explicitly noncanonical child provenance")
    config = json.loads(args.inflows_json.read_text()) if args.inflows_json else None
    fields, report = analyze_boundary(
        child, macro, manifest, inflow_config=config,
        lake_min_area_km2=args.lake_min_area_km2,
        lake_min_depth_m=args.lake_min_depth_m,
        max_lake_supernodes=args.max_lake_supernodes,
    )
    report["source_child"] = manifest["status"]
    args.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output / "boundary-routing-diagnostic.npz", **fields)
    (args.output / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    render_boundary(child, fields, report, args.output / "boundary-routing-preview.png")
    print(json.dumps({
        "macro_D8_candidate_inlets": report["source_A8_D8_candidate_count"],
        "external_area_injected_km2": report["external_inflow"]["injected_external_area_km2"],
        "lake_status": report["lake_topology"]["status"],
        "mass_balance_error_km2": report["area_mass_ledger"]["balance_error_km2"],
    }, indent=2))


if __name__ == "__main__":
    main()
