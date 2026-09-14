from __future__ import annotations

import argparse
import json
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
from domain_generator.layout import generate_layout
from domain_generator.pipeline.rng import RngFactory
from domain_generator.terrain import generate_terrain


def _render_field(
    field: np.ndarray,
    *,
    width_km: float,
    height_km: float,
    cell_size_km: float,
    title: str,
    output_path: Path,
) -> None:
    # Canonical raster row 0 is north. Flip once for ordinary cartographic
    # plotting with +y north and origin at the southwest corner.
    z_m = np.flipud(np.asarray(field, dtype=np.float64))
    z_km = z_m / 1000.0
    x = (np.arange(z_m.shape[1], dtype=np.float64) + 0.5) * cell_size_km
    y = (np.arange(z_m.shape[0], dtype=np.float64) + 0.5) * cell_size_km

    light = LightSource(azdeg=315.0, altdeg=38.0)
    rgb = light.shade(
        z_km,
        cmap=plt.get_cmap("terrain"),
        vert_exag=1.8,
        dx=cell_size_km,
        dy=cell_size_km,
        blend_mode="soft",
    )

    fig, ax = plt.subplots(figsize=(13.5, 9.0), dpi=150)
    image = ax.imshow(
        rgb,
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        interpolation="bilinear",
        aspect="equal",
    )
    del image

    z_min = float(np.min(z_m))
    z_max = float(np.max(z_m))
    if z_max > z_min:
        levels = np.linspace(z_min, z_max, 14)[1:-1]
        ax.contour(
            x,
            y,
            z_m,
            levels=levels,
            linewidths=0.45,
            alpha=0.28,
        )

    # Separate scalar mappable keeps the colorbar tied to actual metres even
    # though the visible raster is hillshaded RGB.
    scalar = plt.cm.ScalarMappable(cmap="terrain")
    scalar.set_clim(z_min, z_max)
    colorbar = fig.colorbar(scalar, ax=ax, fraction=0.035, pad=0.025)
    colorbar.set_label("Elevation, m")

    ax.set_xlim(0.0, width_km)
    ax.set_ylim(0.0, height_km)
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


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
    if plan.plan_version != "0.2":
        raise RuntimeError("terrain checkpoint requires GenerationPlan 0.2")

    rng_factory = RngFactory(plan.seed)
    layout = generate_layout(plan, attempt_index=0, rng_factory=rng_factory)
    terrain = generate_terrain(
        plan,
        layout,
        attempt_index=0,
        rng_factory=rng_factory,
    )
    if terrain.base_elevation_m is None:
        raise RuntimeError("Core 0.2 terrain state must contain base_elevation_m")

    args.output.mkdir(parents=True, exist_ok=True)
    _render_field(
        terrain.base_elevation_m,
        width_km=plan.domain.width_km,
        height_km=plan.domain.height_km,
        cell_size_km=plan.grid.cell_size_km,
        title="Core 0.2 — base continuous elevation",
        output_path=args.output / "base-elevation.png",
    )
    _render_field(
        terrain.elevation_m,
        width_km=plan.domain.width_km,
        height_km=plan.domain.height_km,
        cell_size_km=plan.grid.cell_size_km,
        title="Core 0.2 — final terrain after natural modifiers",
        output_path=args.output / "final-elevation.png",
    )

    contribution = terrain.elevation_m.astype(np.float64) - terrain.base_elevation_m.astype(np.float64)
    metrics = {
        "plan_version": plan.plan_version,
        "shape": list(terrain.elevation_m.shape),
        "cell_size_km": plan.grid.cell_size_km,
        "base": {
            "min_m": float(np.min(terrain.base_elevation_m)),
            "max_m": float(np.max(terrain.base_elevation_m)),
            "std_m": float(np.std(terrain.base_elevation_m)),
        },
        "final": {
            "min_m": float(np.min(terrain.elevation_m)),
            "max_m": float(np.max(terrain.elevation_m)),
            "std_m": float(np.std(terrain.elevation_m)),
        },
        "modifier_contribution": {
            "min_m": float(np.min(contribution)),
            "max_m": float(np.max(contribution)),
            "nonzero_cells": int(np.count_nonzero(np.abs(contribution) > 0.01)),
        },
        "features": sorted(layout.geometry_realizations),
    }
    (args.output / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
