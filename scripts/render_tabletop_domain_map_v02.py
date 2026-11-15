from __future__ import annotations

"""Deterministic, geometry-faithful presentation layers for tabletop/literary maps.

Reads DomainSpec and catalog; generates one accepted DomainData; never edits
world semantics. All map layers align pixel-for-pixel for later stylization.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from domain_generator.application import generate_domain, load_preset_catalog, registry_for_request
from domain_generator.contracts import GenerationRequest
from domain_generator.contracts.data import HydroFeature, PoiFeature


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / "examples" / "tabletop-map" / "domain-request.json"
DEFAULT_PRESETS = ROOT / "tests" / "acceptance" / "cases" / "a08-core-v02-integrated" / "presets.json"
MAP_LAYERS = (
    "01-terrain.png",
    "10-relief-contours.png",
    "02-water.png",
    "03-rivers.png",
    "04-poi-markers.png",
    "05-labels.png",
)
RIVER_COLOR = (225, 245, 245, 250)
DARK = (38, 50, 43, 245)


def _font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _terrain_layer(fields: dict, size: tuple[int, int], *, parchment: bool) -> Image.Image:
    elevation = np.asarray(fields["elevation"], dtype=np.float64)
    moisture = np.clip(fields["moisture"].astype(np.float64), 0.0, 1.0)
    vegetation = np.clip(fields["vegetation_density"].astype(np.float64), 0.0, 1.0)
    # Relief shading is a cartographic visual treatment, not a new physics field.
    north_south, west_east = np.gradient(elevation)
    # Emphasize already-accepted relief at a map-readable scale; the raster
    # is NOT changed, only the brightness of the rendered terrain palette.
    slope_scale = max(8.0, float(np.percentile(np.hypot(west_east, north_south), 85)))
    lighting = np.clip(
        0.93 + 0.24 * west_east / slope_scale
             - 0.18 * north_south / slope_scale,
        0.66, 1.17,
    )
    e_low, e_high = np.percentile(elevation, (2, 98))
    altitude = np.clip((elevation - e_low) / max(1.0, float(e_high - e_low)), 0.0, 1.0)
    green = np.clip(0.72 * vegetation + 0.28 * moisture, 0.0, 1.0)
    if parchment:
        arid = np.array([0.89, 0.82, 0.66])
        lush = np.array([0.50, 0.59, 0.43])
    else:
        arid = np.array([0.81, 0.75, 0.57])
        lush = np.array([0.27, 0.52, 0.36])
    rgb = arid[None, None, :] * (1.0 - green[..., None]) + lush[None, None, :] * green[..., None]
    highland = np.array([0.77, 0.77, 0.68]) if parchment else np.array([0.60, 0.65, 0.59])
    alpha = (np.maximum(altitude - 0.61, 0.0) * 0.67)[..., None]
    rgb = rgb * (1.0 - alpha) + highland[None, None, :] * alpha
    rgb = np.clip(rgb * lighting[..., None], 0.0, 1.0)
    native = Image.fromarray(np.round(rgb * 255).astype(np.uint8), "RGB")
    return native.resize(size, Image.Resampling.BICUBIC).convert("RGBA")


def _contour_layer(
    fields: dict, size: tuple[int, int], *, ppm: int
) -> tuple[Image.Image, float | None]:
    """Subtle vector-like elevation contours from the *accepted* elevation raster.

    Lines are transparent presentation overlays. Neither elevation values nor
    hydrologic/world geometries are smoothed, moved or regenerated.
    """
    raster = np.asarray(fields["elevation"], dtype=np.float64)
    rows, columns = raster.shape
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    low, high = float(np.min(raster)), float(np.max(raster))
    span = high - low
    if not np.isfinite(span) or span < 1.0:
        return layer, None
    # Select a readable *cartographic* contour interval; not new terrain physics.
    interval = min((25.0, 50.0, 100.0, 200.0, 500.0),
                   key=lambda v: abs(span / v - 12.0))
    levels = np.arange(np.ceil(low / interval) * interval, high, interval)
    if not levels.size:
        return layer, None
    x = (np.arange(columns, dtype=np.float64) + 0.5) * (size[0] / columns / ppm)
    y = (rows - np.arange(rows, dtype=np.float64) - 0.5) * (size[1] / rows / ppm)
    fig, ax = plt.subplots()
    try:
        collection = ax.contour(x, y, raster, levels=levels)
        pen = ImageDraw.Draw(layer, "RGBA")
        for index, contours in enumerate(collection.allsegs):
            major = (index % 4) == 0
            ink = (62, 61, 42, 109 if major else 59)
            width = 2 if major else 1
            for contour in contours:
                if len(contour) < 2:
                    continue
                points = [(round(float(x_km) * ppm), round(size[1] - float(y_km) * ppm))
                          for x_km, y_km in contour]
                pen.line(points, fill=ink, width=width, joint="curve")
    finally:
        plt.close(fig)
    return layer, interval


def _geo_point(point, *, ppm: int, size: tuple[int, int]) -> tuple[int, int]:
    return (round(float(point.x_km) * ppm),
            round(size[1] - float(point.y_km) * ppm))


def _water_layer(data, fields: dict, size: tuple[int, int], *, ppm: int) -> Image.Image:
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    sea = fields.get("marine_mask")
    if sea is not None:
        sea_binary = Image.fromarray(np.asarray(sea, dtype=np.uint8) * 255, "L")
        mask = sea_binary.resize(size, Image.Resampling.NEAREST)
        color = Image.new("RGBA", size, (38, 98, 135, 255))
        out.paste(color, (0, 0), mask)
    d = ImageDraw.Draw(out, "RGBA")
    for feature_id, feature in sorted(data.features.items()):
        if not isinstance(feature, HydroFeature):
            continue
        for polygon in feature.geometry.polygons:
            pts = [_geo_point(p, ppm=ppm, size=size) for p in polygon.outer]
            if len(pts) < 3:
                continue
            d.polygon(pts, fill=(66, 136, 156, 255))
            d.line(pts + pts[:1], fill=(216, 238, 228, 230), width=max(1, ppm // 14), joint="curve")
            for hole in polygon.holes:
                # A hole must not be filled with invented water; preserve transparency.
                hole_pts = [_geo_point(p, ppm=ppm, size=size) for p in hole]
                if len(hole_pts) >= 3:
                    d.polygon(hole_pts, fill=(0, 0, 0, 0))
    return out


def _river_layer(data, size: tuple[int, int], *, ppm: int) -> Image.Image:
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    pen = ImageDraw.Draw(layer, "RGBA")
    network = data.networks.get("rivers")
    if network is None:
        return layer
    for segment_id, segment in sorted(network.segments.items()):
        path = [_geo_point(p, ppm=ppm, size=size) for p in segment.centerline]
        if len(path) < 2:
            continue
        width = max(2, ppm // 13)
        pen.line(path, fill=(38, 93, 119, 220), width=width + 2, joint="curve")
        pen.line(path, fill=RIVER_COLOR, width=width, joint="curve")
    return layer


def _settlements(data, size: tuple[int, int], *, ppm: int):
    markers = Image.new("RGBA", size, (0, 0, 0, 0))
    labels = Image.new("RGBA", size, (0, 0, 0, 0))
    d_mark = ImageDraw.Draw(markers, "RGBA")
    d_label = ImageDraw.Draw(labels, "RGBA")
    candidates = []
    for feature_id, feature in sorted(data.features.items()):
        if not isinstance(feature, PoiFeature):
            continue
        pos = _geo_point(feature.geometry, ppm=ppm, size=size)
        if not (0 <= pos[0] < size[0] and 0 <= pos[1] < size[1]):
            raise RuntimeError("Accepted POI lies outside map support")
        label = feature.label or feature_id
        candidates.append((feature_id, label, pos, tuple(feature.tags)))

    # Labels are intended to remain legible after downsampling a 1536-px
    # map for a GM handout. Font size never changes placement coordinates.
    font = _font(max(18, round(ppm * 0.82)))
    seen = []
    ledger = []
    offset = max(17, ppm // 2)
    for feature_id, label, (x, y), tags in candidates:
        r = max(6, ppm // 3)
        # Symbol shape is controlled ONLY by an explicit user-authored tag.
        # It is not a newly inferred settlement size, population or economy.
        role = "fort" if "fort" in tags else "village" if "village" in tags else "poi"
        if role == "fort":
            d_mark.rectangle((x - r - 2, y - r - 2, x + r + 2, y + r + 2),
                             fill=(74, 72, 53, 255), outline=(248, 227, 165, 255), width=3)
            d_mark.rectangle((x - 3, y - 3, x + 3, y + 3), fill=(238, 219, 165, 255))
        elif role == "village":
            d_mark.ellipse((x - r - 2, y - r - 2, x + r + 2, y + r + 2),
                           fill=(247, 228, 164, 255), outline=(49, 52, 41, 255), width=3)
            d_mark.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(62, 66, 45, 255))
        else:
            d_mark.polygon(((x, y - r), (x + r, y), (x, y + r), (x - r, y)),
                           fill=(248, 221, 167, 255))
            d_mark.line(((x, y - r), (x + r, y), (x, y + r), (x - r, y), (x, y - r)),
                        fill=(49, 52, 41, 255), width=2)

        bbox = d_label.textbbox((0, 0), label, font=font, stroke_width=2)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        offsets = (
            (offset, -height // 2),
            (-offset - width, -height // 2),
            (-width // 2, offset),
            (-width // 2, -offset - height),
            (offset, offset),
            (-offset - width, offset),
            (offset, -offset - height),
            (-offset - width, -offset - height),
        )
        chosen = None
        for dx, dy in offsets:
            tx, ty = int(x + dx), int(y + dy)
            b = (tx - 2, ty - 2, tx + width + 3, ty + height + 3)
            if b[0] < 5 or b[1] < 5 or b[2] > size[0] - 5 or b[3] > size[1] - 5:
                continue
            if any(not (b[2] < prior[0] or b[0] > prior[2] or
                        b[3] < prior[1] or b[1] > prior[3]) for prior in seen):
                continue
            chosen = (tx, ty, b)
            break
        if chosen is None:
            # Never move the real settlement; a map may legitimately omit a crowded label.
            ledger.append({"id": feature_id, "label": label, "x_km": x / ppm,
                           "y_km": (size[1] - y) / ppm, "label_drawn": False,
                           "symbol": role, "tags": tags})
            continue
        tx, ty, b = chosen
        # Subtle backing improves readability against dark mountains and rivers
        # without covering large geographic areas or changing marker positions.
        d_label.rounded_rectangle((tx - 5, ty - 5, tx + width + 5, ty + height + 5),
                                  radius=5, fill=(35, 48, 40, 132))
        d_label.text((tx, ty), label, font=font, fill=(253, 244, 215, 255),
                     stroke_fill=DARK, stroke_width=2)
        seen.append(b)
        ledger.append({"id": feature_id, "label": label, "x_km": x / ppm,
                       "y_km": (size[1] - y) / ppm, "label_drawn": True,
                       "symbol": role, "tags": tags})
    return markers, labels, ledger


def _preview(base: Image.Image, *, title: str, ppm: int, data) -> Image.Image:
    width, height = base.size
    border = max(26, ppm * 2)
    header = max(62, ppm * 3)
    footer = max(112, ppm * 5)
    canvas = Image.new("RGB", (width + 2 * border, height + header + footer),
                       (236, 225, 197))
    canvas.paste(base.convert("RGB"), (border, header))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((border - 1, header - 1, border + width, header + height),
                   outline=(74, 67, 52), width=3)
    title_font = _font(max(25, round(ppm * 1.15)))
    annotation_font = _font(max(15, round(ppm * 0.60)))
    draw.text((border + 6, header // 2 - 20), title, font=title_font, fill=(54, 49, 41))
    scale_km = 10
    x0, y = border + 20, header + height + max(15, footer // 3)
    draw.line((x0, y, x0 + scale_km * ppm, y), fill=(41, 45, 39), width=4)
    for xx in (x0, x0 + scale_km * ppm):
        draw.line((xx, y - 6, xx, y + 7), fill=(41, 45, 39), width=2)
    draw.text((x0 + 2, y + 9), f"{scale_km} km", font=annotation_font, fill=(52, 51, 44))
    north_x = border + width - 23
    draw.line((north_x, 42, north_x, 16), fill=(42, 51, 49), width=3)
    draw.polygon(((north_x, 9), (north_x - 7, 23),
                  (north_x + 7, 23)), fill=(42, 51, 49))
    draw.text((north_x - 6, 46), "N", font=annotation_font, fill=(42, 51, 49))
    # Legend describes *only user-supplied tags* and accepted hydrography.
    legend_x = border + width // 3
    legend_y = header + height + 26
    draw.ellipse((legend_x, legend_y - 5, legend_x + 12, legend_y + 7),
                 fill=(244, 222, 169), outline=(43, 51, 41), width=2)
    draw.text((legend_x + 19, legend_y - 9), "Поселение", font=annotation_font, fill=(62, 58, 46))
    fort_x = legend_x + max(170, ppm * 8)
    draw.rectangle((fort_x, legend_y - 5, fort_x + 13, legend_y + 8),
                   fill=(75, 71, 51), outline=(238, 219, 159), width=2)
    draw.text((fort_x + 20, legend_y - 9), "Укрепление", font=annotation_font, fill=(62, 58, 46))
    note = f"Поселений: {sum(isinstance(f, PoiFeature) for f in data.features.values())}  ·  Фрагментов рек: {len(data.networks['rivers'].segments)}"
    draw.text((border + width // 3, legend_y + 37), note,
              font=annotation_font, fill=(70, 67, 58))
    return canvas


def _write_layers(assembly, out: Path, *, ppm: int, request: GenerationRequest) -> dict:
    fields = assembly.field_payloads
    terrain = np.asarray(fields["elevation"])
    rows, cols = terrain.shape
    domain_size = request.domain_spec.domain.size
    w_km = float(domain_size.width_km)
    h_km = float(domain_size.height_km)
    cell_km = float(request.domain_spec.simulation.cell_size_km)
    if not np.isclose(w_km, cols * cell_km) or not np.isclose(h_km, rows * cell_km):
        raise RuntimeError("Exported field/grid dimensions do not match DomainSpec")
    size = (round(w_km * ppm), round(h_km * ppm))
    if min(size) < 150 or max(size) > 6000:
        raise ValueError("Map output size out of supported demo range [150, 6000] px")

    contour_layer, contour_interval_m = _contour_layer(fields, size, ppm=ppm)
    layers = [
        _terrain_layer(fields, size, parchment=False),
        contour_layer,
        _water_layer(assembly.data, fields, size, ppm=ppm),
        _river_layer(assembly.data, size, ppm=ppm),
    ]
    marker, labels, pois = _settlements(assembly.data, size, ppm=ppm)
    layers.extend((marker, labels))
    for filename, layer in zip(MAP_LAYERS, layers):
        layer.save(out / filename)
    composite = layers[0].copy()
    for layer in layers[1:]:
        composite.alpha_composite(layer)
    composite.convert("RGB").save(out / "06-map-full.png")
    no_labels = layers[0].copy()
    for layer in layers[1:-1]:
        no_labels.alpha_composite(layer)
    no_labels.convert("RGB").save(out / "07-map-no-labels.png")
    preview = _preview(composite, title=request.domain_spec.label or request.domain_spec.id,
                       ppm=ppm, data=assembly.data)
    preview.save(out / "08-atlas-preview.png")
    parchment = _terrain_layer(fields, size, parchment=True)
    # Art-friendly source excludes labels so a stylization model cannot
    # silently rewrite settlement names; restore fixed label geometry later.
    for layer in layers[1:-1]:
        parchment.alpha_composite(layer)
    parchment.convert("RGB").save(out / "11-parchment-no-labels.png")
    parchment.alpha_composite(layers[-1])
    parchment.convert("RGB").save(out / "09-parchment-palette.png")

    manifest = {
        "status": "deterministic user-domain cartographic export; presentation only",
        "domain_id": request.domain_spec.id,
        "domain_label": request.domain_spec.label,
        "spec_editable": {
            "surface.water_moisture_decay_km":
                request.domain_spec.surface.water_moisture_decay_km,
            "surface.water_moisture_boost":
                request.domain_spec.surface.water_moisture_boost,
            "features": len(request.domain_spec.features),
            "constraints": len(request.domain_spec.constraints),
        },
        "world_size_km": {"width": w_km, "height": h_km},
        "pixel_size": {"width": size[0], "height": size[1], "pixels_per_km": ppm},
        "axis": "x east, y north; image row 0 is north",
        "aligned_layers": list(MAP_LAYERS),
        "cartographic_elevation_contour_interval_m": contour_interval_m,
        "presentation_palette": "continuous moisture/greenness with strengthened terrain relief",
        "settlements_and_poi": pois,
        "river_segments": len(assembly.data.networks["rivers"].segments),
        "lake_features": sum(isinstance(f, HydroFeature) for f in assembly.data.features.values()),
        "marine_cells": int(np.count_nonzero(fields.get("marine_mask", 0))),
        "limitations": [
            "Color is an artist-oriented continuous moisture/vegetation proxy, not discrete biomes.",
            "No new physical runoff, groundwater, settlements, roads, or procedural POIs are inferred by renderer.",
            "Only existing DomainData point features are marked; label collision avoidance never moves features.",
            "A fully manual fixed-position settlement editor is not implemented by this renderer.",
            "Elevation contour spacing and icon shapes are visual encodings; user-authored tags, not inferred settlement types.",
        ],
    }
    # A compact, reproducible handoff for an OPTIONAL artistic image pass.
    # If an image model changes geography, the authentic RGBA layers remain
    # available for a deterministic final composite.
    named = "; ".join(
        f"{poi['label']} ({poi['x_km']:.2f}, {poi['y_km']:.2f} km)"
        for poi in pois
    )
    art_handoff = (
        f"DOMAIN: {request.domain_spec.label or request.domain_spec.id}\n"
        f"WORLD: {w_km:g} × {h_km:g} km; origin southwest; north is image top.\n"
        f"LANDMARKS: {named}\n\n"
        "STYLE BRIEF (optional, never authoritative geometry):\n"
        "Create an elegant hand-painted fantasy tabletop atlas on warm parchment. "
        "Keep the original coastlines, lake polygons, mountain masses, river "
        "centerlines and settlement coordinates fixed. Improve paper texture, "
        "relief rendering, restrained mountain engraving and color harmony. "
        "Do not invent extra rivers, roads, villages, political boundaries, "
        "biomes or text. Prefer broad artistic texture rather than changing "
        "the geography.\n\n"
        "LAYERS FOR RECOMPOSITING: 01-terrain.png, 10-relief-contours.png, "
        "02-water.png, 03-rivers.png, 04-poi-markers.png, 05-labels.png.\n"
        "BASE FOR STYLIZATION: 11-parchment-no-labels.png; optional clean "
        "color base: 07-map-no-labels.png.\n"
        "CRITICAL: image generation does not guarantee precise geometry. "
        "Compare against 06-map-full.png, and restore original water, rivers, "
        "markers and names from the aligned RGBA layers if needed.\n"
    )
    (out / "12-stylization-brief.txt").write_text(art_handoff, encoding="utf-8")
    manifest["art_direction_files"] = [
        "07-map-no-labels.png",
        "11-parchment-no-labels.png",
        "12-stylization-brief.txt",
    ]
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--presets", type=Path, default=DEFAULT_PRESETS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pixels-per-km", type=int, default=24)
    args = parser.parse_args()
    if args.pixels_per_km < 8 or args.pixels_per_km > 80:
        parser.error("pixels-per-km must be in [8, 80]")

    raw = args.request.read_bytes()
    request = GenerationRequest.model_validate(json.loads(raw.decode("utf-8")))
    catalog = load_preset_catalog(args.presets)
    assembly = generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry_for_request(request, catalog),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    report = _write_layers(assembly, args.output, ppm=args.pixels_per_km, request=request)
    report["request_sha256"] = sha256(raw).hexdigest()
    report["generator_does_not_change_world"] = True
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (args.output / "manifest.json").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
