from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource
from matplotlib.patches import Patch

from domain_generator.contracts.data import RiverNodeKind
from domain_generator.contracts.plan import GenerationPlan
from domain_generator.geometry import backend_region_set
from domain_generator.hydrology import generate_hydrology_v02, validate_hydrology_v02
from domain_generator.terrain.state import TerrainState


ROWS = 54
COLUMNS = 84
CELL_SIZE_KM = 1.0
SEA_LEVEL_M = 0.0


def _plan() -> GenerationPlan:
    return GenerationPlan.model_validate(
        {
            "plan_version": "0.2",
            "source": {
                "spec_id": "h12-coastal-operator-checkpoint",
                "spec_schema_version": "0.2",
                "spec_fingerprint": "sha256:h12-coastal-operator-checkpoint",
                "generator_version": "0.2-checkpoint",
            },
            "seed": 12012,
            "domain": {
                "width_km": float(COLUMNS),
                "height_km": float(ROWS),
            },
            "grid": {
                "cell_size_km": CELL_SIZE_KM,
                "rows": ROWS,
                "columns": COLUMNS,
            },
            "terrain": {
                "base_elevation_m": 100.0,
                "noise_layers": [
                    {"id": "checkpoint", "scale_km": 20.0, "amplitude_m": 1.0}
                ],
            },
            "hydrology": {
                "stream_threshold_km2": 10.0,
                "lake_min_area_km2": 2.0,
                "lake_min_depth_m": 3.0,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
                "marine": {"sea_level_m": SEA_LEVEL_M},
            },
            "surface": {
                "moisture_base": 0.35,
                "water_moisture_boost": 0.55,
                "water_moisture_decay_km": 2.0,
                "moisture_noise_amplitude": 0.1,
                "moisture_noise_scale_km": 8.0,
                "vegetation_slope_zero_deg": 45.0,
                "climate": {
                    "mean_temperature_c": 10.0,
                    "north_minus_south_temperature_c": 0.0,
                    "temperature_noise_amplitude_c": 0.0,
                    "mean_annual_precipitation_mm": 800.0,
                    "moisture_transport_bearing_deg": 90.0,
                    "orographic_scale_km": 20.0,
                    "orographic_strength": 1.0,
                    "precipitation_noise_log_amplitude": 0.0,
                    "climate_noise_scale_km": 30.0,
                },
            },
            "features": [],
            "constraints": [],
        }
    )


