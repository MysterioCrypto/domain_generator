from __future__ import annotations

"""P4-D: source anchor proximity and raw DEM alternatives, diagnostic ONLY.

Read old P4-C2 per-edge evidence, verify its immutable source lineage, and
explain apparent ascents via parent interpolation versus fine residual.
Single-step or greedy raw-D8 descent is a *negative-control probe* to expose
micro-sinks. It is NOT a substitute for the accepted Core MFD network.
"""

import argparse
from collections import Counter
import csv
from hashlib import file_digest
import json
from math import cos, hypot, pi, radians
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from domain_generator.hydrology.routing import priority_flood_surfaces
from scripts.condition_planetary_child_terrain_v02 import _source_fields


class AnchorDrainEvidenceError(ValueError):
    pass


STEPS = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def _font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def parent_stations(macro: dict, child: dict, cm: dict) -> np.ndarray:
    """Compute actual *continuous* parent nodes, not snapped child pixels."""
    if (cm.get('status')!='NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON'
            or cm.get('is_accepted_Core_DomainData') is not False
            or cm.get('detail_coordinate_system') not in ('spherical_xyz_v1', 'legacy_lat_scaled_easting_v1')):
        raise AnchorDrainEvidenceError('requires unaccepted spherical child source')
    lat, lon, _, _ = _source_fields(macro)
    radius=float(cm['planet_radius_km']);center_lat,center_lon=map(float,cm['center_lat_lon_deg'])
    kpd=pi*radius/180.
    ex=(lon-center_lon)*kpd*cos(radians(center_lat))
    ny=(lat-center_lat)*kpd
    x=np.asarray(child['east_km'],dtype=float)
    y=np.asarray(child['north_km_north_first'],dtype=float)
    if (x.ndim!=1 or y.ndim!=1 or len(x)<3 or len(y)<3
            or not np.isfinite(x).all() or not np.isfinite(y).all()
            or not np.all(np.diff(x)>0) or not np.all(np.diff(y)<0)):
        raise AnchorDrainEvidenceError('invalid north-first child axes')
    xx=ex[(ex>=x[0])&(ex<=x[-1])]
    yy=ny[(ny>=y[-1])&(ny<=y[0])]
    exg,nyg=np.meshgrid(xx,yy)
    stations=np.column_stack((exg.ravel(),nyg.ravel()))
    if (stations.shape!=(cm.get('source_elevation_anchors_in_child'),2)
            or len(stations)==0 or cm.get('max_parent_anchor_error_m',1)>1e-6):
        raise AnchorDrainEvidenceError('source height anchors inconsistent with child metadata')
    return stations


def _negative_control_trace(z: np.ndarray, row: int, col: int) -> dict:
    """Probe one deterministic raw-steepest D8 descent, NEVER route water."""
    n,m=z.shape
    step_count=0
    while step_count<=z.size:
        if row in (0,n-1) or col in (0,m-1):
            return {'kind':'boundary', 'terminal_row_col':[row,col], 'steps':step_count}
        options=[]
        for dr,dc in STEPS:
            # deliberately no interpolation/flow fraction: negative control only
            drop=(float(z[row,col])-float(z[row+dr,col+dc]))/hypot(dr,dc)
            if drop>0:
                options.append((-drop,row+dr,col+dc))
        if not options:
            return {'kind':'raw_local_sink_not_a_lake', 'terminal_row_col':[row,col], 'steps':step_count}
        _,row,col=min(options)
        step_count+=1
    raise AnchorDrainEvidenceError('strict descending raw DEM path could not terminate')


