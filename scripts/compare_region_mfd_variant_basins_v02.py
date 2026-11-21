from __future__ import annotations

"""P4-F: independently re-route P4-E child DEMs with unchanged Core MFD.

Diagnostic-only. Dominant-receiver terminal identities are a discrete MODEL
partition, not the fractional MFD catchment and never physical catchment IDs.
Macro A8 entrance/exit are coarse, not authoritative new river geometry.
"""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection


class VariantRoutingError(ValueError):
    pass


STRENGTHS = (0.5, 1.25, 2.0)
SIDES = ('north', 'south', 'east', 'west')


def sha(path: Path) -> str:
    with path.open('rb') as f:
        return file_digest(f, 'sha256').hexdigest()


def boundary_mask(shape):
    rows, cols = shape
    mask = np.zeros(shape, dtype=bool)
    mask[0] = mask[-1] = True
    mask[:, 0] = mask[:, -1] = True
    return mask


def terminal_ids(receiver: np.ndarray, proxy_jumps=None) -> np.ndarray:
    """Follow immutable model's 1-receiver projection, never allocate water.

    A nonlocal receiver is permitted ONLY if it is enumerated as a lake-proxy
    edge, whose semantics are not physical water or an actual lake.
    """
    receiver = np.asarray(receiver)
    if (receiver.ndim != 2 or min(receiver.shape) < 3 or
            not np.issubdtype(receiver.dtype, np.integer)):
        raise VariantRoutingError('invalid dominant receiver raster')
    rows, cols = receiver.shape
    edge = boundary_mask(receiver.shape).ravel()
    f = receiver.ravel()
    if np.any(f < -1) or np.any(f >= f.size):
        raise VariantRoutingError('receiver outside model')
    proxy_set = set()
    if proxy_jumps is not None:
        p = np.asarray(proxy_jumps)
        if p.size:
            if p.ndim != 2 or p.shape[1] != 2 or not np.issubdtype(p.dtype, np.integer):
                raise VariantRoutingError('invalid proxy list')
            proxy_set = set(map(tuple,p.tolist()))
    found = np.full(f.size, -1, dtype=np.int32)
    for i in range(f.size):
        if found[i] >= 0:
            continue
        trail = []
        seen = set()
        cur = i
        while found[cur] < 0:
            if cur in seen:
                raise VariantRoutingError('dominant receiver cycle')
            seen.add(cur)
            trail.append(cur)
            if edge[cur]:
                if f[cur] != -1:
                    raise VariantRoutingError('edge must terminate, not route outside model')
                terminal = cur
                break
            nxt = int(f[cur])
            if nxt < 0:
                raise VariantRoutingError('interior model route ends before boundary')
            a,b=divmod(cur,cols);c,d=divmod(nxt,cols)
            if max(abs(a-c),abs(b-d))!=1 and (cur,nxt) not in proxy_set:
                raise VariantRoutingError('unreported nonlocal receiver')
            cur=nxt
        else:
            terminal = int(found[cur])
        for node in trail:
            found[node]=terminal
    if np.any(found < 0) or not np.all(edge[found]):
        raise VariantRoutingError('terminal resolution invalid')
    return found.reshape(receiver.shape)


def terminal_sides(ids: np.ndarray) -> np.ndarray:
    rows, cols = ids.shape
    rr = ids // cols
    cc = ids % cols
    side = np.full(ids.shape,-1,dtype=np.int8)
    side[rr == 0] = 0
    side[rr == rows-1] = 1
    # First side wins on corners; same rule for all candidates.
    side[(side < 0)&(cc == cols-1)] = 2
    side[(side < 0)&(cc == 0)] = 3
    if np.any(side < 0):
        raise VariantRoutingError('terminal is not on boundary')
    return side


def fractional_terminal_area_sides(area: np.ndarray) -> dict:
    a = np.asarray(area,dtype=np.float64)
    if a.ndim != 2 or min(a.shape)<3 or not np.isfinite(a).all():
        raise VariantRoutingError('bad fractional MFD area grid')
    return {'north':float(np.sum(a[0])), 'south':float(np.sum(a[-1])),
            'east':float(np.sum(a[1:-1,-1])), 'west':float(np.sum(a[1:-1,0]))}


def iou(a: np.ndarray, b: np.ndarray) -> float:
    one=np.asarray(a,dtype=bool);two=np.asarray(b,dtype=bool)
    if one.shape!=two.shape:
        raise VariantRoutingError('mask shapes differ')
    union=int(np.count_nonzero(one | two))
    return float(np.count_nonzero(one & two)/union) if union else 1.0


