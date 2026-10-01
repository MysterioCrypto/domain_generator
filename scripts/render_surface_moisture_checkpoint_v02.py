from __future__ import annotations

import argparse
import json
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
from domain_generator.hydrology import generate_hydrology
from domain_generator.pipeline.rng import RngFactory
from domain_generator.surface import (
    distance_to_water_km,
    effective_surface_moisture_components,
    moisture_field,
    slope_degrees,
)
from domain_generator.terrain.state import TerrainState


def _hillshade(elevation_m: np.ndarray, *, cell_size_km: float) -> np.ndarray:
    light = LightSource(azdeg=315.0, altdeg=38.0)
    return light.hillshade(
        np.flipud(np.asarray(elevation_m, dtype=np.float64)) / 1000.0,
        vert_exag=1.8,
        dx=cell_size_km,
        dy=cell_size_km,
    )


def _save_field(
    output_path: Path,
    *,
    elevation_m: np.ndarray,
    field: np.ndarray,
    width_km: float,
    height_km: float,
    cell_size_km: float,
    title: str,
    label: str,
    cmap: str = "viridis",
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    ax.imshow(
        _hillshade(elevation_m, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="gray",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.38,
    )
    image = ax.imshow(
        np.flipud(np.asarray(field, dtype=np.float64)),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap=cmap,
        interpolation="bilinear",
        aspect="equal",
        alpha=0.78,
        vmin=vmin,
        vmax=vmax,
    )
    bar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    bar.set_label(label)
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_title(title)
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _save_legacy_comparison(
    output_path: Path,
    *,
    elevation_m: np.ndarray,
    legacy_moisture: np.ndarray,
    effective_moisture: np.ndarray,
    width_km: float,
    height_km: float,
    cell_size_km: float,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(18.0, 7.5), dpi=160)
    for ax, field, title in (
        (axes[0], legacy_moisture, "Legacy Surface 0.1 moisture"),
        (axes[1], effective_moisture, "C2-A effective surface moisture"),
    ):
        ax.imshow(
            _hillshade(elevation_m, cell_size_km=cell_size_km),
            origin="lower",
            extent=(0.0, width_km, 0.0, height_km),
            cmap="gray",
            interpolation="bilinear",
            aspect="equal",
            alpha=0.32,
        )
        image = ax.imshow(
            np.flipud(np.asarray(field, dtype=np.float64)),
            origin="lower",
            extent=(0.0, width_km, 0.0, height_km),
            cmap="viridis",
            interpolation="bilinear",
            aspect="equal",
            alpha=0.80,
            vmin=0.0,
            vmax=1.0,
        )
        ax.set_title(title)
        ax.set_xlabel("km east")
        ax.set_ylabel("km north")
        ax.set_xlim(0.0, width_km)
        ax.set_ylim(0.0, height_km)
    bar = fig.colorbar(image, ax=axes.ravel().tolist(), fraction=0.025, pad=0.02)
    bar.set_label("normalized moisture")
    fig.suptitle("C2-A — Legacy heuristic vs climate-aware effective moisture")
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _plot_lakes(ax, hydrology) -> None:
    for _lake_id, feature in sorted(hydrology.lake_features.items()):
        for polygon in feature.geometry.polygons:
            xs = [float(point.x_km) for point in polygon.outer]
            ys = [float(point.y_km) for point in polygon.outer]
            if not xs:
                continue
            ax.fill(xs, ys, alpha=0.68, zorder=7)
            ax.plot(xs + [xs[0]], ys + [ys[0]], linewidth=0.8, zorder=8)


def _plot_rivers(ax, hydrology) -> None:
    network = hydrology.river_network
    if network is None:
        return
    for segment in network.segments.values():
        xs = [float(point.x_km) for point in segment.centerline]
        ys = [float(point.y_km) for point in segment.centerline]
        if len(xs) >= 2:
            ax.plot(xs, ys, linewidth=1.1, alpha=0.90, zorder=9)


def _save_hydrology_overlay(
    output_path: Path,
    *,
    elevation_m: np.ndarray,
    moisture: np.ndarray,
    hydrology,
    width_km: float,
    height_km: float,
    cell_size_km: float,
) -> None:
    fig, ax = plt.subplots(figsize=(15.0, 10.0), dpi=160)
    ax.imshow(
        _hillshade(elevation_m, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="gray",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.30,
    )
    image = ax.imshow(
        np.flipud(np.asarray(moisture, dtype=np.float64)),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="viridis",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.76,
        vmin=0.0,
        vmax=1.0,
    )
    _plot_lakes(ax, hydrology)
    _plot_rivers(ax, hydrology)
    bar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    bar.set_label("effective moisture")
    ax.set_title("C2-A — Effective moisture with accepted rivers and lakes")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _percentiles(array: np.ndarray, mask: np.ndarray | None = None) -> dict[str, float]:
    values = np.asarray(array, dtype=np.float64)
    if mask is not None:
        values = values[np.asarray(mask, dtype=np.bool_)]
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


def _corr(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> float | None:
    av = np.asarray(a, dtype=np.float64)[mask]
    bv = np.asarray(b, dtype=np.float64)[mask]
    if av.size < 2 or float(np.std(av)) == 0.0 or float(np.std(bv)) == 0.0:
        return None
    return float(np.corrcoef(av, bv)[0, 1])


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
        raise RuntimeError("C2-A checkpoint requires Core 0.2 climate plan")

    assembly = generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry,
    )
    elevation = np.asarray(assembly.field_payloads["elevation"], dtype=np.float64)
    water_depth = np.asarray(assembly.field_payloads["water_depth"], dtype=np.float64)
    temperature = np.asarray(assembly.field_payloads["temperature"], dtype=np.float64)
    precipitation = np.asarray(
        assembly.field_payloads["annual_precipitation"],
        dtype=np.float64,
    )
    final_moisture = np.asarray(assembly.field_payloads["moisture"], dtype=np.float64)

    terrain = TerrainState(elevation_m=elevation)
    hydrology = generate_hydrology(plan, terrain)
    slope = slope_degrees(elevation, cell_size_km=plan.grid.cell_size_km)
    adapter = GridAdapter.from_plan(plan)
    components = effective_surface_moisture_components(
        adapter=adapter,
        annual_mean_temperature_c=temperature,
        annual_precipitation_mm=precipitation,
        flow_accumulation_km2=hydrology.flow_accumulation_km2,
        water_depth_m=water_depth,
        slope_deg=slope,
        stream_threshold_km2=plan.hydrology.stream_threshold_km2,
        water_moisture_boost=plan.surface.water_moisture_boost,
        water_moisture_decay_km=plan.surface.water_moisture_decay_km,
    )

    # Representative request has no Surface-family feature bias, so canonical
    # moisture must equal the raw C2 effective-moisture field.
    if any(feature.family.value == "surface" for feature in plan.features):
        raise RuntimeError("C2-A checkpoint request must not contain Surface feature biases")
    np.testing.assert_allclose(
        final_moisture,
        components.effective_moisture,
        rtol=0.0,
        atol=1e-7,
    )

    legacy_moisture = moisture_field(
        adapter=adapter,
        water_depth_m=water_depth,
        moisture_base=plan.surface.moisture_base,
        water_moisture_boost=plan.surface.water_moisture_boost,
        water_moisture_decay_km=plan.surface.water_moisture_decay_km,
        moisture_noise_amplitude=plan.surface.moisture_noise_amplitude,
        moisture_noise_scale_km=plan.surface.moisture_noise_scale_km,
        rng_factory=RngFactory(plan.seed),
        attempt_index=0,
    )
    distance = distance_to_water_km(
        (water_depth > 0.0).astype(np.bool_),
        cell_size_km=plan.grid.cell_size_km,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    width_km = float(plan.domain.width_km)
    height_km = float(plan.domain.height_km)
    cell_size_km = float(plan.grid.cell_size_km)

    _save_field(
        args.output / "01-climatic-wetness.png",
        elevation_m=elevation,
        field=components.climatic_wetness,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C2-A — Climatic wetness (precipitation vs annual PET proxy)",
        label="climatic wetness",
        vmin=0.0,
        vmax=1.0,
    )
    _save_field(
        args.output / "02-water-proximity.png",
        elevation_m=elevation,
        field=components.water_proximity_signal,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C2-A — Canonical-water proximity signal",
        label="local water signal",
        vmin=0.0,
        vmax=1.0,
    )
    _save_field(
        args.output / "03-catchment-signal.png",
        elevation_m=elevation,
        field=components.climate_gated_catchment,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C2-A — Climate-gated contributing-area signal",
        label="gated catchment signal",
        vmin=0.0,
        vmax=1.0,
    )
    _save_field(
        args.output / "04-slope-retention.png",
        elevation_m=elevation,
        field=components.slope_retention,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C2-A — Slope retention proxy",
        label="cos²(slope)",
        vmin=0.0,
        vmax=1.0,
    )
    _save_field(
        args.output / "05-effective-moisture.png",
        elevation_m=elevation,
        field=final_moisture,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C2-A — Final effective surface moisture",
        label="effective moisture",
        vmin=0.0,
        vmax=1.0,
    )
    _save_legacy_comparison(
        args.output / "06-legacy-vs-effective.png",
        elevation_m=elevation,
        legacy_moisture=legacy_moisture,
        effective_moisture=final_moisture,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
    )
    _save_hydrology_overlay(
        args.output / "07-effective-moisture-hydrology.png",
        elevation_m=elevation,
        moisture=final_moisture,
        hydrology=hydrology,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
    )

    water_mask = water_depth > 0.0
    land = ~water_mask
    finite_distance = land & np.isfinite(distance)
    log_accumulation = np.log1p(np.asarray(hydrology.flow_accumulation_km2, dtype=np.float64))
    stats = {
        "checkpoint": "C2-A",
        "seed": int(plan.seed),
        "shape": [int(plan.grid.rows), int(plan.grid.columns)],
        "cell_size_km": cell_size_km,
        "water_cell_count": int(np.count_nonzero(water_mask)),
        "land_cell_count": int(np.count_nonzero(land)),
        "climatic_wetness": _percentiles(components.climatic_wetness, land),
        "water_proximity_signal": _percentiles(components.water_proximity_signal, land),
        "climate_gated_catchment": _percentiles(components.climate_gated_catchment, land),
        "slope_retention": _percentiles(components.slope_retention, land),
        "legacy_moisture": _percentiles(legacy_moisture, land),
        "effective_moisture": _percentiles(final_moisture, land),
        "effective_moisture_fraction_ge_0_8": float(np.mean(final_moisture[land] >= 0.8)),
        "effective_moisture_fraction_le_0_2": float(np.mean(final_moisture[land] <= 0.2)),
        "correlations_on_land": {
            "precipitation": _corr(final_moisture, precipitation, land),
            "temperature": _corr(final_moisture, temperature, land),
            "slope": _corr(final_moisture, slope, land),
            "log1p_accumulation": _corr(final_moisture, log_accumulation, land),
            "distance_to_water": _corr(final_moisture, distance, finite_distance)
            if bool(finite_distance.any())
            else None,
            "legacy_moisture": _corr(final_moisture, legacy_moisture, land),
        },
    }
    (args.output / "statistics.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
