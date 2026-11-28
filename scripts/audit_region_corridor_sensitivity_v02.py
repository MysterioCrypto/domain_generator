from __future__ import annotations

"""P4-C2: read-only sensitivity of P4-C1 dominant-route evidence.

A8 D8 reference catchment areas are NOT outside-only area, Core MFD
receivers are NOT a river, and Priority Flood fill depth is NOT water depth.
Increasing a display threshold cannot repair a non-downhill original DEM.
"""

import argparse
import csv
from hashlib import file_digest
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from domain_generator.hydrology.routing import priority_flood_surfaces
from scripts.reconcile_region_boundary_corridors_v02 import reconcile_boundary


class CorridorSensitivityError(ValueError):
    pass


DEFAULT_THRESHOLDS = (0., 1., 2., 3., 5., 10.)


def _font(size: int):
    for font in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(font).exists():
            return ImageFont.truetype(font, size)
    return ImageFont.load_default()


def audit_route_sensitivity(z: np.ndarray, virtual_fill: np.ndarray,
                            route: list, strict_edges: set[tuple[int,int]],
                            withheld_edges: set[tuple[int,int]],
                            proxy_edges: set[tuple[int,int]],
                            *, thresholds=DEFAULT_THRESHOLDS,
                            baseline_limit_m: float=2., spacing_km: float=1.) -> tuple[dict,list]:
    """Pure diagnostic: no routing recomputation, no DEM edits, no assumptions about Q."""
    z=np.asarray(z, dtype=np.float64)
    virtual_fill=np.asarray(virtual_fill, dtype=np.float64)
    if (z.ndim!=2 or z.shape!=virtual_fill.shape or z.size<4
            or not np.isfinite(z).all() or not np.isfinite(virtual_fill).all()
            or np.any(virtual_fill < -1e-8)):
        raise CorridorSensitivityError("finite, aligned DEM and virtual-fill arrays required")
    if not np.isfinite(spacing_km) or spacing_km<=0:
        raise CorridorSensitivityError("positive kilometre cell spacing required")
    if (not np.isfinite(baseline_limit_m) or baseline_limit_m<0 or baseline_limit_m>100):
        raise CorridorSensitivityError("invalid original P4-B virtual-fill limit")
    try:
        values=tuple(float(v) for v in thresholds)
    except (TypeError, ValueError) as exc:
        raise CorridorSensitivityError("invalid threshold sequence") from exc
    if (not values or len(set(values))!=len(values) or tuple(sorted(values))!=values
            or any(not np.isfinite(v) or v<0 or v>100 for v in values)
            or baseline_limit_m not in values):
        raise CorridorSensitivityError("thresholds must be sorted, finite, unique, and include prior P4-B limit")
    cols=z.shape[1]; rows=z.shape[0]
    sample=[];seen=set(); prior_dst=None
    for idx,(raw_a,raw_b,tag) in enumerate(route):
        a,b=int(raw_a),int(raw_b)
        if not (0<=a<z.size and 0<=b<z.size):
            raise CorridorSensitivityError("route edge index out of grid")
        if prior_dst is not None and a != prior_dst:
            raise CorridorSensitivityError("route is disconnected across sequential edges")
        prior_dst=b
        if (a,b) in seen:
            raise CorridorSensitivityError("route contains repeated edge")
        seen.add((a,b))
        r,c=divmod(a,cols);rr,cc=divmod(b,cols)
        jump=max(abs(rr-r),abs(cc-c))>1 or (rr==r and cc==c)
        if tag=="proxy":
            if (a,b) not in proxy_edges:
                raise CorridorSensitivityError("unverified proxy edge")
        else:
            if jump or tag not in ("safe","withheld"):
                raise CorridorSensitivityError("nonadjacent ordinary edge or bad type")
            if tag=="safe" and (a,b) not in strict_edges:
                raise CorridorSensitivityError("P4-C1 safe edge absent in P4-B strict partition")
            if tag=="withheld" and (a,b) not in withheld_edges:
                raise CorridorSensitivityError("P4-C1 withheld edge absent in P4-B rejected partition")
        # Strict descent is an independent invariant: raw equal elevation is not downhill.
        raw_downhill=bool(z.ravel()[b]<z.ravel()[a])
        max_fill=float(max(virtual_fill.ravel()[a],virtual_fill.ravel()[b]))
        in_fill=max_fill>baseline_limit_m
        expected=(tag!="proxy" and raw_downhill and not in_fill)
        if expected!=(tag=="safe"):
            raise CorridorSensitivityError("P4-B strict baseline cannot be reproduced from original DEM/fill")
        reasons=([] if tag!="proxy" else ["nonphysical_lake_proxy"])
        if tag!="proxy":
            if not raw_downhill:reasons.append("raw_uphill_or_flat")
            if in_fill:reasons.append("virtual_fill_over_baseline")
        sample.append({
            "edge_index":idx, "source_flat":a, "target_flat":b,
            "source_row":r, "source_col":c, "target_row":rr, "target_col":cc,
            "raw_delta_m_target_minus_source":float(z.ravel()[b]-z.ravel()[a]),
            "max_endpoint_virtual_fill_m_NOT_WATER":max_fill,
            "original_p4b_class":tag,
            "reason_baseline":("strict" if not reasons else "+".join(reasons)),
            "raw_downhill":raw_downhill,
            "step_km":float(math.hypot(rr-r, cc-c)*spacing_km),
        })
    counts=[]
    for threshold in values:
        valid=[(item["original_p4b_class"]!="proxy"
                and item["raw_downhill"]
                and item["max_endpoint_virtual_fill_m_NOT_WATER"]<=threshold)
               for item in sample]
        categories={"strict":0,"fill_only":0,"uphill_or_flat_only":0,"both":0,"proxy":0}
        for ok,item in zip(valid,sample):
            if ok:categories["strict"]+=1
            elif item["original_p4b_class"]=="proxy":categories["proxy"]+=1
            else:
                bad_slope=not item["raw_downhill"]
                too_fill=item["max_endpoint_virtual_fill_m_NOT_WATER"]>threshold
                if bad_slope and too_fill:categories["both"]+=1
                elif bad_slope:categories["uphill_or_flat_only"]+=1
                else:categories["fill_only"]+=1
        longest=0;run=0
        for v in valid:
            run=run+1 if v else 0
            longest=max(longest,run)
        counts.append({
            "virtual_fill_limit_m_display_only":threshold,
            "eligible_original_dem_downhill_edges":sum(valid),
            "withheld_edges":len(sample)-sum(valid),
            "reason_counts":categories,
            "longest_consecutive_eligible_edges":longest,
            "eligible_length_km_NOT_RIVER_LENGTH":float(sum(
                item["step_km"] for item,ok in zip(sample,valid) if ok)),
        })
    assert counts[0]["eligible_original_dem_downhill_edges"]<=counts[-1]["eligible_original_dem_downhill_edges"]
    flat_or_uphill=sum(not item["raw_downhill"] for item in sample if item["original_p4b_class"]!="proxy")
    out={
        "edge_count":len(sample), "routing_proxy_edges_NOT_WATER":sum(item["original_p4b_class"]=="proxy" for item in sample),
        "baseline_fill_limit_m":baseline_limit_m,
        "baseline_fill_reasons":next(entry for entry in counts if entry["virtual_fill_limit_m_display_only"]==baseline_limit_m),
        "scenario_thresholds":counts,
        "raw_uphill_or_flat_irreducible_edges":flat_or_uphill,
        "raw_slope_blocker_persists_at_any_fill_threshold":flat_or_uphill>0,
        "strict_continuous_raw_dem_route_proved":(len(sample)>0 and flat_or_uphill==0 and not any(item["original_p4b_class"]=="proxy" for item in sample)
                                                  and all(item["original_p4b_class"]=="safe" for item in sample)),
        "no_terrain_or_core_routing_mutation":True,
    }
    return out,sample