def audit_anchor_alternatives(macro: dict, child: dict, cm: dict,
                              p4c2: dict, source_edges: list[dict],
                              *, anchor_near_km: float=6.0) -> tuple[dict, list[dict]]:
    if not np.isfinite(anchor_near_km) or not 0<anchor_near_km<=100:
        raise AnchorDrainEvidenceError('invalid anchor proximity diagnostic distance')
    if (p4c2.get('status')!='P4_C2_RAW_DEM_ROUTE_SENSITIVITY_NOT_RIVERS'
            or p4c2.get('P4C1_exact_file_lineage_verified') is not True
            or p4c2.get('accepted_water_or_same_basin_identity') is not False
            or p4c2.get('A8_D8_cumulative_area_not_imported_km2') != 0.):
        raise AnchorDrainEvidenceError('requires verified noncanonical P4-C2')
    z=np.asarray(child['child_elevation_m'],dtype=float)
    parent=np.asarray(child['parent_interpolated_m'],dtype=float)
    detail=np.asarray(child['new_local_relief_m'],dtype=float)
    x=np.asarray(child['east_km'],dtype=float);y=np.asarray(child['north_km_north_first'],dtype=float)
    if (z.ndim!=2 or min(z.shape)<3 or z.shape!=parent.shape or z.shape!=detail.shape
            or z.shape!=(len(y),len(x)) or not all(np.isfinite(a).all() for a in (z,parent,detail))):
        raise AnchorDrainEvidenceError('invalid derived DEM/parent/detail alignment')
    if not np.allclose(np.diff(x),x[1]-x[0]) or not np.allclose(-np.diff(y),x[1]-x[0]):
        raise AnchorDrainEvidenceError('nonuniform child source-grid metric')
    # Ongoing source code may clamp coastal sign; the *effective* residual
    # is raw-parent, not blindly new_local_relief, preserving correct identity.
    residual=z-parent
    anchors=parent_stations(macro,child,cm)
    base=float(p4c2['per_route'][0]['baseline_fill_limit_m']) if len(p4c2.get('per_route',[]))==1 else None
    if base is None or not np.isfinite(base) or base < 0 or base > 100:
        raise AnchorDrainEvidenceError('P4-D expects one route and valid P4-C2 original baseline')
    fill=np.maximum(0.,np.asarray(priority_flood_surfaces(z).fill_elevation_m,dtype=float)-z)
    if (len(source_edges)!=p4c2['per_route'][0]['edge_count'] or not source_edges
            or sorted(int(e['edge_index']) for e in source_edges)!=list(range(len(source_edges)))):
        raise AnchorDrainEvidenceError('source edge ledger is incomplete')
    prev_target=None
    out=[]
    for e in source_edges:
        i=int(e['edge_index'])
        sr,sc,tr,tc=[int(e[k]) for k in ('source_row','source_col','target_row','target_col')]
        if (not (0<=sr<z.shape[0] and 0<=tr<z.shape[0] and 0<=sc<z.shape[1] and 0<=tc<z.shape[1])
                or max(abs(sr-tr),abs(sc-tc))>1 or (sr,sc)==(tr,tc)):
            raise AnchorDrainEvidenceError('invalid ordinary route edge geometry')
        if prev_target is not None and (sr,sc)!=prev_target:
            raise AnchorDrainEvidenceError('route edge sequence is disconnected')
        prev_target=(tr,tc)
        raw_delta=float(z[tr,tc]-z[sr,sc])
        parent_delta=float(parent[tr,tc]-parent[sr,sc])
        residual_delta=float(residual[tr,tc]-residual[sr,sc])
        if not np.isclose(raw_delta,parent_delta+residual_delta,rtol=0,atol=1e-8):
            raise AnchorDrainEvidenceError('raw height decomposition is inconsistent')
        max_fill=float(max(fill[sr,sc],fill[tr,tc]))
        if raw_delta<0 and max_fill<=base:
            reason='strict'
        elif raw_delta>=0 and max_fill>base:
            reason='raw_uphill_or_flat+virtual_fill_over_baseline'
        elif raw_delta>=0:
            reason='raw_uphill_or_flat'
        else:
            reason='virtual_fill_over_baseline'
        if (reason!=e['reason_baseline'] or
                e['original_p4b_class']!=('safe' if reason=='strict' else 'withheld') or
                not np.isclose(raw_delta,float(e['raw_delta_m_target_minus_source']),atol=1e-7,rtol=0) or
                not np.isclose(max_fill,float(e['max_endpoint_virtual_fill_m_NOT_WATER']),atol=1e-7,rtol=0)):
            raise AnchorDrainEvidenceError('P4-C2 per-edge evidence failed recomputation')
        px=float((x[sc]+x[tc])/2);py=float((y[sr]+y[tr])/2)
        distance=float(np.min(np.hypot(anchors[:,0]-px,anchors[:,1]-py)))
        is_bad=raw_delta>=0
        local_drops=[(dr,dc) for dr,dc in STEPS if 0<=sr+dr<z.shape[0]
                     and 0<=sc+dc<z.shape[1] and z[sr+dr,sc+dc]<z[sr,sc]]
        diagnostic=_negative_control_trace(z,sr,sc) if is_bad else None
        cls=('fine_residual_reversed_parent_descent' if parent_delta<0
             else 'parent_already_uphill_or_flat') if is_bad else None
        out.append({
            'edge_index':i,'source_row':sr,'source_col':sc,'target_row':tr,'target_col':tc,
            'raw_delta_m':raw_delta,'parent_delta_m':parent_delta,
            'effective_fine_residual_delta_m':residual_delta,
            'source_new_local_relief_m':float(detail[sr,sc]),
            'closest_parent_anchor_distance_km':distance,
            'near_anchor_within_6km':bool(distance<=anchor_near_km),
            'raw_uphill_or_flat':bool(is_bad),'cause_raw_uphill':cls,
            'first_hop_raw_downhill_alternatives':len(local_drops) if is_bad else None,
            'diagnostic_greedy_raw_outcome_NOT_A_CATCHMENT':diagnostic,
            'P4C2_reason':reason,
        })
    # Re-derive P4-C2 aggregated baseline, refuse recomputed mismatch.
    strict=sum(e['P4C2_reason']=='strict' for e in out)
    fill_only=sum(e['P4C2_reason']=='virtual_fill_over_baseline' for e in out)
    uphill_only=sum(e['P4C2_reason']=='raw_uphill_or_flat' for e in out)
    both=sum(e['P4C2_reason']=='raw_uphill_or_flat+virtual_fill_over_baseline' for e in out)
    b=p4c2['per_route'][0]['baseline_fill_reasons']
    if (b['eligible_original_dem_downhill_edges']!=strict or
            b['reason_counts']!={'strict':strict,'fill_only':fill_only,'uphill_or_flat_only':uphill_only,
                                'both':both,'proxy':0}):
        raise AnchorDrainEvidenceError('P4-C2 baseline scenario no longer reproduces')
    raw_bad=[e for e in out if e['raw_uphill_or_flat']]
    strict_rows=[e for e in out if e['P4C2_reason']=='strict']
    classes=Counter(e['cause_raw_uphill'] for e in raw_bad)
    no_first=sum(e['first_hop_raw_downhill_alternatives']==0 for e in raw_bad)
    sink_count=sum(e['diagnostic_greedy_raw_outcome_NOT_A_CATCHMENT']['kind']=='raw_local_sink_not_a_lake'
                   for e in raw_bad)
    runs=[];current=[]
    for row in out:
        if row['raw_uphill_or_flat']:current.append(row['edge_index'])
        elif current:runs.append(current);current=[]
    if current:runs.append(current)
    audit={
        'status':'P4_D_ANCHOR_AND_RAW_DESCENT_NEGATIVE_CONTROL_NOT_RIVERS',
        'is_accepted_hydrology':False,'redefined_Core_MFD':False,
        'changed_original_child_DEM':False,'macro_A8_upstream_area_injected_km2':0,
        'physical_basin_identity_or_river_verified':False,
        'original_parent_stations_continuous_not_child_pixels':len(anchors),
        'raw_uphill_or_flat_edges':len(raw_bad),'parent_gradient_already_non_downhill':classes['parent_already_uphill_or_flat'],
        'fine_residual_reversals_of_descending_parent':classes['fine_residual_reversed_parent_descent'],
        'blocked_sources_with_immediate_alternative_raw_downhill':len(raw_bad)-no_first,
        'blocked_sources_without_immediate_raw_downhill':no_first,
        'greedy_raw_descent_ends_at_local_sinks_NOT_LAKES':sink_count,
        'greedy_raw_descent_reaches_boundary':len(raw_bad)-sink_count,
        'nearest_anchor_distance_km_median_blockers':float(np.median([e['closest_parent_anchor_distance_km'] for e in raw_bad])) if raw_bad else None,
        'nearest_anchor_distance_km_median_strict':float(np.median([e['closest_parent_anchor_distance_km'] for e in strict_rows])) if strict_rows else None,
        'raw_bad_within_anchor_near_threshold':sum(e['near_anchor_within_6km'] for e in raw_bad),
        'strict_within_anchor_near_threshold':sum(e['near_anchor_within_6km'] for e in strict_rows),
        'anchor_near_threshold_km':anchor_near_km,
        'raw_bad_runs_count':len(runs),'max_consecutive_raw_bad_edges':max(map(len,runs),default=0),
        'raw_bad_run_lengths':[len(x) for x in runs],
        'complete_P4C2_partition':{'strict':strict,'fill_only':fill_only,'raw_uphill_only':uphill_only,'both':both},
        'methodology':{'anchor_distances':'continuous parent station coordinates in spherical child tangent chart',
                       'terrain_contribution':'delta_raw = delta_parent_interpolated + delta_effective_residual (not necessarily = new_local_relief near coast)',
                       'alternative_raw_downhill':'immediate physical elevation descent options only, not Core MFD; deterministic greedy-D8 trace a NEGATIVE CONTROL',
                       'raw_greedy_local_sink':'mathematical local minimum; not physical lake, recharge, perennial flow or basin identity'},
        'unresolved':['coarse A8 vs child MFD catchment identity',
                      'raw alternative descent and MFD path are different semantics',
                      'physical drainage through raw micro-pits, lakes, infiltration or erosion',
                      'upstream outside-crop rainfall/runoff and water balance'],
    }
    return audit,out


