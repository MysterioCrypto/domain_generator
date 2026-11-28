from __future__ import annotations

"""P3-MVP: source-conditioned CARTOGRAPHIC land-cover CANDIDATES for an author atlas.

This OPTIONAL, NONCANONICAL layer is driven by explicit scenario code groups
(A12 is one example) and the independently generated child relief. Nothing here
establishes forest species, soils, a perennial wetland or human settlements.
A12 lat is SOUTH-first, child raster is NORTH-first; always sample by coords.
"""

import argparse
import json
from math import cos, pi, radians
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, ListedColormap
from matplotlib.patches import Patch
import numpy as np

CLASSES = {
    0: "NO_REFERENCE_OR_WATER",
    1: "POSSIBLE_WOODLAND",
    2: "POSSIBLE_OPEN_GROUND",
    3: "POSSIBLE_ROCKY_SLOPE",
    4: "POSSIBLE_WET_LOWLAND",
    5: "POSSIBLE_SPARSE_COVER",
}
PALETTE = ["#6d94a1", "#366d4b", "#b5aa75",
           "#a39b8d", "#70a49b", "#c4ae82"]


class CoverEvidenceError(ValueError):
    pass


def _defaults():
    return {
        "schema": "noncanonical-natural-cover-profile-v0.1",
        "status": "WORLD_EDITABLE_NOT_CANON",
        "source_biome_codes": {
            "woodland": [1, 2, 3, 7, 9, 10],
            "open": [4, 5, 8, 11],
            "sparse": [6, 12],
        },
        "scenario_weights": {
            "biome_base": 0.35,
            "biome_moderate": 0.25,
            "biome_precip_minus20": 0.20,
            "biome_precip_plus20": 0.20,
        },
        "forest_threshold": 0.48,
        "patch_strength": 0.23,
        "seed": 1406,
        "rock_slope_start_m_per_km": 105.0,
        "rock_slope_full_m_per_km": 330.0,
        "wetland_low_slope_m_per_km": 16.0,
        "wetland_reference_threshold": 0.58,
        "wetland_depression_min_m": 2.0,
        "forest_gap_bias": 0.30,
    }


def _profile(profile):
    p = _defaults() if profile is None else profile
    if (not isinstance(p, dict) or p.get("schema") != _defaults()["schema"]
            or p.get("status") != "WORLD_EDITABLE_NOT_CANON"):
        raise CoverEvidenceError("explicit editable noncanonical cover profile required")
    codes = p.get("source_biome_codes", {})
    if set(codes) != {"woodland", "open", "sparse"}:
        raise CoverEvidenceError("three explicit source-code groups required")
    normalized = []
    for group in ("woodland", "open", "sparse"):
        v = codes[group]
        if not isinstance(v, list) or not all(isinstance(k, int) and not isinstance(k, bool)
                                               and 1 <= k <= 254 for k in v):
            raise CoverEvidenceError("source codes must be explicit positive integers")
        normalized += v
    if not normalized or len(normalized) != len(set(normalized)):
        raise CoverEvidenceError("source code groups overlap or are empty")
    weights = p.get("scenario_weights", {})
    required = tuple(_defaults()["scenario_weights"])
    if set(weights) != set(required):
        raise CoverEvidenceError("four scenario names required")
    vals = list(weights.values())
    if (not all(isinstance(x, (int, float)) and not isinstance(x,bool)
                and np.isfinite(x) and x >= 0 for x in vals)
            or not np.isclose(sum(vals), 1, atol=1e-10)
            or all(x==0 for x in vals)):
        raise CoverEvidenceError("scenario weights must be normalized nonnegative")
    params = {
        k: p.get(k) for k in (
            "forest_threshold", "patch_strength", "seed",
            "rock_slope_start_m_per_km", "rock_slope_full_m_per_km",
            "wetland_low_slope_m_per_km", "wetland_reference_threshold",
            "wetland_depression_min_m", "forest_gap_bias"
        )
    }
    for key, value in params.items():
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not np.isfinite(value):
            raise CoverEvidenceError(f"invalid profile {key}")
    if not isinstance(params["seed"], int):
        raise CoverEvidenceError("seed must be integer")
    if not 0 < params["forest_threshold"] < 1 or not 0 <= params["patch_strength"] < 1:
        raise CoverEvidenceError("invalid forest configuration")
    if not 0 < params["rock_slope_start_m_per_km"] < params["rock_slope_full_m_per_km"]:
        raise CoverEvidenceError("invalid rock slope thresholds")
    if not 0 < params["wetland_low_slope_m_per_km"]:
        raise CoverEvidenceError("invalid wetland slope threshold")
    if not 0 < params["wetland_reference_threshold"] <= 1:
        raise CoverEvidenceError("invalid wetland evidence threshold")
    if not 0 < params["wetland_depression_min_m"] <= 100:
        raise CoverEvidenceError("invalid local lowland threshold")
    if not 0 <= params["forest_gap_bias"] < 1:
        raise CoverEvidenceError("invalid forest gap bias")
    return p


