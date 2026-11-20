from __future__ import annotations

"""P2-B2.4: compare macro A8 river exits with CONNECTED child Core MFD channels.

Read-only experimental diagnostic. It uses accepted Core's *dominant channel
projection* and conservative MFD area field, but cannot infer perennial Q,
guarantee old A8-to-new-MFD catchment identity or make candidate lakes real.

Outputs explicit geometry-vs-topology evidence, NOT an approved river network.
"""

import argparse
import json
from math import cos, pi, radians
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.continuous import (
    _dominant_channel_receiver_index, choose_lake_outlets,
    continuous_routing_field,
)
from domain_generator.hydrology.routing import (
    HydrologyCapabilityError, priority_flood_surfaces,
)
from scripts.condition_planetary_child_boundary_mfd_v02 import (
    analyze_boundary,
)


class OutletAlignmentError(ValueError):
    pass


_DIRS = ((0, 1), (-1, 1), (-1, 0), (-1, -1),
         (0, -1), (1, -1), (1, 0), (1, 1))


def _edge(shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    out[0] = out[-1] = True
    out[:, 0] = out[:, -1] = True
    return out


def _side(row: int, col: int, shape: tuple[int, int]) -> str:
    rows, cols = shape
    if row == 0:
        return "north"
    if row == rows - 1:
        return "south"
    if col == 0:
        return "west"
    if col == cols - 1:
        return "east"
    raise OutletAlignmentError("terminal must be a boundary cell")


def _crossing(
    start: tuple[float, float], finish: tuple[float, float],
    box: tuple[float, float, float, float],
) -> tuple[str, tuple[float, float]] | None:
    """First unambiguous intersection of a straight macro link with box edge."""
    xmin, xmax, ymin, ymax = box
    x0, y0 = start
    x1, y1 = finish
    result: list[tuple[float, str, float, float]] = []
    for side, axis, border in (
        ("west", 0, xmin), ("east", 0, xmax),
        ("south", 1, ymin), ("north", 1, ymax),
    ):
        a, b = ((x0, x1) if axis == 0 else (y0, y1))
        if abs(b - a) < 1e-12:
            continue
        t = (border - a) / (b - a)
        if not -1e-10 <= t <= 1 + 1e-10:
            continue
        x = x0 + t * (x1 - x0)
        y = y0 + t * (y1 - y0)
        if xmin - 1e-8 <= x <= xmax + 1e-8 and ymin - 1e-8 <= y <= ymax + 1e-8:
            result.append((t, side, x, y))
    if len(result) != 1:
        return None  # corner/tangent ambiguous: no invented unique outlet
    _, side, x, y = result[0]
    return side, (float(x), float(y))


def macro_outlet_candidates(
    macro: dict[str, np.ndarray], child: dict[str, np.ndarray],
    manifest: dict,
) -> tuple[list[dict], dict]:
    """Directed INSIDE -> OUTSIDE coarse A8 links, major mask as subset."""
    needed = (
        "latitude_deg_north_first", "longitude_deg_west_to_east",
        "local_downstream_index", "source_river_mask_D8",
        "source_catchment_km2_D8",
    )
    if any(k not in macro for k in needed):
        raise OutletAlignmentError("macro A8 missing aligned geogrid/D8 fields")
    lat = np.asarray(macro[needed[0]], dtype=float)
    lon = np.asarray(macro[needed[1]], dtype=float)
    downstream = np.asarray(macro[needed[2]])
    river = np.asarray(macro[needed[3]], dtype=bool)
    area = np.asarray(macro[needed[4]], dtype=float)
    if lat.ndim != 1 or lon.ndim != 1 or min(len(lat), len(lon)) < 3:
        raise OutletAlignmentError("macro axes too short")
    shape = (len(lat), len(lon))
    if (any(a.shape != shape for a in (downstream, river, area))
            or not np.all(np.diff(lat) < 0)
            or not np.all(np.diff(lon) > 0)
            or not np.issubdtype(downstream.dtype, np.integer)
            or not np.isfinite(area).all()):
        raise OutletAlignmentError("invalid aligned macro A8 arrays")
    if np.any(downstream < -1) or np.any(downstream >= downstream.size):
        raise OutletAlignmentError("invalid flattened macro D8 downstream receivers")
    radius = float(manifest["planet_radius_km"])
    center_lat, center_lon = map(float, manifest["center_lat_lon_deg"])
    if (not np.isfinite(radius) or radius <= 0 or abs(center_lat) >= 80):
        raise OutletAlignmentError("planet reference invalid")
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    if (min(east.size, north.size) < 5
            or not np.all(np.diff(east) > 0)
            or not np.all(np.diff(north) < 0)):
        raise OutletAlignmentError("invalid child axes")
    box = (float(east[0]), float(east[-1]), float(north[-1]), float(north[0]))
    unit = pi * radius / 180
    x = (lon - center_lon) * unit * cos(radians(center_lat))
    y = (lat - center_lat) * unit
    nc = len(lon)
    results = []
    all_crossings = 0
    for row, col in np.argwhere(downstream >= 0):
        target_row, target_col = divmod(int(downstream[row, col]), nc)
        sx, sy = float(x[col]), float(y[row])
        tx, ty = float(x[target_col]), float(y[target_row])
        first_inside = box[0] <= sx <= box[1] and box[2] <= sy <= box[3]
        next_inside = box[0] <= tx <= box[1] and box[2] <= ty <= box[3]
        if not first_inside or next_inside:
            continue
        hit = _crossing((sx, sy), (tx, ty), box)
        if hit is None:
            continue
        all_crossings += 1
        if not river[row, col]:
            continue
        side, xy = hit
        results.append({
            "key": f"A8-exit-r{row:04d}-c{col:04d}-to-r{target_row:04d}-c{target_col:04d}",
            "side": side,
            "crossing_east_north_km": [round(xy[0], 6), round(xy[1], 6)],
            "old_A8_upstream_area_km2_UNSAFE_HINT": float(area[row, col]),
            "old_source_to_receiver_macro_cells": [
                [int(row), int(col)], [target_row, target_col]
            ],
            "is_A8_coarse_model_only": True,
            "is_verified_child_MFD_outlet": False,
        })
    unresolved_macro_exits = 0
    # D8 links leaving MACRO crop can be represented only by the parent
    # global index. In an undersized macro crop, do not assert completeness.
    if "source_downstream_exits_region" in macro:
        marker = np.asarray(macro["source_downstream_exits_region"])
        if marker.shape != shape:
            raise OutletAlignmentError("bad source macrocrop exit-mask shape")
        for row, col in np.argwhere(marker.astype(bool) & river):
            sx, sy = float(x[col]), float(y[row])
            if box[0] <= sx <= box[1] and box[2] <= sy <= box[3]:
                unresolved_macro_exits += 1
    return sorted(results, key=lambda r: r["key"]), {
        "all_directed_A8_links_exiting_child_box": all_crossings,
        "major_A8_river_links_exiting_child_box": len(results),
        "macro_crop_insufficient_for_inside_major_links": unresolved_macro_exits,
        "coarse_link_position_uncertainty": "one or more original 0.3-degree A8 cells",
    }


def connected_mfd_channel_projection(
    child: dict[str, np.ndarray], macro: dict[str, np.ndarray],
    manifest: dict, *, stream_threshold_km2: float = 30.,
    lake_min_area_km2: float = 16., lake_min_depth_m: float = 10.,
    max_lake_supernodes: int = 12,
) -> tuple[dict[str, np.ndarray], dict]:
    """Trace dominant Core-compatible MFD channels to actual boundary pixels.

    Candidate lake supernodes are routing-proxies only; travel across them is
    NOT drawn as a channel. Every drawn ordinary edge is a selected positive
    receiver from Core's accepted continuous routing field.
    """
    if not np.isfinite(stream_threshold_km2) or stream_threshold_km2 <= 0:
        raise OutletAlignmentError("stream_threshold_km2 must be positive and finite")
    fields, source_report = analyze_boundary(
        child, macro, manifest,
        lake_min_area_km2=lake_min_area_km2,
        lake_min_depth_m=lake_min_depth_m,
        max_lake_supernodes=max_lake_supernodes,
    )
    dem = np.asarray(child["child_elevation_m"], dtype=np.float64)
    shape = dem.shape
    nrows, ncols = shape
    edge = _edge(shape)
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    cell_size_km = float(np.median(np.diff(east)))
    surface = priority_flood_surfaces(dem)
    flow = continuous_routing_field(
        surface.routing_elevation_m, cell_size_km=cell_size_km
    )
    potential_lakes = extract_lake_candidates(
        dem, surface.fill_elevation_m, cell_size_km=cell_size_km,
        lake_min_area_km2=lake_min_area_km2,
        lake_min_depth_m=lake_min_depth_m,
    )
    lake_status = source_report["lake_topology"]["status"]
    routed = int(source_report["lake_topology"]["routed_proxy_supernodes"])
    lakes = ()
    outlets = ()
    if routed:
        if routed != len(potential_lakes):
            raise OutletAlignmentError("child lake proxies inconsistent with source boundary report")
        try:
            outlets = choose_lake_outlets(
                dem, surface.routing_elevation_m, flow, potential_lakes
            )
        except HydrologyCapabilityError as exc:
            raise OutletAlignmentError("could not recreate geometric lake outlet") from exc
        lakes = potential_lakes
    else:
        if lake_status.startswith("GEOMETRIC_CANDIDATE"):
            raise OutletAlignmentError("source report says routed lakes but none selected")

    area = np.asarray(
        fields["mfd_contributing_area_with_explicit_inflows_km2"], dtype=float
    )
    eligible = (area >= stream_threshold_km2) & ~edge
    lake_by_cell = {}
    out_by_lake_id = {o.lake_id: o for o in outlets}
    from domain_generator.hydrology.ids import lake_feature_id
    for i, lake in enumerate(lakes):
        outlet = out_by_lake_id[lake_feature_id(i)]
        for cell in lake.cells:
            if cell in lake_by_cell:
                raise OutletAlignmentError("overlapping lake proxy basins")
            lake_by_cell[cell] = outlet.receiver_cell
            eligible[cell] = False
    receiver = _dominant_channel_receiver_index(
        flow, area, eligible, lake_candidates=lakes,
        lake_outlets=outlets,
    ).astype(np.int64)
    # A lake proxy provides a topological jump to its selected spill receiver.
    # This NONLOCAL link is deliberately separated from drawn channel segments.
    is_lake = np.zeros(shape, dtype=bool)
    for (r, c), (tr, tc) in lake_by_cell.items():
        is_lake[r, c] = True
        receiver[r, c] = tr * ncols + tc

    flat_receiver = receiver.reshape(-1)
    visited = np.zeros(nrows * ncols, dtype=np.int32)
    root = np.full(nrows * ncols, -2, dtype=np.int64)
    active = np.zeros(nrows * ncols, dtype=bool)
    traversed_lake = np.zeros(nrows * ncols, dtype=bool)
    sequence = 0
    for sr, sc in np.argwhere(eligible):
        start = int(sr * ncols + sc)
        if root[start] >= 0:
            continue
        sequence += 1
        trail: list[int] = []
        cur = start
        while True:
            if cur < 0 or cur >= root.size:
                raise OutletAlignmentError("dominant channel receiver outside child")
            if visited[cur] == sequence:
                raise OutletAlignmentError("dominant MFD/lake proxy contains cycle")
            if root[cur] >= 0:
                end_node = int(root[cur])
                break
            visited[cur] = sequence
            trail.append(cur)
            row, col = divmod(cur, ncols)
            if edge[row, col]:
                end_node = cur
                break
            nxt = int(flat_receiver[cur])
            if nxt < 0:
                raise OutletAlignmentError("dominant path stopped before region edge")
            if not is_lake[row, col]:
                nr, nc = divmod(nxt, ncols)
                if abs(nr - row) > 1 or abs(nc - col) > 1:
                    raise OutletAlignmentError("non-lake MFD edge not adjacent")
                if float(flow.fractions[row, col, _DIRS.index((nr-row, nc-col))]) <= 0:
                    raise OutletAlignmentError("dominant link absent from accepted Core MFD")
            cur = nxt
        for node in trail:
            root[node] = end_node
            active[node] = True
    mask = active.reshape(shape)
    lake_mask = is_lake & mask
    ordinary = mask & ~is_lake
    # Only successfully traced channel paths reaching a boundary count.
    endpoints = sorted(
        int(i) for i in np.flatnonzero(mask.reshape(-1) & edge.reshape(-1))
    )
    for idx in endpoints:
        row, col = divmod(idx, ncols)
        if not edge[row, col]:
            raise OutletAlignmentError("reached non-edge channel terminal")
    edges = []
    proxy_jumps = []
    for flat in np.flatnonzero(mask.reshape(-1)):
        row, col = divmod(int(flat), ncols)
        if edge[row, col]:
            continue
        nxt = int(flat_receiver[flat])
        to_row, to_col = divmod(nxt, ncols)
        if is_lake[row, col]:
            proxy_jumps.append([int(flat), nxt])
        elif is_lake[to_row, to_col]:
            # Link reaches proxy lake boundary, not a real over-lake channel.
            proxy_jumps.append([int(flat), nxt])
        else:
            edges.append([int(flat), nxt])
    results = []
    for term in endpoints:
        row, col = divmod(term, ncols)
        results.append({
            "child_edge_cell_row_col": [row, col],
            "side": _side(row, col, shape),
            "crossing_east_north_km": [float(east[col]), float(north[row])],
            "local_MFD_contributing_area_km2_NOT_Q": float(area[row, col]),
            "channel_terminates_at_boundary": True,
        })
    results.sort(key=lambda x: (
        -x["local_MFD_contributing_area_km2_NOT_Q"],
        x["child_edge_cell_row_col"]
    ))
    output = {
        "channel_mask": ordinary.astype(np.uint8),
        "lake_proxy_mask": lake_mask.astype(np.uint8),
        "Core_dominant_receiver_index": receiver.astype(np.int32),
        "channel_edge_flat_from_to": np.asarray(edges, dtype=np.int32).reshape(-1, 2),
        "lake_proxy_jumps_flat_from_to": np.asarray(proxy_jumps, dtype=np.int32).reshape(-1, 2),
        "MFD_contributing_area_km2_NOT_Q": area.astype(np.float32),
    }
    return output, {
        "status": "CONNECTED_CORE_DOMINANT_MFD_CHANNEL_PROJECTION_NOT_REAL_RIVERS",
        "stream_threshold_km2_NOT_Q": stream_threshold_km2,
        "headwater_seed_cells": int(np.count_nonzero(eligible)),
        "routed_ordinary_channel_cells": int(np.count_nonzero(ordinary)),
        "geometric_lake_proxy_cells_traversed": int(np.count_nonzero(lake_mask)),
        "ordinary_adjacent_channel_edges": len(edges),
        "nonphysical_proxy_links_NOT_RIVERS": len(proxy_jumps),
        "connected_boundary_endpoints": results,
        "lake_topology_status": lake_status,
        "internal_mfd_mass_ledger": source_report["area_mass_ledger"],
        "no_external_A8_source_area_auto_injected": (
            source_report["external_inflow"]["injected_external_area_km2"] == 0
        ),
        "is_physical_discharge_or_approved_river": False,
        "limitations": [
            "Dominant one-receiver path is a CARTOGRAPHIC SKELETON, not full MFD fractional transport.",
            "Geometrical lake proxy jumps are not real over-lake river segments.",
            "Channel threshold is adjustable, arbitrary until world profile approves it.",
            "Outlet spatial proximity does not establish same basin or annual discharge.",
        ],
    }


def match_outlets(
    macro_exits: list[dict], child_terminals: list[dict],
    *, tolerance_km: float = 30.0,
) -> dict:
    """Conservative one-to-one same-side spatial comparison (never force match)."""
    if not np.isfinite(tolerance_km) or tolerance_km <= 0:
        raise OutletAlignmentError("tolerance must be positive")
    ranked = []
    candidates = []
    for i, macro in enumerate(macro_exits):
        x, y = macro["crossing_east_north_km"]
        for j, child in enumerate(child_terminals):
            a, b = child["crossing_east_north_km"]
            distance = float(np.hypot(x-a, y-b))
            if macro["side"] == child["side"]:
                candidates.append((distance, i, j))
        nearest_any = min((
            float(np.hypot(x-z["crossing_east_north_km"][0],
                           y-z["crossing_east_north_km"][1]))
            for z in child_terminals
        ), default=None)
        ranked.append({
            "macro_source_exit_key": macro["key"],
            "macro_side": macro["side"],
            "nearest_any_side_child_terminal_km": nearest_any,
            "matched_child_terminal": None,
            "status": "UNMATCHED_MACRO_EXIT",
        })
    used_child = set()
    matched_macro = set()
    for distance, i, j in sorted(candidates):
        if i in matched_macro or j in used_child or distance > tolerance_km:
            continue
        matched_macro.add(i)
        used_child.add(j)
        ranked[i]["matched_child_terminal"] = child_terminals[j]["child_edge_cell_row_col"]
        ranked[i]["same_side_distance_km"] = distance
        ranked[i]["status"] = "GEOMETRICALLY_NEAR_ONLY_NOT_SAME_WATERSHED"
    return {
        "geometry_tolerance_km": tolerance_km,
        "major_A8_macro_exit_count": len(macro_exits),
        "child_MFD_channel_terminal_count": len(child_terminals),
        "same_side_near_matches": len(matched_macro),
        "unmatched_major_macro_exits": len(macro_exits) - len(matched_macro),
        "unmatched_child_terminals": len(child_terminals) - len(used_child),
        "is_hydrologically_validated": False,
        "comparisons": ranked,
        "warning": "close boundary outlets may represent DIFFERENT basins; match is geometry only",
    }


def analyze_outlets(
    child: dict[str, np.ndarray], macro: dict[str, np.ndarray],
    manifest: dict, *, stream_threshold_km2: float = 30.0,
    matching_tolerance_km: float = 30.0,
) -> tuple[dict[str, np.ndarray], dict]:
    exits, source_note = macro_outlet_candidates(macro, child, manifest)
    fields, mfd = connected_mfd_channel_projection(
        child, macro, manifest, stream_threshold_km2=stream_threshold_km2
    )
    matches = match_outlets(
        exits, mfd["connected_boundary_endpoints"],
        tolerance_km=matching_tolerance_km,
    )
    return fields, {
        "status": "P2_B2_4_REFERENCE_EXIT_ALIGNMENT_NOT_ACCEPTED_HYDROLOGY",
        "source_macro_A8_outlets": exits,
        "source_macro_A8_outlet_ledger": source_note,
        "child_core_dominant_channel_ledger": mfd,
        "coarse_to_fine_outlet_alignment": matches,
        "is_accepted_Core_DomainData": False,
        "is_author_approved_local_river_map": False,
        "external_area_auto_injected_km2": 0.0,
    }


def render_outlet_comparison(
    child: dict[str, np.ndarray], fields: dict[str, np.ndarray],
    report: dict, output: Path,
) -> None:
    dem = np.asarray(child["child_elevation_m"], dtype=float)
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    extent = [float(east[0]), float(east[-1]), float(north[-1]), float(north[0])]
    fig, ax = plt.subplots(1, 3, figsize=(18, 6), layout="constrained")
    light = LightSource(azdeg=315, altdeg=45)
    shaded = light.shade(
        dem, cmap=plt.get_cmap("terrain"), dx=1000, dy=1000,
        vert_exag=3,
    )
    for a in ax:
        a.imshow(shaded, extent=extent, origin="upper")
        a.set(xlabel="east km", ylabel="north km", aspect="equal")
        a.grid(alpha=.12)
    mfd = fields["MFD_contributing_area_km2_NOT_Q"]
    im = ax[0].imshow(
        np.log10(np.maximum(mfd, 1.0)),
        cmap="Blues", origin="upper", extent=extent, alpha=.7,
    )
    ax[0].set_title("MFD fractional accumulation, log10 km² (NOT discharge)")
    fig.colorbar(im, ax=ax[0], shrink=.65)
    channel = np.ma.masked_where(fields["channel_mask"] <= 0, fields["channel_mask"])
    for a in (ax[1], ax[2]):
        a.imshow(channel, extent=extent, origin="upper",
                 cmap="Blues", vmin=0, vmax=1,
                 interpolation="nearest", alpha=.88)
    ax[1].set_title("Connected dominant Core MFD channels (modeled)")
    proxies = np.ma.masked_where(
        fields["lake_proxy_mask"] <= 0, fields["lake_proxy_mask"]
    )
    ax[1].imshow(proxies, extent=extent, origin="upper",
                 cmap="magma", alpha=.7)
    comparisons = report["coarse_to_fine_outlet_alignment"]["comparisons"]
    matched_keys = {m["macro_source_exit_key"] for m in comparisons
                    if m["matched_child_terminal"] is not None}
    for old in report["source_macro_A8_outlets"]:
        x, y = old["crossing_east_north_km"]
        color = "#22b887" if old["key"] in matched_keys else "#e16c28"
        for a in (ax[1], ax[2]):
            a.scatter([x], [y], s=110, marker="D",
                      color=color, edgecolors="black", linewidths=.7, zorder=6)
    for outlet in report["child_core_dominant_channel_ledger"]["connected_boundary_endpoints"]:
        x, y = outlet["crossing_east_north_km"]
        ax[2].scatter([x], [y], s=30, marker="o",
                      facecolors="#2d68bd", edgecolors="white", linewidths=.7, zorder=7)
    for comp in comparisons:
        if comp["matched_child_terminal"] is None:
            continue
        old = next(o for o in report["source_macro_A8_outlets"]
                   if o["key"] == comp["macro_source_exit_key"])
        row, col = comp["matched_child_terminal"]
        ox, oy = old["crossing_east_north_km"]
        ax[2].plot([ox, east[col]], [oy, north[row]],
                   linestyle="--", color="white", linewidth=1.5, alpha=.9)
    ax[2].set_title("Orange diamonds: macro A8 EXITS; blue circles: child MFD terminals")
    fig.suptitle("P2-B2.4: spatial outlet evidence ONLY, no verified common watershed")
    fig.savefig(output, dpi=125)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--child-npz", type=Path, required=True)
    p.add_argument("--child-manifest", type=Path, required=True)
    p.add_argument("--macro-npz", type=Path, required=True)
    p.add_argument("--stream-threshold-km2", type=float, default=30)
    p.add_argument("--matching-tolerance-km", type=float, default=30)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    with np.load(args.child_npz, allow_pickle=False) as arr:
        child = {k: arr[k].copy() for k in arr.files}
    with np.load(args.macro_npz, allow_pickle=False) as arr:
        macro = {k: arr[k].copy() for k in arr.files}
    manifest = json.loads(args.child_manifest.read_text(encoding="utf8"))
    if (manifest.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or manifest.get("is_accepted_Core_DomainData") is not False):
        raise OutletAlignmentError("requires noncanonical, source-conditioned child provenance")
    fields, report = analyze_outlets(
        child, macro, manifest,
        stream_threshold_km2=args.stream_threshold_km2,
        matching_tolerance_km=args.matching_tolerance_km,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output / "connected-MFD-channel-reference.npz", **fields)
    (args.output / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    render_outlet_comparison(
        child, fields, report, args.output / "macro-vs-child-outlets.png"
    )
    print(json.dumps({
        "A8_major_macro_exits": report["source_macro_A8_outlet_ledger"]["major_A8_river_links_exiting_child_box"],
        "MFD_channel_terminals": report["coarse_to_fine_outlet_alignment"]["child_MFD_channel_terminal_count"],
        "same_side_near_only": report["coarse_to_fine_outlet_alignment"]["same_side_near_matches"],
        "is_hydrologically_validated": False,
    }, indent=2))


if __name__ == "__main__":
    main()
