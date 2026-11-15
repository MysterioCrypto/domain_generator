from __future__ import annotations

"""Generate NEW 1-km child-scale relief, conditioned on a private planetary macro DEM.

Read-only external adapter. The output is not geological measurements, author
canon, or accepted Core 0.2 DomainData. No child MFD network exists yet.
"""

import argparse
from dataclasses import dataclass
import json
from math import cos, pi, radians
from pathlib import Path

import numpy as np


class ChildTerrainError(ValueError):
    pass


@dataclass(frozen=True)
class ChildTerrainSettings:
    center_lat_deg: float
    center_lon_deg: float
    half_width_km: float
    half_height_km: float
    planet_radius_km: float
    planetary_year_earth_days: float
    spacing_km: float = 1.0
    seed: int = 1406
    relief_strength: float = 1.0


def _hash_grid(ix: np.ndarray, iy: np.ndarray, seed: int) -> np.ndarray:
    """A deterministic 2-D uint64 hash; consistent across regional crop edges."""
    x = np.asarray(ix, dtype=np.int64).view(np.uint64)
    y = np.asarray(iy, dtype=np.int64).view(np.uint64)
    z = (x * np.uint64(0x9E3779B185EBCA87)
         ^ y * np.uint64(0xC2B2AE3D27D4EB4F)
         ^ np.uint64(seed % (1 << 64)))
    z ^= z >> np.uint64(30)
    z *= np.uint64(0xBF58476D1CE4E5B9)
    z ^= z >> np.uint64(27)
    z *= np.uint64(0x94D049BB133111EB)
    z ^= z >> np.uint64(31)
    return ((z >> np.uint64(11)).astype(np.float64) / (1 << 53)) * 2 - 1


def _smooth_value_noise(x_km: np.ndarray, y_km: np.ndarray,
                        scale_km: float, seed: int) -> np.ndarray:
    fx, fy = np.broadcast_arrays(np.asarray(x_km, dtype=np.float64) / scale_km,
                                 np.asarray(y_km, dtype=np.float64) / scale_km)
    ix, iy = np.floor(fx).astype(np.int64), np.floor(fy).astype(np.int64)
    u, v = fx - ix, fy - iy
    u = u * u * u * (u * (6 * u - 15) + 10)
    v = v * v * v * (v * (6 * v - 15) + 10)
    a, b = _hash_grid(ix, iy, seed), _hash_grid(ix + 1, iy, seed)
    c, d = _hash_grid(ix, iy + 1, seed), _hash_grid(ix + 1, iy + 1, seed)
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v


def _detail_noise(lon: np.ndarray, lat: np.ndarray,
                  planet_radius_km: float, seed: int) -> np.ndarray:
    """Global-position-anchored detail: not seeded independently per crop."""
    lon, lat = np.broadcast_arrays(np.asarray(lon, dtype=np.float64),
                                   np.asarray(lat, dtype=np.float64))
    east = planet_radius_km * np.deg2rad(lon) * np.cos(np.deg2rad(lat))
    north = planet_radius_km * np.deg2rad(lat)
    result = np.zeros_like(east, dtype=np.float64)
    for scale, weight, salt in ((48., .42, 0), (18., .32, 1),
                                (7., .18, 2), (3., .08, 3)):
        result += weight * _smooth_value_noise(
            east, north, scale, seed + 1234567 * salt
        )
    return result


