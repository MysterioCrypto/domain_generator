from __future__ import annotations

"""P2-B2.5: bounded, OPTIONAL source-guided river-corridor DEM TRIAL.

Creates a new, explicitly noncanonical candidate DEM from old A8 river LINKS.
Never edits original child files or silently accepts changed relief.

- All original macro DEM station heights remain mathematically exact.
- The numeric correction is negative only, finite and locally bounded.
- Region boundary elevations remain unchanged.
- Old A8 river line is a COARSE GEOMETRIC PRIOR, NOT a validated local channel.
- Any MFD geometry gain is diagnostic, not a proof of basin identity or Q.
"""

import argparse
import json
from math import cos, pi, radians
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource

if __package__:
    from scripts.compare_planetary_child_mfd_outlets_v02 import analyze_outlets
else:
    from compare_planetary_child_mfd_outlets_v02 import analyze_outlets


class CorridorConditioningError(ValueError):
    pass


def macro_river_segments(
    macro: dict[str, np.ndarray], *,
    center_lat: float, center_lon: float, planet_radius_km: float,
) -> tuple[tuple[tuple[float, float], tuple[float, float]], ...]:
    """Old A8 D8 *river-mask* links in child-local coordinates; no new links."""
    lat = np.asarray(macro["latitude_deg_north_first"], dtype=float)
    lon = np.asarray(macro["longitude_deg_west_to_east"], dtype=float)
    river = np.asarray(macro["source_river_mask_D8"], dtype=bool)
    down = np.asarray(macro["local_downstream_index"])
    if (lat.ndim != 1 or lon.ndim != 1
            or min(len(lat), len(lon)) < 3
            or not np.all(np.diff(lat) < 0)
            or not np.all(np.diff(lon) > 0)
            or river.shape != (len(lat), len(lon))
            or down.shape != river.shape
            or not np.issubdtype(down.dtype, np.integer)
            or not np.isfinite(lat).all()
            or not np.isfinite(lon).all()
            or np.any(down < -1) or np.any(down >= down.size)):
        raise CorridorConditioningError("invalid aligned original A8 macro D8 links")
    if not(np.isfinite(planet_radius_km) and planet_radius_km > 0
           and np.isfinite(center_lat) and abs(center_lat) < 80
           and np.isfinite(center_lon)):
        raise CorridorConditioningError("invalid non-Earth world coordinates")
    unit = pi * planet_radius_km / 180
    xs = (lon - center_lon) * unit * cos(radians(center_lat))
    ys = (lat - center_lat) * unit
    cols = len(lon)
    lines = []
    for r, c in np.argwhere(river & (down >= 0)):
        tr, tc = divmod(int(down[r, c]), cols)
        if r == tr and c == tc:
            raise CorridorConditioningError("A8 river self-loop")
        lines.append((
            (float(xs[c]), float(ys[r])),
            (float(xs[tc]), float(ys[tr])),
        ))
    return tuple(lines)


def _nearest_station_distance(
    xx: np.ndarray, yy: np.ndarray, xnodes: np.ndarray, ynodes: np.ndarray,
) -> np.ndarray:
    def one_dim(coord, nodes):
        nodes = np.sort(np.asarray(nodes, dtype=float))
        idx = np.searchsorted(nodes, coord)
        a = nodes[np.clip(idx, 0, len(nodes) - 1)]
        b = nodes[np.clip(idx - 1, 0, len(nodes) - 1)]
        return np.minimum(np.abs(coord-a), np.abs(coord-b))
    return np.hypot(one_dim(xx, xnodes), one_dim(yy, ynodes))


