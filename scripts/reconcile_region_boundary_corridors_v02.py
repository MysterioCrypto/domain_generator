from __future__ import annotations

"""P4-C1: reconcile historical coarse A8 crossing hints with child MFD skeleton.

READ-ONLY diagnostic. A8 D8 and 1-km MFD are models with different routing
semantics. A nearby inlet+outlet pair and a connected child graph do NOT prove
catchment identity, channel permanence, external area or discharge.
"""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.condition_planetary_child_boundary_mfd_v02 import source_inlet_candidates
from scripts.compare_planetary_child_mfd_outlets_v02 import macro_outlet_candidates


class BoundaryCorridorError(ValueError):
    pass


def _font(size: int):
    for candidate in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                      "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _edge_set(a: np.ndarray, n: int, name: str) -> set[tuple[int,int]]:
    a=np.asarray(a)
    if a.ndim != 2 or a.shape[1] != 2 or a.dtype.kind not in 'iu':
        raise BoundaryCorridorError(f"{name} must have integer (N,2) edges")
    if np.any(a < 0) or np.any(a >= n):
        raise BoundaryCorridorError(f"{name} links beyond DEM")
    edges = set(map(tuple, a.tolist()))
    if len(edges) != len(a):
        raise BoundaryCorridorError(f"{name} has duplicate links")
    return edges


def _side_distance(side: str, row: int, col: int, x: np.ndarray, y: np.ndarray) -> float:
    if side == 'west': return float(x[col]-x[0])
    if side == 'east': return float(x[-1]-x[col])
    if side == 'north': return float(y[0]-y[row])
    if side == 'south': return float(y[row]-y[-1])
    raise BoundaryCorridorError(f"invalid boundary side: {side}")


def _boundary_side(row: int, col: int, nr: int, nc: int) -> str | None:
    sides=[]
    if row==0:sides.append('north')
    if row==nr-1:sides.append('south')
    if col==0:sides.append('west')
    if col==nc-1:sides.append('east')
    return sides[0] if len(sides)==1 else None  # corner ambiguous


def _trace(start: int, receiver: np.ndarray, shape: tuple[int,int],
           allowed: dict[tuple[int,int],str]) -> dict:
    nr,nc=shape
    visited=set();cur=int(start);segments=[]
    while True:
        if cur in visited:raise BoundaryCorridorError('Core dominant route contains cycle')
        if cur<0 or cur>=nr*nc:raise BoundaryCorridorError('Core dominant route leaves grid index')
        visited.add(cur)
        r,c=divmod(cur,nc)
        if r in (0,nr-1) or c in (0,nc-1):
            return {'terminal_row_col':[r,c], 'terminal_side':_boundary_side(r,c,nr,nc),
                    'length_edges':len(segments),
                    'strict_downhill_edges':sum(t=='safe' for _,_,t in segments),
                    'withheld_unsafe_edges':sum(t=='withheld' for _,_,t in segments),
                    'lake_proxy_jumps':sum(t=='proxy' for _,_,t in segments),
                    'segments':segments}
        dest=int(receiver[cur]);typ=allowed.get((cur,dest))
        if typ is None:
            raise BoundaryCorridorError('incomplete or contradictory P2/P4-B graph lineage')
        segments.append((cur,dest,typ));cur=dest


