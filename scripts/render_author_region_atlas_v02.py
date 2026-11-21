from __future__ import annotations

"""Human-readable AUTHOR atlas. Unknown landmarks remain unknown."""
import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap
import numpy as np


class AuthorAtlasError(ValueError):
    pass


def _pair(raw, where):
    if (not isinstance(raw, (list, tuple)) or len(raw) != 2
            or any(isinstance(v, bool) or not isinstance(v, (int, float))
                   or not math.isfinite(v) for v in raw)):
        raise AuthorAtlasError(f"{where}: expected finite [east_km, north_km]")
    return tuple(float(v) for v in raw)


def audit_atlas(ledger, child, manifest):
    if ledger.get("schema") != "author-region-atlas-v0.1":
        raise AuthorAtlasError("unknown atlas ledger schema")
    world, story, region = (ledger.get(k) for k in ("world", "story", "region"))
    if not all(isinstance(x, dict) for x in (world, story, region)):
        raise AuthorAtlasError("world/story/region objects required")
    if world.get("name_status") not in ("WORKING_NOT_CANON", "AUTHOR_APPROVED"):
        raise AuthorAtlasError("planet name status required")
    if region.get("status") not in ("MODEL_CANDIDATE_NOT_CANON", "AUTHOR_FIXED"):
        raise AuthorAtlasError("region status required")
    if not isinstance(world.get("name"), str) or not world["name"].strip():
        raise AuthorAtlasError("planet name required")
    if not isinstance(story.get("protagonist"), str) or not story["protagonist"].strip():
        raise AuthorAtlasError("protagonist required")
    if (manifest.get("status") != "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON"
            or manifest.get("is_accepted_Core_DomainData") is not False):
        raise AuthorAtlasError("source-conditioned, explicitly noncanonical child required")
    if not np.allclose(_pair(manifest.get("center_lat_lon_deg"), "manifest center"),
                       _pair(region.get("center_lat_lon_deg"), "region center"),
                       atol=1e-7, rtol=0):
        raise AuthorAtlasError("region/model center does not match source DEM")
    east = np.asarray(child["east_km"], dtype=float)
    north = np.asarray(child["north_km_north_first"], dtype=float)
    dem = np.asarray(child["child_elevation_m"], dtype=float)
    land = np.asarray(child["land_mask"], dtype=bool)
    if (east.ndim != 1 or north.ndim != 1 or min(len(east), len(north)) < 5
            or dem.shape != (len(north), len(east)) or land.shape != dem.shape
            or not np.all(np.isfinite(dem)) or not np.all(np.diff(east) > 0)
            or not np.all(np.diff(north) < 0)):
        raise AuthorAtlasError("invalid north-first DEM")
    if not (np.allclose(np.diff(east), np.diff(east)[0], atol=1e-6)
            and np.allclose(-np.diff(north), np.diff(east)[0], atol=1e-6)):
        raise AuthorAtlasError("requires square uniform km pixels")
    box = (east[0], east[-1], north[-1], north[0])
    places=ledger.get("landmarks")
    if not isinstance(places, list):
        raise AuthorAtlasError("landmarks list required")
    names={}
    for p in places:
        if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not p["id"]:
            raise AuthorAtlasError("invalid landmark")
        if p["id"] in names or not isinstance(p.get("label"), str) or not p["label"]:
            raise AuthorAtlasError("duplicate landmark or missing label")
        if p.get("evidence") not in ("WRITTEN", "AUTHOR_BRIEF", "MODEL_ONLY"):
            raise AuthorAtlasError("landmark evidence status required")
        if p.get("position") is None:
            if p.get("position_status") != "UNPLACED":
                raise AuthorAtlasError("unknown position must be UNPLACED")
        else:
            x,y=_pair(p["position"],p["id"])
            if not(box[0]<=x<=box[1] and box[2]<=y<=box[3]):
                raise AuthorAtlasError("landmark outside actual child region")
            if p.get("position_status") not in ("AUTHOR_FIXED", "MODEL_PROPOSAL"):
                raise AuthorAtlasError("placed position needs explicit approval status")
            if p["position_status"]=="AUTHOR_FIXED" and not p.get("position_source"):
                raise AuthorAtlasError("author-fixed position requires provenance")
        names[p["id"]]=p
    results=[]
    known_routes=set()
    for r in ledger.get("routes",[]):
        if not isinstance(r,dict) or not isinstance(r.get("id"),str):
            raise AuthorAtlasError("route id required")
        if r["id"] in known_routes:
            raise AuthorAtlasError("duplicate route")
        known_routes.add(r["id"])
        a,b=names.get(r.get("from")),names.get(r.get("to"))
        if a is None or b is None or a is b:
            raise AuthorAtlasError("route must join two registered places")
        positions=a.get("position") is not None and b.get("position") is not None
        path=r.get("polyline_east_north_km")
        if path is not None:
            if not positions or not isinstance(path,list) or len(path)<2:
                raise AuthorAtlasError("route geometry requires two placed endpoints")
            points=[_pair(x,r["id"]) for x in path]
            if (math.dist(points[0],_pair(a["position"],"from"))>1e-6
                    or math.dist(points[-1],_pair(b["position"],"to"))>1e-6
                    or any(not(box[0]<=x<=box[1] and box[2]<=y<=box[3])
                           for x,y in points)):
                raise AuthorAtlasError("route path does not connect landmarks inside region")
            dist=sum(math.dist(x,y) for x,y in zip(points,points[1:]))
            kind="DRAWN_MODEL_POLYLINE_NOT_TRAVEL_TIME"
        elif positions:
            dist=math.dist(_pair(a["position"],"from"),_pair(b["position"],"to"))
            kind="STRAIGHT_LINE_LOWER_BOUND_NOT_TRAVEL_DISTANCE"
        else:
            dist=None
            kind="UNPLACED_NO_DISTANCE"
        results.append({
            "id":r["id"],"from":r["from"],"to":r["to"],
            "distance_km":None if dist is None else round(dist,3),
            "distance_kind":kind,"travel_time_inferred":False,
        })
    return {
        "schema":"author-region-atlas-audit-v0.1",
        "planet":world["name"],"planet_status":world["name_status"],
        "protagonist":story["protagonist"],"region_status":region["status"],
        "source_grid_shape":list(dem.shape),
        "landmarks_total":len(places),
        "landmarks_unplaced":sum(p["position"] is None for p in places),
        "routes":results,
        "any_locations_automatically_placed":False,
        "landcover_inferred_from_elevation":False,
        "map_is_author_canon":False,
    }