def _bilinear(x, y, lon, lat, field):
    """Continuous coarse-source support; no nearest-neighbour biome rectangles."""
    x,y = np.broadcast_arrays(x,y)
    ci = np.clip(np.searchsorted(lon,x,"right")-1,0,len(lon)-2)
    ri = np.clip(np.searchsorted(lat,y,"right")-1,0,len(lat)-2)
    u = np.clip((x-lon[ci])/(lon[ci+1]-lon[ci]),0,1)
    v = np.clip((y-lat[ri])/(lat[ri+1]-lat[ri]),0,1)
    return ((1-v)*((1-u)*field[ri,ci]+u*field[ri,ci+1])+
            v*((1-u)*field[ri+1,ci]+u*field[ri+1,ci+1]))


def _hash(ix,iy,seed):
    x=np.asarray(ix,dtype=np.int64).view("uint64")
    y=np.asarray(iy,dtype=np.int64).view("uint64")
    with np.errstate(over="ignore"):
        z=(x*np.uint64(0x9E3779B185EBCA87)^
           y*np.uint64(0xC2B2AE3D27D4EB4F)^
           np.uint64(seed%(1<<64)))
        z^=z>>np.uint64(30)
        z*=np.uint64(0xBF58476D1CE4E5B9)
        z^=z>>np.uint64(27)
        z*=np.uint64(0x94D049BB133111EB)
        z^=z>>np.uint64(31)
    return ((z>>np.uint64(11)).astype(float)/2**53)*2-1


def _value_noise(x,y,km,seed):
    fx,fy=np.broadcast_arrays(np.asarray(x)/km,np.asarray(y)/km)
    ix,iy=np.floor(fx).astype("int64"),np.floor(fy).astype("int64")
    u,v=fx-ix,fy-iy
    u=u*u*u*(u*(6*u-15)+10)
    v=v*v*v*(v*(6*v-15)+10)
    a,b=_hash(ix,iy,seed),_hash(ix+1,iy,seed)
    c,d=_hash(ix,iy+1,seed),_hash(ix+1,iy+1,seed)
    return (a*(1-u)+b*u)*(1-v)+(c*(1-u)+d*u)*v


def _local_smoothed_height(height):
    """Compact 11km neighborhood mean. Pure NumPy, no SciPy/implicit water."""
    n,m=height.shape
    pad=np.pad(height,5,mode="edge")
    out=np.zeros(height.shape,dtype=float)
    for dr in (-5,-3,0,3,5):
        for dc in (-5,-3,0,3,5):
            out+=pad[5+dr:5+dr+n,5+dc:5+dc+m]
    return out/25.


