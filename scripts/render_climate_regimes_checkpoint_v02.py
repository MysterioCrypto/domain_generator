from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
import numpy as np

from domain_generator.application import (
    generate_domain,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.contracts import GenerationRequest
from domain_generator.surface import (
    KOPPEN_GEIGER_CODE_TO_LABEL,
    KOPPEN_GEIGER_SCHEME_ID,
)


SEASONALITY = {
    "temperature_seasonal_amplitude_c": 7.0,
    "temperature_peak_month": 7,
    "precipitation_seasonality_log_amplitude": 1.0,
    "precipitation_peak_month": 1,
}


def _request(base: GenerationRequest, *, classification: bool) -> GenerationRequest:
    payload = base.model_dump(mode="python", by_alias=True, exclude_none=False)
    climate = payload["domain_spec"]["surface"]["climate"]
    climate["seasonality"] = dict(SEASONALITY)
    climate["classification"] = (
        {"scheme": KOPPEN_GEIGER_SCHEME_ID}
        if classification
        else None
    )
    return GenerationRequest.model_validate(payload)


def _hillshade(elevation_m: np.ndarray, cell_size_km: float) -> np.ndarray:
    elevation = np.asarray(elevation_m, dtype=np.float64)
    gy, gx = np.gradient(elevation, cell_size_km * 1000.0)
    slope = np.pi / 2.0 - np.arctan(np.sqrt(gx * gx + gy * gy))
    aspect = np.arctan2(-gx, gy)
    azimuth = np.deg2rad(315.0)
    altitude = np.deg2rad(45.0)
    shade = (
        np.sin(altitude) * np.sin(slope)
        + np.cos(altitude) * np.cos(slope) * np.cos(azimuth - aspect)
    )
    return np.clip((shade + 1.0) / 2.0, 0.0, 1.0)


def _class_cmap() -> tuple[ListedColormap, BoundaryNorm]:
    base = plt.get_cmap("turbo")
    colors = base(np.linspace(0.02, 0.98, 30))
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(0.5, 31.5, 1.0), cmap.N)
    return cmap, norm


def _legend_handles(used_codes: list[int], cmap: ListedColormap) -> list[Patch]:
    return [
        Patch(
            facecolor=cmap((code - 1) / 29.0),
            label=f"{code:02d} {KOPPEN_GEIGER_CODE_TO_LABEL[code]}",
        )
        for code in used_codes
    ]


def _save_class_map(
    path: Path,
    field: np.ndarray,
    *,
    width_km: float,
    height_km: float,
    elevation: np.ndarray | None,
    cell_size_km: float,
    title: str,
) -> None:
    cmap, norm = _class_cmap()
    used_codes = sorted(int(value) for value in np.unique(field))
    fig, ax = plt.subplots(figsize=(15.5, 10.0), dpi=160)
    if elevation is not None:
        ax.imshow(
            np.flipud(_hillshade(elevation, cell_size_km)),
            origin="lower",
            extent=(0.0, width_km, 0.0, height_km),
            cmap="gray",
            interpolation="bilinear",
            aspect="equal",
            alpha=0.48,
        )
        alpha = 0.72
    else:
        alpha = 1.0
    ax.imshow(
        np.flipud(field),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        aspect="equal",
        alpha=alpha,
    )
    ax.set_title(title)
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    handles = _legend_handles(used_codes, cmap)
    if handles:
        ax.legend(
            handles=handles,
            loc="upper left",
            bbox_to_anchor=(1.01, 1.0),
            fontsize=8,
            ncol=1,
            borderaxespad=0.0,
            frameon=False,
        )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _save_continuous(
    path: Path,
    field: np.ndarray,
    *,
    width_km: float,
    height_km: float,
    title: str,
    label: str,
    cmap: str,
) -> None:
    fig, ax = plt.subplots(figsize=(14.0, 9.0), dpi=150)
    image = ax.imshow(
        np.flipud(np.asarray(field, dtype=np.float64)),
        origin="lower",
        extent=(0.0, width_km, 0.0, height_km),
        cmap=cmap,
        interpolation="bilinear",
        aspect="equal",
    )
    bar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    bar.set_label(label)
    ax.set_title(title)
    ax.set_xlabel("km east")
    ax.set_ylabel("km north")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _save_histogram(
    path: Path,
    codes: np.ndarray,
    *,
    cell_area_km2: float,
) -> dict[str, dict[str, float | int]]:
    counts = {
        int(code): int(count)
        for code, count in zip(*np.unique(codes, return_counts=True), strict=True)
    }
    total = int(codes.size)
    used = sorted(counts)
    labels = [KOPPEN_GEIGER_CODE_TO_LABEL[code] for code in used]
    values = [counts[code] * cell_area_km2 for code in used]

    fig, ax = plt.subplots(figsize=(12.0, 6.0), dpi=150)
    ax.bar(labels, values)
    ax.set_ylabel("area, km²")
    ax.set_xlabel("Köppen–Geiger local-season class")
    ax.set_title("C5-A — Climate-regime area by class")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)

    return {
        KOPPEN_GEIGER_CODE_TO_LABEL[code]: {
            "code": code,
            "cells": counts[code],
            "area_km2": counts[code] * cell_area_km2,
            "fraction": counts[code] / total,
        }
        for code in used
    }


