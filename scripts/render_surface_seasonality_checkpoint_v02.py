from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

from domain_generator.application import (
    generate_domain,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.contracts import GenerationRequest


SEASONALITY = {
    "temperature_seasonal_amplitude_c": 7.0,
    "temperature_peak_month": 7,
    "precipitation_seasonality_log_amplitude": 1.0,
    "precipitation_peak_month": 1,
}


def _seasonal_request(request: GenerationRequest) -> GenerationRequest:
    payload = request.model_dump(mode="python", by_alias=True, exclude_none=False)
    payload["domain_spec"]["surface"]["climate"]["seasonality"] = dict(SEASONALITY)
    return GenerationRequest.model_validate(payload)


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
    fig, ax = plt.subplots(figsize=(14.0, 9.5), dpi=160)
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


def _monthly_stack(assembly, prefix: str) -> np.ndarray:
    return np.stack(
        [
            np.asarray(
                assembly.field_payloads[f"{prefix}_{month:02d}"],
                dtype=np.float64,
            )
            for month in range(1, 13)
        ],
        axis=0,
    )


def _save_temperature_curves(
    path: Path,
    monthly: np.ndarray,
    elevation: np.ndarray,
) -> list[dict[str, object]]:
    flat = elevation.reshape(-1)
    indices = [
        int(np.argmin(flat)),
        int(np.argsort(flat)[len(flat) // 2]),
        int(np.argmax(flat)),
    ]
    labels = ("low elevation", "median elevation", "high elevation")
    rows, columns = elevation.shape
    months = np.arange(1, 13)

    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=160)
    report = []
    for label, flat_index in zip(labels, indices, strict=True):
        row, column = divmod(flat_index, columns)
        values = monthly[:, row, column]
        ax.plot(months, values, marker="o", label=label)
        report.append(
            {
                "label": label,
                "row": row,
                "column": column,
                "elevation_m": float(elevation[row, column]),
                "monthly_temperature_c": [float(value) for value in values],
            }
        )
    ax.set_xticks(months)
    ax.set_xlabel("climatological month")
    ax.set_ylabel("monthly mean temperature, °C")
    ax.set_title("C4-A — Monthly temperature at representative terrain cells")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return report


def _save_precipitation_fraction_curve(path: Path, monthly: np.ndarray, annual: np.ndarray) -> list[float]:
    fractions = np.mean(
        monthly / annual[np.newaxis, :, :],
        axis=(1, 2),
        dtype=np.float64,
    )
    months = np.arange(1, 13)
    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=160)
    ax.plot(months, fractions, marker="o")
    ax.set_xticks(months)
    ax.set_xlabel("climatological month")
    ax.set_ylabel("fraction of annual precipitation")
    ax.set_title("C4-A — Regional monthly precipitation fractions")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return [float(value) for value in fractions]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    parser.add_argument("presets", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    annual_request = load_generation_request(args.request)
    seasonal_request = _seasonal_request(annual_request)
    catalog = load_preset_catalog(args.presets)

    annual = generate_domain(
        spec=annual_request.domain_spec,
        config=annual_request.generation_config,
        registry=registry_for_request(annual_request, catalog),
    )
    seasonal = generate_domain(
        spec=seasonal_request.domain_spec,
        config=seasonal_request.generation_config,
        registry=registry_for_request(seasonal_request, catalog),
    )

    canonical = (
        "elevation",
        "water_depth",
        "moisture",
        "vegetation_density",
        "temperature",
        "annual_precipitation",
    )
    unchanged = {}
    for field_id in canonical:
        same = np.array_equal(
            annual.field_payloads[field_id],
            seasonal.field_payloads[field_id],
        )
        unchanged[field_id] = bool(same)
        if not same:
            raise RuntimeError(f"C4-A changed accepted canonical field {field_id!r}")

    if annual.data.features != seasonal.data.features:
        raise RuntimeError("C4-A changed accepted feature geometry")
    if annual.data.networks != seasonal.data.networks:
        raise RuntimeError("C4-A changed accepted network geometry")

    monthly_temperature = _monthly_stack(seasonal, "temperature_month")
    monthly_precipitation = _monthly_stack(seasonal, "precipitation_month")
    annual_temperature = np.asarray(
        seasonal.field_payloads["temperature"], dtype=np.float64
    )
    annual_precipitation = np.asarray(
        seasonal.field_payloads["annual_precipitation"], dtype=np.float64
    )
    elevation = np.asarray(seasonal.field_payloads["elevation"], dtype=np.float64)

    temperature_error = np.mean(
        monthly_temperature,
        axis=0,
        dtype=np.float64,
    ) - annual_temperature
    precipitation_error = np.sum(
        monthly_precipitation,
        axis=0,
        dtype=np.float64,
    ) - annual_precipitation

    args.output.mkdir(parents=True, exist_ok=True)
    width_km = float(seasonal.data.domain.width_km)
    height_km = float(seasonal.data.domain.height_km)
    cell_size_km = float(seasonal.data.grid.cell_size_km)

    _save_field(
        args.output / "01-annual-temperature.png",
        elevation=elevation,
        field=annual_temperature,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C4-A — Accepted annual mean temperature",
        label="°C",
        cmap="coolwarm",
    )
    _save_field(
        args.output / "02-warmest-month-07.png",
        elevation=elevation,
        field=monthly_temperature[6],
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C4-A — Month 07 temperature (configured warm peak)",
        label="°C",
        cmap="coolwarm",
    )
    _save_field(
        args.output / "03-coldest-month-01.png",
        elevation=elevation,
        field=monthly_temperature[0],
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C4-A — Month 01 temperature (opposite trough)",
        label="°C",
        cmap="coolwarm",
    )
    _save_field(
        args.output / "04-annual-precipitation.png",
        elevation=elevation,
        field=annual_precipitation,
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C4-A — Accepted annual precipitation",
        label="mm/year",
        cmap="Blues",
    )
    _save_field(
        args.output / "05-wettest-month-01.png",
        elevation=elevation,
        field=monthly_precipitation[0],
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C4-A — Month 01 precipitation (configured wet peak)",
        label="mm/month",
        cmap="Blues",
    )
    _save_field(
        args.output / "06-driest-month-07.png",
        elevation=elevation,
        field=monthly_precipitation[6],
        width_km=width_km,
        height_km=height_km,
        cell_size_km=cell_size_km,
        title="C4-A — Month 07 precipitation (opposite dry trough)",
        label="mm/month",
        cmap="Blues",
    )

    cell_curves = _save_temperature_curves(
        args.output / "07-temperature-curves.png",
        monthly_temperature,
        elevation,
    )
    precipitation_fractions = _save_precipitation_fraction_curve(
        args.output / "08-precipitation-fractions.png",
        monthly_precipitation,
        annual_precipitation,
    )

    monthly_descriptors = {
        name: descriptor.model_dump(mode="json", by_alias=True, exclude_none=False)
        for name, descriptor in seasonal.data.fields.items()
        if name.startswith("temperature_month_")
        or name.startswith("precipitation_month_")
    }

    report = {
        "checkpoint": "C4-A",
        "seasonality": SEASONALITY,
        "canonical_fields_unchanged": unchanged,
        "features_unchanged": annual.data.features == seasonal.data.features,
        "networks_unchanged": annual.data.networks == seasonal.data.networks,
        "temperature_conservation": {
            "max_abs_error_c": float(np.max(np.abs(temperature_error))),
            "mean_abs_error_c": float(np.mean(np.abs(temperature_error))),
        },
        "precipitation_conservation": {
            "max_abs_error_mm": float(np.max(np.abs(precipitation_error))),
            "mean_abs_error_mm": float(np.mean(np.abs(precipitation_error))),
        },
        "temperature": {
            "annual_min_c": float(np.min(annual_temperature)),
            "annual_max_c": float(np.max(annual_temperature)),
            "month_07_min_c": float(np.min(monthly_temperature[6])),
            "month_07_max_c": float(np.max(monthly_temperature[6])),
            "month_01_min_c": float(np.min(monthly_temperature[0])),
            "month_01_max_c": float(np.max(monthly_temperature[0])),
        },
        "precipitation": {
            "annual_min_mm": float(np.min(annual_precipitation)),
            "annual_max_mm": float(np.max(annual_precipitation)),
            "month_01_min_mm": float(np.min(monthly_precipitation[0])),
            "month_01_max_mm": float(np.max(monthly_precipitation[0])),
            "month_07_min_mm": float(np.min(monthly_precipitation[6])),
            "month_07_max_mm": float(np.max(monthly_precipitation[6])),
            "monthly_fractions": precipitation_fractions,
        },
        "representative_temperature_cells": cell_curves,
        "monthly_descriptor_count": len(monthly_descriptors),
        "monthly_descriptors": monthly_descriptors,
    }

    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