def compare_results(children: dict, macro: dict, meta: dict,
                    historical: dict, previous: dict, *,
                    stream_threshold_km2:float=30.0) -> tuple[dict,dict]:
    """Isolated P2-B2.4 routing for every candidate, not P4-D old-route reuse."""
    if (previous.get('status')!='P4_E_ANCHOR_PRESERVING_CHILD_RELIEF_STRENGTH_ALTERNATIVES_NOT_CANON'
            or previous.get('P4A_and_P4D_source_bytes_verified') is not True
            or previous.get('accepted_geography_or_rivers') is not False
            or previous.get('A8_outside_only_catchment_area_injected_km2')!=0):
        raise VariantRoutingError('requires source-verified noncanonical P4-E')
    a=historical.get('audit',historical)
    if (a.get('status')!='P4_C1_COARSE_INLET_TO_CHILD_DOMINANT_GRAPH_HINTS_NOT_RIVERS'
            or a.get('is_approved_river_map') is not False
            or a.get('external_inflow_area_injected_km2')!=0
            or a.get('source_macro_inlet_count')!=1):
        raise VariantRoutingError('requires bounded verified P4-C1 inlet provenance')
    inlet=a['inlet_results'][0]
    start=inlet.get('selected_candidate',{}).get('child_start_row_col')
    recorded_terminal=inlet.get('selected_candidate',{}).get('terminal_row_col')
    if not (isinstance(start,list) and len(start)==2 and
            isinstance(recorded_terminal,list) and len(recorded_terminal)==2):
        raise VariantRoutingError('missing selected P4-C1 reference location')
    if tuple(children)!=STRENGTHS or len(previous.get('variant_scores',()))!=3 or not np.isfinite(stream_threshold_km2) or stream_threshold_km2<=0:
        raise VariantRoutingError('exact three ordered candidates and finite positive threshold required')
    if [row['relief_strength'] for row in previous['variant_scores']]!=list(STRENGTHS):
        raise VariantRoutingError('candidate strength provenance inconsistent')
    base=children[2.0]
    shape=np.asarray(base['child_elevation_m']).shape
    if shape!=tuple(previous['source_child_grid_shape']):
        raise VariantRoutingError('source grid dimensions mismatch')
    if not (0<=start[0]<shape[0] and 0<=start[1]<shape[1]):
        raise VariantRoutingError('P4-C1 source point outside current DEM')
    base_parent=np.asarray(base['parent_interpolated_m'])
    base_land=np.asarray(base['land_mask'])
    previous_anchors=previous['source_parent_station_count']
    for s,c in children.items():
        row=previous['variant_scores'][STRENGTHS.index(s)]
        if (row['parent_anchor_count']!=previous_anchors or
                row['maximum_parent_anchor_error_m']>1e-6 or
                row['fixed_land_cells']!=int(np.count_nonzero(base_land)) or
                not np.array_equal(c['parent_interpolated_m'],base_parent) or
                not np.array_equal(c['land_mask'],base_land) or
                not np.array_equal(c['east_km'],base['east_km']) or
                not np.array_equal(c['north_km_north_first'],base['north_km_north_first'])):
            raise VariantRoutingError('anchor, parent field, land mask or grid changed')
    outputs={};scores=[];side_grids={};roots={};masks={}
    for s,child in children.items():
        fields,ledger=connected_mfd_channel_projection(child,macro,meta,
                        stream_threshold_km2=stream_threshold_km2)
        balance=ledger['internal_mfd_mass_ledger']
        all_area=float(balance['local_source_area_km2'])
        if (balance['explicit_external_area_km2']!=0 or
            abs(balance['boundary_terminal_area_km2']-all_area)>1e-8*all_area or
            ledger['is_physical_discharge_or_approved_river'] is not False or
            ledger['no_external_A8_source_area_auto_injected'] is not True or
            ledger['lake_topology_status'].startswith('UNRESOLVED')):
            raise VariantRoutingError('model mass balance, lake topology or no-water contract failed')
        mask=fields['channel_mask'].astype(bool)
        root=terminal_ids(fields['Core_dominant_receiver_index'],fields['lake_proxy_jumps_flat_from_to'])
        if s==2.0 and root[tuple(start)]!=int(recorded_terminal[0]*shape[1]+recorded_terminal[1]):
            raise VariantRoutingError('old P4-C1 inlet no longer leads to recorded model terminal')
        alloc=fractional_terminal_area_sides(fields['MFD_contributing_area_km2_NOT_Q'])
        if abs(sum(alloc.values())-all_area)>max(.15,all_area*1e-5):
            # MFD stored float32, whereas ledger uses float64.
            raise VariantRoutingError('model boundary fractional-area reconciliation failed')
        pcell=int(root[tuple(start)]);pr,pc=divmod(pcell,shape[1])
        sides=terminal_sides(root)
        roots[s]=root;masks[s]=mask;side_grids[s]=sides
        outputs[s]=(fields,ledger)
        scores.append({
          'relief_strength':s,
          'channel_mask_cells_NOT_WATER':int(mask.sum()),
          'ordinary_dominant_channel_edges':int(len(fields['channel_edge_flat_from_to'])),
          'lake_proxy_jumps_NOT_WATER':int(len(fields['lake_proxy_jumps_flat_from_to'])),
          'connected_channel_terminal_count':len(ledger['connected_boundary_endpoints']),
          'fractional_MFD_boundary_area_by_side_km2_NOT_Q':alloc,
          'area_local_source_km2':all_area,
          'area_balance_error_km2':float(balance['balance_error_km2']),
          'historical_P4C1_inlet_reference_cell':start,
          'same_inlet_new_dominant_terminal_cell':[int(pr),int(pc)],
          'same_inlet_new_dominant_terminal_side':SIDES[int(sides[tuple(start)])],
          'all_grid_dominant_terminal_same_exact_cell_vs_2p0_fraction':None,
          'all_grid_dominant_terminal_same_side_vs_2p0_fraction':None,
          'channel_support_iou_vs_2p0':None,
          'channel_support_symmetric_difference_cells_vs_2p0':None,
          'top_channel_terminations':ledger['connected_boundary_endpoints'][:5],
          'lake_topology_status':ledger['lake_topology_status']
        })
    base_root=roots[2.0];base_mask=masks[2.0];base_sides=side_grids[2.0]
    for score in scores:
        s=score['relief_strength']
        score['all_grid_dominant_terminal_same_exact_cell_vs_2p0_fraction']=float(np.mean(roots[s]==base_root))
        score['all_grid_dominant_terminal_same_side_vs_2p0_fraction']=float(np.mean(side_grids[s]==base_sides))
        score['channel_support_iou_vs_2p0']=iou(masks[s],base_mask)
        score['channel_support_symmetric_difference_cells_vs_2p0']=int(np.count_nonzero(masks[s]^base_mask))
        score['historical_source_terminal_changed_exact_pixel']=bool(roots[s][tuple(start)]!=base_root[tuple(start)])
        score['dominant_boundary_root_change_cells']=int(np.count_nonzero(roots[s]!=base_root))
    result={
      'status':'P4_F_INDEPENDENT_CORE_MFD_TERRAIN_VARIANT_TOPOLOGY_NOT_RIVERS',
      'geography_or_rivers_approved':False,
      'no_accepted_Core_changes':True,
      'no_A8_external_inflow_injected_km2':0.,
      'P4C1_coarse_A8_to_new_MFD_basin_identity_proved':False,
      'independently_recomputed_for_each_variant':True,
      'dominant_root_is_model_only_not_fractional_MFD_basin':True,
      'source_sample_is_from_P4C1_geometry_only':True,
      'original_parent_stations_preserved':previous_anchors,
      'stream_threshold_km2_NOT_Q':stream_threshold_km2,
      'variant_comparison':scores,
      'pairwise_channel_mask_iou_0p5_vs_1p25':iou(masks[.5],masks[1.25]),
      'limitations':['core MFD fractions are area-transport proxies not physical runoff/discharge',
                     'dominant outlet partition is one-receiver projection, not fractional MFD catchment identity',
                     'lake proxy topology is nonphysical; no lake water storage/occupancy proved',
                     'old P4-C1 source point and old A8 exit are only positional hints',
                     'river permanence, external rainfall and perennial Q still unknown'],
      'next_step':'P4-G evaluate model river morphology/placement constraints and author visual review without automatic acceptance',
    }
    return {'outputs':outputs,'roots':roots,'sides':side_grids,'masks':masks},result


