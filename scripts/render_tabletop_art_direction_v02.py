from __future__ import annotations

"""Art-direction proof over canonical, pixel-aligned tabletop map layers.

This is deterministic raster styling, NOT image generation. All accepted coast,
lake, river, point and label layers are composited UNMODIFIED on top of styled
terrain. It tests the practical handoff for later optional imagegen.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


OVERLAYS = (
    "10-relief-contours.png",
    "02-water.png",
    "03-rivers.png",
    "04-poi-markers.png",
    "05-labels.png",
)
STYLES = (
    ("watercolour", "Акварельная карта"),
    ("engraving", "Старинная гравюра"),
    ("illuminated", "Цветной манускрипт"),
)


def _font(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _noise(width: int, height: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    layers = (
        (max(2, width // 85), max(2, height // 85), 0.55),
        (max(2, width // 14), max(2, height // 14), 0.27),
        (max(2, width // 3), max(2, height // 3), 0.18),
    )
    result = np.zeros((height, width), dtype=np.float32)
    for w, h, weight in layers:
        tile = Image.fromarray(
            np.asarray(rng.integers(0, 256, (h, w), dtype=np.uint8)), "L"
        )
        upscaled = tile.resize((width, height), Image.Resampling.BILINEAR)
        result += (np.asarray(upscaled, dtype=np.float32) - 127.5) * weight / 127.5
    return result


def _style_terrain(original: Image.Image, name: str, *, seed: int) -> Image.Image:
    width, height = original.size
    if name == "watercolour":
        # Blurred pigment edges only in the TERRAIN layer. Overlays remain exact.
        softened = original.filter(ImageFilter.GaussianBlur(2.4))
        base = Image.blend(original, softened, 0.28)
        base = ImageEnhance.Color(base).enhance(0.89)
        rgb = np.asarray(base.convert("RGB"), dtype=np.float32) / 255.0
        paper = np.array([0.976, 0.964, 0.915], dtype=np.float32)
        rgb = rgb * 0.86 + paper[None, None, :] * 0.14
        texture = _noise(width, height, seed + 3)
        rgb += texture[..., None] * 0.032
    elif name == "engraving":
        base = np.asarray(original.convert("RGB"), dtype=np.float32) / 255.0
        lightness = 0.25 * base[..., 0] + 0.62 * base[..., 1] + 0.13 * base[..., 2]
        tint = np.array([0.96, 0.88, 0.69], dtype=np.float32)
        sepia = np.stack((lightness * 0.90 + 0.09,
                          lightness * 0.78 + 0.14,
                          lightness * 0.61 + 0.21), axis=-1)
        rgb = sepia * 0.83 + tint[None, None, :] * 0.17
        # Very fine engraving strokes on dark relief only; they must never
        # represent newly invented forests, roads or watershed boundaries.
        yy, xx = np.indices((height, width), dtype=np.int32)
        ink_mask = (lightness < 0.69) & (((xx + yy) % 9) <= 1)
        rgb[ink_mask] *= 0.83
        texture = _noise(width, height, seed + 9)
        rgb += texture[..., None] * 0.028
    elif name == "illuminated":
        base = ImageEnhance.Color(original).enhance(1.31)
        base = ImageEnhance.Contrast(base).enhance(1.08)
        rgb = np.asarray(base.convert("RGB"), dtype=np.float32) / 255.0
        rgb = rgb * np.array([1.09, 1.035, 0.96], dtype=np.float32)[None, None, :]
        texture = _noise(width, height, seed + 17)
        rgb += texture[..., None] * 0.019
    else:
        raise ValueError(f"Unknown terrain-only visual style: {name}")
    rgb = np.clip(rgb, 0, 1)
    return Image.fromarray(np.round(rgb * 255.0).astype(np.uint8), "RGB").convert("RGBA")


def _compose(terrain: Image.Image, overlays: dict[str, Image.Image]) -> Image.Image:
    out = terrain.copy()
    for name in OVERLAYS:
        out.alpha_composite(overlays[name])
    return out.convert("RGB")


def _bordered_map(
    field: Image.Image, *,
    title: str, style: str, ppm: int, count: int
) -> Image.Image:
    width, height = field.size
    margin = 57
    top, bottom = 102, 120
    background = (
        (233, 224, 191) if style == "engraving"
        else (236, 225, 200) if style == "watercolour"
        else (218, 206, 165)
    )
    art = Image.new("RGB", (width + margin * 2, height + top + bottom), background)
    art.paste(field, (margin, top))
    draw = ImageDraw.Draw(art)
    ink = (69, 59, 45)
    gold = (145, 115, 65)
    rect = (margin - 4, top - 4, margin + width + 4, top + height + 4)
    draw.rectangle(rect, outline=ink, width=4)
    draw.rectangle((margin - 12, top - 12, margin + width + 12, top + height + 12),
                   outline=gold, width=2)
    for x in (margin - 12, margin + width + 12):
        for y in (top - 12, top + height + 12):
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=gold, outline=ink, width=1)
    draw.text((margin + 4, 30), title, font=_font(32), fill=ink)
    draw.text((margin + 6, 72), "Картографическая стилизация · исходная география сохранена",
              font=_font(16), fill=(94, 80, 63))
    x0, y0 = margin + 18, top + height + 46
    draw.line((x0, y0, x0 + ppm * 10, y0), fill=ink, width=4)
    draw.line((x0, y0 - 6, x0, y0 + 6), fill=ink, width=2)
    draw.line((x0 + ppm * 10, y0 - 6, x0 + ppm * 10, y0 + 6), fill=ink, width=2)
    draw.text((x0, y0 + 15), "10 км", font=_font(17), fill=ink)
    draw.text((margin + 400, y0 - 10),
              f"{count} поселения/точки · реки и озёра из исходного домена",
              font=_font(17), fill=ink)
    north_x = margin + width - 35
    draw.polygon(((north_x, 22), (north_x - 10, 52), (north_x + 10, 52)),
                 fill=ink)
    draw.text((north_x - 8, 56), "N", font=_font(19), fill=ink)
    return art


def _contact_sheet(styled: dict[str, Image.Image], target: Path) -> None:
    thumb_width, thumb_height = 640, 480
    margin, heading, footer = 20, 66, 67
    sheet = Image.new(
        "RGB",
        (len(STYLES) * thumb_width + (len(STYLES) + 1) * margin,
         thumb_height + heading + footer),
        (235, 226, 206),
    )
    font = _font(22)
    annotation = _font(17)
    draw = ImageDraw.Draw(sheet)
    for index, (style, title) in enumerate(STYLES):
        x0 = margin + index * (thumb_width + margin)
        image = styled[style].resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        sheet.paste(image, (x0, heading))
        draw.text((x0 + 6, 21), title, fill=(58, 54, 43), font=font)
        draw.rectangle((x0 - 1, heading - 1, x0 + thumb_width, heading + thumb_height),
                       outline=(86, 76, 57), width=2)
    draw.text((margin, heading + thumb_height + 22),
              "Одинаковые реки, озёра и поселения; меняется только визуальный стиль суши.",
              fill=(77, 71, 59), font=annotation)
    sheet.save(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    atlas = args.atlas
    args.output.mkdir(parents=True, exist_ok=True)

    original_manifest = json.loads((atlas / "manifest.json").read_text(encoding="utf-8"))
    source = Image.open(atlas / "01-terrain.png").convert("RGBA")
    size = source.size
    if size != (original_manifest["pixel_size"]["width"], original_manifest["pixel_size"]["height"]):
        raise RuntimeError("Layer image size conflicts with source atlas manifest")
    if set(OVERLAYS) - set(original_manifest["aligned_layers"]):
        raise RuntimeError("Missing authoritative water/river/POI/label layer in manifest")
    overlays: dict[str, Image.Image] = {}
    canonical_hashes = {}
    for name in OVERLAYS:
        path = atlas / name
        rgba = Image.open(path).convert("RGBA")
        if rgba.size != size:
            raise RuntimeError(f"Canonical overlay {name} has mismatched dimensions")
        overlays[name] = rgba
        canonical_hashes[name] = _digest(path)

    seed = int(original_manifest["request_sha256"][:8], 16)
    title = original_manifest.get("domain_label") or original_manifest["domain_id"]
    ppm = int(original_manifest["pixel_size"]["pixels_per_km"])
    result = {}
    names = {}
    for index, (name, heading) in enumerate(STYLES, 1):
        terrain = _style_terrain(source, name, seed=seed)
        composed = _compose(terrain, overlays)
        base_name = f"0{index}-{name}-map.png"
        composed.save(args.output / base_name)
        frame_name = f"0{index + 3}-{name}-framed.png"
        _bordered_map(
            composed, title=title, style=name, ppm=ppm,
            count=len(original_manifest["settlements_and_poi"])
        ).save(args.output / frame_name)
        result[name] = composed
        names[name] = {"map": base_name, "framed": frame_name}

    _contact_sheet(result, args.output / "07-three-style-comparison.png")

    if any(_digest(atlas / name) != expected for name, expected in canonical_hashes.items()):
        raise RuntimeError("Source overlay unexpectedly modified during styling")

    report = {
        "checkpoint": "deterministic art-direction proof, NOT generative image modeling",
        "domain_id": original_manifest["domain_id"],
        "domain_label": title,
        "request_sha256": original_manifest["request_sha256"],
        "pixel_size": original_manifest["pixel_size"],
        "styles": names,
        "contact_sheet": "07-three-style-comparison.png",
        "canonical_immutable_overlays_sha256": canonical_hashes,
        "authoritative_overlays_are_unmodified": True,
        "settlements_and_poi": original_manifest["settlements_and_poi"],
        "river_segments": original_manifest["river_segments"],
        "lake_features": original_manifest["lake_features"],
        "terrain_changes_only_presentation": True,
        "imagegen_performed": False,
        "limitations": (
            "This controlled test applies algorithmic visual styles to terrain only; "
            "it does not demonstrate that an independent image generator preserves geometry. "
            "Keep canonical water/river/markers/labels as aligned overlays for any "
            "future image-generation art pass."
        ),
    }
    serialized = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    (args.output / "report.json").write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