def bounded_corridor_delta(
    xx: np.ndarray, yy: np.ndarray,
    *,
    segments: tuple,
    xnodes: np.ndarray,
    ynodes: np.ndarray,
    bounds: tuple[float, float, float, float],
    depth_m: float,
    width_km: float,
    anchor_taper_km: float,
    boundary_taper_km: float,
) -> np.ndarray:
    """Evaluate mathematical correction at ANY coordinate, not just pixels.

    Exact macro-station anchors follow from g(distance_to_source_node=0)=0.
    At box edge, border envelope =0; neither boundary pixels nor coast are
    silently dragged toward the old coarse river.
    """
    values = (depth_m, width_km, anchor_taper_km, boundary_taper_km)
    if not all(np.isfinite(v) and v > 0 for v in values):
        raise CorridorConditioningError("depth/width/tapers must be finite positive")
    x, y = np.broadcast_arrays(np.asarray(xx, dtype=float),
                               np.asarray(yy, dtype=float))
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise CorridorConditioningError("nonfinite local evaluation coordinates")
    if not segments:
        return np.zeros(x.shape, dtype=float)
    if not len(xnodes) or not len(ynodes):
        raise CorridorConditioningError("missing original DEM anchor coordinate axes")
    squared = np.full(x.shape, np.inf, dtype=float)
    for (x0, y0), (x1, y1) in segments:
        dx, dy = x1-x0, y1-y0
        if dx*dx+dy*dy < 1e-10:
            continue
        t = np.clip(((x-x0)*dx+(y-y0)*dy)/(dx*dx+dy*dy), 0, 1)
        squared = np.minimum(squared, (x-(x0+t*dx))**2+(y-(y0+t*dy))**2)
    nearest = _nearest_station_distance(x, y, xnodes, ynodes)
    anchor_factor = 1-np.exp(-.5*(nearest/anchor_taper_km)**2)
    xmin, xmax, ymin, ymax = bounds
    edge_distance = np.minimum.reduce((
        x-xmin, xmax-x, y-ymin, ymax-y
    ))
    u = np.clip(edge_distance/boundary_taper_km, 0, 1)
    edge_factor = u*u*(3-2*u)
    return (-depth_m*np.exp(-.5*squared/(width_km**2))
            *anchor_factor*edge_factor)


def candidate_corridor_terrain(
    child: dict[str, np.ndarray], macro: dict[str, np.ndarray],
    manifest: dict, *, depth_m: float = 15., width_km: float = 5.,
    anchor_taper_km: float = 2., boundary_taper_km: float = 5.,
) -> tuple[dict[str, np.ndarray], dict]:
    """Make immutable child-DEM trial, never accept as real river/lake."""
    if (manifest.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or manifest.get("is_accepted_Core_DomainData") is not False):
        raise CorridorConditioningError("requires noncanonical source-conditioned child")
    height = np.asarray(child["child_elevation_m"], dtype=float)
    land = np.asarray(child["land_mask"], dtype=bool)
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    if (height.ndim != 2 or min(height.shape) < 5 or height.shape != land.shape
            or height.shape != (len(north), len(east))
            or not np.isfinite(height).all()
            or not np.all(np.diff(east) > 0)
            or not np.all(np.diff(north) < 0)
            or not np.all(land)):
        raise CorridorConditioningError("inland-only, regular north-first finite child DEM required")
    center_lat, center_lon = map(float, manifest["center_lat_lon_deg"])
    radius = float(manifest["planet_radius_km"])
    if not np.isfinite(radius) or radius <= 0:
        raise CorridorConditioningError("positive world radius required")
    segments = macro_river_segments(
        macro, center_lat=center_lat, center_lon=center_lon,
        planet_radius_km=radius,
    )
    original_lat = np.asarray(macro["latitude_deg_north_first"], dtype=float)
    original_lon = np.asarray(macro["longitude_deg_west_to_east"], dtype=float)
    unit = pi*radius/180
    nx = (original_lon-center_lon)*unit*cos(radians(center_lat))
    ny = (original_lat-center_lat)*unit
    bounds = (float(east[0]), float(east[-1]),
              float(north[-1]), float(north[0]))
    X, Y = np.meshgrid(east, north)
    raw = bounded_corridor_delta(
        X, Y, segments=segments, xnodes=nx, ynodes=ny, bounds=bounds,
        depth_m=depth_m, width_km=width_km,
        anchor_taper_km=anchor_taper_km,
        boundary_taper_km=boundary_taper_km,
    )
    # Never create a sea or change coast sign in this INLAND-only trial.
    raw = np.maximum(raw, -(height*0.45))
    proposed = (height+raw).astype(np.float32)
    changed = proposed.astype(float)-height
    original_edge = (np.concatenate((height[0],height[-1],
                                     height[1:-1,0],height[1:-1,-1])))
    proposal_edge = (np.concatenate((proposed[0],proposed[-1],
                                     proposed[1:-1,0],proposed[1:-1,-1])))
    if not np.array_equal(original_edge, proposal_edge):
        raise CorridorConditioningError("boundary heights changed in conditioning trial")
    if not np.array_equal(proposed >= 0, height >= 0):
        raise CorridorConditioningError("conditioning trial changed land/sea sign")
    if np.min(changed) < -depth_m-1e-4 or np.max(changed) > 1e-4:
        raise CorridorConditioningError("trial exceeds bounded excavation or raises terrain")
    # Compare DEM elevations at ORIGINAL STATION COORDINATES analytically.
    pxx, pyy = np.meshgrid(nx, ny)
    anchor_correction = bounded_corridor_delta(
        pxx, pyy, segments=segments, xnodes=nx, ynodes=ny,
        bounds=bounds, depth_m=depth_m, width_km=width_km,
        anchor_taper_km=anchor_taper_km,
        boundary_taper_km=boundary_taper_km,
    )
    if np.max(np.abs(anchor_correction)) > 1e-9:
        raise CorridorConditioningError("original A8/A12 DEM station anchor moved")
    out = dict(child)
    out["child_elevation_m"] = proposed
    return {
        "new_child_elevation_m": proposed,
        "source_guidance_delta_m": changed.astype(np.float32),
        "old_source_river_distance_weighted_strength": (-raw/depth_m).astype(np.float32),
    }, {
        "status": "P2_B2_5_OPTIONAL_NONCANONICAL_DEM_TRIAL",
        "original_macro_river_segments": len(segments),
        "source_anchor_correction_error_m": float(np.max(np.abs(anchor_correction))),
        "source_boundary_max_change_m": float(np.max(np.abs(original_edge-proposal_edge))),
        "maximum_excavation_m": float(-np.min(changed)),
        "modified_child_pixels": int(np.count_nonzero(changed < -1e-5)),
        "relief_correction_is_negative_only": True,
        "source_macro_station_elevations_preserved_analytically": True,
        "shoreline_sign_preserved": True,
        "params": {
            "depth_m": depth_m, "width_km": width_km,
            "anchor_taper_km": anchor_taper_km,
            "boundary_taper_km": boundary_taper_km,
        },
        "not_seamless_for_different_crop_windows": True,
        "not_physically_validated": True,
        "not_author_approved": True,
    }


