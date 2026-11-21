from __future__ import annotations

"""P4-A: map-first regional cartographic base, NOT a numerical diagnostic.

Render-only: no rivers, coastlines, lakes, roads, waterfall or story coordinates
are synthesized. Cover labels are hypotheses; color/texture are display data.
All pixel geometry is derived from a north-first P2-A child DEM and P3 cover.
"""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


class CartographicBaseError(ValueError):
    pass


# Muted, differentiated LAND-cover *candidate* colors, not definitive biomes.
COLORS = np.array([
    [121, 125, 122],  # 0: unknown or non-land, NEVER automatically an ocean
    [55, 83, 58],     # 1: woodland candidate
    [166, 166, 119],  # 2: open cover candidate
    [143, 137, 127],  # 3: rocky terrain candidate
    [94, 122, 106],   # 4: wet-lowland candidate, NOT confirmed water
    [161, 146, 111],  # 5: sparse cover candidate
], dtype=np.float64)

LABELS = {
    0: "Не классифицировано", 1: "Лес?", 2: "Открытые земли?",
    3: "Каменистые склоны?", 4: "Влажные низины?",
    5: "Редкая растительность?",
}


def _noise(x: np.ndarray, y: np.ndarray, scale: float, salt: int) -> np.ndarray:
    """Smooth display-only noise tied to explicit kilometre coordinates."""
    x, y = np.broadcast_arrays(x / scale, y / scale)
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    u, v = x - ix, y - iy
    u, v = u*u*(3-2*u), v*v*(3-2*v)

    def value(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        # Deterministic unsigned mix; avoid randomized Python hash().
        z = (a.astype(np.uint64) * np.uint64(0x9E3779B185EBCA87)
             ^ b.astype(np.uint64) * np.uint64(0xC2B2AE3D27D4EB4F)
             ^ np.uint64(salt))
        z ^= z >> np.uint64(30)
        z *= np.uint64(0xBF58476D1CE4E5B9)
        z ^= z >> np.uint64(27)
        z *= np.uint64(0x94D049BB133111EB)
        z ^= z >> np.uint64(31)
        return (z >> np.uint64(11)).astype(float) / (1 << 53) * 2 - 1

    return ((1-v)*((1-u)*value(ix, iy) + u*value(ix+1, iy))
            + v*((1-u)*value(ix, iy+1) + u*value(ix+1, iy+1)))


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _validate(child: dict, cover: dict, child_meta: dict,
              cover_meta: dict, ledger: dict):
    if (child_meta.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or child_meta.get("is_accepted_Core_DomainData") is not False):
        raise CartographicBaseError("P4-A requires explicitly noncanonical P2 child")
    if (cover_meta.get("status") != "P3_MVP_NONCANONICAL_SOURCE_CONDITIONED_COVER"
            or cover_meta.get("cover_is_author_canon") is not False
            or cover_meta.get("wetland_is_confirmed_water") is not False):
        raise CartographicBaseError("P4-A requires explicit unconfirmed P3 cover")
    required = ("child_elevation_m", "land_mask", "east_km", "north_km_north_first")
    if any(k not in child for k in required) or "cover_class_candidate" not in cover:
        raise CartographicBaseError("missing DEM / land / axes / class raster")
    z = np.asarray(child["child_elevation_m"], dtype=float)
    land = np.asarray(child["land_mask"])
    cls = np.asarray(cover["cover_class_candidate"])
    x, y = np.asarray(child["east_km"], dtype=float), np.asarray(child["north_km_north_first"], dtype=float)
    if (z.ndim != 2 or min(z.shape) < 3
            or z.shape != land.shape or z.shape != cls.shape
            or z.shape != (len(y), len(x)) or x.ndim != 1 or y.ndim != 1
            or not np.isfinite(z).all() or not np.isfinite(x).all() or not np.isfinite(y).all()
            or not np.all(np.diff(x) > 0) or not np.all(np.diff(y) < 0)
            or not np.allclose(np.diff(x), x[1]-x[0], atol=1e-6)
            or not np.allclose(np.diff(y), y[1]-y[0], atol=1e-6)
            or not np.isin(cls, np.arange(6)).all()
            or not np.isin(land, [0, 1]).all()):
        raise CartographicBaseError("incoherent north-first grid, mask or class codes")
    if np.any((land == 0) & (cls != 0)):
        raise CartographicBaseError("cannot color nonland as classified land")
    if not np.any(land):
        raise CartographicBaseError("no land coverage in map region")
    if not (isinstance(ledger, dict)
            and isinstance(ledger.get("world", {}).get("name"), str)
            and isinstance(ledger.get("region", {}).get("id"), str)
            and isinstance(ledger.get("landmarks"), list)
            and isinstance(ledger.get("routes"), list)):
        raise CartographicBaseError("explicit author ledger required")
    if any(p.get("position") is not None for p in ledger["landmarks"]):
        # Placement is outside P4-A. Refuse to silently drop fixed landmarks.
        raise CartographicBaseError("P4-A map-only rendering cannot discard positioned POI")
    if any(r.get("polyline_east_north_km") is not None for r in ledger["routes"]):
        raise CartographicBaseError("P4-A map-only rendering cannot discard route geometry")
    return z, land, cls, x, y


def _base_pixels(z: np.ndarray, cls: np.ndarray,
                 x: np.ndarray, y: np.ndarray) -> Image.Image:
    X, Y = np.meshgrid(x, y)
    # Smooth ONLY the displayed class-edge transitions (~0.8 coarse pixel).
    # Stored P3 categories are never edited.
    weights = []
    for k in range(6):
        layer = Image.fromarray(np.uint8(cls == k) * 255, "L")
        blurred = layer.filter(ImageFilter.GaussianBlur(radius=.8))
        weights.append(np.asarray(blurred, dtype=float)/255)
    W = np.stack(weights)
    W /= np.maximum(np.sum(W, axis=0, keepdims=True), 1e-9)
    rgb = np.einsum("kij,kc->ijc", W, COLORS)

    # A subtle multi-frequency paper/satellite-style surface texture; these
    # variations are visual pigment, NOT new landforms or land-cover patches.
    noise = (.53 * _noise(X, Y, 8., 417)
             + .31 * _noise(X, Y, 3.2, 911)
             + .16 * _noise(X, Y, 1.3, 731))
    forest = W[1]; wet = W[4]
    grain = 1 + noise*(.055 + .070*forest + .025*wet)
    rgb *= grain[..., None]

    # Elevation-borne, non-geographic tonal illumination. No new DEM values.
    dx, dy = x[1]-x[0], y[0]-y[1]
    fine = z
    smoothed = np.asarray(Image.fromarray(z.astype("float32"), "F")
                          .filter(ImageFilter.GaussianBlur(radius=4.0)), dtype=float)
    def brightness(a, vertical=33.0):
        north_grad, east_grad = np.gradient(a, dy, dx)
        # Array rows increase southward; north_grad must be negated.
        north_grad = -north_grad
        nx, ny = -east_grad*vertical/1000, -north_grad*vertical/1000
        normal = np.stack([nx, ny, np.ones_like(nx)], axis=-1)
        normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
        light = np.array([-0.57, 0.57, 0.59])
        light /= np.linalg.norm(light)
        return np.clip(np.sum(normal*light, axis=-1), .05, 1)
    light = .72*brightness(fine) + .28*brightness(smoothed, 47.)
    rgb *= np.clip(.80 + .45*(light-.55), .61, 1.19)[..., None]
    # Tiny hypsometric tint to help read mountain mass; it is a display
    # convention, not a rock/vegetation classification.
    lo, hi = np.percentile(z, [5, 95])
    relief = np.clip((z-lo)/max(hi-lo, 1.), 0, 1)**1.7
    rgb = rgb*(1-.075*relief[..., None]) + np.array([185., 173., 149.])*.075*relief[..., None]
    return Image.fromarray(np.uint8(np.clip(np.rint(rgb), 0, 255)), "RGB")


def render_cartographic_base(child: dict, cover: dict, child_meta: dict,
                             cover_meta: dict, ledger: dict, output: Path,
                             *, pixels_per_cell: int = 9) -> dict:
    """One independent map-first product plus provenance; no invented objects."""
    z, land, cls, x, y = _validate(child, cover, child_meta, cover_meta, ledger)
    if not isinstance(pixels_per_cell, int) or not 4 <= pixels_per_cell <= 16:
        raise CartographicBaseError("pixels_per_cell must be an integer 4..16")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise CartographicBaseError("output must be an empty directory")
    base = _base_pixels(z, cls, x, y)
    width = len(x)*pixels_per_cell
    height = len(y)*pixels_per_cell
    map_img = base.resize((width, height), Image.Resampling.BICUBIC)

    # Keep the cartographic image independent from captions, legends and badges.
    top, bottom, margin = 102, 200, 70
    sheet = Image.new("RGB", (width+2*margin, height+top+bottom),
                      (241, 237, 225))
    draw = ImageDraw.Draw(sheet)
    sheet.paste(map_img, (margin, top))
    draw.rectangle([margin-1, top-1, margin+width, top+height],
                   outline=(113, 116, 102), width=2)
    draw.text((margin, 20),
              ledger["world"]["name"] + "  /  РАЙОН " + ledger["region"]["id"],
              font=_font(39), fill=(43, 52, 41))
    draw.text((margin+width-235, 28), "N  ↑",
              font=_font(39), fill=(49, 62, 52))
    # Width is edge-to-edge raster-span, not number of samples: 230 km for 231 nodes.
    total_km = float(x[-1]-x[0])
    length_km = 50 if total_km >= 100 else 10
    bar_px = int(round(width*length_km/total_km))
    start_x, bar_y = margin+34, top+height+57
    draw.rectangle([start_x,bar_y,start_x+bar_px,bar_y+9], fill=(50,62,52))
    draw.text((start_x,bar_y+16), f"{length_km} км", font=_font(24), fill=(49,62,52))
    draw.text((margin+250,top+height+54),
              "Лес?   •   открытые земли?   •   влажные низины?",
              font=_font(24), fill=(65,76,65))
    draw.text((margin,top+height+132),
              "Рабочая картографическая подложка · природный покров гипотетический",
              font=_font(22), fill=(82,91,78))
    draw.text((margin,top+height+165),
              "Речная сеть, дороги и сюжетные ориентиры не размещены",
              font=_font(22), fill=(82,91,78))

    output.mkdir(parents=True, exist_ok=True)
    base_path = output/"region-cartographic-base.png"
    sheet_path = output/"region-cartographic-sheet.png"
    map_img.save(base_path, optimize=True)
    sheet.save(sheet_path, optimize=True)

    result = {
        "status": "P4A_NONCANONICAL_CARTOGRAPHIC_BASE",
        "is_author_canon": False,
        "is_measured_landcover": False,
        "is_verified_hydrology": False,
        "is_verified_road_network": False,
        "coordinates": "x=east km; north-first y; north at image top",
        "image_size_pixels": [width, height],
        "region_km": [float(x[-1]-x[0]), float(y[0]-y[-1])],
        "detail_coordinate_system": child_meta.get("detail_coordinate_system", "UNSPECIFIED"),
        "land_cover_counts": {str(k): int(np.count_nonzero((cls==k)&(land==1)))
                              for k in range(6)},
        "unplaced_landmarks": len(ledger["landmarks"]),
        "unresolved_routes": len(ledger["routes"]),
        "unsupported_or_undrawn": [
            "rivers and flow permanence", "lakes and open water",
            "roads and bridges", "towns and buildings", "waterfalls",
            "story landmarks and travel distances",
        ],
        "rendering_rules": [
            "visual-only blurred class boundaries (~0.8 parent pixels)",
            "display-only world-km texture, no DEM or class mutations",
            "two-scale hillshade derived solely from supplied DEM",
            "no artificial hydrology or new geographic features",
        ],
        "files": [base_path.name, sheet_path.name],
    }
    (output/"region-cartographic-audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n",
        encoding="utf-8",
    )
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("child-npz", "child-manifest", "cover-npz",
                 "cover-manifest", "ledger-json"):
        p.add_argument("--"+name, type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--pixels-per-cell", type=int, default=9)
    a = p.parse_args()
    def read(path):
        with np.load(path, allow_pickle=False) as z:
            return {k: z[k].copy() for k in z.files}
    child = read(a.child_npz)
    cover = read(a.cover_npz)
    cm = json.loads(a.child_manifest.read_text(encoding="utf-8"))
    cv = json.loads(a.cover_manifest.read_text(encoding="utf-8"))
    ledger = json.loads(a.ledger_json.read_text(encoding="utf-8"))
    result = render_cartographic_base(
        child, cover, cm, cv, ledger, a.output,
        pixels_per_cell=a.pixels_per_cell,
    )
    # Full input-byte provenance remains in the external build audit.
    with (a.output/"region-cartographic-audit.json").open("r+", encoding="utf-8") as f:
        result["input_sha256"] = {}
        for name in ("child_npz", "child_manifest", "cover_npz",
                     "cover_manifest", "ledger_json"):
            path = getattr(a, name)
            with path.open("rb") as inp:
                result["input_sha256"][name] = file_digest(inp, "sha256").hexdigest()
        f.seek(0)
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.truncate()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
