from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import tempfile
from typing import Iterable, Sequence

import numpy as np

from .assembly import DomainAssembly
from .contracts.data import HydroFeature, PoiFeature, SurfaceFeature, TerrainFeature
from .contracts.geometry import AreaGeometry, BandGeometry, CorridorGeometry, PointGeometry, RegionSet, WorldPoint


class TechnicalRenderError(RuntimeError):
    """Technical preview cannot be rendered without violating renderer invariants."""


@dataclass(frozen=True, slots=True)
class RenderedTechnicalMap:
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


def _image_size(width_km: float, height_km: float) -> tuple[int, int]:
    if width_km <= 0.0 or height_km <= 0.0:
        raise TechnicalRenderError("domain dimensions must be positive")
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
        raise TechnicalRenderError(
            f"field descriptor/payload ids mismatch: missing={missing}, extra={extra}"
        )

    missing_required = sorted(set(_REQUIRED_FIELDS) - descriptor_ids)
    if missing_required:
        raise TechnicalRenderError(f"missing canonical renderer fields: {missing_required}")

    expected_shape = (assembly.data.grid.rows, assembly.data.grid.columns)
    for field_id in _REQUIRED_FIELDS:
        descriptor = assembly.data.fields[field_id]
        payload = assembly.field_payloads[field_id]
        if not isinstance(payload, np.ndarray):
            raise TechnicalRenderError(f"field {field_id!r} payload must be numpy ndarray")
        if tuple(payload.shape) != expected_shape or descriptor.shape != expected_shape:
            raise TechnicalRenderError(
                f"field {field_id!r} shape must be {expected_shape}, got descriptor={descriptor.shape}, payload={payload.shape}"
            )
        if descriptor.dtype != "float32" or payload.dtype != np.dtype(np.float32):
            raise TechnicalRenderError(
                f"field {field_id!r} must be float32, got descriptor={descriptor.dtype!r}, payload={payload.dtype}"
            )


def _polyline_arrays(points: Sequence[WorldPoint]) -> tuple[list[float], list[float]]:
    return [point.x_km for point in points], [point.y_km for point in points]


def _sample_polyline(points: Sequence[WorldPoint], t: float) -> tuple[float, float, float, float]:
    if len(points) < 2:
        raise TechnicalRenderError("polyline requires at least two points")
    clamped = min(1.0, max(0.0, float(t)))
    lengths: list[float] = []
    total = 0.0
    for left, right in zip(points, points[1:]):
        length = math.hypot(right.x_km - left.x_km, right.y_km - left.y_km)
        lengths.append(length)
        total += length
    if total == 0.0:
        first = points[0]
        return first.x_km, first.y_km, 1.0, 0.0

    target = clamped * total
    travelled = 0.0
    for index, length in enumerate(lengths):
        if length == 0.0:
            continue
        if travelled + length >= target or index == len(lengths) - 1:
            left = points[index]
            right = points[index + 1]
            local = min(1.0, max(0.0, (target - travelled) / length))
            x = left.x_km + (right.x_km - left.x_km) * local
            y = left.y_km + (right.y_km - left.y_km) * local
            tx = (right.x_km - left.x_km) / length
            ty = (right.y_km - left.y_km) / length
            return x, y, tx, ty
        travelled += length

    last = points[-1]
    return last.x_km, last.y_km, 1.0, 0.0


def _geometry_label_position(geometry: object) -> tuple[float, float] | None:
    if isinstance(geometry, PointGeometry):
        return geometry.x_km, geometry.y_km
    if isinstance(geometry, (CorridorGeometry, BandGeometry)):
        x, y, _, _ = _sample_polyline(geometry.centerline, 0.5)
        return x, y
    if isinstance(geometry, AreaGeometry):
        xs = [point.x_km for point in geometry.boundary]
        ys = [point.y_km for point in geometry.boundary]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    if isinstance(geometry, RegionSet) and geometry.polygons:
        outer = geometry.polygons[0].outer
        xs = [point.x_km for point in outer]
        ys = [point.y_km for point in outer]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    return None


def _closed_xy(points: Iterable[WorldPoint]) -> tuple[list[float], list[float]]:
    materialized = list(points)
    if not materialized:
        return [], []
    xs = [point.x_km for point in materialized]
    ys = [point.y_km for point in materialized]
    xs.append(materialized[0].x_km)
    ys.append(materialized[0].y_km)
    return xs, ys


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
        from matplotlib.lines import Line2D
        from matplotlib.patches import Patch, Rectangle
    except ImportError as exc:
        raise TechnicalRenderError(
            "technical renderer requires optional dependencies; install domain-generator[render]"
        ) from exc
    return FigureCanvasAgg, Figure, Line2D, Patch, Rectangle