def render_diagnostic(base: Image.Image, child: dict, macro: dict, cm: dict,
                      rows: list[dict], audit: dict, output: Path):
    z=np.asarray(child['child_elevation_m']);nr,nc=z.shape
    if base.mode!='RGB' or base.width%nc or base.height%nr or base.width//nc!=base.height//nr:
        raise AnchorDrainEvidenceError('base image does not align with square child cells')
    ppc=base.width//nc
    overlay=Image.new('RGBA',base.size,(0,0,0,0));d=ImageDraw.Draw(overlay)
    anchors=parent_stations(macro,child,cm)
    x=np.asarray(child['east_km']);y=np.asarray(child['north_km_north_first'])
    for ex,ny in anchors:
        px=((ex-x[0])/(x[-1]-x[0])*(nc-1)+.5)*ppc
        py=((y[0]-ny)/(y[0]-y[-1])*(nr-1)+.5)*ppc
        d.ellipse((px-3,py-3,px+3,py+3),outline=(229,233,227,155),width=1)
    for e in rows:
        a=((e['source_col']+.5)*ppc,(e['source_row']+.5)*ppc)
        b=((e['target_col']+.5)*ppc,(e['target_row']+.5)*ppc)
        if e['P4C2_reason']=='strict':
            d.line((a,b),fill=(239,192,104,164),width=max(2,ppc//3))
        elif e['raw_uphill_or_flat']:
            color=(238,90,53,245) if e['cause_raw_uphill']=='fine_residual_reversed_parent_descent' else (248,213,87,255)
            px,py=((a[0]+b[0])/2,(a[1]+b[1])/2)
            d.ellipse((px-5,py-5,px+5,py+5),fill=color)
            if e['first_hop_raw_downhill_alternatives']==0:
                d.line((px-7,py-7,px+7,py+7),fill=(28,29,27,240),width=2)
                d.line((px-7,py+7,px+7,py-7),fill=(28,29,27,240),width=2)
        else:
            px,py=((a[0]+b[0])/2,(a[1]+b[1])/2)
            d.ellipse((px-3,py-3,px+3,py+3),fill=(142,85,149,220))
    img=Image.alpha_composite(base.convert('RGBA'),overlay).convert('RGB')
    margin,top,foot=65,88,226
    sheet=Image.new('RGB',(img.width+2*margin,img.height+top+foot),(240,237,227))
    sheet.paste(img,(margin,top));pen=ImageDraw.Draw(sheet)
    pen.text((margin,20),'ОСВЕРА / P4-D — ИСТОЧНИКИ ЛОКАЛЬНЫХ ПОДЪЁМОВ',font=_font(26),fill='#43473b')
    yy=top+img.height+24
    for message in ('Светлые кольца: 63 высотные опоры исходного A8',
                    'Оранжевый: локальная деталь обратила исходный уклон',
                    'Жёлтый: макроуклон сам не направлен вниз',
                    'Чёрный X: нет соседнего исходного спуска; пурпурный: fill-only',
                    'Проверка альтернативных уклонов — НЕ утверждение о реках'):
        pen.text((margin+9,yy),message,font=_font(18),fill='#4f5149');yy+=36
    output.mkdir(parents=True,exist_ok=False)
    img.save(output/'anchor-gradient-evidence-map.png',optimize=True)
    sheet.save(output/'anchor-gradient-evidence-sheet.png',optimize=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('macro-npz','child-npz','child-manifest','p4c2-audit-json','p4c2-edges-csv','p4a-map-image'):
        p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise AnchorDrainEvidenceError('refuse existing output directory')
    def read(path):
        with np.load(path,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
    macro=read(args.macro_npz);child=read(args.child_npz)
    cm=json.loads(args.child_manifest.read_text(encoding='utf8'))
    p4c2=json.loads(args.p4c2_audit_json.read_text(encoding='utf8'))
    # P4-C2 records the EXACT source bytes used for the diagnosis.
    for k,path in (('macro_npz',args.macro_npz),('child_npz',args.child_npz),
                   ('child_manifest',args.child_manifest),('p4a_map_image',args.p4a_map_image)):
        with path.open('rb') as f:got=file_digest(f,'sha256').hexdigest()
        if p4c2.get('input_sha256',{}).get(k)!=got:
            raise AnchorDrainEvidenceError('P4-C2 SHA lineage mismatch '+k)
    with args.p4c2_edges_csv.open('r',encoding='utf8',newline='') as f:
        edges=list(csv.DictReader(f))
    audit,rows=audit_anchor_alternatives(macro,child,cm,p4c2,edges)
    with Image.open(args.p4a_map_image) as im:base=im.convert('RGB')
    render_diagnostic(base,child,macro,cm,rows,audit,args.output)
    audit['input_sha256']={}
    for key,path in (('macro_npz',args.macro_npz),('child_npz',args.child_npz),
                     ('child_manifest',args.child_manifest),('p4c2_audit_json',args.p4c2_audit_json),
                     ('p4c2_edges_csv',args.p4c2_edges_csv),('p4a_map_image',args.p4a_map_image)):
        with path.open('rb') as f:audit['input_sha256'][key]=file_digest(f,'sha256').hexdigest()
    audit['prior_P4C2_source_file_hashes_verified']=True
    (args.output/'anchor-gradient-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    columns=['edge_index','source_row','source_col','target_row','target_col','raw_delta_m',
             'parent_delta_m','effective_fine_residual_delta_m','source_new_local_relief_m',
             'closest_parent_anchor_distance_km','near_anchor_within_6km',
             'raw_uphill_or_flat','cause_raw_uphill','first_hop_raw_downhill_alternatives',
             'diagnostic_greedy_raw_outcome_NOT_A_CATCHMENT','P4C2_reason']
    with (args.output/'anchor-gradient-all-edges.csv').open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(rows)
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