def _bilinear(x: np.ndarray, y: np.ndarray, source_x: np.ndarray,
              source_y: np.ndarray, field: np.ndarray) -> np.ndarray:
    """Interpolate strictly within center-to-center ascending source axes."""
    x, y = np.broadcast_arrays(np.asarray(x, dtype=np.float64),
                               np.asarray(y, dtype=np.float64))
    sx = np.asarray(source_x, dtype=np.float64)
    sy = np.asarray(source_y, dtype=np.float64)
    if field.shape != (len(sy), len(sx)) or not (
        np.all(np.diff(sx) > 0) and np.all(np.diff(sy) > 0)
    ):
        raise ChildTerrainError("invalid ascending source grid")
    if (np.any(x < sx[0] - 1e-8) or np.any(x > sx[-1] + 1e-8)
            or np.any(y < sy[0] - 1e-8) or np.any(y > sy[-1] + 1e-8)):
        raise ChildTerrainError(
            "child extends beyond source station CENTERS; increase macro crop"
        )
    ii = np.clip(np.searchsorted(sx, x, side="right") - 1, 0, len(sx) - 2)
    jj = np.clip(np.searchsorted(sy, y, side="right") - 1, 0, len(sy) - 2)
    u = np.clip((x - sx[ii]) / (sx[ii + 1] - sx[ii]), 0, 1)
    v = np.clip((y - sy[jj]) / (sy[jj + 1] - sy[jj]), 0, 1)
    return ((1 - v) * ((1 - u) * field[jj, ii] + u * field[jj, ii + 1])
            + v * ((1 - u) * field[jj + 1, ii] + u * field[jj + 1, ii + 1]))


def _source_fields(macro: dict[str, np.ndarray]):
    lat = np.asarray(macro["latitude_deg_north_first"], dtype=np.float64)
    lon = np.asarray(macro["longitude_deg_west_to_east"], dtype=np.float64)
    dem = np.asarray(macro["elevation_m"], dtype=np.float64)
    land = np.asarray(macro["land_mask"], dtype=np.uint8)
    if lat.ndim != 1 or lon.ndim != 1 or min(len(lat), len(lon)) < 3:
        raise ChildTerrainError("macro requires 3 or more source centers per axis")
    if not np.all(np.diff(lat) < 0) or not np.all(np.diff(lon) > 0):
        raise ChildTerrainError("expected north-first rows and west-east columns")
    if (dem.shape != (len(lat), len(lon)) or land.shape != dem.shape
            or not np.isfinite(dem).all()):
        raise ChildTerrainError("macro arrays incompatible/nonfinite height")
    return lat[::-1], lon, dem[::-1], land[::-1]


def _validate_settings(s: ChildTerrainSettings) -> None:
    values = (s.center_lat_deg, s.center_lon_deg, s.half_width_km,
              s.half_height_km, s.spacing_km, s.planet_radius_km,
              s.planetary_year_earth_days, s.relief_strength)
    if not all(np.isfinite(v) for v in values):
        raise ChildTerrainError("settings must be finite")
    if not -80 < s.center_lat_deg < 80 or not -180 <= s.center_lon_deg <= 180:
        raise ChildTerrainError("local chart excludes poles and antimeridian")
    if min(s.half_width_km, s.half_height_km, s.spacing_km,
           s.planet_radius_km, s.planetary_year_earth_days) <= 0:
        raise ChildTerrainError("lengths, radius and planetary year must be positive")
    if not 0 <= s.relief_strength <= 2.5:
        raise ChildTerrainError("relief_strength must be in [0,2.5]")
    if not isinstance(s.seed, int):
        raise ChildTerrainError("seed must be an integer")
    if (2 * s.half_width_km / s.spacing_km > 1400
            or 2 * s.half_height_km / s.spacing_km > 1400):
        raise ChildTerrainError("child grid exceeds safety bound")


