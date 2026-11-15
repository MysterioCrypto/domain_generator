from __future__ import annotations

"""Visual-only C1/C2 gradient experiment; accepted algorithms remain untouched.

This checkpoint tests explicit existing C1 climate recipe settings. It does NOT
apply blur/postprocessing or replace the canonical C1/C2 baseline.
"""

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
SCENARIOS = (
    ("baseline", 18.0, 1.2),
    ("weaker_orography", 18.0, 0.75),
    ("longer_upwind", 27.0, 1.2),
    ("combined_candidate", 27.0, 0.75),
)
LABELS = {
    "baseline": "Baseline: 18 km / 1.20",
    "weaker_orography": "Reduced relief contrast: 18 km / 0.75",
    "longer_upwind": "Longer upwind reference: 27 km / 1.20",
    "combined_candidate": "Combined candidate: 27 km / 0.75",
}


def _generate(*, orographic_scale_km: float, orographic_strength: float):
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    climate = payload["domain_spec"]["surface"]["climate"]
    climate["orographic_scale_km"] = orographic_scale_km
    climate["orographic_strength"] = orographic_strength
    request = GenerationRequest.model_validate(payload)
    catalog = load_preset_catalog(A08 / "presets.json")
    assembly = generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry_for_request(request, catalog),
    )
    return assembly, request


def _plot_four(
    path: Path,
    data: dict[str, np.ndarray],
    *,
    title: str,
    label: str,
    cmap: str,
    vmin: float | None = None,
    vmax: float | None = None,
    log: bool = False,
) -> None:
    first_shape = next(iter(data.values())).shape
    if any(x.shape != first_shape for x in data.values()):
        raise RuntimeError("All four experiment rasters must share a grid")
    scaled = {key: np.log10(np.maximum(x, 1.0)) if log else x for key, x in data.items()}
    if vmin is None:
        vmin = min(float(np.nanmin(x)) for x in scaled.values())
    if vmax is None:
        vmax = max(float(np.nanmax(x)) for x in scaled.values())
    if vmax <= vmin:
        vmax = vmin + 1.0

    rows, cols = first_shape
    fig, axes = plt.subplots(2, 2, figsize=(15, 11), sharex=True, sharey=True)
    for ax, (name, x) in zip(axes.ravel(), scaled.items()):
        im = ax.imshow(
            x, origin="upper", extent=(0, cols, 0, rows),
            interpolation="nearest", cmap=cmap, vmin=vmin, vmax=vmax,
        )
        ax.set_title(LABELS[name], fontsize=10)
        ax.set_xlabel("x (km)")
        ax.set_ylabel("y (km)")
        ax.set_aspect("equal")
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.76, pad=0.012,
                 label=("log10 " if log else "") + label + " — SAME COLOR SCALE")
    fig.suptitle(title + "\nIdentical terrain, seed, stream topology; atmospheric parameters only", fontsize=13)
    fig.subplots_adjust(top=0.88, bottom=0.07, left=0.07, right=0.89, hspace=0.23, wspace=0.14)
    fig.savefig(path, dpi=145)
    plt.close(fig)


def _land_gradients(values: np.ndarray, land: np.ndarray) -> np.ndarray:
    """Per-cell-neighbor absolute differences; exclude water/land boundary edges."""
    if values.shape != land.shape:
        raise RuntimeError("mask mismatch")
    v = values.astype(np.float64)
    horizontal = np.abs(v[:, 1:] - v[:, :-1])[land[:, 1:] & land[:, :-1]]
    vertical = np.abs(v[1:, :] - v[:-1, :])[land[1:, :] & land[:-1, :]]
    return np.concatenate((horizontal, vertical))


def _gradient_image(values: np.ndarray, land: np.ndarray) -> np.ndarray:
    """Per-cell max one-neighbor difference on land, not a smoothing operator."""
    values = values.astype(np.float64)
    result = np.zeros_like(values)
    for row_delta, col_delta in ((0, 1), (1, 0)):
        if row_delta:
            diff = np.abs(values[1:] - values[:-1])
            both = land[1:] & land[:-1]
            diff = np.where(both, diff, 0.0)
            result[1:] = np.maximum(result[1:], diff)
            result[:-1] = np.maximum(result[:-1], diff)
        else:
            diff = np.abs(values[:, 1:] - values[:, :-1])
            both = land[:, 1:] & land[:, :-1]
            diff = np.where(both, diff, 0.0)
            result[:, 1:] = np.maximum(result[:, 1:], diff)
            result[:, :-1] = np.maximum(result[:, :-1], diff)
    return np.where(land, result, np.nan)


