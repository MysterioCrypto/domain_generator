from __future__ import annotations

"""Short three-scene C2 sanity check for tabletop map output.

Only experiment with already-supported request parameters (2 km vs 4 km
water-moisture decay). No generator changes, smoothing filters, biome labels,
groundwater assumptions or normative calibration.
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource, to_rgba

from domain_generator.application import generate_domain, load_preset_catalog, registry_for_request
from domain_generator.contracts import GenerationRequest
from domain_generator.contracts.data import HydroFeature

ROOT = Path(__file__).resolve().parents[1]
A08 = ROOT / "tests" / "acceptance" / "cases" / "a08-core-v02-integrated"
SCENARIOS = (
    ("dry_inland", 180.0, False),
    ("wet_inland", 1500.0, False),
    ("coastal", 800.0, True),
)
BOOST = 0.55
ORIGINAL_DECAY = 2.0
CANDIDATE_DECAY = 4.0


def _world(precip_mm: float, coast: bool, decay: float):
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    payload["domain_spec"]["surface"]["climate"]["mean_annual_precipitation_mm"] = float(precip_mm)
    payload["domain_spec"]["surface"]["water_moisture_boost"] = BOOST
    payload["domain_spec"]["surface"]["water_moisture_decay_km"] = float(decay)
    if coast:
        payload["domain_spec"]["hydrology"]["marine"] = {"sea_level_m": 0.0}
    request = GenerationRequest.model_validate(payload)
    catalog = load_preset_catalog(A08 / "presets.json")
    return generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry_for_request(request, catalog),
    )


def _stats(field: np.ndarray, land: np.ndarray, *, changes: bool = False) -> dict[str, float]:
    field = field.astype(np.float64)
    hd = np.abs(field[:, 1:] - field[:, :-1])
    vd = np.abs(field[1:, :] - field[:-1, :])
    land_edges = np.concatenate(
        [hd[land[:, 1:] & land[:, :-1]], vd[land[1:, :] & land[:-1, :]]]
    )
    all_edges = np.concatenate([hd.ravel(), vd.ravel()])
    if not land_edges.size:
        raise RuntimeError("Expected nonempty land-to-land neighboring-cell mask")
    return {
        "mean_land": float(np.mean(field[land])),
        "p95_land_neighbor_jump": float(np.percentile(land_edges, 95)),
        "p99_land_neighbor_jump": float(np.percentile(land_edges, 99)),
        "p95_including_water_neighbor_jump": float(np.percentile(all_edges, 95)),
        "p99_including_water_neighbor_jump": float(np.percentile(all_edges, 99)),
        "land_fraction_above_0_8": float(np.mean(field[land] > 0.8)),
        "land_fraction_above_0_9": float(np.mean(field[land] > 0.9)),
    }


def _overlay_rivers(ax, assembly, *, color="#e9f8ff", linewidth: float = 0.85):
    for segment in assembly.data.networks["rivers"].segments.values():
        points = segment.centerline
        if len(points) >= 2:
            ax.plot([p.x_km for p in points], [p.y_km for p in points],
                    color=color, lw=linewidth, alpha=0.98, zorder=5)


def _contrast(path: Path, label: str, old, new, *, field: str, cmap: str,
              vmin: float = 0.0, vmax: float = 1.0):
    original = old.field_payloads[field]
    candidate = new.field_payloads[field]
    rows, cols = original.shape
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharex=True, sharey=True)
    for ax, arr, heading in zip(
        axes, (original, candidate),
        ("Baseline: water influence 2 km", "Candidate: water influence 4 km")
    ):
        im = ax.imshow(arr, extent=(0, cols, 0, rows), origin="upper", interpolation="nearest",
                       cmap=cmap, vmin=vmin, vmax=vmax)
        _overlay_rivers(ax, old, color="#ebf8fc", linewidth=0.65)
        ax.set(title=heading, xlabel="World x (km)", ylabel="World y (km)")
        ax.set_aspect("equal")
    fig.suptitle(f"{label}: {field} — identical terrain, rivers, climate, shared color scale", fontsize=13)
    fig.subplots_adjust(left=0.07, right=0.88, bottom=0.10, top=0.85, wspace=0.09)
    cax = fig.add_axes((0.90, 0.16, 0.020, 0.64))
    fig.colorbar(im, cax=cax, label=f"{field} normalized [0,1]")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _style_map(assembly) -> np.ndarray:
    """Pure rendering preview; not an assertion of Earth biome distribution."""
    fields = assembly.field_payloads
    veg = np.clip(np.asarray(fields["vegetation_density"], dtype=np.float64), 0, 1)
    wet = np.clip(np.asarray(fields["moisture"], dtype=np.float64), 0, 1)
    elev = np.asarray(fields["elevation"], dtype=np.float64)
    marine = np.asarray(fields.get("marine_mask", np.zeros_like(elev)), dtype=np.bool_)
    gray = LightSource(azdeg=315, altdeg=42).hillshade(
        np.flipud(elev) / 1000.0, vert_exag=1.65, dx=1.0, dy=1.0
    )
    gray = np.flipud(gray)
    # Renderer-only, continuous palette. Avoid categorical biome or ecosystem claims.
    low = np.array([0.76, 0.69, 0.50])
    high = np.array([0.23, 0.47, 0.31])
    green = np.clip(0.12 + 0.73 * veg + 0.15 * wet, 0, 1)
    rgb = low[None, None, :] * (1 - green[..., None]) + high[None, None, :] * green[..., None]
    light = np.clip(0.72 + 0.50 * gray, 0, 1.20)
    rgb = np.clip(rgb * light[..., None], 0, 1)
    # Only H12 marine water is a broad filled area. Raster channel cells
    # are NOT 1-km-wide rivers on a tabletop map: draw accepted river
    # centerlines as vectors and accepted lake polygons as regions below.
    rgb[marine] = np.array([0.17, 0.40, 0.60])
    return rgb


def _cartographic_preview(path: Path, scene, name: str, new, *, coast: bool):
    rgb = _style_map(new)
    if coast:
        marine_mask = np.asarray(new.field_payloads["marine_mask"], dtype=np.bool_)
        if not np.allclose(rgb[marine_mask], np.array([0.17, 0.40, 0.60])):
            raise RuntimeError("Cartographic preview failed to fill accepted marine sea support")
    rows, cols = rgb.shape[:2]
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.imshow(rgb, extent=(0, cols, 0, rows), origin="upper", interpolation="bilinear")
    # Draw actual accepted lake polygons, not the entire 1-km water-depth mask.
    for feature in new.data.features.values():
        if not isinstance(feature, HydroFeature):
            continue
        for polygon in feature.geometry.polygons:
            xs = [p.x_km for p in polygon.outer]
            ys = [p.y_km for p in polygon.outer]
            if len(xs) >= 3:
                ax.fill(xs, ys, facecolor="#4b849e", edgecolor="#d9eee9",
                        linewidth=0.65, alpha=0.97, zorder=4)
    _overlay_rivers(ax, new, color="#d6eefb", linewidth=0.95)
    # Discrete cartographic contour strokes do not change raster or data.
    elevation = np.asarray(new.field_payloads["elevation"], dtype=np.float64)
    levels = np.linspace(float(np.min(elevation)), float(np.max(elevation)), 10)[1:-1]
    ax.contour(
        np.arange(cols) + 0.5, rows - np.arange(rows) - 0.5,
        elevation, levels=levels, linewidths=0.3, alpha=0.25, colors="#3b3730",
    )
    if coast:
        marine = new.field_payloads.get("marine_mask")
        if marine is None or int(np.count_nonzero(marine)) == 0:
            raise RuntimeError("Coastal scene must contain real H12 marine support")
        ax.contour(
            np.arange(cols) + 0.5, rows - np.arange(rows) - 0.5,
            marine.astype(np.float64), levels=(0.5,), linewidths=1.3, colors="#e0f4f6",
        )
    ax.set(xlabel="km east", ylabel="km north",
           title=f"{name} — illustrative terrain + greenness cartographic preview\n"
                 "C2 4 km candidate; lakes/coast as polygons, rivers as vectors; NOT biomes")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=175)
    plt.close(fig)


def _summary_chart(path: Path, metrics: dict[str, dict]) -> None:
    names = [s[0] for s in SCENARIOS]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
    x = np.arange(len(names))
    for ax, field, title in (
        (axes[0], "p95_land_neighbor_jump", "Adjacent land-cell p95 gradient"),
        (axes[1], "p95_including_water_neighbor_jump", "All-neighbor p95 (incl. water)"),
    ):
        baseline = [metrics[n]["baseline_moisture"][field] for n in names]
        candidate = [metrics[n]["candidate_moisture"][field] for n in names]
        ax.bar(x - 0.18, baseline, 0.36, label="Baseline 2 km")
        ax.bar(x + 0.18, candidate, 0.36, label="Candidate 4 km")
        ax.set_xticks(x, names)
        ax.set(title=title, ylabel="Normalized moisture difference / 1-km cell")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(fontsize=9)
    fig.suptitle("Pragmatic C2 three-scene sanity check — no model changes", fontsize=13)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    metrics = {}
    worlds = {}
    for name, precip, coast in SCENARIOS:
        old = _world(precip, coast, ORIGINAL_DECAY)
        new = _world(precip, coast, CANDIDATE_DECAY)
        for immutable in (
            "elevation", "water_depth", "temperature", "annual_precipitation",
        ):
            np.testing.assert_array_equal(
                old.field_payloads[immutable], new.field_payloads[immutable],
                err_msg=f"{name}: C2 parameter unexpectedly changed {immutable}",
            )
        if old.data.networks != new.data.networks or old.data.features != new.data.features:
            raise RuntimeError(f"{name}: C2 parameter unexpectedly changed features/networks")
        if set(old.field_payloads) != set(new.field_payloads):
            raise RuntimeError(f"{name}: changed the public field schema")
        land = np.asarray(old.field_payloads["water_depth"]) <= 0.0
        if not np.any(land):
            raise RuntimeError(f"{name}: no land cells")
        for obj in (old, new):
            if not np.isfinite(obj.field_payloads["moisture"]).all():
                raise RuntimeError(f"{name}: nonfinite C2 field")
            if np.any(obj.field_payloads["moisture"][~land] != 1.0):
                raise RuntimeError(f"{name}: water cell moisture must equal 1.0")
        if coast:
            marine = old.field_payloads.get("marine_mask")
            if marine is None or not np.any(marine):
                raise RuntimeError("Coastal test has no accepted marine cells")

        metrics[name] = {
            "mean_annual_precipitation_mm": precip,
            "marine_enabled": coast,
            "baseline_moisture": _stats(old.field_payloads["moisture"], land),
            "candidate_moisture": _stats(new.field_payloads["moisture"], land),
            "baseline_vegetation_mean_land": float(np.mean(old.field_payloads["vegetation_density"][land])),
            "candidate_vegetation_mean_land": float(np.mean(new.field_payloads["vegetation_density"][land])),
            "gross_moisture_change_abs_mean_land": float(
                np.mean(np.abs(new.field_payloads["moisture"][land]
                               - old.field_payloads["moisture"][land]))
            ),
            "immutable_elevation_hydrology_c1_features_networks": True,
            "land_cells": int(np.count_nonzero(land)),
            "marine_cells": int(np.count_nonzero(old.field_payloads.get("marine_mask", np.zeros_like(land)))),
        }
        worlds[name] = (old, new)
        title = name.replace("_", " ").title()
        _contrast(args.output / f"01-{name}-moisture-before-after.png", title, old, new,
                  field="moisture", cmap="YlGnBu")
        _contrast(args.output / f"02-{name}-vegetation-before-after.png", title, old, new,
                  field="vegetation_density", cmap="YlGn")
        _cartographic_preview(args.output / f"03-{name}-cartographic-preview.png",
                             old, title, new, coast=coast)

    _summary_chart(args.output / "04-three-scene-p95-summary.png", metrics)

    # The pragmatic default must actually help on both land and water edges
    # and cannot silently convert dry scenes into a uniformly wet world.
    checks = {}
    for name, values in metrics.items():
        b, c = values["baseline_moisture"], values["candidate_moisture"]
        checks[name] = {
            "land_p95_improves": bool(c["p95_land_neighbor_jump"] < b["p95_land_neighbor_jump"]),
            "water_edge_p95_not_worse": bool(
                c["p95_including_water_neighbor_jump"]
                <= b["p95_including_water_neighbor_jump"] * 1.025
            ),
            "mean_moisture_increase": c["mean_land"] - b["mean_land"],
            "candidate_land_mean": c["mean_land"],
        }
    report = {
        "checkpoint": "C2 2km vs 4km 3-scene visual sanity check (A08 controlled family)",
        "semantics": "existing C2 recipe parameter; no changed algorithm or frozen defaults",
        "scenes": metrics,
        "quick_checks": checks,
        "figure_count": 10,
        "product_facing_preview": "continuous greenness/terrain composite with existing rivers; not biome classification",
        "limitations": "same A08 terrain/seed across scenes; dry/wet vary climate mean only, coastal adds accepted H12; not three independent world geographies",
        "suggestion": "Treat as art-direction candidate, not universal hydrological calibration; stop further tuning if maps appear readable",
    }
    output = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (args.output / "report.json").write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
