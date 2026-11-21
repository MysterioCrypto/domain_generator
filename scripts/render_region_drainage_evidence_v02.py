from __future__ import annotations

"""P4-B: conservative candidate drainage evidence on a P4-A map.

This is NOT a river, lake, perennial-flow or discharge model. Reuse existing
P2-B2.4 Core-MFD dominant channel projection; display only adjacent positive
MFD links that are also downhill on the unfilled original child DEM. Priority
Flood virtual-fill regions, geometric lake proxy jumps, and unresolved outside
crop inflows cannot become visually asserted waterways.
"""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from domain_generator.hydrology.continuous import continuous_routing_field
from domain_generator.hydrology.routing import priority_flood_surfaces


DIRS = ((0, 1), (-1, 1), (-1, 0), (-1, -1),
        (0, -1), (1, -1), (1, 0), (1, 1))


class DrainageEvidenceError(ValueError):
    pass


def _font(size: int):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def screen_candidate_links(child: dict, child_meta: dict, projection: dict,
                           projection_report: dict, map_audit: dict,
                           *, virtual_fill_limit_m: float = 2.,
                           min_display_dominant_area_km2: float = 0.) -> tuple[dict, dict]:
    """Validate topology with *actual Core MFD*; suppress unsupported linework."""
    if (not np.isfinite(virtual_fill_limit_m) or virtual_fill_limit_m < 0
            or virtual_fill_limit_m > 100):
        raise DrainageEvidenceError("finite virtual_fill_limit_m 0..100 required")
    if (not np.isfinite(min_display_dominant_area_km2)
            or min_display_dominant_area_km2 < 0):
        raise DrainageEvidenceError("finite nonnegative minimum display area required")
    if (child_meta.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or child_meta.get("is_accepted_Core_DomainData") is not False):
        raise DrainageEvidenceError("noncanonical P2 child manifest required")
    if (map_audit.get("status") != "P4A_NONCANONICAL_CARTOGRAPHIC_BASE"
            or map_audit.get("is_author_canon") is not False):
        raise DrainageEvidenceError("P4-A cartographic source audit required")
    if (projection_report.get("status")
            != "P2_B2_4_REFERENCE_EXIT_ALIGNMENT_NOT_ACCEPTED_HYDROLOGY"
            or projection_report.get("is_author_approved_local_river_map") is not False
            or projection_report.get("is_accepted_Core_DomainData") is not False
            or float(projection_report.get("external_area_auto_injected_km2", -1)) != 0):
        raise DrainageEvidenceError("noncanonical P2-B2.4 projection with zero implicit external area required")
    ledger = projection_report.get("child_core_dominant_channel_ledger", {})
    if (ledger.get("status")
            != "CONNECTED_CORE_DOMINANT_MFD_CHANNEL_PROJECTION_NOT_REAL_RIVERS"
            or ledger.get("is_physical_discharge_or_approved_river") is not False
            or ledger.get("no_external_A8_source_area_auto_injected") is not True):
        raise DrainageEvidenceError("unverified Core-derived channel skeleton ledger required")
    if (map_audit.get("detail_coordinate_system") !=
            child_meta.get("detail_coordinate_system")):
        raise DrainageEvidenceError("source map and child have different terrain coordinate mode")

    z = np.asarray(child["child_elevation_m"], dtype=np.float64)
    east = np.asarray(child["east_km"], dtype=np.float64)
    north = np.asarray(child["north_km_north_first"], dtype=np.float64)
    if (z.ndim != 2 or min(z.shape) < 3 or z.shape != (len(north), len(east))
            or not np.isfinite(z).all() or not np.isfinite(east).all()
            or not np.isfinite(north).all() or not np.all(np.diff(east) > 0)
            or not np.all(np.diff(north) < 0)):
        raise DrainageEvidenceError("invalid north-first child DEM/axes")
    spacing = float(np.median(np.diff(east)))
    if (spacing <= 0 or not np.allclose(np.diff(east), spacing)
            or not np.allclose(-np.diff(north), spacing)):
        raise DrainageEvidenceError("Core MFD requires uniform square kilometre grid")
    if map_audit.get("image_size_pixels") is None:
        raise DrainageEvidenceError("missing geographic map pixel dimensions")
    rows, cols = z.shape
    shape = (rows, cols)
    mask = np.asarray(projection.get("channel_mask"))
    lakes = np.asarray(projection.get("lake_proxy_mask"))
    receiver = np.asarray(projection.get("Core_dominant_receiver_index"))
    edges = np.asarray(projection.get("channel_edge_flat_from_to"))
    jumps = np.asarray(projection.get("lake_proxy_jumps_flat_from_to"))
    dominant_area = np.asarray(projection.get("Core_dominant_channel_area_km2_NOT_Q"))
    if (mask.shape != shape or lakes.shape != shape or receiver.shape != shape
            or mask.dtype.kind not in "biu" or lakes.dtype.kind not in "biu"
            or not np.isin(mask, [0, 1]).all() or not np.isin(lakes, [0, 1]).all()
            or np.any((mask != 0) & (lakes != 0))
            or receiver.dtype.kind not in "iu" or np.any(receiver >= z.size)
            or np.any(receiver < -1)):
        raise DrainageEvidenceError("projection masks/receivers invalid")
    if (dominant_area.shape != shape
            or dominant_area.dtype.kind not in "fi"
            or not np.isfinite(dominant_area).all()
            or np.any(dominant_area < 0)):
        raise DrainageEvidenceError("invalid Core dominant-channel area proxy")
    if edges.ndim != 2 or edges.shape[1] != 2 or edges.dtype.kind not in "iu":
        raise DrainageEvidenceError("expected integer (N,2) Core channel edges")
    if jumps.ndim != 2 or jumps.shape[1] != 2 or jumps.dtype.kind not in "iu":
        raise DrainageEvidenceError("expected integer (N,2) excluded proxy links")
    if (np.any(edges < 0) or np.any(edges >= z.size)
            or np.any(jumps < 0) or np.any(jumps >= z.size)):
        raise DrainageEvidenceError("edge receiver outside child raster")
    if np.unique(edges[:, 0]).size != len(edges):
        raise DrainageEvidenceError("a dominant channel node has multiple receivers")
    if len(set(map(tuple, edges)) & set(map(tuple, jumps))):
        raise DrainageEvidenceError("a physical line overlaps an excluded lake proxy jump")
    if int(ledger.get("ordinary_adjacent_channel_edges", -1)) != len(edges):
        raise DrainageEvidenceError("projection edge count contradicts its ledger")
    if int(ledger.get("nonphysical_proxy_links_NOT_RIVERS", -1)) != len(jumps):
        raise DrainageEvidenceError("lake proxy ledger mismatch")

    routing = priority_flood_surfaces(z)
    flow = continuous_routing_field(routing.routing_elevation_m,
                                    cell_size_km=spacing)
    fill = np.maximum(0., routing.fill_elevation_m - z)
    uncertain = (fill > virtual_fill_limit_m) | (lakes != 0)
    safe_links, withheld = [], []
    seen = set()
    for src, dst in edges:
        sr, sc = divmod(int(src), cols)
        tr, tc = divmod(int(dst), cols)
        off = (tr-sr, tc-sc)
        if (src == dst or off not in DIRS
                or mask[sr, sc] == 0 or lakes[sr, sc] or lakes[tr, tc]
                or int(receiver[sr, sc]) != int(dst)):
            raise DrainageEvidenceError("non-adjacent or unsupported ordinary channel link")
        k = DIRS.index(off)
        if (not flow.fractions[sr, sc, k] > 0
                or not routing.routing_elevation_m[tr, tc] <
                    routing.routing_elevation_m[sr, sc]):
            raise DrainageEvidenceError("candidate edge is not a positive downhill Core MFD link")
        if (uncertain[sr, sc] or uncertain[tr, tc]
                or not z[tr, tc] < z[sr, sc]):
            withheld.append((int(src), int(dst)))
        else:
            safe_links.append((int(src), int(dst)))
        if int(src) in seen:
            raise DrainageEvidenceError("multiple ordinary downstream edges")
        seen.add(int(src))

    # Display-thresholding changes ONLY visual sampling, never physical graph,
    # routing, acceptance or the fully preserved strict-downhill evidence.
    safe_all = np.asarray(safe_links, dtype=np.int32).reshape(-1, 2)
    chosen = [link for link in safe_links
              if dominant_area.ravel()[link[0]] >= min_display_dominant_area_km2]
    minor = [link for link in safe_links
             if dominant_area.ravel()[link[0]] < min_display_dominant_area_km2]
    safe = np.asarray(chosen, dtype=np.int32).reshape(-1, 2)
    minor_hidden = np.asarray(minor, dtype=np.int32).reshape(-1, 2)
    hidden = np.asarray(withheld, dtype=np.int32).reshape(-1, 2)
    masks = {
        "all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS": safe_all,
        "candidate_display_edges_NOT_CONFIRMED_RIVERS": safe,
        "omitted_minor_strict_edges_NOT_DISPLAYED": minor_hidden,
        "withheld_ordinary_edges_NOT_DISPLAYED": hidden,
        "lake_proxy_jumps_NOT_RIVERS": jumps.astype(np.int32),
        "virtual_fill_uncertainty_mask_NOT_WATER": uncertain.astype(np.uint8),
    }
    audit = {
        "status": "P4B_CONSERVATIVE_DRAINAGE_EVIDENCE_NOT_CANONICAL_RIVERS",
        "is_accepted_hydrology": False,
        "is_water_occupancy_or_discharge": False,
        "is_verified_macro_to_child_basin": False,
        "is_cartographic_rendered_only": True,
        "child_shape": [rows, cols],
        "spacing_km": spacing,
        "detail_coordinate_system": child_meta["detail_coordinate_system"],
        "source_status": projection_report["status"],
        "source_lake_topology_status": ledger["lake_topology_status"],
        "source_external_inflow_km2_applied": 0.,
        "raw_candidate_ordinary_edges": len(edges),
        "all_strictly_downhill_edges": len(safe_all),
        "displayable_strictly_downhill_edges": len(safe),
        "omitted_minor_strict_edges_display_only": len(minor_hidden),
        "display_minimum_dominant_area_km2_NOT_Q": min_display_dominant_area_km2,
        "withheld_unsafe_ordinary_edges": len(hidden),
        "undrawn_geometric_lake_proxy_jumps": len(jumps),
        "unresolved_fill_cells_over_limit": int(np.count_nonzero(fill > virtual_fill_limit_m)),
        "max_virtual_fill_m_NOT_LAKE_DEPTH": float(np.max(fill)),
        "virtual_fill_limit_m_display_only": virtual_fill_limit_m,
        "one_receiver_projection_not_perennial_water": True,
        "unknown_external_crop_inflows": True,
        "river_continuity_across_withheld_edges": "NOT_ESTABLISHED",
        "unsupported": [
            "macro A8 D8 as river authority", "discharge, baseflow or permanence",
            "lake or wetland water occupancy", "river connectivity through proxy lakes",
            "cross-boundary catchment identity", "story place and route placement",
        ],
    }
    return masks, audit


