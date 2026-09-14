from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import tempfile

import numpy as np

from .assembly import DomainAssembly
from .contracts.data import PoiFeature


class GuideRenderError(RuntimeError):
    """Guide preview cannot be rendered without violating renderer invariants."""


@dataclass(frozen=True, slots=True)
class RenderedGuideMap:
    path: Path
    width_px: int
    height_px: int

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("path must be pathlib.Path")
        if self.width_px <= 0 or self.height_px <= 0:
            raise ValueError("rendered dimensions must be positive")


_REQUIRED_FIELDS = ("elevation", "water_depth", "moisture", "vegetation_density")
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_LONG_SIDE_PX = 1600
_DPI = 100
_LIGHT_AZIMUTH_DEG = 315.0
_LIGHT_ALTITUDE_DEG = 45.0


def _image_size(width_km: float, height_km: float) -> tuple[int, int]:
    if width_km <= 0.0 or height_km <= 0.0:
        raise GuideRenderError("domain dimensions must be positive")
    if width_km >= height_km:
        width_px = _LONG_SIDE_PX
        height_px = max(1, round(_LONG_SIDE_PX * height_km / width_km))
    else:
        height_px = _LONG_SIDE_PX
        width_px = max(1, round(_LONG_SIDE_PX * width_km / height_km))
    return width_px, height_px


def _validate_assembly(assembly: DomainAssembly) -> None:
    if not isinstance(assembly, DomainAssembly):
        raise TypeError("assembly must be DomainAssembly")

    descriptor_ids = set(assembly.data.fields)
    payload_ids = set(assembly.field_payloads)
    if descriptor_ids != payload_ids:
        missing = sorted(descriptor_ids - payload_ids)
        extra = sorted(payload_ids - descriptor_ids)
        raise GuideRenderError(
            f"field descriptor/payload ids mismatch: missing={missing}, extra={extra}"
        )

    missing_required = sorted(set(_REQUIRED_FIELDS) - descriptor_ids)
    if missing_required:
        raise GuideRenderError(f"missing canonical renderer fields: {missing_required}")

    expected_shape = (assembly.data.grid.rows, assembly.data.grid.columns)
    for field_id in _REQUIRED_FIELDS:
        descriptor = assembly.data.fields[field_id]
        payload = assembly.field_payloads[field_id]
        if not isinstance(payload, np.ndarray):
            raise GuideRenderError(f"field {field_id!r} payload must be numpy ndarray")
        if tuple(payload.shape) != expected_shape or descriptor.shape != expected_shape:
            raise GuideRenderError(
                f"field {field_id!r} shape must be {expected_shape}, got descriptor={descriptor.shape}, payload={payload.shape}"
            )
        if descriptor.dtype != "float32" or payload.dtype != np.dtype(np.float32):
            raise GuideRenderError(
                f"field {field_id!r} must be float32, got descriptor={descriptor.dtype!r}, payload={payload.dtype}"
            )
        if not np.isfinite(payload).all():
            raise GuideRenderError(f"field {field_id!r} must contain only finite values")


def _normalize_elevation(elevation: np.ndarray) -> np.ndarray:
    values = elevation.astype(np.float64, copy=False)
    low = float(np.min(values))
    high = float(np.max(values))
    if math.isclose(low, high, rel_tol=0.0, abs_tol=1e-12):
        return np.full(values.shape, 0.42, dtype=np.float64)
    return np.clip((values - low) / (high - low), 0.0, 1.0)


def _hypsometric_rgb(normalized: np.ndarray) -> np.ndarray:
    stops = np.array([0.0, 0.28, 0.55, 0.78, 1.0], dtype=np.float64)
    colors = np.array(
        [
            [0.25, 0.36, 0.18],
            [0.39, 0.48, 0.24],
            [0.49, 0.43, 0.28],
            [0.46, 0.43, 0.39],
            [0.79, 0.79, 0.76],
        ],
        dtype=np.float64,
    )
    result = np.empty((*normalized.shape, 3), dtype=np.float64)
    flat = normalized.ravel()
    for channel in range(3):
        result[..., channel] = np.interp(flat, stops, colors[:, channel]).reshape(normalized.shape)
    return result


def _hillshade(elevation: np.ndarray, *, cell_size_km: float) -> np.ndarray:
    spacing_m = float(cell_size_km) * 1000.0
    if spacing_m <= 0.0:
        raise GuideRenderError("grid cell size must be positive")

    values = elevation.astype(np.float64, copy=False)
    dz_dy_south, dz_dx_east = np.gradient(values, spacing_m, spacing_m)
    dz_dy_north = -dz_dy_south

    nx = -dz_dx_east
    ny = -dz_dy_north
    nz = np.ones_like(values)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= length
    ny /= length
    nz /= length

    azimuth = math.radians(_LIGHT_AZIMUTH_DEG)
    altitude = math.radians(_LIGHT_ALTITUDE_DEG)
    light_x = math.cos(altitude) * math.sin(azimuth)
    light_y = math.cos(altitude) * math.cos(azimuth)
    light_z = math.sin(altitude)

    illumination = nx * light_x + ny * light_y + nz * light_z
    return np.clip((illumination + 0.15) / 1.15, 0.0, 1.0)