def render_sheet(ledger,child,report,target,channels=None):
    east=np.asarray(child["east_km"],dtype=float)
    north=np.asarray(child["north_km_north_first"],dtype=float)
    dem=np.asarray(child["child_elevation_m"],dtype=float)
    land=np.asarray(child["land_mask"],dtype=bool)
    if channels is not None and (channels.shape!=dem.shape or not np.isfinite(channels).all()):
        raise AuthorAtlasError("MFD channel mask shape or values incompatible")
    extent=[float(east[0]),float(east[-1]),float(north[-1]),float(north[0])]
    fig=plt.figure(figsize=(16,9),facecolor="#f5f2ea")
    ax=fig.add_axes([.055,.11,.58,.76])
    axinfo=fig.add_axes([.675,.12,.29,.76])
    axinfo.axis("off")
    spacing=float(east[1]-east[0])
    # Natural-color elevation + hillshade only, NOT a forest/biome claim.
    relief_palette=LinearSegmentedColormap.from_list(
        "author_relief_only", ["#557b6f", "#8fa78b", "#bfbb9f", "#d6c8ae", "#eee7d5"]
    )
    shade=LightSource(azdeg=315,altdeg=45).shade(
        dem,cmap=relief_palette,vert_exag=2.8,
        dx=spacing*1000,dy=spacing*1000)
    ax.imshow(shade,origin="upper",extent=extent,interpolation="bilinear")
    zmin,zmax=float(np.min(dem)),float(np.max(dem))
    interval=50 if zmax-zmin<500 else 100
    levels=np.arange(math.ceil(zmin/interval)*interval,zmax,interval)
    if 0<len(levels)<35:
        ax.contour(east,north,dem,levels=levels,
                   colors="#354a40",linewidths=.35,alpha=.36)
    if not np.all(land):
        water=np.ma.masked_where(land,np.ones(dem.shape))
        ax.imshow(water,origin="upper",extent=extent,cmap="Blues",alpha=.7)
    if channels is not None and np.any(channels>0):
        lines=np.ma.masked_where(channels<=0,channels)
        ax.imshow(lines,origin="upper",extent=extent,cmap="Blues",alpha=.7,
                  interpolation="nearest",vmin=0,vmax=1)
    for route in ledger.get("routes",[]):
        polyline=route.get("polyline_east_north_km")
        if polyline is not None:
            xs,ys=zip(*polyline)
            ax.plot(xs,ys,color="#d68a39",lw=2.8,linestyle="--",zorder=8)
    for p in ledger["landmarks"]:
        if p["position"] is None:
            continue
        x,y=p["position"]
        fixed=p["position_status"]=="AUTHOR_FIXED"
        ax.scatter([x],[y],marker="s" if fixed else "o",s=95,
                   c="#f1d267" if fixed else "#e6a86c",edgecolor="#34302c",
                   linewidth=1.2,zorder=12)
        ax.annotate(p["label"],(x,y),xytext=(6,7),
                    textcoords="offset points",color="#252b29",
                    fontsize=9,weight="bold",zorder=13)
    width=east[-1]-east[0]
    scale=25 if width>=100 else 10
    px=east[0]+width*.08
    py=north[-1]+(north[0]-north[-1])*.075
    ax.plot([px,px+scale],[py,py],color="white",lw=5,zorder=20)
    ax.plot([px,px+scale],[py,py],color="#232825",lw=2,zorder=21)
    ax.text(px+scale/2,py+3,f"{scale} км",ha="center",fontsize=10,
            bbox=dict(facecolor="#f5f2ea",alpha=.86,edgecolor="none"))
    ax.set(xlabel="Восток от центра модели (км)",ylabel="Север от центра модели (км)")
    ax.set_aspect("equal")
    ax.grid(alpha=.15)
    axinfo.text(0,1,"ИЗВЕСТНЫЕ МЕСТА",va="top",
                size=15,weight="bold",color="#2b2c2a")
    y=.93
    for item in ledger["landmarks"][:12]:
        symbol="○" if item["position"] is None else (
            "■" if item["position_status"]=="AUTHOR_FIXED" else "●")
        axinfo.text(0,y,symbol+"  "+item["label"][:33],
                    va="top",size=10,color="#61564b")
        y-=.052
    y-=.02
    axinfo.text(0,y,"МАРШРУТЫ",va="top",size=13,weight="bold")
    y-=.055
    for leg in report["routes"][:7]:
        route=next(x for x in ledger["routes"] if x["id"]==leg["id"])
        if leg["distance_km"] is None:
            value="расстояние неизвестно"
        elif leg["distance_kind"].startswith("STRAIGHT"):
            value=f"{leg['distance_km']:g} км по прямой, минимум"
        else:
            value=f"{leg['distance_km']:g} км по модельной линии"
        axinfo.text(0,y,route.get("label",leg["id"])[:35],
                    va="top",size=9.5,weight="bold")
        y-=.036
        axinfo.text(.03,y,value,va="top",size=9,color="#806e61")
        y-=.059
    axinfo.text(0,.03,
                "○ координаты не утверждены\n"
                "● модельное положение  ■ авторское\n"
                "Реки и леса не признаются каноном\n"
                "по цвету рельефа.",va="bottom",size=9,color="#615b53")
    fig.text(.055,.95,
             report["planet"]+"  /  РАЙОН "+str(ledger["region"]["id"]),
             weight="bold",size=23,color="#273129")
    fig.text(.057,.91,
             "Рабочая авторская карта · главный герой: "+report["protagonist"]+" · география НЕ утверждена",
             size=11,color="#737267")
    fig.text(.055,.045,
             "Модельный рельеф; положение отмечено только там, где задано явно. "
             "Карта для контроля непротиворечивости будущих арок.",
             size=9,color="#737267")
    fig.savefig(target,dpi=130,facecolor=fig.get_facecolor())
    plt.close(fig)


