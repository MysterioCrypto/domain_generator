from __future__ import annotations

import argparse
import json
from collections import Counter
from math import atan2, cos, hypot, pi, sin
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

import domain_generator
from domain_generator.application import (
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.compiler import compile_domain_spec
from domain_generator.hydrology import generate_hydrology, validate_hydrology
from domain_generator.layout import generate_layout
from domain_generator.pipeline.rng import RngFactory
from domain_generator.terrain import generate_terrain


def _world_xy(row: np.ndarray, column: np.ndarray, *, cell_size_km: float, height_km: float):
    x = (column.astype(np.float64) + 0.5) * cell_size_km
    y = height_km - (row.astype(np.float64) + 0.5) * cell_size_km
    return x, y


def _hillshade(elevation_m: np.ndarray, *, cell_size_km: float) -> np.ndarray:
    z = np.flipud(np.asarray(elevation_m, dtype=np.float64)) / 1000.0
    light = LightSource(azdeg=315.0, altdeg=38.0)
    return light.shade(
        z,
        cmap=plt.get_cmap("terrain"),
        vert_exag=1.8,
        dx=cell_size_km,
        dy=cell_size_km,
        blend_mode="soft",
    )


def _lake_mask(shape: tuple[int, int], lake_candidates) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.bool_)
    for lake in lake_candidates:
        for cell in lake.cells:
            mask[cell] = True
    return mask


def _plot_river_network(ax, network) -> None:
    catches = [
        float(segment.properties.catchment_area_km2)
        for segment in network.segments.values()
    ]
    max_log = max((np.log1p(value) for value in catches), default=1.0)
    for segment in network.segments.values():
        xs = [point.x_km for point in segment.centerline]
        ys = [point.y_km for point in segment.centerline]
        catchment = float(segment.properties.catchment_area_km2)
        width = 0.8 + 1.8 * (np.log1p(catchment) / max_log if max_log > 0.0 else 0.0)
        ax.plot(xs, ys, linewidth=width, color="tab:blue", alpha=0.95, zorder=7)


def _plot_lakes_and_outlets(ax, hydrology, *, cell_size_km: float, height_km: float) -> None:
    lake_mask = _lake_mask(hydrology.routing_elevation_m.shape, hydrology.lake_candidates)
    rows, columns = np.where(lake_mask)
    if rows.size:
        x, y = _world_xy(rows, columns, cell_size_km=cell_size_km, height_km=height_km)
        ax.scatter(x, y, s=9.0, marker="s", color="deepskyblue", alpha=0.48, linewidths=0, zorder=5)

    if hydrology.lake_outlets:
        rows = np.array([item.lake_cell[0] for item in hydrology.lake_outlets], dtype=np.int64)
        columns = np.array([item.lake_cell[1] for item in hydrology.lake_outlets], dtype=np.int64)
        x, y = _world_xy(rows, columns, cell_size_km=cell_size_km, height_km=height_km)
        ax.scatter(x, y, s=45.0, marker="x", color="red", linewidths=1.2, zorder=9)


def _final_direction_stats(network) -> dict[str, float | int]:
    steps = 0
    locked = 0
    total_length = 0.0
    tolerance = pi / 180.0
    for segment in network.segments.values():
        for first, second in zip(segment.centerline, segment.centerline[1:]):
            dx = float(second.x_km - first.x_km)
            dy = float(second.y_km - first.y_km)
            length = hypot(dx, dy)
            if length <= 1e-12:
                continue
            steps += 1
            total_length += length
            angle = atan2(dy, dx) % (2.0 * pi)
            nearest = round(angle / (pi / 4.0)) * (pi / 4.0)
            delta = abs((angle - nearest + pi) % (2.0 * pi) - pi)
            if delta <= tolerance:
                locked += 1
    return {
        "step_count": steps,
        "grid_locked_step_count_1deg": locked,
        "grid_locked_step_fraction_1deg": (locked / steps) if steps else 0.0,
        "total_length_km": total_length,
    }