def build_audit(macro,child,cm,projection,pm,masks,p4b,p4c1,
                *, thresholds=DEFAULT_THRESHOLDS):
    original,geometry=reconcile_boundary(macro,child,cm,projection,pm,masks,p4b)
    # Re-derive the P4-C1 *semantic* result from immutable input to catch stale ledger.
    for key in ("inlet_results", "source_macro_inlet_count", "source_macro_exit_count",
                "P4B_safe_edges_immutable", "P4B_withheld_edges_immutable",
                "P2_geometric_lake_proxy_jumps_NOT_WATER"):
        if original[key]!=p4c1.get(key):
            raise CorridorSensitivityError("P4-C1 recorded route does not match recomputed source: "+key)
    z=np.asarray(child["child_elevation_m"],dtype=np.float64)
    if z.shape!=(len(child["north_km_north_first"]),len(child["east_km"])):
        raise CorridorSensitivityError("invalid child axes")
    dx=np.diff(np.asarray(child["east_km"],dtype=np.float64))
    dy=-np.diff(np.asarray(child["north_km_north_first"],dtype=np.float64))
    if (len(dx)==0 or not np.allclose(dx,dx[0]) or not np.allclose(dy,dx[0]) or dx[0]<=0):
        raise CorridorSensitivityError("nonuniform cell metric")
    routed=priority_flood_surfaces(z)
    fill=np.maximum(0.,np.asarray(routed.fill_elevation_m,dtype=np.float64)-z)
    def edges(key):return set(map(tuple,np.asarray(masks[key]).tolist()))
    strict=edges("all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS")
    withheld=edges("withheld_ordinary_edges_NOT_DISPLAYED")
    proxy=edges("lake_proxy_jumps_NOT_RIVERS")
    if (len(strict)!=p4b["all_strictly_downhill_edges"] or
        len(withheld)!=p4b["withheld_unsafe_ordinary_edges"] or
        len(proxy)!=p4b["undrawn_geometric_lake_proxy_jumps"]):
        raise CorridorSensitivityError("P4-B edge partition count mismatch")
    baseline=float(p4b["virtual_fill_limit_m_display_only"])
    records=[];edges_data=[]
    for i,path in enumerate(geometry["selected_paths"]):
        a,b=audit_route_sensitivity(z,fill,path["route"]["segments"],strict,withheld,proxy,
                                 thresholds=thresholds,baseline_limit_m=baseline,
                                 spacing_km=float(dx[0]))
        a["route_index"]=i
        a["macro_inlet_key"]=path["inlet"]["key"]
        a["route_start_row_col"]=path["start"]
        a["route_terminal_row_col"]=path["route"]["terminal_row_col"]
        a["selected_candidate_uses_proxy_lake_geometry"]=a["routing_proxy_edges_NOT_WATER"]>0
        records.append(a)
        for row in b:edges_data.append({"route_index":i,**row})
    audit={
        "status":"P4_C2_RAW_DEM_ROUTE_SENSITIVITY_NOT_RIVERS",
        "accepted_water_or_same_basin_identity":False,
        "is_canonical_hydrology":False,
        "river_permanence_or_discharge_inferred":False,
        "accepted_core_mfd_recomputed_or_modified":False,
        "original_child_dem_modified":False,
        "A8_D8_external_only_area_known":False,
        "A8_D8_cumulative_area_not_imported_km2":0.0,
        "external_only_inflow_area_km2":"UNKNOWN_NOT_BOUNDED_FROM_A8_CUMULATIVE_HINT",
        "external_water_balance_or_lake_occupancy":"NOT_MODELLED",
        "source_P4B_ordinary_strict_edges":len(strict),
        "source_P4B_ordinary_withheld_edges":len(withheld),
        "source_proxy_lake_jumps_NOT_WATER":len(proxy),
        "P4C1_macro_inlet_count":original["source_macro_inlet_count"],
        "P4C1_candidate_route_count":len(records),
        "max_child_virtual_fill_m_NOT_LAKE_DEPTH":float(np.max(fill)),
        "per_route":records,
        "unsupported":["A8 historical upstream area as outside-only catchment",
                       "Priority Flood fill depth as lake water",
                       "raw-uphill MFD path as continuous real river",
                       "raise visual fill limit to repair original terrain",
                       "computed dominant MFD skeleton as discharge or permanence"],
    }
    return audit,edges_data


