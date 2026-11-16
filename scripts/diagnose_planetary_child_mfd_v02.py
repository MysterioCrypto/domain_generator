from __future__ import annotations

"""P2-B: child MFD routing versus historic planetary macro D8, diagnostics ONLY.

The accepted Core 0.2 Priority-Flood and Freeman MFD fraction authority is used
unchanged. This tool does not equate old A8 D8 channels with a validated fine
river, and does not silently invent upstream boundary inflows or lake discharge.
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

from domain_generator.hydrology.continuous import (
    continuous_routing_field,
    distributed_flow_accumulation_km2,
)
from domain_generator.hydrology.routing import priority_flood_surfaces


# Published Core 0.2 convention: counterclockwise from +x/east; row 0 north.
DIRS = ((0, 1), (-1, 1), (-1, 0), (-1, -1),
        (0, -1), (1, -1), (1, 0), (1, 1))


class ChildDrainageError(ValueError):
    pass


def fast_mfd_accumulation(
    fractions: np.ndarray,
    routing_elevation_m: np.ndarray,
    cell_size_km: float,
) -> tuple[np.ndarray, dict]:
    """Exact-routing-fractions accumulation, O(N log N), no lakes/marine.

    Strictly downhill Priority-Flood elevation gives a topological ordering;
    the accepted Core fractions determine all transfers. Independent small-grid
    regression below verifies equivalence to distributed_flow_accumulation_km2.
    """
    dem = np.asarray(routing_elevation_m, dtype=np.float64)
    f = np.asarray(fractions, dtype=np.float64)
    if dem.ndim != 2 or f.shape != (*dem.shape, 8) or not np.isfinite(dem).all():
        raise ChildDrainageError("routing elevation/fractions shape invalid")
    if not np.isfinite(cell_size_km) or cell_size_km <= 0:
        raise ChildDrainageError("cell_size_km must be positive")
    if not np.isfinite(f).all() or np.any(f < -1e-14):
        raise ChildDrainageError("nonfinite/negative MFD fraction")
    nrows, ncols = dem.shape
    if nrows < 3 or ncols < 3:
        raise ChildDrainageError("need at least 3x3 cells")
    boundary = np.zeros((nrows, ncols), dtype=bool)
    boundary[0] = boundary[-1] = True
    boundary[:, 0] = boundary[:, -1] = True
    total = f.sum(axis=2)
    if (np.max(abs(total[~boundary] - 1)) > 1e-10
            or np.max(abs(total[boundary])) > 1e-12):
        raise ChildDrainageError("accepted interior MFD fractions must sum to 1, edge to 0")

    accumulator = np.full((nrows, ncols), cell_size_km**2, dtype=np.float64)
    order = np.argsort(-dem.ravel(), kind="stable")
    for src in order:
        row, col = divmod(int(src), ncols)
        if boundary[row, col]:
            continue
        flow = float(accumulator[row, col])
        for k, (dr, dc) in enumerate(DIRS):
            weight = float(f[row, col, k])
            if weight <= 0:
                continue
            tr, tc = row + dr, col + dc
            if not dem[tr, tc] < dem[row, col]:
                raise ChildDrainageError("MFD receiver is not strictly downhill")
            accumulator[tr, tc] += flow * weight

    area_in = nrows * ncols * cell_size_km**2
    edge_area = float(accumulator[boundary].sum())
    error = edge_area - area_in
    if abs(error) > 1e-8 * area_in:
        raise ChildDrainageError(f"boundary contributing-area ledger imbalance: {error}")
    ledger = {
        "local_source_area_km2": area_in,
        "all_boundary_terminal_area_km2": edge_area,
        "boundary_balance_error_km2": error,
        "relative_balance_error": error / area_in,
        "boundary_cells": int(boundary.sum()),
    }
    return accumulator, ledger


def _reference_segments(
    macro: dict[str, np.ndarray], *,
    radius_km: float, center_lat: float, center_lon: float,
    child_extent: tuple[float, float, float, float],
) -> tuple[np.ndarray, dict]:
    """Old A8 D8 links for OVERLAY ONLY; distinguish enters/leaves child crop."""
    required = (
        "source_river_mask_D8", "local_downstream_index",
        "latitude_deg_north_first", "longitude_deg_west_to_east",
    )
    if any(name not in macro for name in required):
        raise ChildDrainageError(f"missing macro source D8 fields: {required}")
    lat = np.asarray(macro["latitude_deg_north_first"], dtype=float)
    lon = np.asarray(macro["longitude_deg_west_to_east"], dtype=float)
    river = np.asarray(macro["source_river_mask_D8"])
    dest = np.asarray(macro["local_downstream_index"])
    nr, nc = len(lat), len(lon)
    if (river.shape != (nr, nc) or dest.shape != (nr, nc)
            or not np.issubdtype(dest.dtype, np.integer)):
        raise ChildDrainageError("invalid A8 D8 macro reference arrays")
    kmdeg = pi * radius_km / 180
    xx = (lon - center_lon) * kmdeg * cos(radians(center_lat))
    yy = (lat - center_lat) * kmdeg
    xmin, xmax, ymin, ymax = child_extent
    lines, entry, exit_, inside = [], 0, 0, 0
    for rr, cc in np.argwhere(river.astype(bool)):
        target = int(dest[rr, cc])
        if target < 0:
            continue  # global-exit metadata exists, not a local receiver
        if target >= nr * nc:
            raise ChildDrainageError("source downstream receiver outside cropped macro")
        r1, c1 = divmod(target, nc)
        a = (float(xx[cc]), float(yy[rr]))
        b = (float(xx[c1]), float(yy[r1]))
        is_a = xmin <= a[0] <= xmax and ymin <= a[1] <= ymax
        is_b = xmin <= b[0] <= xmax and ymin <= b[1] <= ymax
        if is_a or is_b:
            lines.append((a, b))
            if is_a and is_b:
                inside += 1
            elif not is_a and is_b:
                entry += 1
            else:
                exit_ += 1
    return np.asarray(lines, dtype=np.float64).reshape(-1, 2, 2), {
        "source_d8_visible_river_links": len(lines),
        "source_d8_inside_links": inside,
        "source_d8_incoming_links": entry,
        "source_d8_outgoing_links": exit_,
        "source_d8_limit": "macro 0.3-degree D8 reference, not accepted child-MFD network",
    }


def _edge_ledger(area: np.ndarray, threshold_km2: float) -> dict:
    """Top outgoing fine-grid MFD terminals and their cardinal side."""
    rows, columns = area.shape
    terminals = []
    for col in range(columns):
        terminals.append((float(area[0, col]), 0, col, "north"))
        terminals.append((float(area[rows - 1, col]), rows - 1, col, "south"))
    for row in range(1, rows - 1):
        terminals.append((float(area[row, 0]), row, 0, "west"))
        terminals.append((float(area[row, columns - 1]), row, columns - 1, "east"))
    by_side = {
        side: sum(value for value, _, _, s in terminals if s == side)
        for side in ("north", "south", "east", "west")
    }
    majors = sorted((t for t in terminals if t[0] >= threshold_km2),
                    key=lambda t: (-t[0], t[1], t[2]))
    return {
        "terminal_area_by_side_km2": by_side,
        "major_outlet_count": len(majors),
        "top_major_outlets": [
            {"contributing_area_km2": value, "row": row, "col": col, "side": side}
            for value, row, col, side in majors[:20]
        ],
        "boundary_inflow_missing": True,
    }


def derive_drainage(
    child: dict[str, np.ndarray],
    macro: dict[str, np.ndarray],
    child_manifest: dict,
    *,
    stream_threshold_km2: float = 45,
) -> tuple[dict[str, np.ndarray], dict, np.ndarray]:
    if not np.isfinite(stream_threshold_km2) or stream_threshold_km2 <= 0:
        raise ChildDrainageError("stream_threshold_km2 must be positive")
    elevation = np.asarray(child["child_elevation_m"], dtype=np.float64)
    x = np.asarray(child["east_km"], dtype=float)
    y = np.asarray(child["north_km_north_first"], dtype=float)
    if (elevation.ndim != 2 or elevation.shape != (len(y), len(x))
            or not np.isfinite(elevation).all()
            or not (np.diff(x) > 0).all() or not (np.diff(y) < 0).all()):
        raise ChildDrainageError("invalid north-first child elevation axes")
    # Explicitly scope to inland-only; Core's H12 marine/lake supernodes must
    # not be approximated with a naïve all-cell ledger.
    land = np.asarray(child["land_mask"], dtype=bool)
    if land.shape != elevation.shape or not land.all():
        raise ChildDrainageError(
            "P2-B diagnostic is inland-only; marine/lake physics need separate H12 gate"
        )
    dx = float(np.median(np.diff(x)))
    dy = float(np.median(-np.diff(y)))
    if not np.isclose(dx, dy, rtol=1e-7) or dx <= 0:
        raise ChildDrainageError("Core MFD requires square uniform child cells")

    surfaces = priority_flood_surfaces(elevation)
    flow = continuous_routing_field(surfaces.routing_elevation_m, cell_size_km=dx)
    area, ledger = fast_mfd_accumulation(flow.fractions, surfaces.routing_elevation_m, dx)
    mask = area >= stream_threshold_km2
    radius = float(child_manifest["planet_radius_km"])
    lat, lon = map(float, child_manifest["center_lat_lon_deg"])
    segment, reference_stats = _reference_segments(
        macro, radius_km=radius, center_lat=lat, center_lon=lon,
        child_extent=(float(x[0]), float(x[-1]), float(y[-1]), float(y[0])),
    )
    out = {
        "child_MFD_accumulation_km2": area,
        "child_MFD_routing_elevation_m": surfaces.routing_elevation_m,
        "child_MFD_flow_angle_rad": flow.flow_angle_rad,
        "child_MFD_major_channel_support_mask": mask.astype(np.uint8),
    }
    diagnostics = {
        "status": "P2_B_DIAGNOSTIC_NOT_MACRO_CONSTRAINED_AND_NOT_CORE_DOMAIN_DATA",
        "source_reference": reference_stats,
        "child_MFD": {
            "method": "accepted Core 0.2 priority_flood_surfaces + continuous_routing_field",
            "accumulation_method": "strict-downhill high-to-low exact accepted fractions",
            "stream_threshold_km2": stream_threshold_km2,
            "major_channel_raster_cells": int(mask.sum()),
            "max_locally_accumulated_area_km2": float(area.max()),
            "lake_and_marine_handling": "NOT IMPLEMENTED: inland-only diagnostic",
        },
        "mass_ledger": ledger,
        "outlets": _edge_ledger(area, stream_threshold_km2),
        "parent_child_consistency": "NOT YET ENFORCED; old D8 is visual/boundary guide only",
        "limitations": [
            "No external upstream area entering the crop is injected: large rivers are truncated.",
            "Macro A8 D8 source reference and child Core MFD have different flow schemes.",
            "The source D8 graph does not constrain child basin outlets in this version.",
            "Raster channel support is not a canonical vector river network.",
            "No lake supernodes or marine classification in this inland-only diagnostic.",
            "Local waterfall, ford, road, settlement and world-specific biomes are not resolved.",
        ],
    }
    return out, diagnostics, segment


def render_preview(child: dict[str, np.ndarray], fields: dict[str, np.ndarray],
                   macro_segments: np.ndarray, output: Path, *, threshold: float) -> None:
    x, y = child["east_km"], child["north_km_north_first"]
    elevation = np.asarray(child["child_elevation_m"], dtype=float)
    extent = [float(x[0]), float(x[-1]), float(y[-1]), float(y[0])]
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), layout="constrained")
    light = LightSource(azdeg=315, altdeg=45)
    shaded = light.shade(elevation, cmap=plt.get_cmap("terrain"),
                         vert_exag=2.5, dx=1000, dy=1000)
    for ax in (axes[0], axes[2]):
        ax.imshow(shaded, origin="upper", extent=extent)
    axes[0].set_title("NEW child relief, source-pinned (no river forcing)")
    area = fields["child_MFD_accumulation_km2"]
    heat = np.ma.masked_where(area < 2, np.log10(np.maximum(area, 1)))
    colored = axes[1].imshow(heat, origin="upper", extent=extent,
                            cmap="Blues", interpolation="nearest")
    axes[1].set_title("ACCEPTED Core MFD fractions: log10 area (km²)")
    fig.colorbar(colored, ax=axes[1], shrink=.65)
    mask = fields["child_MFD_major_channel_support_mask"].astype(bool)
    for ax in (axes[0], axes[2]):
        yy, xx = np.where(mask)
        ax.scatter(x[xx], y[yy], s=2.2, c="#166fa8", alpha=.75, zorder=4)
    for edge in macro_segments:
        (x0, y0), (x1, y1) = edge
        axes[2].plot([x0, x1], [y0, y1], c="#e3a046", lw=2.8, alpha=.93)
        axes[2].scatter([x0], [y0], s=8, c="#7b411d")
    axes[2].set_title("Blue NEW MFD channels vs orange OLD A8 D8 guides")
    for ax in axes:
        ax.set(xlabel="east km", ylabel="north km")
        ax.set_aspect("equal")
        ax.grid(alpha=.08)
    fig.suptitle(
        f"P2-B DIAGNOSTIC, NOT constrained river generation — "
        f"threshold {threshold:g} km²; no outside-crop water"
    )
    fig.savefig(output, dpi=120)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child-npz", type=Path, required=True)
    parser.add_argument("--child-manifest", type=Path, required=True)
    parser.add_argument("--macro-npz", type=Path, required=True)
    parser.add_argument("--threshold-km2", type=float, default=45)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with np.load(args.child_npz, allow_pickle=False) as source:
        child = {key: np.array(source[key], copy=True) for key in source.files}
    with np.load(args.macro_npz, allow_pickle=False) as source:
        macro = {key: np.array(source[key], copy=True) for key in source.files}
    child_manifest = json.loads(args.child_manifest.read_text(encoding="utf-8"))
    if (child_manifest.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or child_manifest.get("is_accepted_Core_DomainData") is not False):
        raise ChildDrainageError("must receive explicit source-conditioned child manifest")
    fields, diagnostics, reference = derive_drainage(
        child, macro, child_manifest, stream_threshold_km2=args.threshold_km2
    )
    args.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output / "child-mfd-diagnostic.npz", **fields)
    render_preview(child, fields, reference, args.output / "child-mfd-comparison.png",
                   threshold=args.threshold_km2)
    diagnostics["source_child"] = child_manifest["status"]
    (args.output / "manifest.json").write_text(
        json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