def reconcile_boundary(macro: dict, child: dict, child_meta: dict,
                       projection: dict, projection_report: dict,
                       p4b_masks: dict, p4b_audit: dict,
                       *, boundary_band_km: float=12.,
                       crossing_radius_km: float=30.,
                       outlet_radius_km: float=30.) -> tuple[dict,dict]:
    """List all inlet hints and trace only existing child dominant routes.

    No recipient areas are mutated or injected.  Nearness is NOT identity.
    """
    for key,v in [('boundary_band_km',boundary_band_km),
                  ('crossing_radius_km',crossing_radius_km),
                  ('outlet_radius_km',outlet_radius_km)]:
        if not np.isfinite(v) or v<=0 or v>200:
            raise BoundaryCorridorError(f'{key} must be finite in (0, 200] km')
    if (child_meta.get('status')!='NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON'
            or child_meta.get('is_accepted_Core_DomainData') is not False
            or projection_report.get('status')!='P2_B2_4_REFERENCE_EXIT_ALIGNMENT_NOT_ACCEPTED_HYDROLOGY'
            or projection_report.get('is_author_approved_local_river_map') is not False
            or projection_report.get('external_area_auto_injected_km2')!=0
            or p4b_audit.get('status')!='P4B_CONSERVATIVE_DRAINAGE_EVIDENCE_NOT_CANONICAL_RIVERS'
            or p4b_audit.get('is_accepted_hydrology') is not False
            or p4b_audit.get('is_water_occupancy_or_discharge') is not False
            or p4b_audit.get('source_external_inflow_km2_applied')!=0
            or p4b_audit.get('p4a_child_npz_sha256_lineage_verified') is not True):
        raise BoundaryCorridorError('noncanonical P2/P4-B, zero implicit external area required')
    ledger=projection_report.get('child_core_dominant_channel_ledger',{})
    if (ledger.get('status')!='CONNECTED_CORE_DOMINANT_MFD_CHANNEL_PROJECTION_NOT_REAL_RIVERS'
            or ledger.get('no_external_A8_source_area_auto_injected') is not True
            or ledger.get('is_physical_discharge_or_approved_river') is not False):
        raise BoundaryCorridorError('P2 channel skeleton provenance missing')
    z=np.asarray(child['child_elevation_m']);x=np.asarray(child['east_km']);y=np.asarray(child['north_km_north_first'])
    if (z.ndim!=2 or z.shape!=(len(y),len(x)) or not np.isfinite(z).all()
            or not np.isfinite(x).all() or not np.isfinite(y).all()
            or not np.all(np.diff(x)>0) or not np.all(np.diff(y)<0)):
        raise BoundaryCorridorError('north-first child grid inconsistent')
    n=z.size; shape=z.shape
    receiver=np.asarray(projection['Core_dominant_receiver_index'])
    if receiver.shape!=shape or receiver.dtype.kind not in 'iu' or np.any((receiver < -1)|(receiver>=n)):
        raise BoundaryCorridorError('Core dominant receiver field invalid')
    safe=_edge_set(p4b_masks['all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS'],n,'strict')
    withheld=_edge_set(p4b_masks['withheld_ordinary_edges_NOT_DISPLAYED'],n,'withheld')
    proxy=_edge_set(p4b_masks['lake_proxy_jumps_NOT_RIVERS'],n,'proxy')
    full=_edge_set(projection['channel_edge_flat_from_to'],n,'source P2 ordinary')
    source_proxy=_edge_set(projection['lake_proxy_jumps_flat_from_to'],n,'source P2 proxy')
    if (safe & withheld or (safe|withheld)!=full or proxy!=source_proxy
            or (safe|withheld)&proxy):
        raise BoundaryCorridorError('P4-B strict/withheld links do not exactly partition P2 projection')
    if (len(safe)!=p4b_audit.get('all_strictly_downhill_edges')
            or len(withheld)!=p4b_audit.get('withheld_unsafe_ordinary_edges')
            or len(proxy)!=p4b_audit.get('undrawn_geometric_lake_proxy_jumps')):
        raise BoundaryCorridorError('P4-B audit contradicts its masks')
    for a,b in full|proxy:
        if receiver.ravel()[a]!=b:
            raise BoundaryCorridorError('candidate P2 edge disagrees with P2 dominant receiver')
    allowed={edge:'safe' for edge in safe}
    allowed.update({edge:'withheld' for edge in withheld})
    allowed.update({edge:'proxy' for edge in proxy})
    inlets=source_inlet_candidates(macro,child,child_meta)
    exits=projection_report.get('source_macro_A8_outlets',[])
    actual_exits,_ = macro_outlet_candidates(macro, child, child_meta)
    if exits != actual_exits:
        raise BoundaryCorridorError('supplied A8 macro does not reproduce P2-B2.4 recorded exits')
    terminals={tuple(t['child_edge_cell_row_col']):t for t in ledger.get('connected_boundary_endpoints',[])}
    nr,nc=shape
    traces={}
    flat_receiver=receiver.ravel()
    candidates=[]
    for src,dst in sorted(safe):
        r,c=divmod(src,nc);rr,cc=divmod(dst,nc)
        for side in ('east','west','north','south'):
            da=_side_distance(side,r,c,x,y); db=_side_distance(side,rr,cc,x,y)
            if da<=boundary_band_km and db>da:
                if src not in traces:traces[src]=_trace(src,flat_receiver,shape,allowed)
                candidates.append((side,src,traces[src]))
    records=[];drawn=[]
    for inlet in inlets:
        if inlet.get('can_auto_inject_area') is not False or inlet.get('is_verified_external_only_area') is not False:
            raise BoundaryCorridorError('historical A8 inlet cannot be promoted to verified upstream area')
        side=inlet['side'];px,py=inlet['crossing_east_north_km'];look=[]
        for candidate_side,src,trace in candidates:
            if side!=candidate_side:continue
            r,c=divmod(src,nc)
            distance=float(np.hypot(x[c]-px,y[r]-py))
            if distance<=crossing_radius_km and trace['terminal_side'] is not None:
                look.append((distance,src,trace))
        look.sort(key=lambda row:(row[0],row[1]))
        grouped={}
        for d,src,t in look:
            endpoint=tuple(t['terminal_row_col'])
            if endpoint not in grouped:grouped[endpoint]=(d,src,t)
        groups=sorted(grouped.values(),key=lambda row:(row[0],row[1]))
        record={
            'historical_macro_inlet_key':inlet['key'],
            'side':side,
            'historical_crossing_east_north_km':inlet['crossing_east_north_km'],
            'A8_upstream_area_km2_UNSAFE_NOT_INJECTED':inlet['a8_upstream_catchment_km2_UNSAFE_HINT'],
            'nearby_strict_inward_edges':len(look),
            'distinct_child_terminals_reachable':len(groups),
            'status':'NO_INWARD_CHILD_GRAPH_CANDIDATE',
            'geographically_supported_only':True,
            'same_basin_identity_verified':False,
            'outside_crop_contribution_km2_applied':0.,
            'selected_candidate':None,
            'other_terminal_options':[],
        }
        if groups:
            best=groups[0];dist,src,t=best
            r,c=divmod(src,nc);tr,tc=t['terminal_row_col']
            old_exit_near=[(float(np.hypot(x[tc]-o['crossing_east_north_km'][0],
                                             y[tr]-o['crossing_east_north_km'][1])),o['key'])
                           for o in exits if o['side']==t['terminal_side']]
            old_exit_near.sort()
            outlet_match=old_exit_near[0] if old_exit_near and old_exit_near[0][0]<=outlet_radius_km else None
            record['status']='AMBIGUOUS_MULTIPLE_CHILD_TERMINALS' if len(groups)>1 else 'ONE_GEOMETRIC_CHILD_ROUTE_HINT_NOT_VERIFIED'
            record['selected_candidate']={
                'child_start_row_col':[r,c],
                'distance_to_historical_inlet_km':dist,
                'terminal_row_col':t['terminal_row_col'],
                'terminal_side':t['terminal_side'],
                'terminal_recorded_in_projection':(tr,tc) in terminals,
                'path_length_edges':t['length_edges'],
                'strict_downhill_edges':t['strict_downhill_edges'],
                'withheld_unsafe_edges':t['withheld_unsafe_edges'],
                'lake_proxy_jumps':t['lake_proxy_jumps'],
                'same_side_macro_exit_near_only':(
                    None if outlet_match is None else {'key':outlet_match[1],
                                                        'distance_km':outlet_match[0]}),
                'full_continuity_as_physical_river_verified':False,
            }
            record['other_terminal_options']=[{'terminal_row_col':t1['terminal_row_col'],
                                                'distance_km':d1} for d1,_,t1 in groups[1:]]
            drawn.append({'inlet':inlet,'start':[r,c],'route':t,'exit':outlet_match})
        records.append(record)
    audit={
        'status':'P4_C1_COARSE_INLET_TO_CHILD_DOMINANT_GRAPH_HINTS_NOT_RIVERS',
        'is_approved_river_map':False,
        'same_macro_to_child_basin_identity_established':False,
        'external_inflow_area_injected_km2':0.,
        'historical_A8_D8_is_authoritative':False,
        'P4B_safe_edges_immutable':len(safe),
        'P4B_withheld_edges_immutable':len(withheld),
        'P2_geometric_lake_proxy_jumps_NOT_WATER':len(proxy),
        'P2_lake_topology_status':ledger.get('lake_topology_status'),
        'source_macro_inlet_count':len(inlets),
        'source_macro_exit_count':len(exits),
        'child_graph_terminal_count':len(terminals),
        'inlets_with_candidate_internal_graph':sum(t['selected_candidate'] is not None for t in records),
        'inlet_corridor_search_boundary_band_km':boundary_band_km,
        'inlet_corridor_search_radius_km':crossing_radius_km,
        'outlet_near_only_radius_km':outlet_radius_km,
        'inlet_results':records,
        'unresolved':[
            'A8 D8 catchment area may count cells already inside fine crop',
            'nearest inward child segment not physically connected across crop boundary',
            'MFD dominant path and D8 source watercourse may be different catchments',
            'virtual-fill/uphill withheld edges break strict raw-DEM river proof',
            'lake proxy transitions do not establish water occupancy or real channels',
            'permanence, discharge, groundwater, baseflow and water balance unknown',
        ],
    }
    return audit, {'selected_paths':drawn}