def _compose_map_rgb(assembly: DomainAssembly) -> np.ndarray:
    elevation = assembly.field_payloads["elevation"]
    moisture = np.clip(assembly.field_payloads["moisture"].astype(np.float64), 0.0, 1.0)
    vegetation = np.clip(
        assembly.field_payloads["vegetation_density"].astype(np.float64), 0.0, 1.0
    )
    water_depth = np.maximum(assembly.field_payloads["water_depth"].astype(np.float64), 0.0)

    base = _hypsometric_rgb(_normalize_elevation(elevation))

    vegetation_tint = np.array([0.16, 0.43, 0.16], dtype=np.float64)
    vegetation_alpha = (0.42 * vegetation)[..., None]
    base = base * (1.0 - vegetation_alpha) + vegetation_tint * vegetation_alpha

    moisture_tint = np.array([0.12, 0.30, 0.24], dtype=np.float64)
    moisture_alpha = (0.10 * moisture)[..., None]
    base = base * (1.0 - moisture_alpha) + moisture_tint * moisture_alpha

    shade = _hillshade(elevation, cell_size_km=assembly.data.grid.cell_size_km)
    brightness = 0.70 + 0.42 * shade
    base = np.clip(base * brightness[..., None], 0.0, 1.0)

    water_mask = water_depth > 0.0
    if np.any(water_mask):
        max_depth = float(np.max(water_depth))
        if max_depth > 0.0:
            depth = np.clip(water_depth / max_depth, 0.0, 1.0)
        else:
            depth = np.zeros_like(water_depth)
        shallow = np.array([0.13, 0.48, 0.68], dtype=np.float64)
        deep = np.array([0.035, 0.20, 0.43], dtype=np.float64)
        water_rgb = shallow + (deep - shallow) * depth[..., None]
        alpha = np.where(water_mask, 0.93, 0.0)[..., None]
        base = base * (1.0 - alpha) + water_rgb * alpha

    return np.clip(base, 0.0, 1.0).astype(np.float32)


def _nice_scale_length(width_km: float) -> float:
    target = width_km / 5.0
    if target <= 0.0:
        return 1.0
    exponent = 10.0 ** math.floor(math.log10(target))
    normalized = target / exponent
    if normalized >= 5.0:
        leading = 5.0
    elif normalized >= 2.0:
        leading = 2.0
    else:
        leading = 1.0
    return leading * exponent


def _load_rendering_modules():
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        from matplotlib.patches import Rectangle
    except ImportError as exc:
        raise GuideRenderError(
            "guide renderer requires optional dependencies; install domain-generator[render]"
        ) from exc
    return FigureCanvasAgg, Figure, Rectangle