def _quality(ledger: dict) -> dict:
    m = ledger["coarse_to_fine_outlet_alignment"]
    comparisons = m["comparisons"]
    near = [float(x["same_side_distance_km"]) for x in comparisons
            if x["matched_child_terminal"] is not None]
    return {
        "major_macro_exits": m["major_A8_macro_exit_count"],
        "same_side_near_count": m["same_side_near_matches"],
        "same_side_matched_distance_sum_km": sum(near),
        "unmatched_macro_exits": m["unmatched_major_macro_exits"],
        "actual_common_watershed_verified": False,
    }


def compare_candidate(
    child: dict[str, np.ndarray], macro: dict[str, np.ndarray],
    manifest: dict, *, depth_m: float = 15, width_km: float = 5,
    anchor_taper_km: float = 2, boundary_taper_km: float = 5,
    stream_threshold_km2: float = 30,
    matching_tolerance_km: float = 30,
) -> tuple[dict[str, np.ndarray], dict]:
    """Always compare BEFORE and AFTER Core MFD. Never silently accept trial."""
    trial, audit = candidate_corridor_terrain(
        child, macro, manifest, depth_m=depth_m, width_km=width_km,
        anchor_taper_km=anchor_taper_km,
        boundary_taper_km=boundary_taper_km,
    )
    old_arrays, old_report = analyze_outlets(
        child, macro, manifest, stream_threshold_km2=stream_threshold_km2,
        matching_tolerance_km=matching_tolerance_km,
    )
    alternate = dict(child)
    alternate["child_elevation_m"] = trial["new_child_elevation_m"]
    proposed_arrays, new_report = analyze_outlets(
        alternate, macro, manifest, stream_threshold_km2=stream_threshold_km2,
        matching_tolerance_km=matching_tolerance_km,
    )
    before, after = _quality(old_report), _quality(new_report)
    if audit["original_macro_river_segments"] == 0:
        gate = "NO_OLD_A8_RIVER_SEGMENTS_NO_TERRAIN_CHANGE"
    elif not before["major_macro_exits"]:
        gate = "NO_MAJOR_MACRO_OUTLETS_CANNOT_VALIDATE_CORRIDOR"
    elif before["same_side_near_count"] == before["major_macro_exits"] and (
        before["same_side_matched_distance_sum_km"] <= 5*before["major_macro_exits"]
    ):
        gate = "BASELINE_MACRO_EXITS_ALREADY_NEAR_NO_AUTOCORRECTION"
    elif after["same_side_near_count"] > before["same_side_near_count"] or (
        after["same_side_near_count"] == before["same_side_near_count"] and
        after["same_side_matched_distance_sum_km"]
        < before["same_side_matched_distance_sum_km"] - 1.0
    ):
        gate = "GEOMETRICALLY_IMPROVED_ONLY_REQUIRES_AUTHOR_AND_BASIN_REVIEW"
    else:
        gate = "NO_GEOMETRIC_IMPROVEMENT_REJECT_CANDIDATE"
    audit.update({
        "decision": gate,
        "before": before,
        "after": after,
        "old_lake_topology_status": old_report["child_core_dominant_channel_ledger"]["lake_topology_status"],
        "new_lake_topology_status": new_report["child_core_dominant_channel_ledger"]["lake_topology_status"],
        "accepted_into_Core_or_original_child": False,
        "new_P2B25_original_river_alignment_approved": False,
        "no_A8_auto_injected_area": (
            old_report["external_area_auto_injected_km2"] == 0
            and new_report["external_area_auto_injected_km2"] == 0
        ),
    })
    return dict(trial, before_channel=old_arrays["channel_mask"],
                after_channel=proposed_arrays["channel_mask"]), audit