def render_evidence(child: dict, map_image: Image.Image, audit: dict,
                    geometries: dict, output: Path) -> None:
    z=np.asarray(child['child_elevation_m']);nr,nc=z.shape
    if map_image.mode!='RGB' or map_image.width%nc or map_image.height%nr:
        raise BoundaryCorridorError('P4-A geographical source image dimensions inconsistent')
    sx=map_image.width/nc;sy=map_image.height/nr
    if abs(sx-sy)>1e-8:raise BoundaryCorridorError('map aspect grid inconsistent')
    x=np.asarray(child['east_km']);y=np.asarray(child['north_km_north_first'])
    image=map_image.convert('RGBA');overlay=Image.new('RGBA',image.size,(0,0,0,0));d=ImageDraw.Draw(overlay)
    def pixel(row,col):return ((col+.5)*sx,(row+.5)*sy)
    def geo(xk,yk):return ((xk-x[0])/(x[-1]-x[0])*(nc-1)+.5)*sx,((y[0]-yk)/(y[0]-y[-1])*(nr-1)+.5)*sy
    for path in geometries['selected_paths']:
        for src,dst,typ in path['route']['segments']:
            r,c=divmod(src,nc);rr,cc=divmod(dst,nc)
            if typ=='safe':
                d.line([pixel(r,c),pixel(rr,cc)],fill=(246,195,84,190),width=max(2,int(sx*.31)))
            else:
                px,py=pixel(r,c); d.ellipse([px-3,py-3,px+3,py+3],fill=(174,55,103,230))
        ir,ic=path['start'];bx,by=pixel(ir,ic)
        d.rectangle((bx-6,by-6,bx+6,by+6),fill=(243,220,134,240),outline=(32,31,25,255),width=2)
        px,py=geo(*path['inlet']['crossing_east_north_km'])
        d.polygon([(px,py-11),(px+11,py+9),(px-11,py+9)],fill=(224,107,57,240))
        tr,tc=path['route']['terminal_row_col'];ex,ey=pixel(tr,tc)
        d.ellipse((ex-10,ey-10,ex+10,ey+10),fill=(231,195,87,240),outline=(40,50,46,255),width=2)
    map_out=Image.alpha_composite(image,overlay).convert('RGB')
    w,h=map_out.size; margin=72;top=90;foot=207
    sheet=Image.new('RGB',(w+2*margin,h+top+foot),(239,235,222));sheet.paste(map_out,(margin,top))
    p=ImageDraw.Draw(sheet)
    p.text((margin,22),'ОСВЕРА / РАЙОН A — ПРОВЕРКА ГРАНИЧНОЙ СВЯЗНОСТИ',fill='#414a3a',font=_font(30))
    yy=top+h+25
    for line in (
        'Треугольник — старый A8/D8 вход (не подтверждён в MFD)',
        'Жёлтый — путь по MFD-проекции, пурпурный — разрыв доказательств',
        'Старая A8 и новая MFD могут описывать РАЗНЫЕ водосборы',
        'Внешние притоки: 0 км² автоматически; это НЕ карта рек',
    ):
        p.text((margin+12,yy),line,fill='#475143',font=_font(22));yy+=39
    output.mkdir(parents=True,exist_ok=False)
    map_out.save(output/'boundary-corridor-evidence-map.png',optimize=True)
    sheet.save(output/'boundary-corridor-evidence-sheet.png',optimize=True)
    (output/'boundary-corridor-audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf8')


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('macro-npz','child-npz','child-manifest','projection-npz',
                'projection-manifest','p4b-masks-npz','p4b-audit-json','p4a-map-image'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--boundary-band-km',type=float,default=12.)
    p.add_argument('--crossing-radius-km',type=float,default=30.)
    p.add_argument('--outlet-radius-km',type=float,default=30.)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    def arrays(path):
        with np.load(path,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
    macro,child,proj,mask=map(arrays,(args.macro_npz,args.child_npz,args.projection_npz,args.p4b_masks_npz))
    child_meta=json.loads(args.child_manifest.read_text(encoding='utf8'))
    report=json.loads(args.projection_manifest.read_text(encoding='utf8'))
    p4b=json.loads(args.p4b_audit_json.read_text(encoding='utf8'))
    # Same EXACT child/projection file bytes as the preceding P4-B audit.
    hashes=p4b.get('input_sha256',{})
    for key,path in [('child_npz',args.child_npz),('projection_npz',args.projection_npz),
                     ('p4a_image',args.p4a_map_image)]:
        with path.open('rb') as f:actual=file_digest(f,'sha256').hexdigest()
        if hashes.get(key)!=actual:raise BoundaryCorridorError(f'P4-B hash lineage mismatch: {key}')
    audit,geometry=reconcile_boundary(
        macro,child,child_meta,proj,report,mask,p4b,
        boundary_band_km=args.boundary_band_km,
        crossing_radius_km=args.crossing_radius_km,
        outlet_radius_km=args.outlet_radius_km)
    with Image.open(args.p4a_map_image) as im:img=im.convert('RGB')
    if args.output.exists():raise BoundaryCorridorError('output directory must not exist')
    audit['input_sha256']={}
    for key in ('macro_npz','child_npz','child_manifest','projection_npz',
                'projection_manifest','p4b_masks_npz','p4b_audit_json','p4a_map_image'):
        with getattr(args,key).open('rb') as inp:
            audit['input_sha256'][key]=file_digest(inp,'sha256').hexdigest()
    audit['p4b_child_projection_and_p4a_map_exact_file_lineage_verified']=True
    render_evidence(child,img,audit,geometry,args.output)
    print(json.dumps(audit,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