def notes(ledger,report):
    lines=["# Авторский атлас: "+report["planet"],"",
           "Планета: "+report["planet_status"],
           "Главный герой: "+report["protagonist"],"",
           "## Места (координаты не подставляются автоматически)"]
    for p in ledger["landmarks"]:
        place="пока не размещено" if p["position"] is None else (
            str(p["position"])+" км ("+p["position_status"]+")")
        lines.append("- "+p["label"]+": "+place+". "+
                     p.get("geography_constraint",""))
    lines+=["","## Контроль маршрутов"]
    for r in report["routes"]:
        dist="неизвестно" if r["distance_km"] is None else str(r["distance_km"])+" км"
        lines.append("- "+r["id"]+": "+dist+"; "+r["distance_kind"])
    lines+=["","Без утверждения рек, дорог и лесов; "
            "длины маршрутов не равны времени в пути.",""]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--child-npz",type=Path,required=True)
    p.add_argument("--child-manifest",type=Path,required=True)
    p.add_argument("--ledger-json",type=Path,required=True)
    p.add_argument("--channels-npz",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    with np.load(a.child_npz,allow_pickle=False) as z:
        child={k:z[k].copy() for k in z.files}
    ledger=json.loads(a.ledger_json.read_text(encoding="utf-8"))
    manifest=json.loads(a.child_manifest.read_text(encoding="utf-8"))
    report=audit_atlas(ledger,child,manifest)
    channels=None
    if a.channels_npz:
        with np.load(a.channels_npz,allow_pickle=False) as z:
            if "channel_mask" not in z.files:
                raise AuthorAtlasError("expected channel_mask from source Core channel NPZ")
            channels=z["channel_mask"].copy()
    a.output.mkdir(parents=True,exist_ok=True)
    render_sheet(ledger,child,report,a.output/"author-atlas-sheet.png",channels)
    (a.output/"author-atlas-audit.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (a.output/"author-atlas-notes.md").write_text(
        notes(ledger,report),encoding="utf-8")
    print(json.dumps({"planet":report["planet"],
                      "unplaced_landmarks":report["landmarks_unplaced"],
                      "routes_without_imagined_distance":sum(
                          r["distance_km"] is None for r in report["routes"])},
                     ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