def _metrics(values: np.ndarray, land: np.ndarray) -> dict[str, float]:
    arr = values.astype(np.float64)
    jumps = _land_gradients(arr, land)
    if jumps.size == 0:
        raise RuntimeError("no land adjacency in fixture")
    return {
        "land_mean": float(np.mean(arr[land])),
        "land_median": float(np.median(arr[land])),
        "land_min": float(np.min(arr[land])),
        "land_max": float(np.max(arr[land])),
        "neighbor_absolute_delta_median": float(np.median(jumps)),
        "neighbor_absolute_delta_p95": float(np.percentile(jumps, 95)),
        "neighbor_absolute_delta_p99": float(np.percentile(jumps, 99)),
        "neighbor_absolute_delta_max": float(np.max(jumps)),
    }


def _plot_delta(path: Path, baseline: np.ndarray, changed: np.ndarray, *, title: str, unit: str) -> None:
    diff = changed.astype(np.float64) - baseline.astype(np.float64)
    bound = max(float(np.max(np.abs(diff))), 1e-10)
    norm = TwoSlopeNorm(vmin=-bound, vcenter=0.0, vmax=bound)
    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(diff, origin="upper", extent=(0, diff.shape[1], 0, diff.shape[0]),
                   cmap="RdBu_r", norm=norm, interpolation="nearest")
    fig.colorbar(im, ax=ax, shrink=0.81, label="Combined minus baseline (" + unit + ")")
    ax.set(title=title, xlabel="x (km)", ylabel="y (km)")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=155)
    plt.close(fig)


def _plot_cross_sections(path: Path, data: dict[str, np.ndarray], *, title: str, unit: str) -> None:
    row = next(iter(data.values())).shape[0] // 2
    fig, ax = plt.subplots(figsize=(13, 5))
    for name, values in data.items():
        ax.plot(np.arange(values.shape[1]) + 0.5, values[row], label=LABELS[name], linewidth=1.7)
    ax.set(xlabel="World x (km), middle row", ylabel=unit, title=title)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=155)
    plt.close(fig)


