from __future__ import annotations

"""Operator-visible H13-A diagnostic: gross source accounting, NOT discharge."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from domain_generator.application import generate_domain, load_preset_catalog, registry_for_request
from domain_generator.compiler import compile_domain_spec
from domain_generator.contracts import GenerationRequest
from domain_generator.geometry import backend_region_set
from domain_generator.hydrology.continuous import generate_hydrology_v02
from domain_generator.hydrology.gross_input import accumulate_gross_precipitation_input
from domain_generator.terrain.state import TerrainState


ROOT = Path(__file__).resolve().parents[1]
A08 = ROOT / "tests" / "acceptance" / "cases" / "a08-core-v02-integrated"
FIELD = "gross_upstream_precipitation_m3_per_year"


def _request(*, mean_precip_mm: float, marine: bool) -> GenerationRequest:
    source = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    source["domain_spec"]["hydrology"]["climatic_input"] = {
        "scheme": "gross_mfd_precipitation_v1",
    }
    source["domain_spec"]["surface"]["climate"]["mean_annual_precipitation_mm"] = mean_precip_mm
    if marine:
        source["domain_spec"]["hydrology"]["marine"] = {"sea_level_m": 0.0}
    return GenerationRequest.model_validate(source)


def _calculate(*, mean_precip_mm: float, marine: bool):
    request = _request(mean_precip_mm=mean_precip_mm, marine=marine)
    catalog = load_preset_catalog(A08 / "presets.json")
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(request.domain_spec, registry=registry, generator_version="0.2.0.dev0")
    assembly = generate_domain(spec=request.domain_spec, config=request.generation_config, registry=registry)
    terrain = TerrainState(elevation_m=assembly.field_payloads["elevation"])
    hydrology = generate_hydrology_v02(plan, terrain)
    assert hydrology.continuous_routing is not None
    ledger = accumulate_gross_precipitation_input(
        hydrology.continuous_routing,
        assembly.field_payloads["annual_precipitation"],
        cell_size_km=plan.grid.cell_size_km,
        lake_candidates=hydrology.lake_candidates,
        lake_outlets=hydrology.lake_outlets,
        marine_mask=hydrology.marine_mask,
        marine_candidates=hydrology.marine_candidates,
    )
    np.testing.assert_array_equal(
        ledger.gross_upstream_precipitation_m3_per_year,
        assembly.field_payloads[FIELD],
    )
    tolerance = max(1e-4, 1e-9 * ledger.source_total_m3_per_year)
    if abs(ledger.balance_error_m3_per_year) > tolerance:
        raise RuntimeError(f"H13 ledger mismatch: {ledger.balance_error_m3_per_year}")
    return assembly, hydrology, ledger, plan


def _render_field(path: Path, arr: np.ndarray, title: str, *, unit: str, log: bool = False, assembly=None, network: bool = False):
    rows, cols = arr.shape
    values = np.log10(np.maximum(arr.astype(np.float64), 1.0)) if log else arr
    fig, ax = plt.subplots(figsize=(12, 7))
    image = ax.imshow(
        values, origin="upper",
        extent=(0.0, float(cols), 0.0, float(rows)),
        cmap="viridis", interpolation="nearest",
    )
    bar = fig.colorbar(image, ax=ax, shrink=0.80)
    bar.set_label(("log10 " if log else "") + unit)
    if assembly is not None and "marine_mask" in assembly.field_payloads:
        marine_mask = assembly.field_payloads["marine_mask"].astype(bool)
        masked = np.ma.masked_where(~marine_mask, np.ones_like(marine_mask))
        ax.imshow(masked, origin="upper", extent=(0.0, float(cols), 0.0, float(rows)),
                  cmap="Greys", vmin=0.0, vmax=2.0, alpha=0.45, interpolation="nearest")
        for feature in assembly.data.features.values():
            if getattr(feature, "kind", "") != "marine":
                continue
            boundary = backend_region_set(feature.geometry)._value.boundary
            geoms = getattr(boundary, "geoms", (boundary,))
            for geom in geoms:
                if hasattr(geom, "xy"):
                    ax.plot(*geom.xy, color="white", linewidth=1.2, alpha=0.95)
    if network and assembly is not None:
        for network_id, alpha, width in (("potential_drainage", 0.27, 0.55), ("rivers", 0.9, 1.0)):
            for segment in assembly.data.networks[network_id].segments.values():
                points = segment.centerline
                ax.plot([p.x_km for p in points], [p.y_km for p in points],
                        color="cyan" if network_id == "rivers" else "white", alpha=alpha, lw=width)
    ax.set(xlabel="World x (km)", ylabel="World y (km)", title=title)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _summarize(assembly, hydrology, ledger) -> dict[str, object]:
    data = assembly.field_payloads[FIELD]
    land = (hydrology.marine_mask == 0) if hydrology.marine_mask is not None else np.ones_like(data, dtype=bool)
    return {
        "source_total_m3_per_year": ledger.source_total_m3_per_year,
        "land_edge_terminal_m3_per_year": ledger.land_edge_terminal_m3_per_year,
        "marine_terminal_by_component_m3_per_year": ledger.marine_terminal_by_id_m3_per_year,
        "terminal_total_m3_per_year": ledger.terminal_total_m3_per_year,
        "balance_error_m3_per_year": ledger.balance_error_m3_per_year,
        "relative_balance_error": ledger.balance_error_m3_per_year / max(1.0, ledger.source_total_m3_per_year),
        "raster_land_median_m3_per_year": float(np.median(data[land])),
        "raster_land_max_m3_per_year": float(np.max(data[land])),
        "marine_cells": int(np.count_nonzero(~land)),
        "lake_count": len(hydrology.lake_candidates),
        "regional_segments": len(assembly.data.networks["rivers"].segments),
        "potential_segments": len(assembly.data.networks["potential_drainage"].segments),
        "derived_field_role": assembly.data.fields[FIELD].role.value,
        "derived_field_dtype": assembly.data.fields[FIELD].dtype,
        "derived_field_unit": assembly.data.fields[FIELD].unit,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.output
    root.mkdir(parents=True, exist_ok=True)

    dry, dry_hydro, dry_ledger, _ = _calculate(mean_precip_mm=100.0, marine=False)
    wet, wet_hydro, wet_ledger, _ = _calculate(mean_precip_mm=1800.0, marine=False)
    coast, coast_hydro, coast_ledger, _ = _calculate(mean_precip_mm=900.0, marine=True)
    inland, inland_hydro, inland_ledger, _ = _calculate(mean_precip_mm=900.0, marine=False)

    # The only changed input between inland and coast is the accepted H12 marine recipe.
    for field_id in ("temperature", "annual_precipitation"):
        np.testing.assert_array_equal(inland.field_payloads[field_id], coast.field_payloads[field_id])

    # Exact off/on isolation: the H13 recipe has no upstream feedback.
    no_h13_payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    no_h13_payload["domain_spec"]["surface"]["climate"]["mean_annual_precipitation_mm"] = 900.0
    no_h13_request = GenerationRequest.model_validate(no_h13_payload)
    catalog = load_preset_catalog(A08 / "presets.json")
    without = generate_domain(spec=no_h13_request.domain_spec,
                              config=no_h13_request.generation_config,
                              registry=registry_for_request(no_h13_request, catalog))
    exact_world = all(
        np.array_equal(without.field_payloads[k], inland.field_payloads[k])
        for k in without.field_payloads
    )
    exact_geometry = without.data.features == inland.data.features and without.data.networks == inland.data.networks
    if not (exact_world and exact_geometry):
        raise RuntimeError("H13 off/on changed an accepted world field or topology")

    uniform = accumulate_gross_precipitation_input(
        inland_hydro.continuous_routing,
        np.full_like(inland.field_payloads["annual_precipitation"], 1000.0, dtype=np.float32),
        cell_size_km=1.0, lake_candidates=inland_hydro.lake_candidates,
        lake_outlets=inland_hydro.lake_outlets,
    )
    identity_diff = uniform.gross_upstream_precipitation_m3_per_year - inland_hydro.flow_accumulation_km2 * 1e6
    max_diff = float(np.max(np.abs(identity_diff)))
    if not np.allclose(identity_diff, 0.0, rtol=1e-12, atol=1e-5):
        raise RuntimeError(f"H13 uniform-rain versus area identity failed: {max_diff}")

    _render_field(root / "01-dry-c1-precipitation.png", dry.field_payloads["annual_precipitation"],
                  "Dry inland: accepted C1 annual precipitation", unit="mm/year")
    _render_field(root / "02-dry-gross-input.png", dry.field_payloads[FIELD],
                  "Dry inland: no-loss gross upstream input", unit="m3/year", log=True, assembly=dry, network=True)
    _render_field(root / "03-wet-c1-precipitation.png", wet.field_payloads["annual_precipitation"],
                  "Wet inland: accepted C1 annual precipitation", unit="mm/year")
    _render_field(root / "04-wet-gross-input.png", wet.field_payloads[FIELD],
                  "Wet inland: no-loss gross upstream input", unit="m3/year", log=True, assembly=wet, network=True)
    _render_field(root / "05-accepted-mfd-area.png", inland_hydro.flow_accumulation_km2,
                  "Accepted weighted MFD contributing area", unit="km2", log=True)
    _render_field(root / "06-coastal-gross-input.png", coast.field_payloads[FIELD],
                  "Coastal: gross input + accepted drainage and marine coastline", unit="m3/year",
                  log=True, assembly=coast, network=True)
    _render_field(root / "07-uniform-identity-error.png", identity_diff,
                  "Uniform rainfall: gross input minus accepted MFD area x 1e6", unit="m3/year")

    report = {
        "checkpoint": "H13-A implementation operator review, NOT ACCEPTED",
        "semantics": "mathematically allocated gross annual atmospheric input, not runoff, discharge, recharge, or flow permanence",
        "input": {
            "fixture": "A08 v0.2 deterministic generation",
            "inland_dry_mean_precipitation_mm": 100.0,
            "inland_wet_mean_precipitation_mm": 1800.0,
            "coastal_mean_precipitation_mm": 900.0,
            "marine_sea_level_m": 0.0,
        },
        "dry": _summarize(dry, dry_hydro, dry_ledger),
        "wet": _summarize(wet, wet_hydro, wet_ledger),
        "coastal": _summarize(coast, coast_hydro, coast_ledger),
        "inland_reference": _summarize(inland, inland_hydro, inland_ledger),
        "off_on_upstream_fields_exact": exact_world,
        "off_on_features_and_networks_exact": exact_geometry,
        "uniform_precipitation_versus_accepted_area_max_abs_error_m3_per_year": max_diff,
        "finite_nonnegative_all": all(
            np.isfinite(a.field_payloads[FIELD]).all() and np.all(a.field_payloads[FIELD] >= 0)
            for a in (dry, wet, coast)
        ),
        "gross_precipitation_median_wet_over_dry": (
            float(np.median(wet.field_payloads[FIELD]))
            / max(1.0, float(np.median(dry.field_payloads[FIELD])))
        ),
    }
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (root / "report.json").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