def render_evidence(base: Image.Image, child: dict, masks: dict, audit: dict) -> tuple[Image.Image, Image.Image]:
    z = np.asarray(child["child_elevation_m"])
    rows, cols = z.shape
    if base.mode != "RGB" or base.width % cols or base.height % rows:
        raise DrainageEvidenceError("map pixel dimensions do not align with DEM")
    sx, sy = base.width/cols, base.height/rows
    if abs(sx-sy) > 1e-6:
        raise DrainageEvidenceError("non-square map-to-DEM pixels")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # A pale-violet WARNING overlay marks unresolved virtual filling / proxy
    # regions, never actual standing water.
    for r, c in np.argwhere(masks["virtual_fill_uncertainty_mask_NOT_WATER"] != 0):
        draw.rectangle([int(c*sx), int(r*sy),
                        int((c+1)*sx), int((r+1)*sy)], fill=(160, 63, 125, 53))
    w = max(1, int(round(sx*.32)))
    for src, dst in masks["candidate_display_edges_NOT_CONFIRMED_RIVERS"]:
        sr, sc = divmod(int(src), cols)
        tr, tc = divmod(int(dst), cols)
        a = ((sc+.5)*sx, (sr+.5)*sy)
        b = ((tc+.5)*sx, (tr+.5)*sy)
        # Ochre lines distinguish uncertain valley-channel skeletons from water.
        draw.line([a, b], fill=(230, 187, 94, 220), width=w)
    merged = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    margin, top, foot = 54, 92, 200
    page = Image.new("RGB", (merged.width+2*margin,
                              merged.height+top+foot), (241, 237, 225))
    page.paste(merged, (margin, top))
    pen = ImageDraw.Draw(page)
    pen.rectangle([margin-1, top-1, margin+merged.width,
                   top+merged.height], outline="#6a6a5a", width=2)
    pen.text((margin, 18), "ОСВЕРА / РАЙОН A — ДРЕНАЖНЫЕ ГИПОТЕЗЫ",
             font=_font(27), fill="#353e36")
    pen.text((merged.width+margin-125, 24), "N ↑",
             font=_font(26), fill="#353e36")
    y = top+merged.height+27
    pen.rectangle((margin+4, y+5, margin+29, y+23), fill="#e6bb5e")
    threshold = audit["display_minimum_dominant_area_km2_NOT_Q"]
    legend = ("Кандидатный сток, НЕ река" if threshold == 0 else
              f"Кандидатный сток от {threshold:g} км², НЕ река")
    pen.text((margin+38, y-2), legend,
             font=_font(21), fill="#343e35")
    y += 38
    pen.rectangle((margin+4, y+5, margin+29, y+23), fill="#ad819c")
    pen.text((margin+38, y-2), "Неопределённые чаши и виртуальное заполнение",
             font=_font(19), fill="#343e35")
    y += 42
    pen.text((margin+4, y), "Внешние притоки и водность не установлены",
             font=_font(20), fill="#394539")
    y += 35
    pen.text((margin+4, y), "Геометрия только из существующих данных Core MFD",
             font=_font(19), fill="#586357")
    return merged, page