def _plot_neighbor_p95(
    path: Path, metrics: dict[str, dict[str, dict[str, float]]], field: str,
    *,
    title: str, unit: str
) -> None:
    names = list(metrics)
    p95 = [metrics[name][field]["neighbor_absolute_delta_p95"] for name in names]
    p99 = [metrics[name][field]["neighbor_absolute_delta_p99"] for name in names]
    xs = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.bar(xs - 0.17, p95, 0.34, label="95th percentile (land neighbors)")
    ax.bar(xs + 0.17, p99, 0.34, label="99th percentile (land neighbors)")
    ax.set_xticks(xs)
    ax.set_xticklabels([LABELS[name] for name in names], rotation=8, fontsize=8)
    ax.set(ylabel=unit + " per 1 km neighboring cell", title=title)
    ax.grid(axis="y", alpha=0.22)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=155)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.output
    root.mkdir(parents=True, exist_ok=True)

    assemblies = {}
    requests = {}
    for name, scale, strength in SCENARIOS:
        assemblies[name], requests[name] = _generate(
            orographic_scale_km=scale, orographic_strength=strength,
        )

    original = assemblies["baseline"]
    baseline_fields = original.field_payloads
    unchanged = ("elevation", "water_depth")
    for name, assembly in assemblies.items():
        for field in unchanged:
            np.testing.assert_array_equal(
                baseline_fields[field], assembly.field_payloads[field],
                err_msg=f"{name} changed accepted upstream {field}",
            )
        if assembly.data.networks != original.data.networks:
            raise RuntimeError(f"{name} changed accepted river topology")
        if assembly.data.features != original.data.features:
            raise RuntimeError(f"{name} changed feature geometry")
        for field in ("annual_precipitation", "moisture", "vegetation_density"):
            arr = assembly.field_payloads[field]
            if not bool(np.isfinite(arr).all()):
                raise RuntimeError(f"{name}/{field} is nonfinite")

    land = baseline_fields["water_depth"] <= 0
    if not np.any(land):
        raise RuntimeError("A08 has no land cells")

    precipitation = {name: assembly.field_payloads["annual_precipitation"] for name, assembly in assemblies.items()}
    moisture = {name: assembly.field_payloads["moisture"] for name, assembly in assemblies.items()}
    vegetation = {name: assembly.field_payloads["vegetation_density"] for name, assembly in assemblies.items()}

    if all(np.array_equal(precipitation["baseline"], precipitation[n]) for n in precipitation if n != "baseline"):
        raise RuntimeError("C1 parameter experiment failed to alter precipitation")

    metric = {}
    for name in assemblies:
        metric[name] = {
            "annual_precipitation": _metrics(precipitation[name], land),
            "moisture": _metrics(moisture[name], land),
            "vegetation_density": _metrics(vegetation[name], land),
        }

    _plot_four(root / "01-precipitation-4ways-shared-scale.png", precipitation,
               title="C1 precipitation: baseline versus explicit recipe alternatives",
               label="annual precipitation (mm/year)", cmap="viridis", log=True)
    _plot_four(root / "02-moisture-4ways-shared-scale.png", moisture,
               title="C2 effective surface moisture: does local contrast really soften?",
               label="effective moisture (normalized)", cmap="YlGnBu", vmin=0.0, vmax=1.0)
    _plot_four(root / "03-vegetation-4ways-shared-scale.png", vegetation,
               title="C3 vegetation response (diagnostic only; no C3 algorithm change)",
               label="vegetation density (normalized)", cmap="YlGn", vmin=0.0, vmax=1.0)
    _plot_delta(root / "04-c1-combined-minus-baseline.png",
                precipitation["baseline"], precipitation["combined_candidate"],
                title="C1 precipitation redistribution: combined candidate vs baseline",
                unit="mm/year")
    _plot_delta(root / "05-c2-combined-minus-baseline.png",
                moisture["baseline"], moisture["combined_candidate"],
                title="C2 effective moisture difference: same terrain and hydrology",
                unit="normalized")
    _plot_neighbor_p95(root / "06-c1-neighbor-jump-percentiles.png", metric, "annual_precipitation",
                       title="C1 adjacent 1 km land-cell contrasts: measured, not visually guessed",
                       unit="mm/year")
    _plot_neighbor_p95(root / "07-c2-neighbor-jump-percentiles.png", metric, "moisture",
                       title="C2 adjacent 1 km land-cell contrasts (water boundary excluded)",
                       unit="normalized")
    _plot_cross_sections(root / "08-c1-middle-row-transect.png", precipitation,
                         title="C1 annual precipitation along middle row", unit="mm/year")
    _plot_cross_sections(root / "09-c2-middle-row-transect.png", moisture,
                         title="C2 effective moisture along middle row", unit="normalized")
    _plot_four(
        root / "10-c1-local-gradient-magnitude.png",
        {name: _gradient_image(field, land) for name, field in precipitation.items()},
        title="C1 maximum local jump to land neighbor (diagnostic, not smoothing)",
        label="absolute neighbor difference (mm/year)", cmap="magma",
    )
    _plot_four(
        root / "11-c2-local-gradient-magnitude.png",
        {name: _gradient_image(field, land) for name, field in moisture.items()},
        title="C2 maximum local jump to land neighbor (water boundaries excluded)",
        label="absolute neighbor difference (normalized)", cmap="magma",
    )

    relative_p95 = {
        name: {
            key: (
                metric[name][key]["neighbor_absolute_delta_p95"]
                / metric["baseline"][key]["neighbor_absolute_delta_p95"]
                if metric["baseline"][key]["neighbor_absolute_delta_p95"] > 0 else None
            )
            for key in ("annual_precipitation", "moisture", "vegetation_density")
        }
        for name in metric
    }
    report = {
        "checkpoint": "C1/C2 moisture gradient visual recipe experiment — NO MODEL CHANGE / NO ACCEPT",
        "fixed_inputs": "A08 same terrain/seed/Hydrology; same precipitation mean 850 mm/year; same climate noise; same C2/C3 recipes",
        "scenarios": {
            name: {"orographic_scale_km": scale, "orographic_strength": strength}
            for name, scale, strength in SCENARIOS
        },
        "metric_definitions": {
            "local_gradient": "absolute difference between 4-connected adjacent 1-km land cells, excluding edges that touch water",
            "median_and_p95": "distribution of per-edge differences, not a guarantee of climate realism",
            "color_scale": "identical within each 2x2 panel; log only for annual precipitation",
        },
        "land_cell_count": int(np.count_nonzero(land)),
        "baseline_world_and_hydrology_unchanged": True,
        "statistics": metric,
        "p95_ratio_to_baseline": relative_p95,
        "figure_count": 11,
        "scientific_caveat": "Parameter sensitivity only: no atmospheric conservation model, no hydrological runoff, no universal optimum or claim of increased physical accuracy",
        "operator_action": "Compare shared-scale 01 and 02, then 06/07 metrics; decide visually if recipe deserves a separate later change",
    }
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (root / "report.json").write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