def classify_cover(child, macro_eco, manifest, profile=None):
    """Never mutate child/source or promote the A12 codes to actual biomes."""
    p=_profile(profile)
    if (manifest.get("status")!="NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or manifest.get("is_accepted_Core_DomainData") is not False):
        raise CoverEvidenceError("requires unaccepted source-conditioned child terrain")
    required=("lat","lon","land","biome_base","biome_moderate",
              "biome_precip_minus20","biome_precip_plus20","stable4",
              "wetland_candidate")
    if any(k not in macro_eco for k in required):
        raise CoverEvidenceError("missing A12-equivalent scenario/reference fields")
    latitude=np.asarray(macro_eco["lat"],dtype=float)
    longitude=np.asarray(macro_eco["lon"],dtype=float)
    if (latitude.ndim!=1 or longitude.ndim!=1
            or min(len(latitude),len(longitude))<3
            or not np.isfinite(latitude).all() or not np.isfinite(longitude).all()
            or not np.all(np.diff(longitude)>0)
            or not (np.all(np.diff(latitude)>0) or np.all(np.diff(latitude)<0))):
        raise CoverEvidenceError("incoherent global source geogrid axes")
    north_first=latitude[0]>latitude[-1]
    if north_first:
        latitude=latitude[::-1]
    shape=(len(latitude),len(longitude))
    source={}
    for k in required[2:]:
        a=np.asarray(macro_eco[k])
        if a.shape!=shape or not np.isfinite(a).all():
            raise CoverEvidenceError("missing/invalid shape for source "+k)
        source[k]=a[::-1] if north_first else a
    east=np.asarray(child["east_km"],dtype=float)
    north=np.asarray(child["north_km_north_first"],dtype=float)
    height=np.asarray(child["child_elevation_m"],dtype=float)
    land=np.asarray(child["land_mask"],dtype=bool)
    if (height.ndim!=2 or height.shape!=(len(north),len(east))
            or land.shape!=height.shape or not np.isfinite(height).all()
            or not np.all(np.diff(east)>0) or not np.all(np.diff(north)<0)
            or not np.allclose(np.diff(east),np.diff(east)[0],atol=1e-6)
            or not np.allclose(np.diff(north),np.diff(north)[0],atol=1e-6)):
        raise CoverEvidenceError("invalid regular child north-first DEM")
    radius=float(manifest["planet_radius_km"])
    lat0,lon0=map(float,manifest["center_lat_lon_deg"])
    if not(np.isfinite(radius) and radius>0 and abs(lat0)<80):
        raise CoverEvidenceError("invalid world radius/center")
    U=radius*pi/180
    X,Y=np.meshgrid(east,north)
    geo_lon=lon0+X/(U*cos(radians(lat0)))
    geo_lat=lat0+Y/U
    if (np.min(geo_lon)<longitude[0] or np.max(geo_lon)>longitude[-1]
            or np.min(geo_lat)<latitude[0] or np.max(geo_lat)>latitude[-1]):
        raise CoverEvidenceError("child outside source grid; no silent extrapolation")
    source_land=_bilinear(geo_lon,geo_lat,longitude,latitude,
                          source["land"].astype(float))
    if np.any(land & (source_land<0.50)):
        raise CoverEvidenceError("child land contradicts source sea mask")
    vote={g:np.zeros(height.shape,dtype=float) for g in ("woodland","open","sparse")}
    for field,weight in p["scenario_weights"].items():
        codes=source[field]
        for group in vote:
            gmask=np.isin(codes,p["source_biome_codes"][group]).astype(float)
            vote[group]+=float(weight)*_bilinear(
                geo_lon,geo_lat,longitude,latitude,gmask)
    stable=np.clip(_bilinear(geo_lon,geo_lat,longitude,latitude,
                             source["stable4"].astype(float)),0,1)
    wetref=np.clip(_bilinear(geo_lon,geo_lat,longitude,latitude,
                             source["wetland_candidate"].astype(float)),0,1)
    # Noise in PLANET coordinates: result stable for shifted/re-cropped child windows.
    global_x=radius*pi/180*geo_lon*np.cos(np.deg2rad(geo_lat))
    global_y=radius*pi/180*geo_lat
    patch=(0.65*_value_noise(global_x,global_y,24,int(p["seed"]))+
           0.25*_value_noise(global_x,global_y,9,int(p["seed"])+17)+
           0.10*_value_noise(global_x,global_y,3,int(p["seed"])+53))
    dx=float(np.diff(east)[0])
    dy=float(-np.diff(north)[0])
    sy,sx=np.gradient(height,dy,dx)
    slope=np.hypot(sx,sy)
    forest_score=(vote["woodland"]-float(p["forest_gap_bias"])+
                  float(p["patch_strength"])*patch)
    forest_score-=np.clip(
        (slope-float(p["rock_slope_start_m_per_km"]))/
        float(p["rock_slope_full_m_per_km"]),0,1)*0.45
    cover=np.zeros(height.shape,dtype=np.uint8)
    cover[land]=2
    cover[land & (vote["sparse"]>=0.60)]=5
    cover[land & (forest_score>=float(p["forest_threshold"]))]=1
    rock=(land & (slope>=float(p["rock_slope_full_m_per_km"])))
    cover[rock]=3
    local_lowland=_local_smoothed_height(height)-height
    wet=(land & (wetref>=float(p["wetland_reference_threshold"])) &
         (slope<=float(p["wetland_low_slope_m_per_km"])) &
         (local_lowland>=float(p["wetland_depression_min_m"])) & ~rock)
    cover[wet]=4
    fractions={CLASSES[i]:round(float(np.mean(cover[land]==i)),5)
               for i in (1,2,3,4,5)} if np.any(land) else {}
    coverout={
        "cover_class_candidate":cover,
        "A12_scenario_agreement_interpolated":stable.astype("float32"),
        "source_woodland_vote":vote["woodland"].astype("float32"),
        "child_slope_m_per_km":slope.astype("float32"),
        "wetland_candidate_reference":wetref.astype("float32"),
        "child_local_lowland_depth_proxy_m_NOT_WATER":local_lowland.astype("float32"),
    }
    audit={
        "status":"P3_MVP_NONCANONICAL_SOURCE_CONDITIONED_COVER",
        "source_is_author_canon":False,
        "cover_is_author_canon":False,
        "cover_is_measured_vegetation":False,
        "wetland_is_confirmed_water":False,
        "wetland_requires_local_depression_not_just_climate_mask":True,
        "not_koppen_to_biome":True,
        "no_species_or_groundwater_inferred":True,
        "no_terrain_changed":True,
        "no_story_landmark_or_route_changed":True,
        "source_lat_was_north_first":bool(north_first),
        "source_sample_resolution":"original macro lat/lon, NOT child 1-km observation",
        "scenario_agreement_mean":round(float(np.mean(stable[land])),5) if np.any(land) else None,
        "land_cover_area_fractions":fractions,
        "class_legend":{str(k):v for k,v in CLASSES.items()},
        "profile":p,
    }
    return coverout,audit


def render_preview(child,cover,audit,path):
    height=np.asarray(child["child_elevation_m"],dtype=float)
    C=np.asarray(cover["cover_class_candidate"])
    east=np.asarray(child["east_km"],dtype=float)
    north=np.asarray(child["north_km_north_first"],dtype=float)
    extent=[east[0],east[-1],north[-1],north[0]]
    ls=LightSource(azdeg=315,altdeg=48)
    fig,axs=plt.subplots(1,2,figsize=(15,7),layout="constrained")
    base=ls.shade(height,cmap=plt.get_cmap("gist_earth"),dx=1000,dy=1000,
                  vert_exag=2)
    for a in axs:
        a.imshow(base,extent=extent,origin="upper")
        a.set(xlabel="east km",ylabel="north km",aspect="equal")
    axs[0].set_title("Model relief (not accepted world geography)")
    axs[1].imshow(C,origin="upper",extent=extent,
                  cmap=ListedColormap(PALETTE),vmin=0,vmax=5,
                  interpolation="nearest",alpha=.68)
    axs[1].set_title("OPTIONAL land-cover candidates, not measured biomes")
    legend=[Patch(facecolor=PALETTE[k],label=v.replace("POSSIBLE_","").replace("_"," ").title())
            for k,v in CLASSES.items() if k]
    axs[1].legend(handles=legend,ncol=2,loc="lower center",
                  bbox_to_anchor=(.5,-.26),frameon=False,fontsize=9)
    fig.suptitle("P3-MVP / source scenario-conditioned author land cover — NONCANON")
    fig.savefig(path,dpi=115)
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child-npz",type=Path,required=True)
    parser.add_argument("--child-manifest",type=Path,required=True)
    parser.add_argument("--eco-npz",type=Path,required=True)
    parser.add_argument("--profile-json",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    with np.load(args.child_npz,allow_pickle=False) as z:
        child={k:z[k].copy() for k in z.files}
    with np.load(args.eco_npz,allow_pickle=False) as z:
        source={k:z[k].copy() for k in z.files}
    manifest=json.loads(args.child_manifest.read_text(encoding="utf8"))
    profile=(json.loads(args.profile_json.read_text(encoding="utf8"))
             if args.profile_json else None)
    cover,audit=classify_cover(child,source,manifest,profile)
    args.output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.output/"natural-cover-candidates.npz",**cover)
    (args.output/"manifest.json").write_text(
        json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    render_preview(child,cover,audit,args.output/"cover-before-after.png")
    print(json.dumps({"status":audit["status"],
                      "fractions":audit["land_cover_area_fractions"],
                      "canon":False},indent=2))


if __name__=="__main__":
    main()
