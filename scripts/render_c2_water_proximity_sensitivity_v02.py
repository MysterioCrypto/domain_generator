from __future__ import annotations

"""C2 local water-proximity sensitivity only. No changes to canonical C2 formula."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

from domain_generator.application import generate_domain, load_preset_catalog, registry_for_request
from domain_generator.contracts import GenerationRequest

ROOT = Path(__file__).resolve().parents[1]
A08 = ROOT / "tests" / "acceptance" / "cases" / "a08-core-v02-integrated"
CASES = (
    ("baseline", 0.55, 2.0),
    ("lower_boost", 0.40, 2.0),
    ("longer_decay", 0.55, 4.0),
    ("combined", 0.40, 4.0),
)
LABELS = {
    "baseline": "Baseline: boost 0.55, decay 2 km",
    "lower_boost": "Lower proximity boost: 0.40, 2 km",
    "longer_decay": "Longer proximity decay: 0.55, 4 km",
    "combined": "Combined: boost 0.40, decay 4 km",
}


def _world(boost: float, decay: float):
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    payload["domain_spec"]["surface"]["water_moisture_boost"] = boost
    payload["domain_spec"]["surface"]["water_moisture_decay_km"] = decay
    req = GenerationRequest.model_validate(payload)
    cat = load_preset_catalog(A08 / "presets.json")
    return generate_domain(
        spec=req.domain_spec, config=req.generation_config,
        registry=registry_for_request(req, cat),
    )


def _common_panel(path: Path, values: dict[str, np.ndarray], *, title: str, cmap="YlGnBu",
                  vmin: float = 0.0, vmax: float = 1.0) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    for ax, (name, raster) in zip(axes.flat, values.items()):
        rows, cols = raster.shape
        im = ax.imshow(raster, origin="upper", extent=(0, cols, 0, rows),
                       cmap=cmap, interpolation="nearest", vmin=vmin, vmax=vmax)
        ax.set(title=LABELS[name], xlabel="x (km)", ylabel="y (km)")
        ax.set_aspect("equal")
    cax = fig.add_axes((0.90, 0.15, 0.020, 0.66))
    fig.colorbar(im, cax=cax, label="same absolute normalized 0–1 color scale")
    fig.suptitle(title + "\nSame climate, terrain, MFD, lakes and rivers", fontsize=13)
    fig.subplots_adjust(left=0.055, right=0.87, bottom=0.08, top=0.89, hspace=0.22, wspace=0.12)
    fig.savefig(path, dpi=153)
    plt.close(fig)


def _edges(values: np.ndarray, land: np.ndarray, *, include_water: bool) -> np.ndarray:
    v = values.astype(np.float64)
    if include_water:
        h = np.abs(v[:, 1:] - v[:, :-1]).ravel()
        z = np.abs(v[1:] - v[:-1]).ravel()
    else:
        h = np.abs(v[:, 1:] - v[:, :-1])[land[:, 1:] & land[:, :-1]]
        z = np.abs(v[1:] - v[:-1])[land[1:] & land[:-1]]
    return np.concatenate((h, z))


def _stats(values: np.ndarray, land: np.ndarray) -> dict[str, float]:
    all_adjacent = _edges(values, land, include_water=True)
    land_adjacent = _edges(values, land, include_water=False)
    return {
        "mean_land": float(np.mean(values[land])),
        "p95_land_neighbor_jump": float(np.percentile(land_adjacent, 95)),
        "p99_land_neighbor_jump": float(np.percentile(land_adjacent, 99)),
        "p95_all_neighbor_jump_including_water_boundary": float(np.percentile(all_adjacent, 95)),
        "p99_all_neighbor_jump_including_water_boundary": float(np.percentile(all_adjacent, 99)),
        "max_land_neighbor_jump": float(np.max(land_adjacent)),
    }


def _delta(path: Path, baseline: np.ndarray, changed: np.ndarray) -> None:
    d = changed.astype(np.float64) - baseline.astype(np.float64)
    bound = max(1e-8, float(np.max(np.abs(d))))
    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(d, cmap="RdBu_r", origin="upper",
                   extent=(0, d.shape[1], 0, d.shape[0]),
                   norm=TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound),
                   interpolation="nearest")
    fig.colorbar(im, ax=ax, shrink=0.80, label="C2 combined candidate − baseline (normalized)")
    ax.set(title="Where changing C2 water proximity actually changes effective moisture",
           xlabel="x (km)", ylabel="y (km)")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=157)
    plt.close(fig)


def _comparison(path: Path, stats: dict[str, dict[str, float]]) -> None:
    keys = tuple(stats)
    x = np.arange(len(keys))
    p95 = [stats[k]["p95_land_neighbor_jump"] for k in keys]
    p99 = [stats[k]["p99_land_neighbor_jump"] for k in keys]
    p95_water = [stats[k]["p95_all_neighbor_jump_including_water_boundary"] for k in keys]
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.bar(x - 0.23, p95, width=0.22, label="p95 land-to-land")
    ax.bar(x, p99, width=0.22, label="p99 land-to-land")
    ax.bar(x + 0.23, p95_water, width=0.22, label="p95 including water edges")
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS[k] for k in keys], fontsize=9, rotation=6)
    ax.set(ylabel="absolute moisture change per adjacent 1 km cell",
           title="Are water-proximity changes actually smoothing C2 gradients?")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=158)
    plt.close(fig)


def _transect(path: Path, moisture: dict[str, np.ndarray], water: np.ndarray) -> None:
    # One fixed transect where water cells visibly constrain C2 to exactly 1.0.
    row = water.shape[0] // 2
    x = np.arange(water.shape[1]) + 0.5
    fig, ax = plt.subplots(figsize=(13, 5))
    for name, arr in moisture.items():
        ax.plot(x, arr[row, :], lw=1.6, label=LABELS[name])
    wet = water[row, :] > 0.0
    for col in np.flatnonzero(wet):
        ax.axvspan(col, col + 1, alpha=0.10, color="black", linewidth=0)
    ax.set(title="C2 transect through fixed river/water cells (shaded)",
           xlabel="x (km)", ylabel="effective moisture (0–1)")
    ax.set_ylim(-0.04, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=155)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    worlds = {name: _world(boost, decay) for name, boost, decay in CASES}
    base = worlds["baseline"]
    invariants = (
        "elevation", "water_depth", "annual_precipitation", "temperature",
    )
    moisture = {}
    vegetation = {}
    land = base.field_payloads["water_depth"] <= 0.0
    for name, assembly in worlds.items():
        for field in invariants:
            np.testing.assert_array_equal(
                assembly.field_payloads[field], base.field_payloads[field],
                err_msg=f"Changing C2 water-proximity recipe changed accepted {field}",
            )
        if assembly.data.features != base.data.features or assembly.data.networks != base.data.networks:
            raise RuntimeError("C2-only parameter experiment altered terrain/river feature geometry")
        moisture[name] = assembly.field_payloads["moisture"]
        vegetation[name] = assembly.field_payloads["vegetation_density"]
        if not bool(np.isfinite(moisture[name]).all()):
            raise RuntimeError("nonfinite C2 moisture")
        if not bool(np.all(moisture[name][~land] == 1.0)):
            raise RuntimeError("C2 water cell must remain exactly wet")

    stats = {name: _stats(arr, land) for name, arr in moisture.items()}
    ratios = {
        name: {
            "p95_land_ratio": values["p95_land_neighbor_jump"] / stats["baseline"]["p95_land_neighbor_jump"],
            "p99_land_ratio": values["p99_land_neighbor_jump"] / stats["baseline"]["p99_land_neighbor_jump"],
            "p95_including_water_ratio":
                values["p95_all_neighbor_jump_including_water_boundary"]
                / stats["baseline"]["p95_all_neighbor_jump_including_water_boundary"],
        }
        for name, values in stats.items()
    }
    _common_panel(args.output / "01-c2-moisture-4ways.png", moisture,
                  title="C2 surface moisture: isolate water-proximity settings")
    _common_panel(args.output / "02-c3-vegetation-4ways.png", vegetation,
                  title="C3 downstream vegetation response without changing C3 formula", cmap="YlGn")
    _delta(args.output / "03-c2-combined-minus-baseline.png", moisture["baseline"], moisture["combined"])
    _comparison(args.output / "04-c2-adjacent-cell-gradient-statistics.png", stats)
    _transect(args.output / "05-c2-transect-with-fixed-water-cells.png",
              moisture, base.field_payloads["water_depth"])
    report = {
        "checkpoint": "C2 water-proximity recipe sensitivity — visual-only, NO ACCEPT",
        "fixture": "A08; identical elevation, water, precipitation, temperature, networks and features",
        "scenarios": {name: {"water_moisture_boost": b, "water_moisture_decay_km": d}
                      for name, b, d in CASES},
        "stats": stats, "relative_neighbor_jump_ratios": ratios,
        "water_mask_exact_moisture_one_in_all_scenarios": True,
        "all_existing_climate_hydrology_topology_exact": True,
        "figure_count": 5,
        "caution": "These are temporary parameter variations, not model changes or physically calibrated groundwater/runoff. A lower gradient alone is not proof of greater realism.",
    }
    text = json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    (args.output / "report.json").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