def evaluate_terrain(macro: dict[str, np.ndarray], s: ChildTerrainSettings,
                     east_km: np.ndarray, north_km: np.ndarray):
    """Reconstruct at any coordinate; original DEM station heights exactly held.

    raw_noise(x,y) - bilinear(raw_noise at all parent DEM stations)
    vanishes at parent nodes, while preserving coherent geographic texture.
    """
    _validate_settings(s)
    latitude, longitude, heights, land = _source_fields(macro)
    east, north = np.broadcast_arrays(np.asarray(east_km, dtype=np.float64),
                                      np.asarray(north_km, dtype=np.float64))
    km_per_deg = pi * s.planet_radius_km / 180
    lat = s.center_lat_deg + north / km_per_deg
    lon = s.center_lon_deg + east / (km_per_deg * cos(radians(s.center_lat_deg)))
    if (np.any(lat > 80) or np.any(lat < -80)
            or np.any(lon > 180) or np.any(lon < -180)):
        raise ChildTerrainError("child crosses local projection validity bound")
    baseline = _bilinear(lon, lat, longitude, latitude, heights)

    # Broad parent relief determines maximum local variation. These are
    # artistic/geomorphological priors, not measured sub-grid terrain.
    parent_grad_n, parent_grad_e_equator = np.gradient(
        heights, latitude * km_per_deg, longitude * km_per_deg
    )
    # Use each planet-source station latitude, NOT the region center latitude.
    # Overlapping child windows with different centers share the same slope prior.
    parent_grad_e = parent_grad_e_equator / np.cos(np.deg2rad(latitude[:, None]))
    parent_slope = np.hypot(parent_grad_e, parent_grad_n)
    amplitude = s.relief_strength * np.clip(
        10 + 12 * np.sqrt(np.maximum(
            _bilinear(lon, lat, longitude, latitude, parent_slope), 0
        )), 10, 90
    )
    lon_nodes, lat_nodes = np.meshgrid(longitude, latitude)
    coarse_noise = _detail_noise(
        lon_nodes, lat_nodes, s.planet_radius_km, s.seed
    )
    raw = _detail_noise(lon, lat, s.planet_radius_km, s.seed)
    detail = amplitude * (
        raw - _bilinear(lon, lat, longitude, latitude, coarse_noise)
    ) * np.clip(np.maximum(baseline, 0) / 45, 0, 1)

    # Reference coastal sign preserved: no surprise new islands/seas.
    refined = np.where(baseline >= 0, np.maximum(0, baseline + detail), baseline)
    return refined, baseline, detail


