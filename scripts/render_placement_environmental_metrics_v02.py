from __future__ import annotations

import argparse
from hashlib import sha256
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
from domain_generator.contracts.geometry import RegionPolygon, RegionSet, WorldPoint
from domain_generator.contracts.layout import PlacementReservation
from domain_generator.contracts.plan import (
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    FeatureMetadata,
    FixedParameter,
    ParameterType,
    ReservationLayoutRecipe,
    ResolvedFeature,
    SitePreference,
    SiteProfile,
    SiteRequirement,
)
from domain_generator.contracts.validation import ValidationStage
from domain_generator.hydrology import hydrology_stage
from domain_generator.layout import layout_stage
from domain_generator.pipeline import StageStep, run_generation
from domain_generator.pipeline.final import final_stage
from domain_generator.pipeline.rng import RngFactory
from domain_generator.poi import (
    SiteMetricContext,
    evaluate_candidate_sites,
    filter_valid_sites,
    generate_candidate_points,
    near_best_sites,
    score_valid_sites,
    select_final_site,
)
from domain_generator.poi.generate import placement_stage
from domain_generator.surface import surface_stage
from domain_generator.terrain import terrain_stage


CANONICAL_STEPS = (
    StageStep(stage=ValidationStage.LAYOUT, handler=layout_stage),
    StageStep(stage=ValidationStage.TERRAIN, handler=terrain_stage),
    StageStep(stage=ValidationStage.HYDROLOGY, handler=hydrology_stage),
    StageStep(stage=ValidationStage.SURFACE, handler=surface_stage),
    StageStep(stage=ValidationStage.PLACEMENT, handler=placement_stage),
    StageStep(stage=ValidationStage.FINAL, handler=final_stage),
)


def _array_sha256(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    digest = sha256()
    digest.update(str(value.dtype).encode("ascii"))
    digest.update(str(tuple(value.shape)).encode("ascii"))
    digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def _hillshade(elevation_m: np.ndarray, *, cell_size_km: float) -> np.ndarray:
    light = LightSource(azdeg=315.0, altdeg=38.0)
    return light.hillshade(
        np.flipud(np.asarray(elevation_m, dtype=np.float64)) / 1000.0,
        vert_exag=1.8,
        dx=cell_size_km,
        dy=cell_size_km,
    )


def _save_field(
    path: Path,
    *,
    elevation: np.ndarray,
    field: np.ndarray,
    width_km: float,
    height_km: float,
    cell_size_km: float,
    title: str,
    label: str,
    cmap: str,
) -> None:
    fig, ax = plt.subplots(figsize=(15, 10), dpi=160)
    ax.imshow(
        _hillshade(elevation, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="gray",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.30,
    )
    image = ax.imshow(
        np.flipud(np.asarray(field, dtype=np.float64)),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap=cmap,
        interpolation="bilinear",
        aspect="equal",
        alpha=0.82,
    )
    bar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    bar.set_label(label)
    ax.set_title(title)
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _plot_network(ax, network, *, linewidth: float = 0.7, alpha: float = 0.7) -> None:
    for segment_id in sorted(network.segments):
        segment = network.segments[segment_id]
        xs = [float(point.x_km) for point in segment.centerline]
        ys = [float(point.y_km) for point in segment.centerline]
        ax.plot(xs, ys, linewidth=linewidth, alpha=alpha, zorder=6)


def _diagnostic_feature() -> ResolvedFeature:
    return ResolvedFeature(
        id="p08-a-diagnostic-site",
        metadata=FeatureMetadata(source_preset="p08-a-diagnostic"),
        family=FeatureFamily.POI,
        layout=ReservationLayoutRecipe(),
        effect=EffectRecipe(
            stage=EffectStage.DEPENDENT_PLACEMENT,
            operator="suitability_placement",
            parameters={
                "candidate_spacing_km": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=12.0,
                ),
                "near_best_delta": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=0.08,
                ),
            },
            site_profile=SiteProfile(
                footprint_radius_km=2.0,
                requirements=(
                    SiteRequirement(
                        metric="temperature_mean",
                        evaluator="greater_or_equal",
                        value=4.0,
                    ),
                    SiteRequirement(
                        metric="annual_precipitation_mean",
                        evaluator="greater_or_equal",
                        value=550.0,
                    ),
                ),
                preferences=(
                    SitePreference(
                        metric="temperature_mean",
                        evaluator="preferred_range",
                        min=6.0,
                        max=10.0,
                        weight=1.0,
                    ),
                    SitePreference(
                        metric="annual_precipitation_mean",
                        evaluator="maximize",
                        weight=1.0,
                    ),
                    SitePreference(
                        metric="distance_to_potential_drainage",
                        evaluator="minimize",
                        weight=1.0,
                    ),
                ),
            ),
        ),
    )


