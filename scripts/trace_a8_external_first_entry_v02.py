from __future__ import annotations

"""P2-B2.3: audit EXACT FIRST ENTRY of each original A8 macro land source.

Input is the user's ORIGINAL GLOBAL A8 ZIP (not a cropped NPZ). For every
outside source cell, follow old D8 downstream to its FIRST entry into the
specified child region. This partitions its own area exactly once, regardless
of downstream exit/re-entry. Requires global acyclic D8; fail closed otherwise.

This is only A8 macro provenance: not finely located 1-km inflows, physically
measured discharge, accepted Core MFD, or author-approved world geography.
"""

import argparse
from collections import deque
from io import BytesIO
import json
from math import cos, pi, radians
from pathlib import Path
from zipfile import ZipFile

import numpy as np


class ExternalProvenanceError(ValueError):
    pass


def read_global_a8(path: Path) -> dict[str, np.ndarray]:
    with ZipFile(path) as archive:
        files = [f for f in archive.namelist() if f.endswith("/A8_hydrology.npz")]
        if len(files) != 1:
            raise ExternalProvenanceError("expected one original global A8_hydrology.npz")
        with np.load(BytesIO(archive.read(files[0])), allow_pickle=False) as source:
            keys = ("lat", "lon", "land", "downstream_index",
                    "catchment_area_km2", "river_mask")
            if not set(keys).issubset(source.files):
                raise ExternalProvenanceError("original A8 ZIP missing D8 source fields")
            return {key: source[key].copy() for key in keys}


def first_entry_partition(
    downstream: np.ndarray, land: np.ndarray,
    inside: np.ndarray, row_area_km2: np.ndarray,
) -> tuple[dict[int, float], np.ndarray, dict]:
    """One global land cell -> at most one earliest downstream boundary entry.

    Results are keyed by flattened GLOBAL A8 outside-source node ID at the
    corresponding outside->inside edge. Coast/sea area is not considered land.
    The cell area is per latitude row. No global catchment is copied blindly.
    """
    raw = np.asarray(downstream)
    mask = np.asarray(land, dtype=bool)
    region = np.asarray(inside, dtype=bool)
    areas = np.asarray(row_area_km2, dtype=np.float64)
    if (raw.ndim != 2 or raw.shape != mask.shape or raw.shape != region.shape
            or areas.shape != (raw.shape[0],)
            or not np.issubdtype(raw.dtype, np.integer)
            or not np.isfinite(areas).all() or np.any(areas <= 0)):
        raise ExternalProvenanceError("invalid global graph/mask/latitude area")
    nr, nc = raw.shape
    total = raw.size
    d = raw.reshape(-1).astype(np.int64, copy=False)
    valid = d >= 0
    if np.any(d < -1) or np.any(d >= total):
        raise ExternalProvenanceError("D8 downstream reference outside source grid")
    inside_flat = region.reshape(-1)
    land_flat = mask.reshape(-1)
    # Require no marine graph traversal: source semantics remain explicit.
    if np.any(valid & ~land_flat):
        raise ExternalProvenanceError("D8 graph has receivers from nonland cells")

    indeg = np.bincount(d[valid], minlength=total).astype(np.int32, copy=False)
    queue = deque(np.flatnonzero(indeg == 0).tolist())
    order = np.empty(total, dtype=np.int32)
    upstream_touched_inside = inside_flat.copy()
    nprocessed = 0
    while queue:
        node = queue.popleft()
        order[nprocessed] = node
        nprocessed += 1
        target = int(d[node])
        if target >= 0:
            if upstream_touched_inside[node]:
                upstream_touched_inside[target] = True
            indeg[target] -= 1
            if indeg[target] == 0:
                queue.append(target)
    if nprocessed != total:
        raise ExternalProvenanceError("global A8 D8 contains cycle; source cannot be partitioned")

    label = np.full(total, -1, dtype=np.int32)
    # Reverse topological order: receiver has already been classified.
    for node in order[::-1]:
        if not land_flat[node] or inside_flat[node]:
            continue
        target = int(d[node])
        if target < 0:
            continue
        if inside_flat[target]:
            label[node] = node  # directed outside->inside edge uniquely identified by source
        else:
            label[node] = label[target]

    entry_src = np.flatnonzero(
        land_flat & ~inside_flat & valid & inside_flat[np.maximum(d, 0)]
    )
    if entry_src.size == 0:
        return {}, label.reshape(raw.shape), {
            "all_directed_a8_entries": 0,
            "contributed_external_land_cells": 0,
            "all_directed_external_area_km2": 0.0,
            "entry_with_prior_inside_upstream_count": 0,
            "no_source_cell_counted_twice": True,
            "full_global_D8_cycle_free": True,
        }
    labels_valid = label[land_flat & ~inside_flat]
    labels_valid = labels_valid[labels_valid >= 0]
    if np.any(~np.isin(labels_valid, entry_src)):
        raise ExternalProvenanceError("first-entry labels do not correspond to actual entries")

    # Latitude-dependent A8 area exactly follows historical A8 approximation.
    # Summation uses a unique partition of macro land cells.
    weights = np.broadcast_to(areas[:, None], raw.shape).reshape(-1)
    counted = (land_flat & ~inside_flat & (label >= 0))
    sums = np.bincount(label[counted], weights=weights[counted], minlength=total)
    per_entry = {int(src): float(sums[src]) for src in entry_src}
    if not np.isclose(sum(per_entry.values()), float(np.sum(weights[counted])),
                      atol=1e-7, rtol=1e-12):
        raise ExternalProvenanceError("external source area partition not conservative")
    return per_entry, label.reshape(raw.shape), {
        "all_directed_a8_entries": len(per_entry),
        "contributed_external_land_cells": int(np.count_nonzero(counted)),
        "all_directed_external_area_km2": float(np.sum(weights[counted])),
        "entry_with_prior_inside_upstream_count": int(np.count_nonzero(
            upstream_touched_inside[entry_src]
        )),
        "no_source_cell_counted_twice": True,
        "full_global_D8_cycle_free": True,
        "entry_with_prior_inside_upstream_global_source_ids": [
            int(x) for x in entry_src[upstream_touched_inside[entry_src]][:80]
        ],
    }