def generate_child(macro: dict[str, np.ndarray], s: ChildTerrainSettings):
    _validate_settings(s)
    nx = round(2 * s.half_width_km / s.spacing_km) + 1
    ny = round(2 * s.half_height_km / s.spacing_km) + 1
    east = np.linspace(-s.half_width_km, s.half_width_km, nx)
    north = np.linspace(s.half_height_km, -s.half_height_km, ny)
    xx, yy = np.meshgrid(east, north)
    refined, baseline, detail = evaluate_terrain(macro, s, xx, yy)

    source_lat, source_lon, original, land = _source_fields(macro)
    kpd = pi * s.planet_radius_km / 180
    parent_e = (source_lon - s.center_lon_deg) * kpd * cos(radians(s.center_lat_deg))
    parent_n = (source_lat - s.center_lat_deg) * kpd
    parent_cols = np.flatnonzero((parent_e >= east[0]) & (parent_e <= east[-1]))
    parent_rows = np.flatnonzero(
        (parent_n >= north[-1]) & (parent_n <= north[0])
    )
    if not len(parent_cols) or not len(parent_rows):
        raise ChildTerrainError("child contains no original elevation anchors")
    xxn, yyn = np.meshgrid(parent_e[parent_cols], parent_n[parent_rows])
    check, _, _ = evaluate_terrain(macro, s, xxn, yyn)
    max_error = float(np.max(np.abs(
        check - original[np.ix_(parent_rows, parent_cols)]
    )))
    if max_error > 1e-6 or not np.isfinite(refined).all():
        raise ChildTerrainError(f"source anchor mismatch/nonfinite: {max_error}m")

    result = {
        "east_km": east,
        "north_km_north_first": north,
        "child_elevation_m": refined.astype(np.float32),
        "parent_interpolated_m": baseline.astype(np.float32),
        "new_local_relief_m": detail.astype(np.float32),
        "land_mask": (refined >= 0).astype(np.uint8),
    }
    meta = {
        "status": "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData": False,
        "child_shape": [ny, nx],
        "child_spacing_km": [float(east[1] - east[0]),
                             float(north[0] - north[1])],
        "source_step_degrees": float(np.median(np.diff(source_lon))),
        "source_elevation_anchors_in_child":
            int(len(parent_cols) * len(parent_rows)),
        "max_parent_anchor_error_m": max_error,
        "planet_radius_km": s.planet_radius_km,
        "planet_year_earth_days": s.planetary_year_earth_days,
        "center_lat_lon_deg": [s.center_lat_deg, s.center_lon_deg],
        "seed": s.seed,
        "relief_strength": s.relief_strength,
        "added_relief_m_min_max": [float(np.min(detail)), float(np.max(detail))],
        "land_marine_sign_preserved":
            bool(np.array_equal(refined >= 0, baseline >= 0)),
        "routing_status":
            "NOT_RECOMPUTED; historical A8 D8 remains guide, not accepted Core MFD",
        "limitations": [
            "fine pixels are generated model samples, not measured terrain",
            "parent DEM exact at its sample stations, not necessarily child pixels",
            "waterfalls, roads and local rivers are not resolved or computed",
            "planetary ecology classes are not universal land-cover categories",
        ],
    }
    return result, meta


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--macro-npz", type=Path, required=True)
    p.add_argument("--macro-manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--half-width-km", type=float, required=True)
    p.add_argument("--half-height-km", type=float, required=True)
    p.add_argument("--spacing-km", type=float, default=1)
    p.add_argument("--seed", type=int, default=1406)
    p.add_argument("--relief-strength", type=float, default=1)
    args = p.parse_args()
    with np.load(args.macro_npz, allow_pickle=False) as source:
        macro = {key: np.array(source[key], copy=True) for key in source.files}
    meta = json.loads(args.macro_manifest.read_text(encoding="utf8"))
    if meta.get("is_DomainData") is not False:
        raise ChildTerrainError(
            "source manifest must expressly reject canonical DomainData"
        )
    settings = ChildTerrainSettings(
        center_lat_deg=args.lat, center_lon_deg=args.lon,
        half_width_km=args.half_width_km,
        half_height_km=args.half_height_km,
        spacing_km=args.spacing_km,
        planet_radius_km=meta["planet_radius_km"],
        planetary_year_earth_days=meta["planetary_year_earth_days"],
        seed=args.seed, relief_strength=args.relief_strength
    )
    fields, report = generate_child(macro, settings)
    args.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output / "child-terrain-generated.npz", **fields)
    (args.output / "manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), layout="constrained")
    extent = [
        float(fields["east_km"][0]), float(fields["east_km"][-1]),
        float(fields["north_km_north_first"][-1]),
        float(fields["north_km_north_first"][0])
    ]
    light = LightSource(azdeg=315, altdeg=48)
    for ax, key, label in (
        (axes[0], "parent_interpolated_m", "Old 0.3-degree DEM: interpolated"),
        (axes[1], "child_elevation_m", "NEW 1-km modeled child terrain"),
    ):
        shaded = light.shade(
            fields[key], cmap=plt.get_cmap("terrain"),
            vert_exag=3, dx=settings.spacing_km * 1000,
            dy=settings.spacing_km * 1000
        )
        ax.imshow(shaded, extent=extent, origin="upper")
        ax.set_title(label)
    delta = fields["new_local_relief_m"]
    limit = max(5, float(np.percentile(abs(delta), 99)))
    image = axes[2].imshow(
        delta, extent=extent, origin="upper",
        cmap="RdBu_r", vmin=-limit, vmax=limit
    )
    axes[2].set_title("Added NEW local relief (m), not source data")
    fig.colorbar(image, ax=axes[2], shrink=.7)
    for ax in axes:
        ax.set(xlabel="east km", ylabel="north km", aspect="equal")
        ax.grid(alpha=.12)
    fig.suptitle("Synthetic child detail held to macro source; NO local MFD")
    fig.savefig(args.output / "child-terrain-preview.png", dpi=135)
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