def _routing_direction_stats(flow_angle_rad: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(flow_angle_rad, dtype=np.float64)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {
            "sample_count": 0,
            "grid_locked_count_1deg": 0,
            "grid_locked_fraction_1deg": 0.0,
        }
    unit = pi / 4.0
    tolerance = pi / 180.0
    nearest = np.round(finite / unit) * unit
    delta = np.abs((finite - nearest + pi) % (2.0 * pi) - pi)
    locked = int(np.count_nonzero(delta <= tolerance))
    return {
        "sample_count": int(finite.size),
        "grid_locked_count_1deg": locked,
        "grid_locked_fraction_1deg": float(locked / finite.size),
    }


def _save_terrain_rivers(
    output: Path,
    terrain,
    hydrology,
    *,
    width_km: float,
    height_km: float,
    cell_size_km: float,
) -> None:
    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    ax.imshow(
        _hillshade(terrain.elevation_m, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="bilinear",
        aspect="equal",
    )
    _plot_lakes_and_outlets(ax, hydrology, cell_size_km=cell_size_km, height_km=height_km)
    _plot_river_network(ax, hydrology.river_network)
    ax.set_title("H09 — Terrain 0.2 with final continuous river network")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output / "01-terrain-final-rivers.png", bbox_inches="tight")
    plt.close(fig)


def _save_drainage_field(
    output: Path,
    terrain,
    hydrology,
    *,
    width_km: float,
    height_km: float,
    cell_size_km: float,
) -> None:
    field = hydrology.continuous_routing
    assert field is not None
    angle = field.flow_angle_rad
    rows, columns = angle.shape
    stride = max(1, int(round(max(rows, columns) / 42.0)))
    rr, cc = np.mgrid[0:rows:stride, 0:columns:stride]
    aa = angle[0:rows:stride, 0:columns:stride]
    valid = np.isfinite(aa)
    x, y = _world_xy(rr[valid], cc[valid], cell_size_km=cell_size_km, height_km=height_km)
    u = np.cos(aa[valid])
    v = np.sin(aa[valid])

    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    ax.imshow(
        _hillshade(terrain.elevation_m, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="bilinear",
        aspect="equal",
        alpha=0.62,
    )
    ax.quiver(
        x,
        y,
        u,
        v,
        angles="xy",
        scale_units="xy",
        scale=0.42,
        width=0.0018,
        alpha=0.72,
        color="black",
        zorder=5,
    )
    _plot_lakes_and_outlets(ax, hydrology, cell_size_km=cell_size_km, height_km=height_km)
    ax.set_title(f"H09 — Continuous drainage field (sampled every {stride} cells)")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output / "02-continuous-drainage-field.png", bbox_inches="tight")
    plt.close(fig)


def _save_channel_support(
    output: Path,
    hydrology,
    *,
    width_km: float,
    height_km: float,
    cell_size_km: float,
) -> None:
    support = hydrology.channel_support_mask
    assert support is not None
    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    ax.imshow(
        np.flipud(support.astype(np.float64)),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="nearest",
        aspect="equal",
        cmap="Greys",
        vmin=0.0,
        vmax=1.0,
    )
    _plot_lakes_and_outlets(ax, hydrology, cell_size_km=cell_size_km, height_km=height_km)
    _plot_river_network(ax, hydrology.river_network)
    ax.set_title("H09 — Channel support (raster) with final semantic rivers (vector)")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output / "03-channel-support-vs-rivers.png", bbox_inches="tight")
    plt.close(fig)