def _source_node_for_macro(
    proposal: dict, macro: dict[str, np.ndarray], global_lat: np.ndarray,
    global_lon: np.ndarray, downstream: np.ndarray,
) -> int:
    (r, c), (tr, tc) = proposal["source_link_macro_cells"]
    lat = np.asarray(macro["latitude_deg_north_first"])
    lon = np.asarray(macro["longitude_deg_west_to_east"])
    if not(0 <= r < len(lat) and 0 <= tr < len(lat)
           and 0 <= c < len(lon) and 0 <= tc < len(lon)):
        raise ExternalProvenanceError("macro original link source/receiver outside macro")
    source_row = int(np.searchsorted(-global_lat, -lat[r]))
    source_col = int(np.searchsorted(global_lon, lon[c]))
    receiver_row = int(np.searchsorted(-global_lat, -lat[tr]))
    receiver_col = int(np.searchsorted(global_lon, lon[tc]))
    if any(v >= bound for v, bound in (
        (source_row, len(global_lat)), (source_col, len(global_lon)),
        (receiver_row, len(global_lat)), (receiver_col, len(global_lon))
    )):
        raise ExternalProvenanceError("macro source axes don't appear in ORIGINAL global A8")
    if not (global_lat[source_row] == lat[r]
            and global_lon[source_col] == lon[c]
            and global_lat[receiver_row] == lat[tr]
            and global_lon[receiver_col] == lon[tc]):
        raise ExternalProvenanceError("macro lat/lon not exactly aligned to original A8")
    node = source_row * len(global_lon) + source_col
    expected_target = receiver_row * len(global_lon) + receiver_col
    if int(downstream.reshape(-1)[node]) != expected_target:
        raise ExternalProvenanceError("cropped A8 graph link disagrees with original source")
    return node