def _render_png(assembly: DomainAssembly, path: Path, *, width_px: int, height_px: int) -> None:
    FigureCanvasAgg, Figure, Line2D, Patch, Rectangle = _load_rendering_modules()

    data = assembly.data
    width_km = data.domain.width_km
    height_km = data.domain.height_km
    extent = (0.0, width_km, 0.0, height_km)

    figure = Figure(figsize=(width_px / _DPI, height_px / _DPI), dpi=_DPI, facecolor="white")
    FigureCanvasAgg(figure)
    axes = figure.add_axes((0.08, 0.10, 0.84, 0.82))
    axes.set_facecolor("white")

    elevation = assembly.field_payloads["elevation"]
    axes.imshow(
        elevation,
        origin="upper",
        extent=extent,
        interpolation="nearest",
        cmap="gray",
        aspect="auto",
        zorder=1,
    )

    vegetation = np.clip(assembly.field_payloads["vegetation_density"], 0.0, 1.0)
    vegetation_rgba = np.zeros((*vegetation.shape, 4), dtype=np.float32)
    vegetation_rgba[..., 0] = 0.08
    vegetation_rgba[..., 1] = 0.45
    vegetation_rgba[..., 2] = 0.12
    vegetation_rgba[..., 3] = vegetation * 0.45
    axes.imshow(
        vegetation_rgba,
        origin="upper",
        extent=extent,
        interpolation="nearest",
        aspect="auto",
        zorder=2,
    )

    water = assembly.field_payloads["water_depth"] > 0.0
    water_rgba = np.zeros((*water.shape, 4), dtype=np.float32)
    water_rgba[..., 0] = 0.10
    water_rgba[..., 1] = 0.45
    water_rgba[..., 2] = 0.85
    water_rgba[..., 3] = water.astype(np.float32) * 0.68
    axes.imshow(
        water_rgba,
        origin="upper",
        extent=extent,
        interpolation="nearest",
        aspect="auto",
        zorder=3,
    )

    for feature_id in sorted(data.features):
        feature = data.features[feature_id]
        geometry = feature.geometry

        if isinstance(feature, HydroFeature):
            for polygon in geometry.polygons:
                xs, ys = _closed_xy(polygon.outer)
                axes.plot(xs, ys, color="#1d4ed8", linewidth=1.6, zorder=5)
                for hole in polygon.holes:
                    hx, hy = _closed_xy(hole)
                    axes.plot(hx, hy, color="#1d4ed8", linewidth=1.0, linestyle="--", zorder=5)
        elif isinstance(geometry, PointGeometry):
            marker = "D" if isinstance(feature, PoiFeature) else "o"
            color = "#b91c1c" if isinstance(feature, PoiFeature) else "#d97706"
            axes.scatter(
                [geometry.x_km],
                [geometry.y_km],
                marker=marker,
                s=32,
                facecolors=color,
                edgecolors="black",
                linewidths=0.6,
                zorder=8,
            )
        elif isinstance(geometry, CorridorGeometry):
            xs, ys = _polyline_arrays(geometry.centerline)
            axes.plot(xs, ys, color="#7c3aed", linewidth=1.4, zorder=6)
        elif isinstance(geometry, BandGeometry):
            xs, ys = _polyline_arrays(geometry.centerline)
            axes.plot(xs, ys, color="#d97706", linewidth=1.8, zorder=6)
            for sample in geometry.width_profile:
                x, y, tx, ty = _sample_polyline(geometry.centerline, sample.t)
                nx, ny = -ty, tx
                half = sample.width_km / 2.0
                axes.plot(
                    [x - nx * half, x + nx * half],
                    [y - ny * half, y + ny * half],
                    color="#d97706",
                    linewidth=1.0,
                    zorder=6,
                )
        elif isinstance(geometry, AreaGeometry):
            xs, ys = _closed_xy(geometry.boundary)
            if isinstance(feature, SurfaceFeature):
                axes.fill(xs, ys, facecolor="#16a34a", alpha=0.12, zorder=4)
                axes.plot(xs, ys, color="#15803d", linewidth=1.2, zorder=6)
            elif isinstance(feature, TerrainFeature):
                axes.plot(xs, ys, color="#d97706", linewidth=1.5, zorder=6)
            else:
                axes.plot(xs, ys, color="#374151", linewidth=1.2, zorder=6)

        label = feature.label or feature_id
        position = _geometry_label_position(geometry)
        if position is not None:
            axes.text(
                position[0],
                position[1],
                label,
                fontsize=7,
                ha="left",
                va="bottom",
                color="black",
                bbox={"facecolor": "white", "alpha": 0.60, "edgecolor": "none", "pad": 1.0},
                zorder=10,
            )

    rivers = data.networks.get("rivers")
    if rivers is not None:
        for segment_id in sorted(rivers.segments):
            segment = rivers.segments[segment_id]
            xs, ys = _polyline_arrays(segment.centerline)
            axes.plot(xs, ys, color="#075985", linewidth=1.3, zorder=7)
            if len(segment.centerline) >= 2:
                x0, y0, _, _ = _sample_polyline(segment.centerline, 0.46)
                x1, y1, _, _ = _sample_polyline(segment.centerline, 0.54)
                axes.annotate(
                    "",
                    xy=(x1, y1),
                    xytext=(x0, y0),
                    arrowprops={"arrowstyle": "->", "color": "#075985", "lw": 1.0},
                    zorder=8,
                )

    axes.add_patch(
        Rectangle(
            (0.0, 0.0),
            width_km,
            height_km,
            fill=False,
            edgecolor="black",
            linewidth=1.2,
            zorder=20,
        )
    )

    scale = _nice_scale_length(width_km)
    sx = width_km * 0.05
    sy = height_km * 0.05
    axes.plot([sx, sx + scale], [sy, sy], color="black", linewidth=2.0, zorder=20)
    axes.plot([sx, sx], [sy - height_km * 0.008, sy + height_km * 0.008], color="black", linewidth=1.2, zorder=20)
    axes.plot(
        [sx + scale, sx + scale],
        [sy - height_km * 0.008, sy + height_km * 0.008],
        color="black",
        linewidth=1.2,
        zorder=20,
    )
    axes.text(sx + scale / 2.0, sy + height_km * 0.018, f"{scale:g} km", ha="center", va="bottom", fontsize=7, zorder=20)

    axes.annotate(
        "N",
        xy=(0.96, 0.96),
        xytext=(0.96, 0.84),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        arrowprops={"arrowstyle": "-|>", "color": "black", "lw": 1.2},
        zorder=20,
    )

    legend_handles = [
        Patch(facecolor="#bdbdbd", edgecolor="black", label="Elevation"),
        Patch(facecolor="#16732a", alpha=0.45, label="Vegetation"),
        Patch(facecolor="#1a73d9", alpha=0.68, label="Water / lakes"),
        Line2D([0], [0], color="#075985", lw=1.3, label="River"),
        Line2D([0], [0], color="#d97706", lw=1.5, label="Terrain / band"),
        Line2D([0], [0], color="#15803d", lw=1.2, label="Surface feature"),
        Line2D([0], [0], marker="D", color="none", markerfacecolor="#b91c1c", markeredgecolor="black", markersize=5, label="POI"),
    ]
    axes.legend(handles=legend_handles, loc="upper left", fontsize=6, framealpha=0.78, borderpad=0.4)

    axes.set_xlim(0.0, width_km)
    axes.set_ylim(0.0, height_km)
    axes.set_aspect("equal", adjustable="box")
    axes.set_xlabel("x (km)", fontsize=8)
    axes.set_ylabel("y (km)", fontsize=8)
    axes.tick_params(axis="both", labelsize=7)
    title = data.identity.label or data.identity.id
    axes.set_title(f"Technical map — {title}", fontsize=9)

    try:
        figure.savefig(
            path,
            format="png",
            dpi=_DPI,
            metadata={"Software": "domain_generator Technical Renderer v0.1"},
        )
    finally:
        figure.clear()