def _save_channel_skeleton(
    output: Path,
    hydrology,
    *,
    width_km: float,
    height_km: float,
    cell_size_km: float,
) -> None:
    support = hydrology.channel_support_mask
    skeleton = hydrology.channel_skeleton_mask
    assert support is not None
    assert skeleton is not None

    diagnostic = support.astype(np.float64) * 0.28
    diagnostic[skeleton] = 1.0

    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    image = ax.imshow(
        np.flipud(diagnostic),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="nearest",
        aspect="equal",
        cmap="Greys",
        vmin=0.0,
        vmax=1.0,
    )
    _plot_lakes_and_outlets(ax, hydrology, cell_size_km=cell_size_km, height_km=height_km)
    _plot_river_network(ax, hydrology.river_network)

    source_x = []
    source_y = []
    confluence_x = []
    confluence_y = []
    for node in hydrology.river_network.nodes.values():
        if node.kind.value == "source":
            source_x.append(node.position.x_km)
            source_y.append(node.position.y_km)
        elif node.kind.value == "confluence":
            confluence_x.append(node.position.x_km)
            confluence_y.append(node.position.y_km)
    if source_x:
        ax.scatter(source_x, source_y, s=18.0, marker="o", color="limegreen", zorder=9)
    if confluence_x:
        ax.scatter(confluence_x, confluence_y, s=24.0, marker="D", color="magenta", zorder=9)

    ax.set_title("H09-D — Raw MFD support (gray), terrain-aware skeleton (black), final rivers (blue)")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output / "05-channel-skeleton-vs-support.png", bbox_inches="tight")
    plt.close(fig)


def _save_accumulation_overlay(
    output: Path,
    terrain,
    hydrology,
    *,
    width_km: float,
    height_km: float,
    cell_size_km: float,
) -> None:
    accumulation = np.asarray(hydrology.flow_accumulation_km2, dtype=np.float64)
    log_acc = np.log1p(accumulation)

    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    ax.imshow(
        _hillshade(terrain.elevation_m, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="bilinear",
        aspect="equal",
        alpha=0.48,
    )
    image = ax.imshow(
        np.flipud(log_acc),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="bilinear",
        aspect="equal",
        cmap="viridis",
        alpha=0.58,
    )
    _plot_lakes_and_outlets(ax, hydrology, cell_size_km=cell_size_km, height_km=height_km)
    _plot_river_network(ax, hydrology.river_network)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    colorbar.set_label("log(1 + contributing area km²)")
    ax.set_title("H09 — Distributed accumulation with final river traces")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output / "04-accumulation-final-overlay.png", bbox_inches="tight")
    plt.close(fig)


def _source_points(hydrology) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for node in hydrology.river_network.nodes.values():
        if node.kind.value == "source":
            xs.append(float(node.position.x_km))
            ys.append(float(node.position.y_km))
    return xs, ys


def _save_local_slope(
    output: Path,
    hydrology,
    *,
    width_km: float,
    height_km: float,
) -> None:
    field = hydrology.continuous_routing
    assert field is not None and field.local_slope is not None
    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    image = ax.imshow(
        np.flipud(field.local_slope),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="bilinear",
        aspect="equal",
        cmap="viridis",
    )
    xs, ys = _source_points(hydrology)
    if xs:
        ax.scatter(xs, ys, s=28.0, marker="o", color="red", zorder=9)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    colorbar.set_label("dimensionless slope (rise/run)")
    ax.set_title("H09-D — Conditioned local slope with selected sources")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    fig.tight_layout()
    fig.savefig(output / "06-local-slope-sources.png", bbox_inches="tight")
    plt.close(fig)


def _save_convergence(
    output: Path,
    hydrology,
    *,
    width_km: float,
    height_km: float,
) -> None:
    convergence = hydrology.channel_convergence
    assert convergence is not None
    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    image = ax.imshow(
        np.flipud(convergence),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="bilinear",
        aspect="equal",
        cmap="viridis",
    )
    xs, ys = _source_points(hydrology)
    if xs:
        ax.scatter(xs, ys, s=28.0, marker="o", color="red", zorder=9)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    colorbar.set_label("incoming MFD fraction sum")
    ax.set_title("H09-D — MFD flow convergence with selected sources")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    fig.tight_layout()
    fig.savefig(output / "07-flow-convergence-sources.png", bbox_inches="tight")
    plt.close(fig)