def audit_global_first_entry(
    a8: dict[str, np.ndarray],
    macro: dict[str, np.ndarray],
    child: dict[str, np.ndarray],
    child_manifest: dict,
    candidates: list[dict],
) -> tuple[dict, np.ndarray]:
    lat = np.asarray(a8["lat"], dtype=np.float64)
    lon = np.asarray(a8["lon"], dtype=np.float64)
    down = np.asarray(a8["downstream_index"])
    land = np.asarray(a8["land"], dtype=bool)
    river = np.asarray(a8["river_mask"], dtype=bool)
    catchment = np.asarray(a8["catchment_area_km2"], dtype=np.float64)
    if (lat.ndim != 1 or lon.ndim != 1 or len(lat) < 3 or len(lon) < 3
            or not np.all(np.diff(lat) < 0) or not np.all(np.diff(lon) > 0)):
        raise ExternalProvenanceError("original A8 must have descending latitude and ascending longitude")
    shape = (len(lat), len(lon))
    if any(v.shape != shape for v in (down, land, river, catchment)):
        raise ExternalProvenanceError("original global A8 raster dimensions mismatch")
    if not np.isfinite(catchment).all():
        raise ExternalProvenanceError("source catchment contains nonfinite numbers")
    center_lat, center_lon = map(float, child_manifest["center_lat_lon_deg"])
    radius = float(child_manifest["planet_radius_km"])
    if not np.isfinite(radius) or radius <= 0 or abs(center_lat) >= 80:
        raise ExternalProvenanceError("planet radius/center unsuitable for chart")
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    if (len(east) < 5 or len(north) < 5
            or not np.all(np.diff(east) > 0)
            or not np.all(np.diff(north) < 0)):
        raise ExternalProvenanceError("child coordinates invalid")
    degrees_to_km = pi * radius / 180
    x = (lon - center_lon) * degrees_to_km * cos(radians(center_lat))
    y = (lat - center_lat) * degrees_to_km
    inside = ((y[:, None] >= float(north[-1]))
              & (y[:, None] <= float(north[0]))
              & (x[None, :] >= float(east[0]))
              & (x[None, :] <= float(east[-1])))
    if np.count_nonzero(inside) < 3:
        raise ExternalProvenanceError("child region has too few original grid nodes")
    delta_lon, delta_lat = float(np.median(np.diff(lon))), float(np.median(-np.diff(lat)))
    if (not np.allclose(np.diff(lon), delta_lon, atol=1e-4)
            or not np.allclose(-np.diff(lat), delta_lat, atol=1e-4)):
        raise ExternalProvenanceError("irregular source grid cell area not supported")
    row_areas = radius**2 * radians(delta_lon) * radians(delta_lat) * np.cos(np.deg2rad(lat))
    by_source, labels, ledger = first_entry_partition(down, land, inside, row_areas)
    entries = []
    used: set[int] = set()
    for p in candidates:
        node = _source_node_for_macro(p, macro, lat, lon, down)
        if node not in by_source or node in used:
            raise ExternalProvenanceError("macro candidate missing from original first-entry graph or repeated")
        if not river.reshape(-1)[node]:
            raise ExternalProvenanceError("macro river inlet isn't in original A8 river mask")
        used.add(node)
        area = by_source[node]
        entries.append({
            "source_link_key": p["key"],
            "global_A8_outside_source_flat_id": int(node),
            "global_A8_source_row_col": list(divmod(node, len(lon))),
            "old_A8_total_upstream_catchment_km2_UNSAFE_HINT": float(catchment.reshape(-1)[node]),
            "A8_external_macro_land_source_area_km2_FIRST_ENTRY_ONLY": area,
            "is_verified_A8_global_first_entry_partition": True,
            "is_verified_real_child_MFD_external_area": False,
            "may_auto_inject_into_child": False,
            "reason": "unique macro first-entry source accounting; child MFD basin and world water balance NOT verified",
        })
    # Every incoming original link is represented in by_source, regardless
    # of whether the old river mask classified it as a large river.
    outside_all = float(sum(by_source.values()))
    showcased = float(sum(by_source[n] for n in used))
    ledger.update({
        "status": "A8_GLOBAL_FIRST_ENTRY_MACRO_AREA_VERIFIED_NOT_CHILD_MFD",
        "old_A8_major_river_inlets_matched": len(entries),
        "old_A8_major_river_entry_area_km2": showcased,
        "other_unmapped_macro_entry_area_km2": outside_all-showcased,
        "original_source_region_interior_land_cells": int(np.count_nonzero(inside & land)),
        "planet_radius_km": radius,
        "input_area_unit": "A8 latitude-weighted source-cell km2, NOT cubic meters/second",
        "genuine_child_MFD_topology_validated": False,
        "auto_injected_external_area_km2": 0,
        "return_flow_double_counted": False,
        "original_A8_source_cells_partitioned_once": True,
        "limitations": [
            "A8 global D8 catchment is source-model geography, not accepted fine MFD.",
            "Every exterior land cell is assigned to first later region entry, even if another upstream source passed inside earlier.",
            "Actual lake occupancy, physical river discharge Q and annual water balance not inferred.",
            "Cells on region boundary are classified by original cell CENTERS only (0.3 degree).",
            "No auto-injection: coarse macro entry may not coincide with fine MFD river corridor.",
        ],
        "entries": sorted(entries, key=lambda d: d["source_link_key"]),
    })
    return ledger, labels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--global-a8", type=Path, required=True)
    parser.add_argument("--macro-npz", type=Path, required=True)
    parser.add_argument("--child-npz", type=Path, required=True)
    parser.add_argument("--child-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from scripts.condition_planetary_child_boundary_mfd_v02 import source_inlet_candidates
    with np.load(args.macro_npz, allow_pickle=False) as f:
        macro = {k: f[k].copy() for k in f.files}
    with np.load(args.child_npz, allow_pickle=False) as f:
        child = {k: f[k].copy() for k in f.files}
    manifest = json.loads(args.child_manifest.read_text(encoding="utf-8"))
    if (manifest.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or manifest.get("is_accepted_Core_DomainData") is not False):
        raise ExternalProvenanceError("expected source-conditioned noncanonical child manifest")
    original = read_global_a8(args.global_a8)
    proposals = source_inlet_candidates(macro, child, manifest)
    report, labels = audit_global_first_entry(
        original, macro, child, manifest, proposals
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # Not a canonical world map; save compact cropped source provenance for QA.
    inside_nodes = np.argwhere(labels >= 0)
    if len(inside_nodes):
        rs = max(0, int(np.min(inside_nodes[:, 0])) - 8)
        re = min(labels.shape[0], int(np.max(inside_nodes[:, 0])) + 9)
        cs = max(0, int(np.min(inside_nodes[:, 1])) - 8)
        ce = min(labels.shape[1], int(np.max(inside_nodes[:, 1])) + 9)
    else:
        rs, re, cs, ce = 0, 1, 0, 1
    np.savez_compressed(args.output / "a8-first-entry-preview-crop.npz",
                        first_entry_source_id=labels[rs:re, cs:ce],
                        global_row_start=rs, global_col_start=cs)
    print(json.dumps({
        "matched_major_A8_entries": report["old_A8_major_river_inlets_matched"],
        "all_directed_entry_links": report["all_directed_a8_entries"],
        "external_land_area_macro_km2": report["all_directed_external_area_km2"],
        "major_river_external_area_macro_km2": report["old_A8_major_river_entry_area_km2"],
        "injected_into_child_km2": report["auto_injected_external_area_km2"],
    }, indent=2))


if __name__ == "__main__":
    main()