def render_map(base: Image.Image, child: dict, edges_data: list, audit: dict, output: Path):
    z=child["child_elevation_m"]
    rows,cols=z.shape
    if base.mode!="RGB" or base.width%cols or base.height%rows or base.width//cols!=base.height//rows:
        raise CorridorSensitivityError("map base and child raster dimensions differ")
    ppc=base.width//cols
    overlay=Image.new("RGBA",base.size,(0,0,0,0))
    d=ImageDraw.Draw(overlay)
    palette={"strict":(237,203,124,165),
             "raw_uphill_or_flat":(192,78,39,245),
             "virtual_fill_over_baseline":(142,69,131,235),
             "raw_uphill_or_flat+virtual_fill_over_baseline":(95,37,53,255),
             "nonphysical_lake_proxy":(65,62,59,255)}
    for item in edges_data:
        src=(item["source_col"]+.5)*ppc,(item["source_row"]+.5)*ppc
        dst=(item["target_col"]+.5)*ppc,(item["target_row"]+.5)*ppc
        why=item["reason_baseline"]
        if why=="strict":
            d.line((src,dst),fill=palette[why],width=max(2,ppc//3))
        else:
            # Mark the failure location but DO NOT draw a fake connecting river.
            x,y=((src[0]+dst[0])/2,(src[1]+dst[1])/2)
            radius=max(3,ppc//2)
            d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=palette[why])
    image=Image.alpha_composite(base.convert("RGBA"),overlay).convert("RGB")
    margin,top,footer=70,95,235
    page=Image.new("RGB",(image.width+margin*2,image.height+top+footer),(240,236,223))
    page.paste(image,(margin,top));draw=ImageDraw.Draw(page)
    draw.text((margin,24),"ОСВЕРА / P4-C2 — ПРОВЕРКА РАЗРЫВОВ МАРШРУТА",font=_font(28),fill="#383b34")
    baseline=audit["per_route"][0]["baseline_fill_reasons"] if audit["per_route"] else None
    counts=baseline["reason_counts"] if baseline else {}
    yy=top+image.height+25
    for label,value in (("Строгий спуск / модельный маршрут", "strict"),
                        ("Недопустимый подъём / горизонталь исходного DEM", "raw_uphill_or_flat"),
                        ("Виртуальное заполнение (НЕ вода)", "virtual_fill_over_baseline"),
                        ("Обе причины одновременно", "raw_uphill_or_flat+virtual_fill_over_baseline")):
        rgb=palette[value]
        draw.ellipse((margin+8,yy+6,margin+25,yy+23),fill=rgb[:3])
        draw.text((margin+36,yy),label,font=_font(20),fill="#45483b")
        yy+=42
    draw.text((margin+8,yy+3),"Статус: диагностика, не реальные реки и не принятая география",
              font=_font(18),fill="#555347")
    output.mkdir(parents=True,exist_ok=False)
    image.save(output/"corridor-sensitivity-base.png",optimize=True)
    page.save(output/"corridor-sensitivity-sheet.png",optimize=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("macro-npz","child-npz","child-manifest","projection-npz","projection-manifest",
              "p4b-masks-npz","p4b-audit-json","p4c1-audit-json","p4a-map-image"):
        p.add_argument("--"+k,required=True,type=Path)
    p.add_argument("--thresholds-m",type=float,nargs="+",default=list(DEFAULT_THRESHOLDS))
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise CorridorSensitivityError("refuse nonempty or existing output folder")
    def read(path):
        with np.load(path,allow_pickle=False) as a:return {k:a[k].copy() for k in a.files}
    paths={k:getattr(args,k.replace("-","_")) for k in (
        "macro-npz","child-npz","child-manifest","projection-npz","projection-manifest",
        "p4b-masks-npz","p4b-audit-json","p4c1-audit-json","p4a-map-image")}
    c1=json.loads(paths["p4c1-audit-json"].read_text(encoding="utf-8"))
    if (c1.get("status")!="P4_C1_COARSE_INLET_TO_CHILD_DOMINANT_GRAPH_HINTS_NOT_RIVERS"
            or c1.get("is_approved_river_map") is not False
            or c1.get("external_inflow_area_injected_km2") != 0):
        raise CorridorSensitivityError("unverified P4-C1 source")
    for key,filepath in paths.items():
        if key=="p4c1-audit-json":continue
        c1key=key.replace("-","_")
        if c1.get("input_sha256",{}).get(c1key) is None:
            raise CorridorSensitivityError("missing required prior P4-C1 hash for "+c1key)
        with filepath.open("rb") as fp:got=file_digest(fp,"sha256").hexdigest()
        if got!=c1["input_sha256"][c1key]:
            raise CorridorSensitivityError("P4-C1 SHA lineage mismatch on "+c1key)
    macro=read(paths["macro-npz"]);child=read(paths["child-npz"])
    proj=read(paths["projection-npz"]);mask=read(paths["p4b-masks-npz"])
    cm=json.loads(paths["child-manifest"].read_text(encoding="utf-8"))
    pm=json.loads(paths["projection-manifest"].read_text(encoding="utf-8"))
    p4b=json.loads(paths["p4b-audit-json"].read_text(encoding="utf-8"))
    audit,edge_data=build_audit(macro,child,cm,proj,pm,mask,p4b,c1,
                                thresholds=args.thresholds_m)
    with Image.open(paths["p4a-map-image"]) as im:base=im.convert("RGB")
    render_map(base,child,edge_data,audit,args.output)
    audit["input_sha256"]={}
    for key,path in paths.items():
        with path.open("rb") as fp:audit["input_sha256"][key.replace("-","_")]=file_digest(fp,"sha256").hexdigest()
    audit["P4C1_exact_file_lineage_verified"]=True
    (args.output/"corridor-sensitivity-audit.json").write_text(
        json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    fieldnames=["route_index","edge_index","source_row","source_col","target_row","target_col",
                "raw_delta_m_target_minus_source","max_endpoint_virtual_fill_m_NOT_WATER",
                "original_p4b_class","reason_baseline","raw_downhill","step_km"]
    with (args.output/"corridor-sensitivity-edges.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames,extrasaction="ignore")
        writer.writeheader();writer.writerows(edge_data)
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