def _render_png(assembly: DomainAssembly, path: Path, *, width_px: int, height_px: int) -> None:
    FigureCanvasAgg, Figure, Rectangle = _load_rendering_modules()

    data = assembly.data
    width_km = data.domain.width_km
    height_km = data.domain.height_km
    extent = (0.0, width_km, 0.0, height_km)
    rgb = _compose_map_rgb(assembly)

    figure = Figure(
        figsize=(width_px / _DPI, height_px / _DPI),
        dpi=_DPI,
        facecolor="#d8d0bd",
    )
    FigureCanvasAgg(figure)
    axes = figure.add_axes((0.0, 0.0, 1.0, 1.0))
    axes.set_facecolor("#d8d0bd")
    axes.imshow(
        rgb,
        origin="upper",
        extent=extent,
        interpolation="bilinear",
        aspect="auto",
        zorder=1,
    )

    rivers = data.networks.get("rivers")
    if rivers is not None:
        for segment_id in sorted(rivers.segments):
            segment = rivers.segments[segment_id]
            xs = [point.x_km for point in segment.centerline]
            ys = [point.y_km for point in segment.centerline]
            catchment = float(segment.properties.catchment_area_km2)
            linewidth = min(3.0, 0.75 + 0.42 * math.log1p(catchment))
            axes.plot(
                xs,
                ys,
                color="#155f86",
                linewidth=linewidth + 1.0,
                alpha=0.45,
                solid_capstyle="round",
                solid_joinstyle="round",
                zorder=5,
            )
            axes.plot(
                xs,
                ys,
                color="#65b9d8",
                linewidth=linewidth,
                alpha=0.95,
                solid_capstyle="round",
                solid_joinstyle="round",
                zorder=6,
            )

    for feature_id in sorted(data.features):
        feature = data.features[feature_id]
        if not isinstance(feature, PoiFeature):
            continue
        point = feature.geometry
        axes.scatter(
            [point.x_km],
            [point.y_km],
            marker="o",
            s=34,
            facecolors="#d8b15a",
            edgecolors="#30291e",
            linewidths=1.1,
            zorder=10,
        )
        axes.scatter(
            [point.x_km],
            [point.y_km],
            marker=".",
            s=12,
            color="#3b2f22",
            zorder=11,
        )

    axes.add_patch(
        Rectangle(
            (0.0, 0.0),
            width_km,
            height_km,
            fill=False,
            edgecolor="#30291e",
            linewidth=1.0,
            zorder=20,
        )
    )

    scale = _nice_scale_length(width_km)
    sx = width_km * 0.045
    sy = height_km * 0.055
    tick = max(height_km * 0.008, 0.06)
    axes.plot([sx, sx + scale], [sy, sy], color="white", linewidth=4.0, alpha=0.72, zorder=20)
    axes.plot([sx, sx + scale], [sy, sy], color="#241f18", linewidth=2.0, zorder=21)
    for x in (sx, sx + scale):
        axes.plot([x, x], [sy - tick, sy + tick], color="white", linewidth=3.0, alpha=0.72, zorder=20)
        axes.plot([x, x], [sy - tick, sy + tick], color="#241f18", linewidth=1.2, zorder=21)
    axes.text(
        sx + scale / 2.0,
        sy + height_km * 0.022,
        f"{scale:g} km",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#241f18",
        bbox={"facecolor": "white", "alpha": 0.58, "edgecolor": "none", "pad": 1.0},
        zorder=22,
    )

    axes.annotate(
        "N",
        xy=(0.955, 0.955),
        xytext=(0.955, 0.86),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#241f18",
        arrowprops={"arrowstyle": "-|>", "color": "#241f18", "lw": 1.5},
        zorder=22,
    )

    axes.set_xlim(0.0, width_km)
    axes.set_ylim(0.0, height_km)
    axes.set_aspect("equal", adjustable="box")
    axes.set_axis_off()

    try:
        figure.savefig(
            path,
            format="png",
            dpi=_DPI,
            metadata={"Software": "domain_generator Guide Renderer v0.1"},
            facecolor=figure.get_facecolor(),
        )
    finally:
        figure.clear()


def _verify_png(path: Path) -> None:
    if not path.is_file() or path.stat().st_size <= len(_PNG_SIGNATURE):
        raise GuideRenderError("renderer did not produce a complete PNG file")
    with path.open("rb") as handle:
        signature = handle.read(len(_PNG_SIGNATURE))
    if signature != _PNG_SIGNATURE:
        raise GuideRenderError("renderer output is not a PNG file")


def render_guide_map(*, assembly: DomainAssembly, output_path: Path) -> RenderedGuideMap:
    """Render a deterministic non-canonical top-down human-readable guide PNG."""
    _validate_assembly(assembly)
    if not isinstance(output_path, Path):
        raise TypeError("output_path must be pathlib.Path")
    if output_path.suffix.lower() != ".png":
        raise GuideRenderError("guide renderer output_path must end with .png")
    if output_path.exists():
        raise GuideRenderError("output path already exists")

    parent = output_path.parent
    if parent.exists():
        if not parent.is_dir():
            raise GuideRenderError("output parent exists but is not a directory")
    else:
        grandparent = parent.parent
        if not grandparent.exists() or not grandparent.is_dir():
            raise GuideRenderError("output parent may be created only when its own parent already exists")
        try:
            parent.mkdir()
        except OSError as exc:
            raise GuideRenderError("failed to create output parent directory") from exc

    width_px, height_px = _image_size(
        assembly.data.domain.width_km,
        assembly.data.domain.height_km,
    )

    fd: int | None = None
    temp_path: Path | None = None
    try:
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.tmp-",
            suffix=".png",
            dir=parent,
        )
        os.close(fd)
        fd = None
        temp_path = Path(temp_name)

        _render_png(assembly, temp_path, width_px=width_px, height_px=height_px)
        _verify_png(temp_path)

        if output_path.exists():
            raise GuideRenderError("output path appeared during rendering; refusing to overwrite")
        temp_path.rename(output_path)
        temp_path = None
        return RenderedGuideMap(path=output_path, width_px=width_px, height_px=height_px)
    except GuideRenderError:
        raise
    except Exception as exc:
        raise GuideRenderError("failed to render guide map") from exc
    finally:
        if fd is not None:
            os.close(fd)
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


__all__ = ["GuideRenderError", "RenderedGuideMap", "render_guide_map"]