def _boundary_samples(
    codes: np.ndarray,
    *,
    temperature: np.ndarray,
    precipitation: np.ndarray,
    vegetation: np.ndarray,
    monthly_temperature: np.ndarray,
    monthly_precipitation: np.ndarray,
    max_samples: int = 16,
) -> list[dict[str, object]]:
    rows, columns = codes.shape
    samples: list[dict[str, object]] = []
    seen_pairs: set[tuple[int, int]] = set()

    for row in range(rows):
        for column in range(columns):
            for dr, dc in ((0, 1), (1, 0)):
                other_row = row + dr
                other_column = column + dc
                if other_row >= rows or other_column >= columns:
                    continue
                first = int(codes[row, column])
                second = int(codes[other_row, other_column])
                if first == second:
                    continue
                pair = tuple(sorted((first, second)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                def cell_payload(r: int, c: int) -> dict[str, object]:
                    return {
                        "row": r,
                        "column": c,
                        "class_code": int(codes[r, c]),
                        "class_label": KOPPEN_GEIGER_CODE_TO_LABEL[int(codes[r, c])],
                        "annual_temperature_c": float(temperature[r, c]),
                        "annual_precipitation_mm": float(precipitation[r, c]),
                        "vegetation_density": float(vegetation[r, c]),
                        "monthly_temperature_c": [
                            float(value) for value in monthly_temperature[:, r, c]
                        ],
                        "monthly_precipitation_mm": [
                            float(value) for value in monthly_precipitation[:, r, c]
                        ],
                    }

                samples.append(
                    {
                        "class_pair": [
                            KOPPEN_GEIGER_CODE_TO_LABEL[pair[0]],
                            KOPPEN_GEIGER_CODE_TO_LABEL[pair[1]],
                        ],
                        "a": cell_payload(row, column),
                        "b": cell_payload(other_row, other_column),
                    }
                )
                if len(samples) >= max_samples:
                    return samples
    return samples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    parser.add_argument("presets", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    base = load_generation_request(args.request)
    catalog = load_preset_catalog(args.presets)

    c4_request = _request(base, classification=False)
    c5_request = _request(base, classification=True)

    c4 = generate_domain(
        spec=c4_request.domain_spec,
        config=c4_request.generation_config,
        registry=registry_for_request(c4_request, catalog),
    )
    c5 = generate_domain(
        spec=c5_request.domain_spec,
        config=c5_request.generation_config,
        registry=registry_for_request(c5_request, catalog),
    )

    for field_id, payload in c4.field_payloads.items():
        if field_id not in c5.field_payloads:
            raise RuntimeError(f"C5 removed C4 field {field_id!r}")
        if not np.array_equal(payload, c5.field_payloads[field_id]):
            raise RuntimeError(f"C5 changed upstream field {field_id!r}")
    if c4.data.features != c5.data.features:
        raise RuntimeError("C5 changed features")
    if c4.data.networks != c5.data.networks:
        raise RuntimeError("C5 changed networks")

    codes = np.asarray(
        c5.field_payloads["climate_regime_koppen_geiger"],
        dtype=np.uint8,
    )
    if np.any((codes < 1) | (codes > 30)):
        raise RuntimeError("C5 produced invalid climate-regime code")

    temperature = np.asarray(c5.field_payloads["temperature"], dtype=np.float64)
    precipitation = np.asarray(
        c5.field_payloads["annual_precipitation"], dtype=np.float64
    )
    vegetation = np.asarray(
        c5.field_payloads["vegetation_density"], dtype=np.float64
    )
    elevation = np.asarray(c5.field_payloads["elevation"], dtype=np.float64)
    monthly_temperature = np.stack(
        [
            np.asarray(
                c5.field_payloads[f"temperature_month_{month:02d}"],
                dtype=np.float64,
            )
            for month in range(1, 13)
        ]
    )
    monthly_precipitation = np.stack(
        [
            np.asarray(
                c5.field_payloads[f"precipitation_month_{month:02d}"],
                dtype=np.float64,
            )
            for month in range(1, 13)
        ]
    )

    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    width_km = float(c5.data.domain.width_km)
    height_km = float(c5.data.domain.height_km)
    cell_size_km = float(c5.data.grid.cell_size_km)

    _save_class_map(
        output / "01-climate-regimes.png",
        codes,
        width_km=width_km,
        height_km=height_km,
        elevation=None,
        cell_size_km=cell_size_km,
        title="C5-A — Köppen–Geiger local-season climate regimes",
    )
    _save_class_map(
        output / "02-climate-regimes-hillshade.png",
        codes,
        width_km=width_km,
        height_km=height_km,
        elevation=elevation,
        cell_size_km=cell_size_km,
        title="C5-A — Climate regimes over terrain hillshade",
    )
    _save_continuous(
        output / "03-annual-temperature.png",
        temperature,
        width_km=width_km,
        height_km=height_km,
        title="C5-A context — annual mean temperature",
        label="°C",
        cmap="coolwarm",
    )
    _save_continuous(
        output / "04-annual-precipitation.png",
        precipitation,
        width_km=width_km,
        height_km=height_km,
        title="C5-A context — annual precipitation",
        label="mm/year",
        cmap="Blues",
    )
    _save_continuous(
        output / "05-vegetation-density.png",
        vegetation,
        width_km=width_km,
        height_km=height_km,
        title="C5-A comparison — accepted C3 vegetation potential",
        label="normalized",
        cmap="YlGn",
    )
    _save_continuous(
        output / "06-warmest-month-temperature.png",
        np.max(monthly_temperature, axis=0),
        width_km=width_km,
        height_km=height_km,
        title="C5-A context — hottest monthly mean temperature",
        label="°C",
        cmap="coolwarm",
    )
    _save_continuous(
        output / "07-driest-month-precipitation.png",
        np.min(monthly_precipitation, axis=0),
        width_km=width_km,
        height_km=height_km,
        title="C5-A context — driest monthly precipitation",
        label="mm/month",
        cmap="Blues",
    )

    class_summary = _save_histogram(
        output / "08-class-area-histogram.png",
        codes,
        cell_area_km2=cell_size_km * cell_size_km,
    )
    transitions = _boundary_samples(
        codes,
        temperature=temperature,
        precipitation=precipitation,
        vegetation=vegetation,
        monthly_temperature=monthly_temperature,
        monthly_precipitation=monthly_precipitation,
    )

    descriptor = c5.data.fields["climate_regime_koppen_geiger"]
    report = {
        "checkpoint": "C5-A",
        "scheme": KOPPEN_GEIGER_SCHEME_ID,
        "seasonality": SEASONALITY,
        "upstream_c4_fields_exact_equal": True,
        "features_exact_equal": True,
        "networks_exact_equal": True,
        "field_contract": descriptor.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=False,
        ),
        "used_codes": sorted(int(value) for value in np.unique(codes)),
        "used_labels": [
            KOPPEN_GEIGER_CODE_TO_LABEL[int(value)]
            for value in sorted(np.unique(codes))
        ],
        "class_summary": class_summary,
        "boundary_samples": transitions,
        "temperature": {
            "annual_min_c": float(np.min(temperature)),
            "annual_max_c": float(np.max(temperature)),
            "hottest_month_min_c": float(np.min(np.max(monthly_temperature, axis=0))),
            "hottest_month_max_c": float(np.max(np.max(monthly_temperature, axis=0))),
            "coldest_month_min_c": float(np.min(np.min(monthly_temperature, axis=0))),
            "coldest_month_max_c": float(np.max(np.min(monthly_temperature, axis=0))),
        },
        "precipitation": {
            "annual_min_mm": float(np.min(precipitation)),
            "annual_max_mm": float(np.max(precipitation)),
            "driest_month_min_mm": float(np.min(np.min(monthly_precipitation, axis=0))),
            "driest_month_max_mm": float(np.max(np.min(monthly_precipitation, axis=0))),
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
