from __future__ import annotations

import argparse
import json
from math import cos, radians, sin
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

import domain_generator
from domain_generator.application import (
    generate_domain,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.compiler import compile_domain_spec
from domain_generator.grid import GridAdapter
from domain_generator.pipeline.rng import RngFactory
from domain_generator.surface import annual_precipitation_field


def _hillshade(elevation_m: np.ndarray, *, cell_size_km: float) -> np.ndarray:
    light = LightSource(azdeg=315.0, altdeg=38.0)
    return light.hillshade(
        np.flipud(np.asarray(elevation_m, dtype=np.float64)) / 1000.0,
        vert_exag=1.8,
        dx=cell_size_km,
        dy=cell_size_km,
    )


def _save_overlay(
    output_path: Path,
    *,
    elevation_m: np.ndarray,
    field: np.ndarray,
    width_km: float,
    height_km: float,
    cell_size_km: float,
    title: str,
    colorbar_label: str,
    cmap: str,
) -> None:
    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    ax.imshow(
        _hillshade(elevation_m, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="gray",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.48,
    )
    image = ax.imshow(
        np.flipud(np.asarray(field, dtype=np.float64)),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap=cmap,
        interpolation="bilinear",
        aspect="equal",
        alpha=0.72,
    )
    bar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    bar.set_label(colorbar_label)
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_title(title)
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _save_precipitation_with_wind(
    output_path: Path,
    *,
    elevation_m: np.ndarray,
    precipitation_mm: np.ndarray,
    width_km: float,
    height_km: float,
    cell_size_km: float,
    bearing_deg: float,
) -> None:
    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    ax.imshow(
        _hillshade(elevation_m, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="gray",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.42,
    )
    image = ax.imshow(
        np.flipud(np.asarray(precipitation_mm, dtype=np.float64)),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="viridis",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.76,
    )
    theta = radians(bearing_deg)
    dx = sin(theta)
    dy = cos(theta)
    length = min(width_km, height_km) * 0.16
    x0 = width_km * 0.12
    y0 = height_km * 0.88
    ax.annotate(
        "",
        xy=(x0 + dx * length, y0 + dy * length),
        xytext=(x0, y0),
        arrowprops={"arrowstyle": "->", "linewidth": 2.8, "color": "black"},
        zorder=12,
    )
    ax.text(
        x0,
        y0 - height_km * 0.035,
        f"moisture transport {bearing_deg:.0f}°",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.72, "edgecolor": "none"},
        zorder=12,
    )
    bar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    bar.set_label("Annual precipitation, mm/year")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_title("C1-A — Annual precipitation with moisture-transport direction")
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _sample_bilinear(
    field: np.ndarray,
    *,
    x_km: float,
    y_km: float,
    width_km: float,
    height_km: float,
    cell_size_km: float,
) -> float:
    columns = field.shape[1]
    rows = field.shape[0]
    column_f = x_km / cell_size_km - 0.5
    row_f = (height_km - y_km) / cell_size_km - 0.5
    c0 = int(np.floor(column_f))
    r0 = int(np.floor(row_f))
    tx = column_f - c0
    ty = row_f - r0
    value = 0.0
    total = 0.0
    for dr, wy in ((0, 1.0 - ty), (1, ty)):
        for dc, wx in ((0, 1.0 - tx), (1, tx)):
            row = min(rows - 1, max(0, r0 + dr))
            column = min(columns - 1, max(0, c0 + dc))
            weight = max(0.0, wx * wy)
            value += weight * float(field[row, column])
            total += weight
    return value / total


def _save_along_wind_cross_section(
    output_path: Path,
    *,
    elevation_m: np.ndarray,
    precipitation_mm: np.ndarray,
    width_km: float,
    height_km: float,
    cell_size_km: float,
    bearing_deg: float,
) -> None:
    max_row, max_column = np.unravel_index(
        int(np.argmax(elevation_m)),
        elevation_m.shape,
    )
    center_x = (max_column + 0.5) * cell_size_km
    center_y = height_km - (max_row + 0.5) * cell_size_km
    theta = radians(bearing_deg)
    dx = sin(theta)
    dy = cos(theta)
    extent = np.hypot(width_km, height_km)
    samples = []
    for t in np.linspace(-extent, extent, 800):
        x = center_x + dx * float(t)
        y = center_y + dy * float(t)
        if 0.0 <= x <= width_km and 0.0 <= y <= height_km:
            samples.append((float(t), x, y))
    if len(samples) < 2:
        raise RuntimeError("cross-section did not intersect enough of the domain")

    distance = np.array([item[0] for item in samples], dtype=np.float64)
    elevation = np.array(
        [
            _sample_bilinear(
                elevation_m,
                x_km=x,
                y_km=y,
                width_km=width_km,
                height_km=height_km,
                cell_size_km=cell_size_km,
            )
            for _t, x, y in samples
        ],
        dtype=np.float64,
    )
    precipitation = np.array(
        [
            _sample_bilinear(
                precipitation_mm,
                x_km=x,
                y_km=y,
                width_km=width_km,
                height_km=height_km,
                cell_size_km=cell_size_km,
            )
            for _t, x, y in samples
        ],
        dtype=np.float64,
    )

    fig, ax1 = plt.subplots(figsize=(14.0, 7.0), dpi=160)
    ax1.plot(distance, elevation, linewidth=2.0)
    ax1.set_xlabel("distance along moisture transport, km")
    ax1.set_ylabel("elevation, m")
    ax2 = ax1.twinx()
    ax2.plot(distance, precipitation, linewidth=1.8, linestyle="--")
    ax2.set_ylabel("annual precipitation, mm/year")
    ax1.axvline(0.0, linewidth=0.8, alpha=0.45)
    ax1.set_title("C1-A — Along-wind cross-section through highest terrain")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _save_temperature_elevation_diagnostic(
    output_path: Path,
    *,
    elevation_m: np.ndarray,
    temperature_c: np.ndarray,
) -> None:
    elevation = np.asarray(elevation_m, dtype=np.float64).ravel()
    temperature = np.asarray(temperature_c, dtype=np.float64).ravel()
    edges = np.linspace(float(np.min(elevation)), float(np.max(elevation)), 17)
    centers = []
    means = []
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (elevation >= low) & (elevation < high)
        if high == edges[-1]:
            mask = (elevation >= low) & (elevation <= high)
        if bool(mask.any()):
            centers.append(float(np.mean(elevation[mask])))
            means.append(float(np.mean(temperature[mask])))

    fig, ax = plt.subplots(figsize=(10.0, 7.0), dpi=160)
    ax.scatter(elevation, temperature, s=5.0, alpha=0.16)
    ax.plot(centers, means, marker="o", linewidth=2.0)
    ax.set_xlabel("elevation, m")
    ax.set_ylabel("annual mean temperature, °C")
    ax.set_title("C1-A — Temperature response to elevation")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _percentiles(array: np.ndarray) -> dict[str, float]:
    values = np.asarray(array, dtype=np.float64)
    return {
        "min": float(np.min(values)),
        "p05": float(np.percentile(values, 5)),
        "p25": float(np.percentile(values, 25)),
        "p50": float(np.percentile(values, 50)),
        "p75": float(np.percentile(values, 75)),
        "p95": float(np.percentile(values, 95)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
    }


def _synthetic_windward_lee_fixture(seed: int) -> dict[str, float | bool]:
    rows = columns = 21
    adapter = GridAdapter(
        width_km=21.0,
        height_km=21.0,
        cell_size_km=1.0,
        rows=rows,
        columns=columns,
    )
    terrain = np.zeros((rows, columns), dtype=np.float64)
    center = (columns - 1) / 2.0
    for column in range(columns):
        terrain[:, column] = max(0.0, 1200.0 - 180.0 * abs(column - center))
    precipitation = annual_precipitation_field(
        adapter=adapter,
        elevation_m=terrain,
        water_depth_m=np.zeros((rows, columns), dtype=np.float32),
        mean_annual_precipitation_mm=900.0,
        moisture_transport_bearing_deg=90.0,
        orographic_scale_km=8.0,
        orographic_strength=3.0,
        precipitation_noise_log_amplitude=0.0,
        climate_noise_scale_km=10.0,
        rng_factory=RngFactory(seed),
        attempt_index=0,
    )
    windward = float(precipitation[10, 8])
    lee = float(precipitation[10, 12])
    return {
        "windward_mm": windward,
        "lee_mm": lee,
        "windward_over_lee": windward / lee,
        "passed": windward > lee,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
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
    if plan.plan_version != "0.2" or plan.surface.climate is None:
        raise RuntimeError("C1 climate checkpoint requires Core 0.2 climate plan")

    assembly = generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry,
    )
    elevation = assembly.field_payloads["elevation"]
    temperature = assembly.field_payloads["temperature"]
    precipitation = assembly.field_payloads["annual_precipitation"]
    water = assembly.field_payloads["water_depth"]
    climate = plan.surface.climate

    args.output.mkdir(parents=True, exist_ok=True)
    _save_overlay(
        args.output / "01-terrain-temperature.png",
        elevation_m=elevation,
        field=temperature,
        width_km=plan.domain.width_km,
        height_km=plan.domain.height_km,
        cell_size_km=plan.grid.cell_size_km,
        title="C1-A — Terrain + annual mean temperature",
        colorbar_label="Annual mean temperature, °C",
        cmap="coolwarm",
    )
    _save_overlay(
        args.output / "02-terrain-precipitation.png",
        elevation_m=elevation,
        field=precipitation,
        width_km=plan.domain.width_km,
        height_km=plan.domain.height_km,
        cell_size_km=plan.grid.cell_size_km,
        title="C1-A — Terrain + annual precipitation",
        colorbar_label="Annual precipitation, mm/year",
        cmap="viridis",
    )
    _save_precipitation_with_wind(
        args.output / "03-precipitation-wind.png",
        elevation_m=elevation,
        precipitation_mm=precipitation,
        width_km=plan.domain.width_km,
        height_km=plan.domain.height_km,
        cell_size_km=plan.grid.cell_size_km,
        bearing_deg=climate.moisture_transport_bearing_deg,
    )
    _save_along_wind_cross_section(
        args.output / "04-along-wind-cross-section.png",
        elevation_m=elevation,
        precipitation_mm=precipitation,
        width_km=plan.domain.width_km,
        height_km=plan.domain.height_km,
        cell_size_km=plan.grid.cell_size_km,
        bearing_deg=climate.moisture_transport_bearing_deg,
    )
    _save_temperature_elevation_diagnostic(
        args.output / "05-temperature-elevation.png",
        elevation_m=elevation,
        temperature_c=temperature,
    )

    land = water <= 0.0
    statistics = {
        "checkpoint": "C1-A",
        "seed": int(plan.seed),
        "shape": [int(plan.grid.rows), int(plan.grid.columns)],
        "cell_size_km": float(plan.grid.cell_size_km),
        "configured": climate.model_dump(mode="json"),
        "temperature_c": _percentiles(temperature),
        "precipitation_mm_year": _percentiles(precipitation),
        "land_mean_precipitation_mm_year": float(np.mean(precipitation[land]))
        if bool(land.any())
        else float(np.mean(precipitation)),
        "temperature_elevation_correlation": float(
            np.corrcoef(
                np.asarray(elevation, dtype=np.float64).ravel(),
                np.asarray(temperature, dtype=np.float64).ravel(),
            )[0, 1]
        ),
        "synthetic_windward_lee_fixture": _synthetic_windward_lee_fixture(plan.seed),
    }
    (args.output / "statistics.json").write_text(
        json.dumps(statistics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(statistics, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
