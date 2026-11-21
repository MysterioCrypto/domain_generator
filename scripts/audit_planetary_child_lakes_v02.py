from __future__ import annotations

"""P2-B2.1: review provisional lake basins on already generated child terrain.

Uses UNMODIFIED accepted Core 0.2 Priority-Flood, depression classification,
spill candidates and small-grid lake-supernode accounting. This is NOT a new
world lake classifier, an accepted perennial-lake map or a macro-constrained
river network. Old A8 D8 is never interpreted as new fine-grid MFD.
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.continuous import (
    choose_lake_outlets,
    continuous_routing_field,
    distributed_flow_accumulation_km2,
)
from domain_generator.hydrology.depression_hierarchy import (
    build_nested_depression_hierarchy,
)
from domain_generator.hydrology.routing import (
    HydrologyCapabilityError,
    priority_flood_surfaces,
)


class ChildLakeAuditError(ValueError):
    pass


def _boundary_mask(shape: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.bool_)
    mask[0] = mask[-1] = True
    mask[:, 0] = mask[:, -1] = True
    return mask


def audit_child_depressions(
    child: dict[str, np.ndarray],
    *,
    lake_min_area_km2: float = 4.0,
    lake_min_depth_m: float = 2.0,
    max_outlet_review: int = 64,
    max_hierarchy_cells: int = 256,
    reference_graph_cell_limit: int = 3000,
) -> tuple[dict[str, np.ndarray], dict]:
    """Inventory prospective basins with explicit topology and evidence limits.

    Priority-Flood fill depth is a *required artificial fill*, not water depth.
    Passing geometric thresholds does not establish rain-fed lake permanence.
    """
    height = np.asarray(child.get("child_elevation_m"), dtype=np.float64)
    latmask = np.asarray(child.get("land_mask"))
    east = np.asarray(child.get("east_km"), dtype=np.float64)
    north = np.asarray(child.get("north_km_north_first"), dtype=np.float64)
    if (height.ndim != 2 or min(height.shape) < 3
            or height.shape != latmask.shape
            or height.shape != (len(north), len(east))
            or not np.isfinite(height).all()
            or not (np.diff(east) > 0).all()
            or not (np.diff(north) < 0).all()):
        raise ChildLakeAuditError("invalid source-conditioned child terrain or XY axes")
    if not np.all(latmask.astype(bool)):
        raise ChildLakeAuditError(
            "P2-B2.1 is inland-only: source marine boundaries require H12 handling"
        )
    dx = float(np.median(np.diff(east)))
    dy = float(np.median(-np.diff(north)))
    if (dx <= 0 or not np.isclose(dx, dy, rtol=1e-8, atol=1e-8)
            or not np.allclose(np.diff(east), dx, atol=1e-7, rtol=1e-7)
            or not np.allclose(-np.diff(north), dy, atol=1e-7, rtol=1e-7)):
        raise ChildLakeAuditError("Core lake routing requires a uniform square grid")
    if (not np.isfinite(lake_min_area_km2) or lake_min_area_km2 <= 0
            or not np.isfinite(lake_min_depth_m) or lake_min_depth_m <= 0):
        raise ChildLakeAuditError("lake review thresholds must be finite and positive")
    for name, value in (
        ("max_outlet_review", max_outlet_review),
        ("max_hierarchy_cells", max_hierarchy_cells),
        ("reference_graph_cell_limit", reference_graph_cell_limit),
    ):
        if not isinstance(value, int) or value <= 0:
            raise ChildLakeAuditError(f"{name} must be a positive integer")

    surface = priority_flood_surfaces(height)
    physical_fill = np.maximum(surface.fill_elevation_m - height, 0.0)
    candidates = extract_lake_candidates(
        height, surface.fill_elevation_m, cell_size_km=dx,
        lake_min_area_km2=lake_min_area_km2,
        lake_min_depth_m=lake_min_depth_m,
    )
    ids = np.zeros(height.shape, dtype=np.int32)
    for idx, candidate in enumerate(candidates, 1):
        for cell in candidate.cells:
            if ids[cell]:
                raise ChildLakeAuditError("candidate lake basins overlap")
            ids[cell] = idx
    if np.any(ids[_boundary_mask(height.shape)]):
        raise ChildLakeAuditError("accepted candidate crosses the cut-region boundary")

    routing = continuous_routing_field(surface.routing_elevation_m, cell_size_km=dx)
    outlet_status = "not-reviewed: too many provisional basins"
    outlets = ()
    graph_diagnostics = {
        "attempted": False, "passed": False,
        "reason": "graph accumulation skipped on region-sized grid",
    }
    if len(candidates) <= max_outlet_review:
        try:
            outlets = choose_lake_outlets(
                height, surface.routing_elevation_m, routing, candidates
            )
            outlet_status = "candidate spill transitions identified by accepted Core"
        except HydrologyCapabilityError as exc:
            outlet_status = "unresolved: " + str(exc)
            outlets = ()
    elif not candidates:
        outlet_status = "no threshold-qualified basins"

    # Reference only: the accepted Core supernode accumulator has a general
    # Python graph, not the P2-B1 large-grid optimized no-lake accumulator.
    # Never pretend that the latter has accounted for lake supernodes.
    if height.size <= reference_graph_cell_limit and len(outlets) == len(candidates):
        try:
            result = distributed_flow_accumulation_km2(
                routing, cell_size_km=dx,
                lake_candidates=candidates, lake_outlets=outlets,
            )
            boundary = _boundary_mask(height.shape)
            area_in = float(height.size * dx * dx)
            total_out = float(np.sum(result[boundary]))
            error = total_out - area_in
            if abs(error) > 1e-8 * area_in:
                raise ChildLakeAuditError(
                    f"supernode conservation failed: {error} km2"
                )
            graph_diagnostics = {
                "attempted": True, "passed": True,
                "local_area_km2": area_in,
                "boundary_terminal_area_km2": total_out,
                "balance_error_km2": error,
                "source_external_inflow_included": False,
            }
        except HydrologyCapabilityError as exc:
            graph_diagnostics = {
                "attempted": True, "passed": False,
                "reason": "Core supernode topology not validated: " + str(exc),
            }
    elif len(candidates) > 0:
        graph_diagnostics["reason"] = (
            "large grid or unresolved outlets: no supernode accumulation claim"
        )

    records = []
    outlet_lookup = {i + 1: outlet for i, outlet in enumerate(outlets)}
    for idx, candidate in enumerate(candidates, 1):
        rows = np.fromiter((p[0] for p in candidate.cells), dtype=int)
        cols = np.fromiter((p[1] for p in candidate.cells), dtype=int)
        depths = physical_fill[rows, cols]
        volume_proxy_km3 = float(depths.sum() * dx * dx / 1000.0)
        outlet = outlet_lookup.get(idx)
        hierarchy = {"computed": False, "note": "too many cells for bounded review"}
        if len(candidate.cells) <= max_hierarchy_cells:
            try:
                tree = build_nested_depression_hierarchy(
                    height, candidate, cell_size_km=dx,
                    lake_min_area_km2=lake_min_area_km2,
                    lake_min_depth_m=lake_min_depth_m,
                )
                hierarchy = {
                    "computed": True, "nodes": len(tree.nodes),
                    "significant_leaf_basins": int(sum(
                        node.threshold_significant for node in tree.leaf_nodes()
                    )),
                }
            except HydrologyCapabilityError as exc:
                hierarchy = {"computed": False, "note": "hierarchy unresolved: " + str(exc)}
        records.append({
            "basin_id": idx,
            "status": "geometrically-qualified-PROVISIONAL-not-author-approved",
            "area_km2": float(candidate.area_km2),
            "max_required_fill_m": float(candidate.max_depth_m),
            "virtual_spill_surface_m": float(candidate.surface_elevation_m),
            "storage_to_spill_proxy_km3": volume_proxy_km3,
            "deepest_cell_row_col": [int(rows[np.argmax(depths)]),
                                     int(cols[np.argmax(depths)])],
            "outlet": None if outlet is None else {
                "lake_cell": list(outlet.lake_cell),
                "receiver_cell": list(outlet.receiver_cell),
                "saddle_elevation_m": float(outlet.saddle_elevation_m),
                "kind": "candidate spill geometry, not demonstrated actual discharge",
            },
            "nested_basins": hierarchy,
        })

    total_filled = int(np.count_nonzero(physical_fill > 1e-8))
    candidate_filled = int(np.count_nonzero(ids))
    report = {
        "status": "P2_B2_1_GEOMETRIC_PROSPECTIVE_LAKES_NOT_WATER_OCCUPANCY",
        "algorithm": "accepted Core Priority-Flood + exact lake component thresholds + provisional spill review",
        "thresholds": {
            "lake_min_area_km2": lake_min_area_km2,
            "lake_min_depth_m": lake_min_depth_m,
        },
        "grid_cells": list(height.shape),
        "cell_size_km": dx,
        "fill_required_cells": total_filled,
        "fill_required_over_2m": int(np.count_nonzero(physical_fill > 2.0)),
        "max_virtual_fill_m": float(np.max(physical_fill)),
        "threshold_qualified_basins": len(candidates),
        "threshold_qualified_cells": candidate_filled,
        "other_virtual_fill_cells": total_filled - candidate_filled,
        "candidate_spill_status": outlet_status,
        "candidate_spill_count": len(outlets),
        "small_grid_core_supernode_area_ledger": graph_diagnostics,
        "basins": records,
        "physical_water_coverage_inferred": False,
        "author_approved_lakes": 0,
        "external_macro_inflow_used": False,
        "macro_A8_D8_forced": False,
        "limitations": [
            "Virtual fill is NOT water depth; even a large basin may be dry or seasonal.",
            "Core threshold qualification is only geometric and not author canon.",
            "Deep or large basins require per-world water balance and author controls.",
            "Candidate spill is a routing reference, not proven perennial outflow.",
            "No new macro boundary inflows, river permanence, glacier, spring, groundwater or marine handling.",
            "Large-grid supernode accumulation is NOT computed by the fast P2-B1 no-lake accumulator.",
        ],
    }
    return {
        "required_fill_depth_m": physical_fill,
        "provisional_lake_basin_id": ids,
        "nonqualified_fill_mask": (
            (physical_fill > 1e-8) & (ids == 0)
        ).astype(np.uint8),
    }, report


def render_lake_review(
    child: dict[str, np.ndarray],
    fields: dict[str, np.ndarray],
    report: dict,
    output: Path,
) -> None:
    terrain = np.asarray(child["child_elevation_m"], dtype=float)
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    extent = [float(east[0]), float(east[-1]),
              float(north[-1]), float(north[0])]
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), layout="constrained")
    illumination = LightSource(azdeg=315, altdeg=45)
    shade = illumination.shade(
        terrain, cmap=plt.get_cmap("terrain"),
        vert_exag=2.5, dx=report["cell_size_km"] * 1000,
        dy=report["cell_size_km"] * 1000,
    )
    for ax in axes:
        ax.imshow(shade, origin="upper", extent=extent)
        ax.set(xlabel="east km", ylabel="north km", aspect="equal")
        ax.grid(alpha=0.08)
    axes[0].set_title("NEW child DEM: terrain (source-conditioned, not canon)")
    depth = fields["required_fill_depth_m"]
    max_depth = max(1.0, float(np.percentile(depth[depth > 0], 95))) if np.any(depth > 0) else 1.0
    virtual = np.ma.masked_where(depth <= 1e-8, depth)
    heat = axes[1].imshow(
        virtual, origin="upper", extent=extent,
        cmap="magma", vmin=0, vmax=max_depth, alpha=0.83
    )
    axes[1].set_title("Required VIRTUAL fill (m) — NOT a real lake")
    fig.colorbar(heat, ax=axes[1], shrink=.68)
    ids = fields["provisional_lake_basin_id"]
    if np.any(ids):
        cmap = plt.get_cmap("tab20")
        rgba = cmap((ids.astype(float) % 20) / 20)
        rgba[..., 3] = (ids > 0).astype(float) * 0.84
        axes[2].imshow(rgba, origin="upper", extent=extent,
                       interpolation="nearest")
    rejected = fields["nonqualified_fill_mask"].astype(bool)
    if np.any(rejected):
        axes[2].contourf(east, north, rejected.astype(int),
                         levels=[.5, 1.5], colors=["#dd4b64"], alpha=.24)
    for item in report["basins"]:
        outlet = item["outlet"]
        if outlet is None:
            continue
        lr, lc = outlet["lake_cell"]
        rr, rc = outlet["receiver_cell"]
        axes[2].plot(
            [east[lc], east[rc]], [north[lr], north[rr]],
            color="white", linewidth=2, alpha=.96,
        )
        axes[2].scatter([east[rc]], [north[rr]], color="#111111", s=18)
    axes[2].set_title(
        "Qualified prospective basins + spill points; red = unqualified"
    )
    fig.suptitle(
        f"P2-B2.1: geometric lake candidates only; {report['threshold_qualified_basins']} "
        "basins; no proven lake water or macro inflow"
    )
    fig.savefig(output, dpi=125)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child-npz", type=Path, required=True)
    parser.add_argument("--child-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lake-min-area-km2", type=float, default=4.0)
    parser.add_argument("--lake-min-depth-m", type=float, default=2.0)
    args = parser.parse_args()
    with np.load(args.child_npz, allow_pickle=False) as source:
        child = {name: source[name].copy() for name in source.files}
    manifest = json.loads(args.child_manifest.read_text(encoding="utf-8"))
    if (manifest.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or manifest.get("is_accepted_Core_DomainData") is not False):
        raise ChildLakeAuditError("expected a generated, explicitly noncanonical child")
    fields, report = audit_child_depressions(
        child, lake_min_area_km2=args.lake_min_area_km2,
        lake_min_depth_m=args.lake_min_depth_m,
    )
    report["child_provenance"] = manifest["status"]
    report["planet_radius_km"] = manifest["planet_radius_km"]
    report["planet_year_earth_days"] = manifest["planet_year_earth_days"]
    args.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output / "child-lake-basin-review.npz", **fields)
    render_lake_review(child, fields, report,
                       args.output / "child-lake-basin-review.png")
    (args.output / "manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "provisional_basins": report["threshold_qualified_basins"],
        "virtual_fill_cells": report["fill_required_cells"],
        "outlets_reviewed": report["candidate_spill_count"],
        "small_grid_ledger": report["small_grid_core_supernode_area_ledger"],
    }, indent=2))


if __name__ == "__main__":
    main()
