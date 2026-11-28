from __future__ import annotations

"""Read-only A8/A12 planetary MACRO-grid adapter for non-Earth domain research.

Does not modify Core 0.2, its canonical terrain/rivers, or fictional canon.
The old A8 D8 downstream graph is source metadata, NOT accepted MFD routing.
Private original ZIPs are loaded only from user-supplied local paths.
"""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from math import cos, pi, radians
from pathlib import Path
from zipfile import ZipFile

import numpy as np


class WorldSourceMismatch(ValueError):
    """Archives cannot be safely aligned as the same planetary geometry."""


def _read_member(zip_path: Path, suffix: str, keys: tuple[str, ...]) -> dict[str, np.ndarray]:
    with ZipFile(zip_path) as source:
        matching = [n for n in source.namelist() if n.endswith("/" + suffix)]
        if len(matching) != 1:
            raise WorldSourceMismatch(f"{zip_path.name}: expected exactly one {suffix!r}")
        with np.load(BytesIO(source.read(matching[0])), allow_pickle=False) as arrays:
            absent = set(keys) - set(arrays.files)
            if absent:
                raise WorldSourceMismatch(f"{suffix}: missing fields {sorted(absent)}")
            return {key: np.array(arrays[key], copy=True) for key in keys}


def load_archives(
    a8_zip: Path, a12_zip: Path, a10_zip: Path | None = None,
) -> dict[str, np.ndarray]:
    """Verify exact global geometry, row direction, and optional A10 Q provenance."""
    a8 = _read_member(
        a8_zip, "A8_hydrology.npz",
        ("lat", "lon", "land", "elevation_m", "downstream_index",
         "catchment_area_km2", "river_mask"),
    )
    a12 = _read_member(
        a12_zip, "A12_biome_fields.npz",
        ("lat", "lon", "land", "elevation_m", "temperature_annual_C",
         "precip_planet_year_mm", "biome_base"),
    )
    lat8, lat12, lon8, lon12 = a8["lat"], a12["lat"], a8["lon"], a12["lon"]
    if any(v.ndim != 1 or len(v) < 3 or not np.isfinite(v).all()
           for v in (lat8, lat12, lon8, lon12)):
        raise WorldSourceMismatch("lat/lon must be finite 1D axes with at least 3 points")
    if not (np.all(np.diff(lat8) < 0) and np.all(np.diff(lat12) > 0)
            and np.all(np.diff(lon8) > 0) and np.array_equal(lon8, lon12)
            and np.array_equal(lat8[::-1], lat12)):
        raise WorldSourceMismatch("A8/A12 geographic axes disagree or have wrong orientation")
    shape = (len(lat12), len(lon12))
    if any(a8[k].shape != shape for k in ("land", "elevation_m",
                                        "downstream_index", "catchment_area_km2",
                                        "river_mask")):
        raise WorldSourceMismatch("A8 raster shape/axes mismatch")
    if any(a12[k].shape != shape for k in
           ("land", "elevation_m", "temperature_annual_C",
            "precip_planet_year_mm", "biome_base")):
        raise WorldSourceMismatch("A12 raster shape/axes mismatch")
    if not (np.array_equal(a8["elevation_m"][::-1], a12["elevation_m"])
            and np.array_equal(a8["land"][::-1], a12["land"])):
        raise WorldSourceMismatch(
            "A8/A12 land and elevation must agree EXACTLY after latitude reversal"
        )
    for key in ("elevation_m", "catchment_area_km2"):
        if not np.isfinite(a8[key]).all():
            raise WorldSourceMismatch(f"nonfinite source {key}")
    if not np.isfinite(a12["precip_planet_year_mm"]).all():
        raise WorldSourceMismatch("nonfinite planetary-year source precipitation")
    downstream = a8["downstream_index"]
    if not np.issubdtype(downstream.dtype, np.integer):
        raise WorldSourceMismatch("A8 downstream_index must be an integer flat grid index")
    if bool(np.any(downstream < -1)) or bool(np.any(downstream >= downstream.size)):
        raise WorldSourceMismatch("A8 downstream_index points outside original global grid")
    out = {"a8_" + k: v for k, v in a8.items()}
    out.update({"a12_" + k: v for k, v in a12.items()})
    if a10_zip is not None:
        a10 = _read_member(
            a10_zip, "A10_water_balance.npz",
            ("lat", "lon", "land", "annual_Q_m3s"),
        )
        if not (np.array_equal(a10["lat"], lat12)
                and np.array_equal(a10["lon"], lon12)
                and np.array_equal(a10["land"], a12["land"])):
            raise WorldSourceMismatch("A10 Q grid differs from A12 grid")
        if not np.isfinite(a10["annual_Q_m3s"]).all():
            raise WorldSourceMismatch("nonfinite model Q values")
        out["a10_Q_m3s"] = a10["annual_Q_m3s"]
    return out