def _save_initiation_score(
    output: Path,
    hydrology,
    *,
    width_km: float,
    height_km: float,
    threshold_km2: float,
) -> None:
    score = hydrology.channel_initiation_score_km2
    convergence = hydrology.channel_convergence
    assert score is not None and convergence is not None
    eligible = (score >= threshold_km2) & (convergence > 1.0 + 1e-9)

    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    image = ax.imshow(
        np.flipud(np.log1p(score)),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="bilinear",
        aspect="equal",
        cmap="viridis",
    )
    rows, columns = np.where(eligible)
    if rows.size:
        x = (columns.astype(np.float64) + 0.5) * (width_km / score.shape[1])
        y = height_km - (rows.astype(np.float64) + 0.5) * (height_km / score.shape[0])
        ax.scatter(x, y, s=8.0, marker=".", color="white", alpha=0.45, zorder=7)
    xs, ys = _source_points(hydrology)
    if xs:
        ax.scatter(xs, ys, s=32.0, marker="o", color="red", zorder=9)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    colorbar.set_label("log(1 + area–slope initiation score km²)")
    ax.set_title("H09-D — Initiation score; white=eligible, red=selected source")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    fig.tight_layout()
    fig.savefig(output / "08-initiation-score-sources.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Core 0.2 hydrology H09 checkpoint")
    parser.add_argument("request", type=Path)
    parser.add_argument("presets", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    request = load_generation_request(args.request)
    catalog = load_preset_catalog(args.presets)
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version=domain_generator.__version__,
    )
    if plan.plan_version != "0.2":
        raise RuntimeError("H09 checkpoint requires GenerationPlan 0.2")

    rng = RngFactory(plan.seed)
    layout = generate_layout(plan, attempt_index=0, rng_factory=rng)
    terrain = generate_terrain(plan, layout, attempt_index=0, rng_factory=rng)
    hydrology = generate_hydrology(plan, terrain)
    if hydrology.routing_mode != "continuous" or hydrology.continuous_routing is None:
        raise RuntimeError("H09 checkpoint requires continuous Core 0.2 hydrology")
    if hydrology.channel_support_mask is None:
        raise RuntimeError("H09 checkpoint requires channel_support_mask")
    if hydrology.channel_skeleton_mask is None:
        raise RuntimeError("H09-D checkpoint requires channel_skeleton_mask")

    validation = validate_hydrology(plan, terrain, hydrology, attempt_index=0)

    args.output.mkdir(parents=True, exist_ok=True)
    width_km = float(plan.domain.width_km)
    height_km = float(plan.domain.height_km)
    cell_size_km = float(plan.grid.cell_size_km)

    _save_terrain_rivers(
        args.output,
        terrain,
        hydrology,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
    )
    _save_drainage_field(
        args.output,
        terrain,
        hydrology,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
    )
    _save_channel_support(
        args.output,
        hydrology,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
    )
    _save_accumulation_overlay(
        args.output,
        terrain,
        hydrology,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
    )
    _save_channel_skeleton(
        args.output,
        hydrology,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
    )
    _save_local_slope(
        args.output,
        hydrology,
        width_km=width_km,
        height_km=height_km,
    )
    _save_convergence(
        args.output,
        hydrology,
        width_km=width_km,
        height_km=height_km,
    )
    _save_initiation_score(
        args.output,
        hydrology,
        width_km=width_km,
        height_km=height_km,
        threshold_km2=float(plan.hydrology.stream_threshold_km2),
    )

    node_kinds = Counter(node.kind.value for node in hydrology.river_network.nodes.values())
    final_stats = _final_direction_stats(hydrology.river_network)
    routing_stats = _routing_direction_stats(hydrology.continuous_routing.flow_angle_rad)
    unique_area = np.asarray(hydrology.channel_unique_area_km2, dtype=np.float64)
    convergence = np.asarray(hydrology.channel_convergence, dtype=np.float64)
    initiation_score = np.asarray(hydrology.channel_initiation_score_km2, dtype=np.float64)
    local_slope = np.asarray(hydrology.continuous_routing.local_slope, dtype=np.float64)
    threshold_km2 = float(plan.hydrology.stream_threshold_km2)
    convergent_mask = convergence > 1.0 + 1e-9
    score_mask = initiation_score >= threshold_km2
    eligible_mask = convergent_mask & score_mask

    def _percentiles(values: np.ndarray) -> dict[str, float]:
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            return {}
        return {
            "p50": float(np.percentile(finite, 50)),
            "p75": float(np.percentile(finite, 75)),
            "p90": float(np.percentile(finite, 90)),
            "p95": float(np.percentile(finite, 95)),
            "p99": float(np.percentile(finite, 99)),
            "max": float(np.max(finite)),
        }

    candidate_cells = list(zip(*np.where(convergent_mask)))
    candidate_cells.sort(
        key=lambda cell: (
            -float(initiation_score[cell]),
            -float(unique_area[cell]),
            -float(local_slope[cell]),
            cell[0],
            cell[1],
        )
    )
    top_candidates = [
        {
            "row": int(row),
            "column": int(column),
            "unique_area_km2": float(unique_area[row, column]),
            "local_slope": float(local_slope[row, column]),
            "convergence": float(convergence[row, column]),
            "score_km2": float(initiation_score[row, column]),
        }
        for row, column in candidate_cells[:20]
    ]

    stats = {
        "checkpoint": "H09-D",
        "generator_version": domain_generator.__version__,
        "plan_version": plan.plan_version,
        "routing_mode": hydrology.routing_mode,
        "domain": {
            "width_km": width_km,
            "height_km": height_km,
            "cell_size_km": cell_size_km,
            "rows": int(plan.grid.rows),
            "columns": int(plan.grid.columns),
        },
        "terrain_elevation_m": {
            "min": float(np.min(terrain.elevation_m)),
            "max": float(np.max(terrain.elevation_m)),
            "std": float(np.std(terrain.elevation_m)),
        },
        "hydrology": {
            "accepted_lake_count": len(hydrology.lake_candidates),
            "canonical_lake_outlet_count": len(hydrology.lake_outlets),
            "channel_support_cells": int(np.count_nonzero(hydrology.channel_support_mask)),
            "channel_skeleton_cells": int(np.count_nonzero(hydrology.channel_skeleton_mask)),
            "max_local_slope": float(np.max(hydrology.continuous_routing.local_slope)),
            "max_channel_convergence": float(np.max(hydrology.channel_convergence)),
            "max_initiation_score_km2": float(np.max(hydrology.channel_initiation_score_km2)),
            "initiation_diagnostics": {
                "threshold_km2": threshold_km2,
                "convergent_cell_count": int(np.count_nonzero(convergent_mask)),
                "score_at_or_above_threshold_count": int(np.count_nonzero(score_mask)),
                "eligible_cell_count": int(np.count_nonzero(eligible_mask)),
                "unique_area_all_km2": _percentiles(unique_area),
                "unique_area_convergent_km2": _percentiles(unique_area[convergent_mask]),
                "local_slope_all": _percentiles(local_slope),
                "local_slope_convergent": _percentiles(local_slope[convergent_mask]),
                "score_all_km2": _percentiles(initiation_score),
                "score_convergent_km2": _percentiles(initiation_score[convergent_mask]),
                "top_convergent_candidates": top_candidates,
            },
            "final_stream_cells": int(np.count_nonzero(hydrology.stream_mask)),
            "river_node_count": len(hydrology.river_network.nodes),
            "river_segment_count": len(hydrology.river_network.segments),
            "river_node_kinds": dict(sorted(node_kinds.items())),
            "max_accumulation_km2": float(np.max(hydrology.flow_accumulation_km2)),
            "continuous_routing_direction": routing_stats,
            "final_vector_geometry": final_stats,
        },
        "validation": {
            "engine_invariants_passed": bool(validation.engine_invariants.passed),
            "hard_constraints_passed": bool(validation.hard_constraints.passed),
        },
    }
    serialized_stats = json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (args.output / "statistics.json").write_text(
        serialized_stats,
        encoding="utf-8",
    )
    print(serialized_stats, end="")


if __name__ == "__main__":
    main()