def _verify_png(path: Path) -> None:
    if not path.is_file() or path.stat().st_size <= len(_PNG_SIGNATURE):
        raise TechnicalRenderError("renderer did not produce a complete PNG file")
    with path.open("rb") as handle:
        signature = handle.read(len(_PNG_SIGNATURE))
    if signature != _PNG_SIGNATURE:
        raise TechnicalRenderError("renderer output is not a PNG file")


def render_technical_map(*, assembly: DomainAssembly, output_path: Path) -> RenderedTechnicalMap:
    """Render a deterministic non-canonical top-down diagnostic PNG for one DomainAssembly."""
    _validate_assembly(assembly)
    if not isinstance(output_path, Path):
        raise TypeError("output_path must be pathlib.Path")
    if output_path.suffix.lower() != ".png":
        raise TechnicalRenderError("technical renderer output_path must end with .png")
    if output_path.exists():
        raise TechnicalRenderError("output path already exists")

    parent = output_path.parent
    if parent.exists():
        if not parent.is_dir():
            raise TechnicalRenderError("output parent exists but is not a directory")
    else:
        grandparent = parent.parent
        if not grandparent.exists() or not grandparent.is_dir():
            raise TechnicalRenderError("output parent may be created only when its own parent already exists")
        try:
            parent.mkdir()
        except OSError as exc:
            raise TechnicalRenderError("failed to create output parent directory") from exc

    width_px, height_px = _image_size(assembly.data.domain.width_km, assembly.data.domain.height_km)

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
            raise TechnicalRenderError("output path appeared during rendering; refusing to overwrite")
        temp_path.rename(output_path)
        temp_path = None
        return RenderedTechnicalMap(path=output_path, width_px=width_px, height_px=height_px)
    except TechnicalRenderError:
        raise
    except Exception as exc:
        raise TechnicalRenderError("failed to render technical map") from exc
    finally:
        if fd is not None:
            os.close(fd)
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


__all__ = ["RenderedTechnicalMap", "TechnicalRenderError", "render_technical_map"]