def build_evidence(child: dict, child_meta: dict, projection: dict,
                   projection_report: dict, base: Image.Image, map_audit: dict,
                   output: Path, *, virtual_fill_limit_m: float = 2.,
                   min_display_dominant_area_km2: float = 0.) -> dict:
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise DrainageEvidenceError("output must be empty")
    masks, audit = screen_candidate_links(
        child, child_meta, projection, projection_report, map_audit,
        virtual_fill_limit_m=virtual_fill_limit_m,
        min_display_dominant_area_km2=min_display_dominant_area_km2)
    if list(base.size) != map_audit["image_size_pixels"]:
        raise DrainageEvidenceError("P4-A image and audit pixel sizes disagree")
    layer, sheet = render_evidence(base, child, masks, audit)
    output.mkdir(parents=True, exist_ok=True)
    layer.save(output/"drainage-evidence-map.png", optimize=True)
    sheet.save(output/"drainage-evidence-sheet.png", optimize=True)
    np.savez_compressed(output/"drainage-evidence-masks.npz", **masks)
    (output/"drainage-evidence-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("child-npz", "child-manifest", "projection-npz",
                 "projection-manifest", "p4a-image", "p4a-audit"):
        p.add_argument("--"+name, type=Path, required=True)
    p.add_argument("--virtual-fill-limit-m", type=float, default=2.)
    p.add_argument("--min-display-dominant-area-km2", type=float, default=0.)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    def read(path):
        with np.load(path, allow_pickle=False) as npz:
            return {k: npz[k].copy() for k in npz.files}
    child = read(args.child_npz)
    projection = read(args.projection_npz)
    child_meta = json.loads(args.child_manifest.read_text(encoding="utf-8"))
    projection_meta = json.loads(args.projection_manifest.read_text(encoding="utf-8"))
    map_audit = json.loads(args.p4a_audit.read_text(encoding="utf-8"))
    p4_child_sha = map_audit.get("input_sha256", {}).get("child_npz")
    if not isinstance(p4_child_sha, str) or len(p4_child_sha) != 64:
        raise DrainageEvidenceError("P4-A audit missing source child-NPZ SHA-256; cannot align maps")
    with args.child_npz.open("rb") as inp:
        actual_child_sha = file_digest(inp, "sha256").hexdigest()
    if actual_child_sha != p4_child_sha:
        raise DrainageEvidenceError("P4-A source child-NPZ hash differs from candidate DEM")
    with Image.open(args.p4a_image) as im:
        img = im.convert("RGB")
    audit = build_evidence(
        child, child_meta, projection, projection_meta, img, map_audit,
        args.output, virtual_fill_limit_m=args.virtual_fill_limit_m,
        min_display_dominant_area_km2=args.min_display_dominant_area_km2)
    audit["p4a_child_npz_sha256_lineage_verified"] = True
    audit["projection_child_bitwise_sha256_lineage_verified"] = False
    audit["input_sha256"] = {}
    for key in ("child_npz", "child_manifest", "projection_npz",
                "projection_manifest", "p4a_image", "p4a_audit"):
        with getattr(args, key).open("rb") as f:
            audit["input_sha256"][key] = file_digest(f, "sha256").hexdigest()
    (args.output/"drainage-evidence-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