def _font(size):
    for name in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(name).exists():
            return ImageFont.truetype(name,size)
    return ImageFont.load_default()


def render_sheet(analysis:dict, audit:dict, terrain_png_by_strength:dict,
                 output:Path):
    """Top: newly re-routed model edges. Bottom: exit-cell stability vs baseline."""
    strength=STRENGTHS
    sizes=[]
    for s in strength:
        with Image.open(terrain_png_by_strength[s]) as picture:
            sizes.append(picture.size)
    if len(set(sizes))!=1 or sizes[0][0]!=sizes[0][1]:
        raise VariantRoutingError('three aligned square terrain images required')
    n=sizes[0][0]
    shape=analysis['roots'][2.0].shape
    if n%shape[1]!=0 or n//shape[1]<2:
        raise VariantRoutingError('terrain image scale does not match model grid')
    cell=n//shape[1]
    margin=60; gap=25;top=90;between=70;bottom=160
    sheet=Image.new('RGB',(3*n+2*margin+2*gap,2*n+top+between+bottom),(240,235,220))
    draw=ImageDraw.Draw(sheet)
    draw.text((margin,19),'ОСВЕРА / P4-F — МОДЕЛЬНЫЕ MFD-КОРИДОРЫ (НЕ РЕКИ)',
              font=_font(29),fill=(48,50,45))
    start=audit['variant_comparison'][0]['historical_P4C1_inlet_reference_cell']
    for i,s in enumerate(strength):
        x=margin+i*(n+gap)
        with Image.open(terrain_png_by_strength[s]) as picture:
            terrain=picture.convert('RGBA').copy()
        paint=Image.new('RGBA',terrain.size,(0,0,0,0))
        pen=ImageDraw.Draw(paint)
        edges=analysis['outputs'][s][0]['channel_edge_flat_from_to']
        ncols=shape[1]
        for src,dest in edges:
            sr,sc=divmod(int(src),ncols);tr,tc=divmod(int(dest),ncols)
            pen.line(((sc+.5)*cell,(sr+.5)*cell,(tc+.5)*cell,(tr+.5)*cell),
                     fill=(63,65,147,208),width=max(1,cell//3))
        for endpoint in audit['variant_comparison'][i]['top_channel_terminations'][:5]:
            rr,cc=endpoint['child_edge_cell_row_col'];cx=(cc+.5)*cell;cy=(rr+.5)*cell
            pen.ellipse((cx-5,cy-5,cx+5,cy+5),fill=(239,102,43,255))
        sr,sc=start;px=(sc+.5)*cell;py=(sr+.5)*cell
        pen.ellipse((px-7,py-7,px+7,py+7),fill=(249,243,185,255),outline=(46,46,47,255),width=2)
        topmap=Image.alpha_composite(terrain,paint).convert('RGB')
        sheet.paste(topmap,(x,top))
        score=audit['variant_comparison'][i]
        draw.text((x,top+n+10),f'strength={s:g} | ends={score["connected_channel_terminal_count"]} | overlap={score["channel_support_iou_vs_2p0"]:.1%}',
                  font=_font(17),fill=(52,55,47))
        if s==2.0:
            side=analysis['sides'][s]
            palette=np.array([[143,126,171],[178,130,96],[190,164,112],[91,151,133]],dtype=np.uint8)
            lower=palette[side]
        else:
            exact=analysis['roots'][s]==analysis['roots'][2.0]
            same_side=analysis['sides'][s]==analysis['sides'][2.0]
            lower=np.empty((*shape,3),dtype=np.uint8)
            lower[exact]=[106,158,124]
            lower[~exact & same_side]=[218,163,87]
            lower[~same_side]=[165,80,91]
        frame=Image.fromarray(lower,'RGB').resize((n,n),Image.Resampling.NEAREST)
        sheet.paste(frame,(x,top+n+between))
        y=top+n+between+n+10
        draw.text((x,y),f'Exact terminal: {score["all_grid_dominant_terminal_same_exact_cell_vs_2p0_fraction"]:.1%}  |  Same side: {score["all_grid_dominant_terminal_same_side_vs_2p0_fraction"]:.1%}',
                  font=_font(16),fill=(52,55,47))
        if s!=2.0:
            for rgb,label,offset in [((106,158,124),'same pixel',0),((218,163,87),'other pixel',175),((165,80,91),'other side',355)]:
                yy=y+32;draw.rectangle((x+offset,yy,x+offset+14,yy+14),fill=rgb)
                draw.text((x+offset+20,yy-3),label,font=_font(14),fill=(55,52,49))
    yy=top+2*n+between+67
    draw.text((margin,yy),'Верх: новые модельные 1D рёбра Core (фиолетовый), 5 крупнейших терминалов (оранжевый), исходная проба P4-C1 (светлая).',
              font=_font(17),fill=(59,60,52))
    draw.text((margin,yy+27),'Низ: Вариант 2.0 — сторона выхода. Остальные — изменение конечного пикселя по сравнению с 2.0.',
              font=_font(17),fill=(59,60,52))
    draw.text((margin,yy+54),'Это топология моделирования, НЕ карта постоянных рек, расхода воды или подтверждённых бассейнов.',
              font=_font(17),fill=(59,60,52))
    output.mkdir(parents=True,exist_ok=False)
    sheet.save(output/'region-mfd-variant-topology-sheet.png',optimize=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('macro-npz','baseline-child-npz','child-manifest',
                 'baseline-projection-npz','baseline-projection-manifest',
                 'variant-0p5-npz','variant-1p25-npz','p4e-audit-json','p4c1-audit-json',
                 'terrain-0p5-png','terrain-1p25-png','terrain-2p0-png'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise VariantRoutingError('no destructive overwrite allowed')
    def read(path):
        with np.load(path,allow_pickle=False) as a:return {k:a[k].copy() for k in a.files}
    e=json.loads(args.p4e_audit_json.read_text(encoding='utf8'))
    c=json.loads(args.p4c1_audit_json.read_text(encoding='utf8'))
    c1=c.get('audit',c)
    for id,path in [('macro_npz',args.macro_npz),('child_npz',args.baseline_child_npz),('child_manifest',args.child_manifest)]:
        if sha(path)!=e.get('source_sha256',{}).get(id) or sha(path)!=c1.get('input_sha256',{}).get(id):
            raise VariantRoutingError('P4-E/P4-C1 independent source hash mismatch '+id)
    for id,path in [('projection_npz',args.baseline_projection_npz),('projection_manifest',args.baseline_projection_manifest)]:
        if sha(path)!=c1.get('input_sha256',{}).get(id):
            raise VariantRoutingError('P4-C1 projection hash mismatch '+id)
    for i,name in enumerate(('variant_0p5_npz','variant_1p25_npz')):
        if (e.get('variant_scores',[{},{}])[i].get('derived_variant_npz_sha256')!=sha(getattr(args,name))):
            raise VariantRoutingError('P4-E alternative variant SHA mismatch')
    children={.5:read(args.variant_0p5_npz),1.25:read(args.variant_1p25_npz),2.:read(args.baseline_child_npz)}
    old=read(args.baseline_projection_npz)
    macro=read(args.macro_npz)
    meta=json.loads(args.child_manifest.read_text(encoding='utf8'))
    analysis,audit=compare_results(children,macro,meta,c,e)
    for k,v in old.items():
        if k not in analysis['outputs'][2.][0] or not np.array_equal(v,analysis['outputs'][2.][0][k]):
            raise VariantRoutingError('P4-F baseline projection does not bit-exactly replay P2-B2.4')
    old_report=json.loads(args.baseline_projection_manifest.read_text(encoding='utf8'))
    if old_report['child_core_dominant_channel_ledger']!=analysis['outputs'][2.][1]:
        raise VariantRoutingError('baseline projection report changed')
    backgrounds={.5:args.terrain_0p5_png,1.25:args.terrain_1p25_png,2.:args.terrain_2p0_png}
    render_sheet(analysis,audit,backgrounds,args.output)
    audit['baseline_P2B2p4_exact_replay_verified']=True
    audit['source_sha256']={key:sha(path) for key,path in (
        ('macro_npz',args.macro_npz),('baseline_child_npz',args.baseline_child_npz),
        ('child_manifest',args.child_manifest),('baseline_projection_npz',args.baseline_projection_npz),
        ('baseline_projection_manifest',args.baseline_projection_manifest),
        ('variant_0p5_npz',args.variant_0p5_npz),('variant_1p25_npz',args.variant_1p25_npz),
        ('p4e_audit_json',args.p4e_audit_json),('p4c1_audit_json',args.p4c1_audit_json))}
    audit['source_existing_P4E_and_P4C1_SHA_checked']=True
    (args.output/'region-mfd-variant-topology-audit.json').write_text(
        json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for s in (.5,1.25):
        fields,report=analysis['outputs'][s]
        np.savez_compressed(args.output/f'mfd-strength-{str(s).replace(".","p")}-derived.npz',**fields)
        (args.output/f'mfd-strength-{str(s).replace(".","p")}-report.json').write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