def render_trial(
    child: dict[str, np.ndarray], fields: dict[str, np.ndarray],
    audit: dict, target: Path,
) -> None:
    east = np.asarray(child["east_km"])
    north = np.asarray(child["north_km_north_first"])
    extent = [float(east[0]),float(east[-1]),
              float(north[-1]),float(north[0])]
    fig, axes = plt.subplots(1, 3, figsize=(16,5.5), layout="constrained")
    for i, (z,mask,title) in enumerate((
        (child["child_elevation_m"],fields["before_channel"],"Before: accepted Core MFD path"),
        (fields["new_child_elevation_m"],fields["after_channel"],"OPTIONAL proposal: MFD recomputed"),
    )):
        axes[i].imshow(
            z, extent=extent, origin="upper",cmap="terrain"
        )
        on=np.ma.masked_where(mask <= 0,mask)
        axes[i].imshow(on,extent=extent,origin="upper",cmap="Blues",
                       interpolation="nearest",alpha=.85)
        axes[i].set_title(title)
    axes[2].imshow(
        fields["source_guidance_delta_m"],origin="upper",extent=extent,
        cmap="RdBu",vmin=-audit["params"]["depth_m"],vmax=audit["params"]["depth_m"]
    )
    axes[2].set_title("Change to DEM (m); no macro station/edge moves")
    for a in axes:
        a.set(xlabel="east km",ylabel="north km",aspect="equal")
        a.grid(alpha=.12)
    fig.suptitle("P2-B2.5 NONCANONICAL CORRIDOR TRIAL — "+audit["decision"])
    fig.savefig(target,dpi=130)
    plt.close(fig)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--child-npz",type=Path,required=True)
    p.add_argument("--child-manifest",type=Path,required=True)
    p.add_argument("--macro-npz",type=Path,required=True)
    p.add_argument("--depth-m",type=float,default=15.)
    p.add_argument("--width-km",type=float,default=5.)
    p.add_argument("--anchor-taper-km",type=float,default=2.)
    p.add_argument("--boundary-taper-km",type=float,default=5.)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    with np.load(a.child_npz,allow_pickle=False) as f:
        child={k:f[k].copy() for k in f.files}
    with np.load(a.macro_npz,allow_pickle=False) as f:
        macro={k:f[k].copy() for k in f.files}
    manifest=json.loads(a.child_manifest.read_text(encoding="utf8"))
    fields,report=compare_candidate(
        child,macro,manifest,depth_m=a.depth_m,width_km=a.width_km,
        anchor_taper_km=a.anchor_taper_km,boundary_taper_km=a.boundary_taper_km
    )
    a.output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(a.output/"noncanonical-corridor-trial.npz",**fields)
    (a.output/"manifest.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8"
    )
    render_trial(child,fields,report,a.output/"before-after-corridor-trial.png")
    print(json.dumps({
        "decision":report["decision"],
        "max_excavation_m":report["maximum_excavation_m"],
        "source_anchors_error_m":report["source_anchor_correction_error_m"],
        "before":report["before"],"after":report["after"],
        "accepted_into_Core":False,
    },indent=2))


if __name__=="__main__":
    main()