def region_crop(
    data: dict[str, np.ndarray], *,
    center_lat_deg: float, center_lon_deg: float,
    half_width_km: float, half_height_km: float, planet_radius_km: float,
    planetary_year_earth_days: float,
) -> tuple[dict[str, np.ndarray], dict]:
    """Coarse macro-region, north-first rows; preserve whole-global D8 references.

    This does NOT downscale A8/A12 or produce a canonical 1-km DomainData.
    """
    values = (center_lat_deg, center_lon_deg, half_width_km, half_height_km,
              planet_radius_km, planetary_year_earth_days)
    if not all(np.isfinite(v) for v in values):
        raise ValueError("all geographic inputs must be finite")
    if abs(center_lat_deg) >= 85 or not -180 <= center_lon_deg <= 180:
        raise ValueError("local longitude/latitude planar approximation excludes poles")
    if any(v <= 0 for v in (half_width_km, half_height_km,
                            planet_radius_km, planetary_year_earth_days)):
        raise ValueError("lengths, radius and planetary calendar must be positive")
    lat_ascending = data["a12_lat"]
    lon = data["a12_lon"]
    lat_delta = half_height_km * 180 / (pi * planet_radius_km)
    lon_delta = half_width_km * 180 / (pi * planet_radius_km *
                                       cos(radians(center_lat_deg)))
    r12 = np.flatnonzero((lat_ascending >= center_lat_deg - lat_delta)
                         & (lat_ascending <= center_lat_deg + lat_delta))
    cc = np.flatnonzero((lon >= center_lon_deg - lon_delta)
                        & (lon <= center_lon_deg + lon_delta))
    if r12.size < 3 or cc.size < 3:
        raise WorldSourceMismatch("region contains fewer than 3x3 global source cells")
    nrows, ncols = data["a8_land"].shape
    rs = nrows - 1 - int(r12[-1])
    re = nrows - int(r12[0])
    cs, ce = int(cc[0]), int(cc[-1]) + 1
    rr = re - rs
    columns = ce - cs
    a8slice = np.s_[rs:re, cs:ce]
    a12slice = np.s_[int(r12[0]):int(r12[-1]) + 1, cs:ce]
    result = {
        "latitude_deg_north_first": lat_ascending[r12][::-1].copy(),
        "longitude_deg_west_to_east": lon[cc].copy(),
        "elevation_m": data["a8_elevation_m"][a8slice].copy(),
        "land_mask": data["a8_land"][a8slice].copy(),
        "source_river_mask_D8": data["a8_river_mask"][a8slice].copy(),
        "source_catchment_km2_D8": data["a8_catchment_area_km2"][a8slice].copy(),
        "source_temperature_annual_C":
            data["a12_temperature_annual_C"][a12slice][::-1].copy(),
        "source_precip_mm_per_planetary_year":
            data["a12_precip_planet_year_mm"][a12slice][::-1].copy(),
        "source_ecoclimate_code_MODEL":
            data["a12_biome_base"][a12slice][::-1].copy(),
    }
    if "a10_Q_m3s" in data:
        result["source_A10_model_annual_Q_m3s"] = (
            data["a10_Q_m3s"][a12slice][::-1].copy()
        )
    if not (np.array_equal(result["elevation_m"],
                            data["a12_elevation_m"][a12slice][::-1])
            and np.array_equal(result["land_mask"],
                               data["a12_land"][a12slice][::-1])):
        raise WorldSourceMismatch("cropped geographic source field identity failed")

    # A8 downstream_index is a GLOBAL north-first 1-D flat index. Remap
    # receiver into local cropped coordinates; out-of-crop edges remain
    # annotated, not silently turned into physical river sinks.
    full = data["a8_downstream_index"][a8slice].astype(np.int64, copy=True)
    valid = full >= 0
    global_target_row = np.where(valid, full // ncols, -1)
    global_target_col = np.where(valid, full % ncols, -1)
    inside = (valid & (global_target_row >= rs) & (global_target_row < re)
              & (global_target_col >= cs) & (global_target_col < ce))
    local = np.full((rr, columns), -1, dtype=np.int64)
    local[inside] = ((global_target_row[inside] - rs) * columns
                     + (global_target_col[inside] - cs))
    exits = valid & ~inside
    result["source_global_downstream_index"] = full
    result["local_downstream_index"] = local
    result["source_downstream_exits_region"] = exits.astype(np.uint8)

    km_per_degree_lat = pi * planet_radius_km / 180
    km_per_degree_lon = km_per_degree_lat * cos(radians(center_lat_deg))
    result["x_km_from_center"] = (
        result["longitude_deg_west_to_east"] - center_lon_deg
    ) * km_per_degree_lon
    result["y_km_from_center_north_first"] = (
        result["latitude_deg_north_first"] - center_lat_deg
    ) * km_per_degree_lat
    manifest = {
        "status": "PRIVATE_SOURCE_DERIVED_WORKING_MODEL_NOT_CANON",
        "is_DomainData": False,
        "is_newly_generated_geography": False,
        "input_raster_orientation": "A8 north-first; A12/A10 south-first",
        "output_raster_orientation": "north-first; x east; y north",
        "original_planet_shape": [nrows, ncols],
        "region_shape": [rr, columns],
        "center_degrees": [center_lat_deg, center_lon_deg],
        "source_crop_bounds": {"a8_row_start": rs, "a8_row_stop": re,
                               "column_start": cs, "column_stop": ce},
        "planet_radius_km": planet_radius_km,
        "planetary_year_earth_days": planetary_year_earth_days,
        "source_precip_unit": "mm per planetary year",
        "source_A10_Q_unit": "m3/s from old bucket model, not Core discharge",
        "global_D8_receiver_index_preserved": True,
        "local_D8_exits_region_count": int(np.count_nonzero(exits)),
        "local_D8_links_inside_count": int(np.count_nonzero(inside)),
        "limitations": [
            "Local planar offsets are approximate and should not span a pole or dateline.",
            "A8 D8 graph is research source, NOT Core 0.2 accepted MFD routing.",
            "Cropped graph exits are external connections, NOT validated physical sinks.",
            "0.3-degree source raster cannot locate roads, waterfalls or buildings.",
            "Image and model-class labels are NOT canon and NOT botanical proof.",
            "This macro source does not implement Core terrain injection or downscaling.",
        ],
    }
    return result, manifest


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        from hashlib import file_digest
        return file_digest(stream, "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a8", type=Path, required=True)
    parser.add_argument("--a12", type=Path, required=True)
    parser.add_argument("--a10", type=Path, default=None)
    parser.add_argument("--expected-a8-sha256", default=None)
    parser.add_argument("--expected-a12-sha256", default=None)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--half-width-km", type=float, required=True)
    parser.add_argument("--half-height-km", type=float, required=True)
    parser.add_argument("--planet-radius-km", type=float, required=True)
    parser.add_argument("--planet-year-earth-days", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    paths = {"A8": args.a8, "A12": args.a12}
    if args.a10 is not None:
        paths["A10"] = args.a10
    digests = {name: _sha256(path) for name, path in paths.items()}
    for name, expected in (
        ("A8", args.expected_a8_sha256), ("A12", args.expected_a12_sha256)
    ):
        if expected and digests[name] != expected.lower():
            raise WorldSourceMismatch(f"{name} archive SHA mismatch")
    sources = load_archives(args.a8, args.a12, args.a10)
    arrays, report = region_crop(
        sources, center_lat_deg=args.lat, center_lon_deg=args.lon,
        half_width_km=args.half_width_km, half_height_km=args.half_height_km,
        planet_radius_km=args.planet_radius_km,
        planetary_year_earth_days=args.planet_year_earth_days,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output / "macro-region-source.npz", **arrays)
    report["source_sha256"] = digests

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    fig, axes = plt.subplots(1, 3, figsize=(16, 6), layout="constrained")
    x, y = arrays["x_km_from_center"], arrays["y_km_from_center_north_first"]
    X0, X1 = float(x[0]), float(x[-1])
    Y0, Y1 = float(y[-1]), float(y[0])
    extent = [X0, X1, Y0, Y1]
    sea = ~arrays["land_mask"].astype(bool)
    images = (
        (np.ma.masked_where(sea, arrays["elevation_m"]), "terrain",
         "Source terrain (m)"),
        (np.ma.masked_where(sea, np.log10(np.maximum(
            arrays["source_catchment_km2_D8"], 1))), "YlGnBu",
         "A8 D8 contributing area, log10 km2"),
        (np.ma.masked_where(sea, arrays["source_ecoclimate_code_MODEL"]),
         "tab20", "A12 model eco-climate codes (not literal biomes)"),
    )
    for ax, (arr, color, title) in zip(axes, images):
        img = ax.imshow(arr, extent=extent, origin="upper",
                        interpolation="nearest", cmap=color)
        ax.set(title=title, xlabel="east km", ylabel="north km")
        ax.grid(alpha=0.15)
        fig.colorbar(img, ax=ax, shrink=0.65)
    fig.suptitle("Original planetary SOURCE: aligned A8/A12 macro-region; NOT local terrain")
    fig.savefig(args.output / "macro-region-preview.png", dpi=140)
    plt.close(fig)
    report["outputs"] = ["macro-region-source.npz", "macro-region-preview.png",
                         "manifest.json"]
    serialized = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    (args.output / "manifest.json").write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