def _full_domain_region(width_km: float, height_km: float) -> RegionSet:
    return RegionSet(
        polygons=(
            RegionPolygon(
                outer=(
                    WorldPoint(x_km=0.0, y_km=0.0),
                    WorldPoint(x_km=width_km, y_km=0.0),
                    WorldPoint(x_km=width_km, y_km=height_km),
                    WorldPoint(x_km=0.0, y_km=height_km),
                )
            ),
        )
    )


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
        raise RuntimeError("P08-A checkpoint requires Core 0.2")

    run = run_generation(
        plan=plan,
        config=request.generation_config,
        steps=CANONICAL_STEPS,
    )
    candidate = run.selected
    state = candidate.state
    if (
        state.layout is None
        or state.terrain is None
        or state.hydrology is None
        or state.surface is None
    ):
        raise RuntimeError("representative candidate is missing required upstream state")
    if state.hydrology.potential_river_network is None:
        raise RuntimeError("representative candidate is missing potential drainage")
    if (
        state.surface.annual_mean_temperature_c is None
        or state.surface.annual_precipitation_mm is None
    ):
        raise RuntimeError("representative candidate is missing accepted C1 fields")

    before = {
        "elevation": _array_sha256(state.terrain.elevation_m),
        "water_depth": _array_sha256(state.hydrology.water_depth_m),
        "moisture": _array_sha256(state.surface.moisture),
        "vegetation": _array_sha256(state.surface.vegetation_density),
        "temperature": _array_sha256(state.surface.annual_mean_temperature_c),
        "precipitation": _array_sha256(state.surface.annual_precipitation_mm),
    }
    potential_before = state.hydrology.potential_river_network.model_dump(
        mode="json", by_alias=True, exclude_none=False
    )

    feature = _diagnostic_feature()
    diagnostic_plan = plan.model_copy(
        update={"features": tuple(plan.features) + (feature,)}
    )
    reservations = dict(state.layout.placement_reservations)
    reservations[feature.id] = PlacementReservation(
        allowed_region=_full_domain_region(
            float(plan.domain.width_km),
            float(plan.domain.height_km),
        )
    )
    diagnostic_layout = state.layout.model_copy(
        update={"placement_reservations": reservations}
    )

    context = SiteMetricContext.from_states(
        diagnostic_plan,
        state.terrain,
        state.hydrology,
        state.surface,
    )
    points = generate_candidate_points(
        diagnostic_plan,
        diagnostic_layout,
        feature.id,
        attempt_index=candidate.attempt_index,
        rng_factory=RngFactory(plan.seed),
    )
    assert feature.effect.site_profile is not None
    profile = feature.effect.site_profile
    evaluated = evaluate_candidate_sites(context, points, profile)
    valid = filter_valid_sites(
        evaluated,
        profile.requirements,
        metric_ids=context.metric_ids,
    )
    scored = score_valid_sites(
        valid,
        profile.preferences,
        metric_ids=context.metric_ids,
    )
    near_best = near_best_sites(scored, 0.08)
    selected = select_final_site(
        feature,
        valid,
        attempt_index=candidate.attempt_index,
        rng_factory=RngFactory(plan.seed),
        metric_ids=context.metric_ids,
    )
    if selected is None:
        raise RuntimeError("P08-A diagnostic fixture produced no selected site")

    after = {
        "elevation": _array_sha256(state.terrain.elevation_m),
        "water_depth": _array_sha256(state.hydrology.water_depth_m),
        "moisture": _array_sha256(state.surface.moisture),
        "vegetation": _array_sha256(state.surface.vegetation_density),
        "temperature": _array_sha256(state.surface.annual_mean_temperature_c),
        "precipitation": _array_sha256(state.surface.annual_precipitation_mm),
    }
    potential_after = state.hydrology.potential_river_network.model_dump(
        mode="json", by_alias=True, exclude_none=False
    )

    args.output.mkdir(parents=True, exist_ok=True)
    width_km = float(plan.domain.width_km)
    height_km = float(plan.domain.height_km)
    cell_size_km = float(plan.grid.cell_size_km)
    elevation = np.asarray(state.terrain.elevation_m, dtype=np.float64)
    temperature = np.asarray(
        state.surface.annual_mean_temperature_c, dtype=np.float64
    )
    precipitation = np.asarray(
        state.surface.annual_precipitation_mm, dtype=np.float64
    )

    _save_field(
        args.output / "01-temperature.png",
        elevation=elevation,
        field=temperature,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="P08-A — Accepted annual mean temperature",
        label="°C",
        cmap="coolwarm",
    )
    _save_field(
        args.output / "02-precipitation.png",
        elevation=elevation,
        field=precipitation,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="P08-A — Accepted annual precipitation",
        label="mm/year",
        cmap="Blues",
    )

    fig, ax = plt.subplots(figsize=(15, 10), dpi=160)
    ax.imshow(
        _hillshade(elevation, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="gray",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.55,
    )
    _plot_network(ax, state.hydrology.potential_river_network, linewidth=0.8, alpha=0.8)
    ax.scatter(
        [site.point.x_km for site in evaluated],
        [site.point.y_km for site in evaluated],
        s=12,
        alpha=0.55,
        zorder=8,
    )
    ax.set_title("P08-A — Potential drainage and diagnostic candidate lattice")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    fig.tight_layout()
    fig.savefig(args.output / "03-potential-drainage-candidates.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(15, 10), dpi=160)
    ax.imshow(
        _hillshade(elevation, cell_size_km=cell_size_km),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap="gray",
        interpolation="bilinear",
        aspect="equal",
        alpha=0.45,
    )
    _plot_network(ax, state.hydrology.potential_river_network, linewidth=0.7, alpha=0.55)
    ax.scatter(
        [site.point.x_km for site in evaluated],
        [site.point.y_km for site in evaluated],
        s=9,
        alpha=0.22,
        zorder=7,
        label="all candidates",
    )
    ax.scatter(
        [site.point.x_km for site in valid],
        [site.point.y_km for site in valid],
        s=18,
        alpha=0.50,
        zorder=8,
        label="valid",
    )
    ax.scatter(
        [site.site.point.x_km for site in near_best],
        [site.site.point.y_km for site in near_best],
        s=44,
        alpha=0.85,
        zorder=9,
        label="near-best",
    )
    ax.scatter(
        [selected.site.point.x_km],
        [selected.site.point.y_km],
        s=160,
        marker="*",
        zorder=10,
        label="selected",
    )
    ax.set_title("P08-A — Diagnostic placement fixture (not production policy)")
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(args.output / "04-diagnostic-selection.png", bbox_inches="tight")
    plt.close(fig)

    candidate_rows = []
    for site in evaluated:
        candidate_rows.append(
            {
                "x_km": float(site.point.x_km),
                "y_km": float(site.point.y_km),
                "temperature_mean": float(site.metrics["temperature_mean"]),
                "annual_precipitation_mean": float(
                    site.metrics["annual_precipitation_mean"]
                ),
                "distance_to_potential_drainage": float(
                    site.metrics["distance_to_potential_drainage"]
                ),
                "valid": site in valid,
            }
        )

    new_metric_ranges = {}
    for metric_id in (
        "temperature_mean",
        "annual_precipitation_mean",
        "distance_to_potential_drainage",
    ):
        values = np.asarray(
            [site.metrics[metric_id] for site in evaluated],
            dtype=np.float64,
        )
        finite = values[np.isfinite(values)]
        new_metric_ranges[metric_id] = {
            "min": float(np.min(finite)) if finite.size else None,
            "median": float(np.median(finite)) if finite.size else None,
            "max": float(np.max(finite)) if finite.size else None,
        }

    report = {
        "checkpoint": "P08-A",
        "fixture_policy": "diagnostic-only; not a production settlement heuristic",
        "attempt_index": candidate.attempt_index,
        "candidate_count": len(evaluated),
        "valid_count": len(valid),
        "near_best_count": len(near_best),
        "selected": {
            "x_km": float(selected.site.point.x_km),
            "y_km": float(selected.site.point.y_km),
            "suitability": float(selected.suitability),
            "metrics": {
                metric_id: float(selected.site.metrics[metric_id])
                for metric_id in (
                    "temperature_mean",
                    "annual_precipitation_mean",
                    "distance_to_potential_drainage",
                    "moisture_mean",
                    "vegetation_density_mean",
                    "distance_to_water",
                )
            },
        },
        "new_metric_ranges": new_metric_ranges,
        "upstream_hashes_unchanged": before == after,
        "potential_network_unchanged": potential_before == potential_after,
        "potential_network_segments": len(
            state.hydrology.potential_river_network.segments
        ),
    }
    if not report["upstream_hashes_unchanged"]:
        raise RuntimeError("P08-A diagnostic mutated upstream arrays")
    if not report["potential_network_unchanged"]:
        raise RuntimeError("P08-A diagnostic mutated potential drainage")

    (args.output / "candidate-metrics.json").write_text(
        json.dumps(candidate_rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
