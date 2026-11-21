from __future__ import annotations

"""P2-B2.6: source-child geometric basins vs exact Core MFD/lake outlet topology.

This is a READ-ONLY, explicitly noncanonical diagnostic of what happens if
threshold-qualified depression polygons are treated as routing supernodes.
Priority-Flood fill != actual lake surface. Even successful mass conservation
and Core outlet selection do NOT establish physical water, annual discharge,
author lore or real river permanence.

Uses accepted Core Priority-Flood, lake candidate extraction, lake outlet
choice and MFD fractions; the large-grid area accumulator is the P2-B2.2
Core-parity-tested Kahn implementation, NOT accepted Core's slower graph.
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, TwoSlopeNorm
import numpy as np

from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.continuous import (
    choose_lake_outlets, continuous_routing_field,
)
from domain_generator.hydrology.depression_hierarchy import (
    build_nested_depression_hierarchy,
)
from domain_generator.hydrology.routing import (
    HydrologyCapabilityError, priority_flood_surfaces,
)
if __package__:
    from scripts.condition_planetary_child_boundary_mfd_v02 import (
        BoundaryIntegrationError, accumulate_mfd_with_lake_nodes,
    )
else:
    from condition_planetary_child_boundary_mfd_v02 import (
        BoundaryIntegrationError, accumulate_mfd_with_lake_nodes,
    )


class BasinTopologyReviewError(ValueError):
    pass


def _edge(shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    out[0] = out[-1] = True
    out[:, 0] = out[:, -1] = True
    return out


def _validate_child(child: dict[str, np.ndarray]) -> tuple[np.ndarray, float]:
    dem = np.asarray(child.get("child_elevation_m"), dtype=np.float64)
    land = np.asarray(child.get("land_mask"))
    east = np.asarray(child.get("east_km"), dtype=np.float64)
    north = np.asarray(child.get("north_km_north_first"), dtype=np.float64)
    if (dem.ndim != 2 or min(dem.shape) < 5 or dem.shape != land.shape
            or dem.shape != (len(north), len(east))
            or not np.isfinite(dem).all() or not np.isfinite(east).all()
            or not np.isfinite(north).all()):
        raise BasinTopologyReviewError("invalid finite child DEM and coordinate axes")
    if not np.all(land.astype(bool)):
        raise BasinTopologyReviewError(
            "inland-only review: marine boundary needs separate H12 handling"
        )
    dx, dy = np.diff(east), -np.diff(north)
    spacing = float(np.median(dx))
    if (spacing <= 0 or not np.allclose(dx, spacing, rtol=1e-8, atol=1e-8)
            or not np.allclose(dy, spacing, rtol=1e-8, atol=1e-8)):
        raise BasinTopologyReviewError("Core MFD comparison requires uniform square grid")
    return dem, spacing


def _basin_summary(
    dem: np.ndarray, fill: np.ndarray, candidates: tuple,
    outlets: tuple, spacing: float, hierarchy_cell_limit: int,
) -> tuple[np.ndarray, list[dict]]:
    labels = np.zeros(dem.shape, dtype=np.int32)
    descriptions = []
    if outlets and len(outlets) != len(candidates):
        raise BasinTopologyReviewError("partial outlet mapping is not supported")
    for i, candidate in enumerate(candidates, 1):
        rows = np.fromiter((p[0] for p in candidate.cells), dtype=np.int32)
        cols = np.fromiter((p[1] for p in candidate.cells), dtype=np.int32)
        if not len(rows) or np.any(labels[rows, cols]):
            raise BasinTopologyReviewError("overlapping/empty Core lake candidate")
        labels[rows, cols] = i
        if np.any(_edge(dem.shape)[rows, cols]):
            raise BasinTopologyReviewError("threshold-qualified basin crosses map boundary")
        depth = fill[rows, cols] - dem[rows, cols]
        outlet = outlets[i - 1] if outlets else None
        hierarchy = {
            "status": "NOT_RUN_COMPLEXITY_BOUND",
            "node_count": None, "significant_leaf_count": None,
        }
        if len(rows) <= hierarchy_cell_limit:
            try:
                nodes = build_nested_depression_hierarchy(
                    dem, candidate, cell_size_km=spacing,
                    lake_min_area_km2=1.0, lake_min_depth_m=1.0,
                )
                hierarchy = {
                    "status": "CORE_NESTED_HIERARCHY_COMPUTED",
                    "node_count": len(nodes.nodes),
                    "significant_leaf_count": sum(
                        n.threshold_significant for n in nodes.leaf_nodes()
                    ),
                }
            except HydrologyCapabilityError as exc:
                hierarchy = {"status": "CORE_HIERARCHY_UNRESOLVED",
                             "reason": str(exc)}
        descriptions.append({
            "candidate_id": i,
            "status": "GEOMETRIC_PRIORITY_FLOOD_BASIN_NOT_OBSERVED_LAKE",
            "area_km2": float(candidate.area_km2),
            "max_virtual_fill_m": float(candidate.max_depth_m),
            "virtual_storage_to_spill_proxy_km3": float(
                np.sum(depth) * spacing**2 / 1000.
            ),
            "spill_surface_m": float(candidate.surface_elevation_m),
            "deepest_row_col": [
                int(rows[int(np.argmax(depth))]),
                int(cols[int(np.argmax(depth))]),
            ],
            "spill": None if outlet is None else {
                "lake_cell_row_col": list(outlet.lake_cell),
                "receiver_row_col": list(outlet.receiver_cell),
                "saddle_m": float(outlet.saddle_elevation_m),
                "is_perennial_water_discharge": False,
            },
            "nested_geometry": hierarchy,
        })
    return labels, descriptions


def audit_child_lake_routing(
    child: dict[str, np.ndarray], *,
    lake_min_area_km2: float = 16.,
    lake_min_depth_m: float = 10.,
    max_lake_supernodes: int = 12,
    max_total_candidate_cells: int = 12000,
    hierarchy_cell_limit: int = 160,
) -> tuple[dict[str, np.ndarray], dict]:
    """Compare SAME DEM with and without geometrical lake routing proxies.

    Fail closed: if topology is unresolved or over complexity limits, no
    alternate area is fabricated or substituted as a validated 'lake route'.
    """
    dem, spacing = _validate_child(child)
    if (not np.isfinite(lake_min_area_km2) or lake_min_area_km2 <= 0
            or not np.isfinite(lake_min_depth_m) or lake_min_depth_m <= 0):
        raise BasinTopologyReviewError("positive finite threshold required")
    for name, value in (
        ("max_lake_supernodes", max_lake_supernodes),
        ("max_total_candidate_cells", max_total_candidate_cells),
        ("hierarchy_cell_limit", hierarchy_cell_limit),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise BasinTopologyReviewError(f"{name} requires nonnegative integer")

    # The accepted Core DEM and outlet selection are used WITHOUT altering DEM.
    surface = priority_flood_surfaces(dem)
    fill = np.maximum(surface.fill_elevation_m-dem, 0.)
    candidates = extract_lake_candidates(
        dem, surface.fill_elevation_m, cell_size_km=spacing,
        lake_min_area_km2=lake_min_area_km2,
        lake_min_depth_m=lake_min_depth_m,
    )
    field = continuous_routing_field(
        surface.routing_elevation_m, cell_size_km=spacing
    )
    try:
        without, no_lake_ledger = accumulate_mfd_with_lake_nodes(
            field, cell_size_km=spacing
        )
    except BoundaryIntegrationError as exc:
        raise BasinTopologyReviewError("baseline Core MFD topology failed") from exc

    total_cells = sum(len(c.cells) for c in candidates)
    reason = None
    outlets = ()
    if not candidates:
        status = "NO_THRESHOLD_QUALIFIED_BASINS"
    elif max_lake_supernodes == 0 or len(candidates) > max_lake_supernodes:
        status = "UNRESOLVED_TOO_MANY_CANDIDATE_BASINS"
        reason = "explicit max_lake_supernodes limit"
    elif total_cells > max_total_candidate_cells:
        status = "UNRESOLVED_LAKE_CELL_COMPLEXITY_LIMIT"
        reason = "candidate lake cells exceed explicit operator safety limit"
    else:
        try:
            outlets = choose_lake_outlets(
                dem, surface.routing_elevation_m, field, candidates
            )
            status = "CORE_SPILL_TOPOLOGY_SELECTED_PROXY_ROUTING_ONLY"
        except HydrologyCapabilityError as exc:
            status = "UNRESOLVED_CORE_SPILL_SELECTION"
            reason = str(exc)
            outlets = ()

    labels, summaries = _basin_summary(
        dem, surface.fill_elevation_m, candidates, outlets,
        spacing, hierarchy_cell_limit
    )
    if status == "CORE_SPILL_TOPOLOGY_SELECTED_PROXY_ROUTING_ONLY":
        try:
            with_lakes, lake_ledger = accumulate_mfd_with_lake_nodes(
                field, cell_size_km=spacing,
                lakes=candidates, outlets=outlets,
            )
        except BoundaryIntegrationError as exc:
            status = "UNRESOLVED_LAKE_MFD_CYCLE_OR_CONSERVATION"
            reason = str(exc)
            with_lakes = None
            lake_ledger = None
    else:
        with_lakes, lake_ledger = None, None

    edge = _edge(dem.shape)
    total_expected = float(dem.size * spacing**2)
    no_lake_error = float(np.sum(without[edge]) - total_expected)
    if abs(no_lake_error) > 1e-8 * total_expected:
        raise BasinTopologyReviewError("no-lake reference area not conserved")
    if with_lakes is None:
        difference = np.zeros(dem.shape, dtype=np.float64)
        changed_outlets = None
        boundary_l1 = None
        largest_boundary_shift = None
        changed_pixels = None
        largest_interior_shift = None
        comparable = False
    else:
        difference = with_lakes-without
        changes = difference[edge]
        changed_outlets = int(np.count_nonzero(np.abs(changes) > 1e-6))
        boundary_l1 = float(np.sum(np.abs(changes)))
        largest_boundary_shift = float(np.max(np.abs(changes)))
        changed_pixels = int(np.count_nonzero(np.abs(difference) > 1e-6))
        largest_interior_shift = float(np.max(np.abs(difference[~edge])))
        comparable = True
        if abs(float(np.sum(with_lakes[edge])) - total_expected) > 1e-8 * total_expected:
            raise BasinTopologyReviewError("Core lake-supernode proxy area not conserved")
        if abs(float(np.sum(changes))) > 1e-8 * total_expected:
            raise BasinTopologyReviewError("lake routing changed TOTAL catchment area")
    # Zero-filled difference when comparison is impossible is a display raster
    # ONLY, never an implied zero-impact scientific result.
    fields = {
        "virtual_fill_depth_m_NOT_WATER": fill.astype(np.float32),
        "geometric_candidate_id_NOT_WATER": labels,
        "area_baseline_without_lake_proxy_km2": without.astype(np.float32),
        "area_with_candidate_lake_proxy_km2_UNRESOLVED_ZERO_IF_ABSENT": (
            np.zeros(dem.shape, dtype=np.float32)
            if with_lakes is None else with_lakes.astype(np.float32)
        ),
        "display_area_difference_km2_NOT_COMPARABLE_IF_UNRESOLVED":
            difference.astype(np.float32),
        "lake_comparison_available_mask": np.full(
            dem.shape, int(comparable), dtype=np.uint8
        ),
    }
    report = {
        "status": "P2_B2_6_GEOMETRIC_CORE_LAKE_SUPERNODE_REVIEW_NOT_REAL_WATER",
        "core_priority_flood_used": True,
        "core_lake_candidate_extraction_used": True,
        "core_spill_selection_used": bool(outlets),
        "fast_accumulator_core_parity_confirmed_on_small_fixtures_only": True,
        "original_terrain_modified": False,
        "actual_lakes_inferred": False,
        "river_discharge_m3s_inferred": False,
        "external_macro_A8_inflow_applied": False,
        "parameters": {
            "lake_min_area_km2": lake_min_area_km2,
            "lake_min_depth_m": lake_min_depth_m,
            "max_lake_supernodes": max_lake_supernodes,
            "max_total_candidate_cells": max_total_candidate_cells,
            "hierarchy_cell_limit": hierarchy_cell_limit,
        },
        "grid_shape": list(dem.shape),
        "cell_size_km": spacing,
        "virtual_fill_max_m": float(np.max(fill)),
        "virtual_fill_cells": int(np.count_nonzero(fill > 1e-9)),
        "virtual_fill_max_not_necessarily_in_lake_candidate": True,
        "geometric_candidate_count": len(candidates),
        "geometric_candidate_total_cells": total_cells,
        "candidate_routing_status": status,
        "candidate_routing_unresolved_reason": reason,
        "basins": summaries,
        "no_lake_mass_balance": no_lake_ledger,
        "candidate_lake_mass_balance": lake_ledger,
        "with_vs_without_lakes_comparable": comparable,
        "affected_child_terminal_cells_count": changed_outlets,
        "absolute_terminal_redistribution_km2": boundary_l1,
        "largest_single_terminal_change_km2": largest_boundary_shift,
        "interior_and_edge_changed_cells_count": changed_pixels,
        "largest_interior_MFD_area_proxy_change_km2": largest_interior_shift,
        "limitations": [
            "Priority Flood virtual fill is NOT liquid water or lake depth.",
            "A routing proxy lake is NOT a world-verified permanent/seasonal lake.",
            "Without A8 boundary inflows this is only LOCAL child catchment topology.",
            "Full Core slow graph was compared on small tests; large grids use tested separate Kahn accumulator.",
            "No macro source D8 river alignment, river vectors, Q, annual climate or author acceptance.",
            "Even when edge terminal sums are unchanged, internal routing support can change enormously.",
            "If candidate routing unresolved, zero-valued DISPLAY difference is NOT no impact.",
        ],
    }
    return fields, report


def render_basin_topology(
    child: dict[str, np.ndarray], fields: dict[str, np.ndarray],
    report: dict, destination: Path,
) -> None:
    dem = np.asarray(child["child_elevation_m"], dtype=float)
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    extent = [float(east[0]), float(east[-1]),
              float(north[-1]), float(north[0])]
    fig, axes = plt.subplots(2, 2, figsize=(13, 11), layout="constrained")
    a, b, c, d = axes.flat
    shade = LightSource(azdeg=315, altdeg=45).shade(
        dem, cmap=plt.get_cmap("terrain"), vert_exag=2.7,
        dx=report["cell_size_km"]*1000,
        dy=report["cell_size_km"]*1000,
    )
    for panel in (a, b, c, d):
        panel.imshow(shade, extent=extent, origin="upper")
        panel.set(xlabel="east km", ylabel="north km", aspect="equal")
    a.set_title("Original modeled child DEM (unchanged)")
    depth = np.ma.masked_where(
        fields["virtual_fill_depth_m_NOT_WATER"] <= 1e-8,
        fields["virtual_fill_depth_m_NOT_WATER"]
    )
    if np.ma.count(depth):
        lim = max(1., float(np.percentile(depth.compressed(), 99)))
        im = b.imshow(
            depth, extent=extent, origin="upper", cmap="magma",
            vmin=0, vmax=lim, alpha=.86,
        )
        fig.colorbar(im, ax=b, shrink=.65, label="virtual fill (m), NOT lake depth")
    b.set_title("Priority Flood: virtual fill to drain (NOT water)")
    ids = fields["geometric_candidate_id_NOT_WATER"]
    if np.any(ids):
        palette = plt.get_cmap("tab20")
        colors = palette((ids % 20)/20)
        colors[...,3] = (ids > 0)*.86
        c.imshow(colors, extent=extent, origin="upper",
                 interpolation="nearest")
    for basin in report["basins"]:
        spill = basin["spill"]
        if spill is None:
            continue
        lr, lc = spill["lake_cell_row_col"]
        rr, rc = spill["receiver_row_col"]
        c.plot([east[lc],east[rc]], [north[lr],north[rr]],
               color="white", linewidth=2)
        c.scatter(east[rc],north[rr],color="black",s=12)
    c.set_title("Core geometric basin candidates and proxy spill points")
    if report["with_vs_without_lakes_comparable"]:
        delta = fields["display_area_difference_km2_NOT_COMPARABLE_IF_UNRESOLVED"]
        vmax = max(.1, float(np.percentile(abs(delta), 99.5)))
        im = d.imshow(
            delta, extent=extent, origin="upper",
            cmap="RdBu", norm=TwoSlopeNorm(vcenter=0, vmin=-vmax, vmax=vmax),
            alpha=.85,
        )
        fig.colorbar(im, ax=d, shrink=.65, label="candidate minus baseline km² (NOT Q)")
        d.set_title("MFD upstream area changes: geometry only")
    else:
        d.text(.5,.5,"UNRESOLVED / NOT COMPARABLE\nNo alternate routing claim",
               transform=d.transAxes, ha="center",va="center",
               bbox=dict(facecolor="white",alpha=.9))
        d.set_title("Lake proxy graph was NOT accepted for comparison")
    fig.suptitle(
        f"P2-B2.6 source-conditioned lakes: {report['geometric_candidate_count']} "
        f"candidate basins — {report['candidate_routing_status']}\n"
        "No observed lake occupancy, climate, physical Q or approved rivers",
        fontsize=12
    )
    fig.savefig(destination, dpi=125)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--child-npz", type=Path, required=True)
    p.add_argument("--child-manifest", type=Path, required=True)
    p.add_argument("--lake-min-area-km2", type=float, default=16)
    p.add_argument("--lake-min-depth-m", type=float, default=10)
    p.add_argument("--max-lake-supernodes", type=int, default=12)
    p.add_argument("--max-total-candidate-cells", type=int, default=12000)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    with np.load(a.child_npz, allow_pickle=False) as archive:
        child = {key: archive[key].copy() for key in archive.files}
    source = json.loads(a.child_manifest.read_text(encoding="utf8"))
    if (source.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or source.get("is_accepted_Core_DomainData") is not False):
        raise BasinTopologyReviewError("requires explicitly noncanonical child manifest")
    fields, report = audit_child_lake_routing(
        child, lake_min_area_km2=a.lake_min_area_km2,
        lake_min_depth_m=a.lake_min_depth_m,
        max_lake_supernodes=a.max_lake_supernodes,
        max_total_candidate_cells=a.max_total_candidate_cells,
    )
    report["child_source_status"] = source["status"]
    report["planet_radius_km"] = source["planet_radius_km"]
    report["planet_year_earth_days"] = source["planet_year_earth_days"]
    a.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.output/"lake-topology-comparison.npz", **fields)
    (a.output/"manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf8"
    )
    render_basin_topology(child, fields, report, a.output/"lake-topology-review.png")
    print(json.dumps({
        "candidate_count": report["geometric_candidate_count"],
        "virtual_fill_max_m": report["virtual_fill_max_m"],
        "status": report["candidate_routing_status"],
        "comparable": report["with_vs_without_lakes_comparable"],
        "edge_area_redistribution_km2": report["absolute_terminal_redistribution_km2"],
        "original_changed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