def _cell_for_world(x_km: float, y_km: float) -> tuple[int, int]:
    column = min(COLUMNS - 1, max(0, int(x_km // CELL_SIZE_KM)))
    row = min(
        ROWS - 1,
        max(0, int((ROWS * CELL_SIZE_KM - y_km) // CELL_SIZE_KM)),
    )
    return row, column


def _set_square(
    terrain: np.ndarray,
    *,
    x_km: float,
    y_km: float,
    radius_cells: int,
    value_m: float,
) -> None:
    row, column = _cell_for_world(x_km, y_km)
    terrain[
        max(0, row - radius_cells) : min(ROWS, row + radius_cells + 1),
        max(0, column - radius_cells) : min(COLUMNS, column + radius_cells + 1),
    ] = np.float32(value_m)


def _ring_square(
    terrain: np.ndarray,
    *,
    x_km: float,
    y_km: float,
    inner_radius_cells: int,
    outer_radius_cells: int,
    value_m: float,
) -> None:
    row, column = _cell_for_world(x_km, y_km)
    for rr in range(max(0, row - outer_radius_cells), min(ROWS, row + outer_radius_cells + 1)):
        for cc in range(max(0, column - outer_radius_cells), min(COLUMNS, column + outer_radius_cells + 1)):
            distance = max(abs(rr - row), abs(cc - column))
            if inner_radius_cells < distance <= outer_radius_cells:
                terrain[rr, cc] = np.float32(value_m)


def _terrain() -> np.ndarray:
    terrain = np.empty((ROWS, COLUMNS), dtype=np.float32)
    center_y = ROWS * CELL_SIZE_KM / 2.0

    for row in range(ROWS):
        y = ROWS * CELL_SIZE_KM - (row + 0.5) * CELL_SIZE_KM
        for column in range(COLUMNS):
            x = (column + 0.5) * CELL_SIZE_KM

            # Continental surface descends eastward into an open marine basin.
            value = 180.0 - 4.25 * x + 0.040 * (y - center_y) ** 2

            # Broad low valley makes at least one terrestrial drainage line reach sea.
            value -= 52.0 * np.exp(-((y - center_y) / 5.2) ** 2)

            # Secondary relief avoids a perfectly planar coast.
            value += 12.0 * np.sin(y / 6.0) + 7.0 * np.sin((x + y) / 8.0)

            # Three positive island massifs inside the eastern marine basin.
            for ix, iy, amplitude, sigma in (
                (58.0, 14.0, 145.0, 4.2),
                (66.0, 37.0, 160.0, 4.8),
                (74.0, 24.0, 125.0, 3.5),
            ):
                value += amplitude * np.exp(
                    -((x - ix) ** 2 + (y - iy) ** 2) / (2.0 * sigma * sigma)
                )

            terrain[row, column] = np.float32(value)

    # Ordinary inland closed depression above sea datum.
    _ring_square(
        terrain,
        x_km=24.0,
        y_km=13.0,
        inner_radius_cells=2,
        outer_radius_cells=3,
        value_m=92.0,
    )
    _set_square(
        terrain,
        x_km=24.0,
        y_km=13.0,
        radius_cells=2,
        value_m=34.0,
    )

    # Enclosed basin whose floor lies below sea level. Its positive rim proves
    # that H12 uses connectivity rather than "elevation < 0 means ocean".
    _ring_square(
        terrain,
        x_km=18.0,
        y_km=41.0,
        inner_radius_cells=1,
        outer_radius_cells=2,
        value_m=88.0,
    )
    _set_square(
        terrain,
        x_km=18.0,
        y_km=41.0,
        radius_cells=1,
        value_m=-22.0,
    )

    return terrain


def _hillshade(terrain: np.ndarray) -> np.ndarray:
    z = np.flipud(terrain.astype(np.float64)) / 1000.0
    light = LightSource(azdeg=315.0, altdeg=38.0)
    return light.shade(
        z,
        cmap=plt.get_cmap("terrain"),
        vert_exag=2.0,
        dx=CELL_SIZE_KM,
        dy=CELL_SIZE_KM,
        blend_mode="soft",
    )


def _plot_marine(ax, hydrology, *, alpha: float = 0.55) -> None:
    for feature in hydrology.marine_features.values():
        for polygon in feature.geometry.polygons:
            outer_x = [float(point.x_km) for point in polygon.outer]
            outer_y = [float(point.y_km) for point in polygon.outer]
            ax.fill(outer_x, outer_y, color="royalblue", alpha=alpha, zorder=3)
            ax.plot(
                outer_x + [outer_x[0]],
                outer_y + [outer_y[0]],
                color="navy",
                linewidth=1.0,
                zorder=5,
            )
            for hole in polygon.holes:
                hx = [float(point.x_km) for point in hole]
                hy = [float(point.y_km) for point in hole]
                ax.plot(
                    hx + [hx[0]],
                    hy + [hy[0]],
                    color="navy",
                    linewidth=1.0,
                    zorder=5,
                )


def _plot_lakes(ax, hydrology) -> None:
    for feature in hydrology.lake_features.values():
        for polygon in feature.geometry.polygons:
            xs = [float(point.x_km) for point in polygon.outer]
            ys = [float(point.y_km) for point in polygon.outer]
            ax.fill(xs, ys, color="deepskyblue", alpha=0.75, zorder=6)
            ax.plot(
                xs + [xs[0]],
                ys + [ys[0]],
                color="dodgerblue",
                linewidth=0.9,
                zorder=7,
            )


def _plot_network(ax, network, *, potential: bool = False) -> None:
    catches = [
        float(segment.properties.catchment_area_km2)
        for segment in network.segments.values()
    ]
    max_log = max((np.log1p(value) for value in catches), default=1.0)
    for segment in network.segments.values():
        catchment = float(segment.properties.catchment_area_km2)
        width = 0.55 + 1.6 * (
            np.log1p(catchment) / max_log if max_log > 0.0 else 0.0
        )
        if potential:
            width *= 0.65
        ax.plot(
            [float(point.x_km) for point in segment.centerline],
            [float(point.y_km) for point in segment.centerline],
            linewidth=width,
            color="cyan" if potential else "blue",
            alpha=0.80 if potential else 0.96,
            zorder=9,
        )

    mouths = [
        node
        for node in network.nodes.values()
        if node.kind is RiverNodeKind.MARINE_OUTLET
    ]
    if mouths:
        ax.scatter(
            [float(node.position.x_km) for node in mouths],
            [float(node.position.y_km) for node in mouths],
            marker="x",
            s=42,
            linewidths=1.4,
            color="red",
            zorder=12,
        )


def _base_ax(title: str, terrain: np.ndarray):
    fig, ax = plt.subplots(figsize=(15.5, 10.0), dpi=160)
    ax.imshow(
        _hillshade(terrain),
        origin="lower",
        extent=(0.0, float(COLUMNS), 0.0, float(ROWS)),
        interpolation="bilinear",
        aspect="equal",
    )
    ax.set_title(title)
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_xlim(0.0, float(COLUMNS))
    ax.set_ylim(0.0, float(ROWS))
    return fig, ax


def _save_terrain_sea_level(output: Path, terrain: np.ndarray) -> None:
    fig, ax = _base_ax("H12-A — raw diagnostic terrain with explicit sea-level contour", terrain)
    xs = np.arange(COLUMNS, dtype=np.float64) + 0.5
    ys = np.arange(ROWS, dtype=np.float64) + 0.5
    ax.contour(
        xs,
        ys,
        np.flipud(terrain.astype(np.float64)),
        levels=[SEA_LEVEL_M],
        linewidths=1.4,
        colors="black",
    )
    fig.tight_layout()
    fig.savefig(output / "01-terrain-sea-level.png", bbox_inches="tight")
    plt.close(fig)


def _save_marine_mask(output: Path, terrain: np.ndarray, hydrology) -> None:
    assert hydrology.marine_mask is not None
    fig, ax = _base_ax("H12-A — boundary-connected marine raster support", terrain)
    overlay = np.flipud(hydrology.marine_mask.astype(np.float64))
    ax.imshow(
        overlay,
        origin="lower",
        extent=(0.0, float(COLUMNS), 0.0, float(ROWS)),
        interpolation="nearest",
        cmap="Blues",
        vmin=0.0,
        vmax=1.0,
        alpha=0.58,
        aspect="equal",
    )
    fig.tight_layout()
    fig.savefig(output / "02-marine-mask.png", bbox_inches="tight")
    plt.close(fig)


def _save_refined_coast(output: Path, terrain: np.ndarray, hydrology) -> None:
    fig, ax = _base_ax("H12-A — refined marine geometry and coastline", terrain)
    _plot_marine(ax, hydrology, alpha=0.55)
    _plot_lakes(ax, hydrology)
    fig.tight_layout()
    fig.savefig(output / "03-refined-coastline.png", bbox_inches="tight")
    plt.close(fig)


def _save_water_depth(output: Path, hydrology) -> None:
    fig, ax = plt.subplots(figsize=(15.5, 10.0), dpi=160)
    image = ax.imshow(
        np.flipud(hydrology.water_depth_m.astype(np.float64)),
        origin="lower",
        extent=(0.0, float(COLUMNS), 0.0, float(ROWS)),
        interpolation="nearest",
        cmap="Blues",
        aspect="equal",
    )
    bar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    bar.set_label("canonical water depth, m")
    ax.set_title("H12-A — canonical water depth: marine + lakes + rivers")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    fig.tight_layout()
    fig.savefig(output / "04-canonical-water-depth.png", bbox_inches="tight")
    plt.close(fig)


def _save_network(
    output: Path,
    terrain: np.ndarray,
    hydrology,
    *,
    potential: bool,
) -> None:
    title = (
        "H12-A — potential drainage terminating at marine coastline"
        if potential
        else "H12-A — regional rivers / lakes / marine receiving environment"
    )
    fig, ax = _base_ax(title, terrain)
    _plot_marine(ax, hydrology, alpha=0.42)
    _plot_lakes(ax, hydrology)
    network = (
        hydrology.potential_river_network
        if potential
        else hydrology.river_network
    )
    assert network is not None
    _plot_network(ax, network, potential=potential)
    ax.legend(
        handles=[
            Patch(facecolor="royalblue", alpha=0.55, label="marine"),
            Patch(facecolor="deepskyblue", alpha=0.75, label="lake"),
        ],
        loc="upper left",
    )
    fig.tight_layout()
    name = "06-potential-drainage-marine.png" if potential else "05-regional-rivers-marine.png"
    fig.savefig(output / name, bbox_inches="tight")
    plt.close(fig)


def _save_mouth_contact_sheet(output: Path, terrain: np.ndarray, hydrology) -> None:
    network = hydrology.river_network
    mouths = [
        node
        for node in network.nodes.values()
        if node.kind is RiverNodeKind.MARINE_OUTLET
    ]
    if not mouths:
        raise RuntimeError("H12 operator fixture produced no regional marine outlets")

    shown = mouths[:6]
    columns = min(3, len(shown))
    rows = int(np.ceil(len(shown) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(5.2 * columns, 4.8 * rows), dpi=150)
    axes_array = np.atleast_1d(axes).ravel()

    for ax, mouth in zip(axes_array, shown):
        x = float(mouth.position.x_km)
        y = float(mouth.position.y_km)
        radius = 5.0
        ax.imshow(
            _hillshade(terrain),
            origin="lower",
            extent=(0.0, float(COLUMNS), 0.0, float(ROWS)),
            interpolation="bilinear",
            aspect="equal",
        )
        _plot_marine(ax, hydrology, alpha=0.42)
        _plot_lakes(ax, hydrology)
        _plot_network(ax, network)
        ax.scatter([x], [y], marker="x", s=60, color="red", linewidths=1.7, zorder=15)
        ax.set_xlim(max(0.0, x - radius), min(float(COLUMNS), x + radius))
        ax.set_ylim(max(0.0, y - radius), min(float(ROWS), y + radius))
        ax.set_title(f"marine mouth @ ({x:.2f}, {y:.2f}) km")
        ax.set_xlabel("km east")
        ax.set_ylabel("km north")

    for ax in axes_array[len(shown):]:
        ax.axis("off")

    fig.suptitle("H12-A — regional marine-mouth close-ups")
    fig.tight_layout()
    fig.savefig(output / "07-marine-mouth-closeups.png", bbox_inches="tight")
    plt.close(fig)


def _save_enclosed_basin(output: Path, terrain: np.ndarray, hydrology) -> None:
    center_x, center_y = 18.0, 41.0
    radius = 6.0
    fig, ax = _base_ax(
        "H12-A — enclosed below-sea basin remains disconnected from marine water",
        terrain,
    )
    assert hydrology.marine_mask is not None
    ax.imshow(
        np.flipud(hydrology.marine_mask.astype(np.float64)),
        origin="lower",
        extent=(0.0, float(COLUMNS), 0.0, float(ROWS)),
        interpolation="nearest",
        cmap="Blues",
        vmin=0.0,
        vmax=1.0,
        alpha=0.50,
        aspect="equal",
    )
    _plot_lakes(ax, hydrology)
    ax.scatter([center_x], [center_y], marker="+", s=120, color="red", linewidths=2.0, zorder=15)
    ax.set_xlim(center_x - radius, center_x + radius)
    ax.set_ylim(center_y - radius, center_y + radius)
    fig.tight_layout()
    fig.savefig(output / "08-enclosed-below-sea-basin.png", bbox_inches="tight")
    plt.close(fig)


def _marine_outlet_count(network) -> int:
    return sum(
        node.kind is RiverNodeKind.MARINE_OUTLET
        for node in network.nodes.values()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    plan = _plan()
    terrain_values = _terrain()
    terrain = TerrainState(elevation_m=terrain_values)
    hydrology = generate_hydrology_v02(plan, terrain)
    validation = validate_hydrology_v02(
        plan,
        terrain,
        hydrology,
        attempt_index=0,
    )
    if not validation.engine_invariants.passed:
        failed = [
            item.id
            for item in validation.engine_invariants.results
            if not item.passed
        ]
        raise RuntimeError(f"H12 checkpoint hydrology invariants failed: {failed}")

    if hydrology.marine_mask is None or not bool(hydrology.marine_mask.any()):
        raise RuntimeError("H12 checkpoint has no marine support")
    if hydrology.potential_river_network is None:
        raise RuntimeError("H12 checkpoint has no potential drainage network")

    enclosed_cell = _cell_for_world(18.0, 41.0)
    if not float(terrain_values[enclosed_cell]) < SEA_LEVEL_M:
        raise RuntimeError("enclosed diagnostic basin is not below sea level")
    if bool(hydrology.marine_mask[enclosed_cell]):
        raise RuntimeError("enclosed below-sea basin was incorrectly classified marine")

    regional_mouths = _marine_outlet_count(hydrology.river_network)
    potential_mouths = _marine_outlet_count(hydrology.potential_river_network)
    if regional_mouths < 1 or potential_mouths < 1:
        raise RuntimeError("checkpoint requires marine outlets in both drainage networks")
    if len(hydrology.lake_features) < 1:
        raise RuntimeError("checkpoint requires at least one ordinary inland lake")

    total_cells = ROWS * COLUMNS
    marine_cells = int(np.count_nonzero(hydrology.marine_mask))
    marine_fraction = marine_cells / total_cells
    if not 0.12 <= marine_fraction <= 0.72:
        raise RuntimeError(
            f"checkpoint marine fraction is not representative: {marine_fraction:.3f}"
        )

    marine_raster_area = marine_cells * CELL_SIZE_KM * CELL_SIZE_KM
    refined_marine_area = sum(
        float(feature.properties.area_km2)
        for feature in hydrology.marine_features.values()
    )
    shoreline_length = sum(
        float(backend_region_set(feature.geometry)._value.boundary.length)
        for feature in hydrology.marine_features.values()
    )
    island_hole_count = sum(
        len(polygon.holes)
        for feature in hydrology.marine_features.values()
        for polygon in feature.geometry.polygons
    )

    _save_terrain_sea_level(args.output, terrain_values)
    _save_marine_mask(args.output, terrain_values, hydrology)
    _save_refined_coast(args.output, terrain_values, hydrology)
    _save_water_depth(args.output, hydrology)
    _save_network(args.output, terrain_values, hydrology, potential=False)
    _save_network(args.output, terrain_values, hydrology, potential=True)
    _save_mouth_contact_sheet(args.output, terrain_values, hydrology)
    _save_enclosed_basin(args.output, terrain_values, hydrology)

    report = {
        "checkpoint": "H12-A",
        "fixture": "deterministic coastal / archipelago diagnostic",
        "sea_level_m": SEA_LEVEL_M,
        "domain": {
            "rows": ROWS,
            "columns": COLUMNS,
            "cell_size_km": CELL_SIZE_KM,
            "area_km2": float(total_cells) * CELL_SIZE_KM * CELL_SIZE_KM,
        },
        "terrain_elevation_m": {
            "min": float(np.min(terrain_values)),
            "max": float(np.max(terrain_values)),
        },
        "marine": {
            "component_count": len(hydrology.marine_candidates),
            "raster_cells": marine_cells,
            "raster_area_km2": marine_raster_area,
            "refined_area_km2": refined_marine_area,
            "fraction_of_domain": marine_fraction,
            "shoreline_length_km_including_island_boundaries": shoreline_length,
            "island_hole_count": island_hole_count,
        },
        "enclosed_below_sea_basin": {
            "world_x_km": 18.0,
            "world_y_km": 41.0,
            "cell": list(enclosed_cell),
            "terrain_elevation_m": float(terrain_values[enclosed_cell]),
            "classified_marine": bool(hydrology.marine_mask[enclosed_cell]),
        },
        "lakes": {
            "count": len(hydrology.lake_features),
            "ids": sorted(hydrology.lake_features),
        },
        "regional_rivers": {
            "node_count": len(hydrology.river_network.nodes),
            "segment_count": len(hydrology.river_network.segments),
            "marine_outlet_count": regional_mouths,
            "node_kinds": dict(
                sorted(
                    Counter(
                        node.kind.value
                        for node in hydrology.river_network.nodes.values()
                    ).items()
                )
            ),
        },
        "potential_drainage": {
            "node_count": len(hydrology.potential_river_network.nodes),
            "segment_count": len(hydrology.potential_river_network.segments),
            "marine_outlet_count": potential_mouths,
            "node_kinds": dict(
                sorted(
                    Counter(
                        node.kind.value
                        for node in hydrology.potential_river_network.nodes.values()
                    ).items()
                )
            ),
        },
        "validation": {
            "engine_invariants_passed": validation.engine_invariants.passed,
            "hard_constraints_passed": validation.hard_constraints.passed,
        },
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (args.output / "report.json").write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
