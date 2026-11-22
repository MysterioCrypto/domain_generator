from __future__ import annotations

"""P4-H: cause-localized directional-bias diagnosis, NONCANONICAL.

The parent-only interpolant is a **negative control**, not a valid physical
terrain or map. The same accepted routing algorithm is used with all models.
Do not confuse eight-connected channel edges with continuous MFD direction.
"""

import argparse
import json
import csv
from hashlib import file_digest
from pathlib import Path
from math import pi
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from domain_generator.hydrology.routing import priority_flood_surfaces
from domain_generator.hydrology.continuous import continuous_routing_field
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection


class DirectionBiasError(ValueError):
    pass


STRENGTHS = (0.0, 0.5, 1.25, 2.0)
SNAP_DEG = 7.5
RUN_CELLS = 8


def _sha(path:Path)->str:
    with path.open('rb') as f:return file_digest(f,'sha256').hexdigest()


def _npz(path:Path)->dict:
    with np.load(path,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}


def _font(n:int):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(path).exists():return ImageFont.truetype(path,n)
    return ImageFont.load_default()


def angular_gap_rad(a,b):
    return np.abs(np.arctan2(np.sin(np.asarray(a)-np.asarray(b)),np.cos(np.asarray(a)-np.asarray(b))))


def snap_fraction(angle, mask, *, tol_deg=SNAP_DEG):
    if not 0<tol_deg<22.5:raise DirectionBiasError('octant tolerance invalid')
    a=np.asarray(angle,dtype=float)
    if a.shape!=np.asarray(mask).shape:raise DirectionBiasError('angle sample shape mismatch')
    selected=a[np.asarray(mask,bool)]
    selected=selected[np.isfinite(selected)]
    if not selected.size:raise DirectionBiasError('no finite angular samples')
    nearest_gap=np.abs(np.arctan2(np.sin(8*selected),np.cos(8*selected)))/8
    return float(np.mean(nearest_gap<=np.deg2rad(tol_deg)))


def direction_from_elevation(z,spacing:float):
    if not np.isfinite(z).all() or z.ndim!=2 or min(z.shape)<3:
        raise DirectionBiasError('bad elevation raster')
    # raster row increases toward SOUTH, so physical downhill north component
    # is +dZ/d(row_south), and physical downhill east component is -dZ/d(col_east).
    drow,dcol=np.gradient(np.asarray(z,dtype=np.float64),spacing,spacing)
    x=-dcol;y=drow
    a=np.arctan2(y,x)
    a[np.hypot(x,y)<1e-10]=np.nan
    return a


def _edge_angles(edge:np.ndarray,shape:tuple[int,int]):
    e=np.asarray(edge)
    if e.ndim!=2 or e.shape[1]!=2 or not np.issubdtype(e.dtype,np.integer):
        raise DirectionBiasError('invalid ordinary model edge list')
    rows,cols=shape
    if e.size and (np.min(e)<0 or np.max(e)>=rows*cols):
        raise DirectionBiasError('edge out of bounds')
    src=e[:,0];dst=e[:,1]
    dr=dst//cols-src//cols;dc=dst%cols-src%cols
    if np.any(np.maximum(np.abs(dr),np.abs(dc))!=1):
        raise DirectionBiasError('nonadjacent ordinary model edge')
    if len(np.unique(src))!=len(src):
        raise DirectionBiasError('duplicate outgoing ordinary edge')
    return np.arctan2(-dr.astype(float),dc.astype(float)),(dr+1)*3+(dc+1)


def straight_chain_runs(edge:np.ndarray,shape:tuple[int,int],*,min_run:int=RUN_CELLS)->dict:
    """Partition edges into disjoint maximal same-heading directed chains.

    A junction cannot fabricate double-counted edge mileage. For every cell,
    one outgoing link; incoming links from one heading have at most one source.
    """
    angle,heading=_edge_angles(edge,shape)
    nedge=len(edge)
    if not nedge:raise DirectionBiasError('no ordinary edges for straight-run diagnostic')
    source_to_edge=np.full(shape[0]*shape[1],-1,dtype=np.int32)
    source_to_edge[edge[:,0]]=np.arange(nedge,dtype=np.int32)
    # Detect ANY directed receiver cycle, even when the heading changes inside it.
    # Same-heading segmentation alone cannot expose a 2-edge E/W loop.
    states=np.zeros(nedge,dtype=np.uint8)
    for start in range(nedge):
        if states[start]:continue
        trail=[];cursor=start
        while cursor>=0 and states[cursor]==0:
            states[cursor]=1;trail.append(cursor)
            cursor=int(source_to_edge[edge[cursor,1]])
        if cursor>=0 and states[cursor]==1:
            raise DirectionBiasError('directed channel graph contains cycle')
        for node in trail:states[node]=2
    has_predecessor=np.zeros(nedge,dtype=bool)
    for i,target in enumerate(edge[:,1]):
        nxt=source_to_edge[target]
        if nxt>=0 and heading[nxt]==heading[i]:has_predecessor[nxt]=True
    lengths=[]
    for idx in np.flatnonzero(~has_predecessor):
        cursor=int(idx);distance=0;visited=set()
        while cursor>=0:
            if cursor in visited:raise DirectionBiasError('channel graph cycle')
            visited.add(cursor);distance+=1
            next_idx=int(source_to_edge[edge[cursor,1]])
            cursor=next_idx if next_idx>=0 and heading[next_idx]==heading[cursor] else -1
        lengths.append(distance)
    if sum(lengths)!=nedge:
        raise DirectionBiasError('channel edges do not partition into acyclic straight runs')
    return {'straight_run_min_length_cells':min_run,'edge_count':nedge,
            'number_of_maximal_same_heading_runs':len(lengths),
            'maximum_same_heading_run_cells':max(lengths),
            'edges_in_straight_runs_ge_8_fraction':float(sum(x for x in lengths if x>=min_run)/nedge),
            'straight_runs_ge_8_count':int(sum(x>=min_run for x in lengths)),
            'diagonal_edges_fraction':float(np.mean((heading//3!=1)&(heading%3!=1)))}


def _flow_and_grad(child:dict, spacing:float):
    z=np.asarray(child['child_elevation_m'],np.float64)
    f=continuous_routing_field(priority_flood_surfaces(z).routing_elevation_m,
                               cell_size_km=spacing)
    return f.flow_angle_rad,direction_from_elevation(z,spacing)


def inspect_directional_bias(children:dict, macro:dict, meta:dict, archived:dict, p4f:dict, p4g:dict):
    if (tuple(children)!=STRENGTHS or tuple(archived)!=(.5,1.25,2.)
            or p4f.get('status')!='P4_F_INDEPENDENT_CORE_MFD_TERRAIN_VARIANT_TOPOLOGY_NOT_RIVERS'
            or p4g.get('status')!='P4_G_THREE_THRESHOLD_MODEL_CHANNEL_MORPHOLOGY_NOT_RIVERS'
            or p4f.get('geography_or_rivers_approved') is not False
            or p4g.get('is_approved_physical_river_or_Q') is not False
            or p4f.get('baseline_P2B2p4_exact_replay_verified') is not True
            or p4g.get('P4F_threshold_30_bit_exact_all_3_variants') is not True
            or p4f.get('original_parent_stations_preserved')!=p4g.get('P4F_original_63_parent_stations_preserved')):
        raise DirectionBiasError('P4-F/P4-G provenance not consistent or approved elsewhere')
    parent=children[0.0]['parent_interpolated_m']
    baseline=children[2.0]
    shape=parent.shape
    for s,c in children.items():
        if (c['child_elevation_m'].shape!=shape or
                not np.array_equal(c['parent_interpolated_m'],parent) or
                not np.array_equal(c['land_mask'],baseline['land_mask']) or
                not np.array_equal(c['east_km'],baseline['east_km']) or
                not np.array_equal(c['north_km_north_first'],baseline['north_km_north_first'])):
            raise DirectionBiasError('unaligned DEM,parent,mask or metric axes')
    if not np.array_equal(children[0.0]['child_elevation_m'],parent):
        raise DirectionBiasError('parent-only control altered')
    east=np.asarray(baseline['east_km'],float)
    south=np.asarray(baseline['north_km_north_first'],float)
    dx=np.diff(east);dy=np.diff(south)
    if (not np.isfinite(dx).all() or not np.isfinite(dy).all() or
            dx.min()<=0 or dy.max()>=0 or
            not np.allclose(dx,dx[0],atol=1e-8) or not np.allclose(dy,-dx[0],atol=1e-8)):
        raise DirectionBiasError('unequal x/y spacing invalid for direction comparison')
    spacing=float(dx[0]);nr,nc=shape
    base_mask=np.asarray(archived[2.0]['channel_mask'],bool)
    if base_mask.shape!=shape or not np.any(base_mask):raise DirectionBiasError('missing fixed baseline sample')
    fixed=np.asarray(base_mask,bool)
    fixed[0,:]=fixed[-1,:]=False;fixed[:,0]=fixed[:,-1]=False
    if not np.any(fixed):raise DirectionBiasError('no interior reference cells')
    outputs={};stats=[];angles={}
    pdir=direction_from_elevation(parent,spacing)
    for s in STRENGTHS:
        child=children[s]
        if s==0.0:fields,ledger=connected_mfd_channel_projection(child,macro,meta,stream_threshold_km2=30.)
        else:
            # Call accepted current projection even when archives exist, to catch drift.
            fields,ledger=connected_mfd_channel_projection(child,macro,meta,stream_threshold_km2=30.)
            a=archived[s]
            if set(a)!=set(fields) or any(not np.array_equal(a[k],fields[k]) for k in a):
                raise DirectionBiasError('P4-F source projection bit-exact replay failed')
            old=p4f['variant_comparison'][list((.5,1.25,2.)).index(s)]
            if (int(fields['channel_mask'].sum())!=old['channel_mask_cells_NOT_WATER'] or
                    len(ledger['connected_boundary_endpoints'])!=old['connected_channel_terminal_count']):
                raise DirectionBiasError('P4-F archived channel count mismatch')
        mfd,raw=_flow_and_grad(child,spacing)
        edge=fields['channel_edge_flat_from_to']
        starts=edge[:,0];heading,_=_edge_angles(edge,shape)
        run=straight_chain_runs(edge,shape)
        mfd_at_edge=mfd.ravel()[starts]
        if not np.all(np.isfinite(mfd_at_edge)):
            raise DirectionBiasError('selected edge has no continuous MFD angle')
        own=np.asarray(fields['channel_mask'],bool).copy()
        own[0,:]=own[-1,:]=False;own[:,0]=own[:,-1]=False
        valid_fixed=fixed&np.isfinite(raw)&np.isfinite(pdir)&np.isfinite(mfd)
        valid_own=own&np.isfinite(raw)&np.isfinite(pdir)&np.isfinite(mfd)
        if not np.any(valid_fixed) or not np.any(valid_own):
            raise DirectionBiasError('too few angular raster samples')
        ar=angular_gap_rad(raw[valid_fixed],pdir[valid_fixed])
        mr=angular_gap_rad(mfd[valid_fixed],raw[valid_fixed])
        chosen_gap=angular_gap_rad(heading,mfd_at_edge)
        shape_m={**run,
            'relief_strength':s,
            'model_channel_cells':int(np.count_nonzero(fields['channel_mask'])),
            'model_channel_terminal_count':len(ledger['connected_boundary_endpoints']),
            'source_parent_samples_on_fixed_original_channel':int(valid_fixed.sum()),
            'parent_continuous_raw_gradient_octant_snap_on_fixed_sample':snap_fraction(pdir,valid_fixed),
            'current_continuous_raw_gradient_octant_snap_on_fixed_sample':snap_fraction(raw,valid_fixed),
            'current_CONTINUOUS_MFD_octant_snap_on_fixed_sample':snap_fraction(mfd,valid_fixed),
            'raw_child_vs_parent_gradient_abs_turn_mean_deg_on_fixed_sample':float(np.rad2deg(ar.mean())),
            'MFD_vs_raw_child_gradient_abs_turn_mean_deg_on_fixed_sample':float(np.rad2deg(mr.mean())),
            'selected_discrete_receiver_vs_its_CONTINUOUS_MFD_mean_turn_deg':float(np.rad2deg(chosen_gap.mean())),
            'selected_discrete_receiver_vs_its_CONTINUOUS_MFD_p90_turn_deg':float(np.rad2deg(np.percentile(chosen_gap,90))),
            'reference_baseline_mask_octant_snap_excludes_boundary':True,
            'parent_only_is_negative_control_not_valid_geography':s==0.0,
        }
        totals=ledger['internal_mfd_mass_ledger']
        if totals['explicit_external_area_km2']!=0 or abs(totals['balance_error_km2'])>1e-6:
            raise DirectionBiasError('MFD area balance or A8 external area not conserved')
        stats.append(shape_m);outputs[s]=(fields,ledger);angles[s]={'raw':raw,'mfd':mfd}
    parent_only=stats[0]
    report={
       'status':'P4_H_PARENT_ONLY_NEGATIVE_CONTROL_AND_DIRECTIONAL_BIAS_NOT_RIVERS',
       'operator_accepted_geography':False,'physical_river_or_discharge_verified':False,
       'parent_only_is_valid_natural_terrain':False,
       'accepted_core_or_A8_modified':False,
       'prior_P4F_and_P4G_model_archives_bit_exact_replayed':True,
       'A8_external_area_autoinjected_km2':0.,
       'sample_frame':'same 2.0 strength 30-km2 model-channel interior pixels for CONTINUOUS direction snapshots',
       'zero_detail_control':'parent_interpolated_m copied as child_elevation_m, rerouted by EXACT accepted Core projection',
       'baseline_anchored_station_count':p4f['original_parent_stations_preserved'],
       'raw_direction_octant_snap_tolerance_deg':SNAP_DEG,
       'same_direction_chain_min_run_cells':RUN_CELLS,
       'metrics':stats,
       'limitations':['A8 macro raster and interpolation jointly define parent terrain; cannot isolate interpolation algorithm without a new interpolation-method control',
          'parent-only negative control overproduces model channels and does not represent an acceptable natural terrain',
          'model 1-receiver path is necessarily 8-way and quantized; continuous MFD resultant is distinct',
          'long straight runs quantify visual regularity, not physical river geometry',
          'fixed baseline sample avoids different-mask confounding for continuous-direction comparisons',
          'MFD is area-routing geometry, not discharge or permanent rivers',
          'no topology-preserving smoothing is applied; that requires a separate proven geometric design'],
       'next_step':'P4-I optional separate interpolation-method control/continuous geometry while holding parent A8 anchors and selected terminal topology fixed',
    }
    return outputs,angles,report


def render_report(outputs,angles,report,backgrounds,out):
    if out.exists():raise DirectionBiasError('no destructive overwrite')
    shape=next(iter(outputs.values()))[0]['channel_mask'].shape
    nrow,ncol=shape
    scale=4;panel_w=ncol*scale;panel_h=nrow*scale
    margin=44;gap=20;top=110;bottom=185
    w=margin*2+4*panel_w+3*gap;h=top+panel_h+bottom
    board=Image.new('RGB',(w,h),(237,234,223));draw=ImageDraw.Draw(board)
    draw.text((margin,13),'ОСВЕРА / P4-H — ДИАГНОСТИКА НАПРАВЛЕННОСТИ',font=_font(31),fill=(44,49,48))
    draw.text((margin,56),'Родительская высота без локальной детали  |  relief_strength: 0.5 / 1.25 / 2.0',font=_font(20),fill=(56,61,56))
    for i,s in enumerate(STRENGTHS):
        x=margin+i*(panel_w+gap)
        if s==0.0:
            bg=Image.new('RGB',(panel_w,panel_h),(218,214,201))
        else:
            with Image.open(backgrounds[s]) as img:bg=img.convert('RGB').resize((panel_w,panel_h),Image.Resampling.BILINEAR)
        background=bg.convert('RGBA')
        paths=Image.new('RGBA',bg.size,(0,0,0,0));lines=ImageDraw.Draw(paths)
        field=outputs[s][0];links=field['channel_edge_flat_from_to'];weight=field['Core_dominant_channel_area_km2_NOT_Q'].ravel()
        for a,b in links:
            r,c=divmod(int(a),ncol);rr,cc=divmod(int(b),ncol)
            pos=((c+.5)*scale,(r+.5)*scale,(cc+.5)*scale,(rr+.5)*scale)
            if s==0.0:
                col=(55,66,78,64);wid=1
            else:
                mass=float(weight[a]);col=(38,76,127,224) if mass>=150 else (66,102,143,146)
                wid=3 if mass>=150 else 1
            lines.line(pos,fill=col,width=wid)
        result=Image.alpha_composite(background,paths).convert('RGB')
        board.paste(result,(x,top));draw.rectangle((x,top,x+panel_w-1,top+panel_h-1),outline=(91,97,90),width=2)
        metric=report['metrics'][i]
        draw.text((x,top+panel_h+14),f'{"Без детали / контроль" if s==0. else f"Деталь {s:g}"}',font=_font(21),fill=(52,56,53))
        draw.text((x,top+panel_h+44),f'Прямые цепочки ≥8: {metric["edges_in_straight_runs_ge_8_fraction"]:.1%}',font=_font(17),fill=(55,60,58))
        draw.text((x,top+panel_h+68),f'Макс. прямая: {metric["maximum_same_heading_run_cells"]} яч.',font=_font(17),fill=(55,60,58))
        draw.text((x,top+panel_h+93),f'Модельных рёбер: {metric["edge_count"]:,}',font=_font(17),fill=(55,60,58))
    draw.text((margin,h-43),'Только 1-receiver модельные рёбра. Родительский контроль НЕ является допустимой картой природных рек.',font=_font(19),fill=(75,64,60))
    out.mkdir(parents=True)
    board.save(out/'p4h-parent-vs-detail-directional-run-review.png',compress_level=3)
    # Separate compact quantitative bar chart; fixed reference and explicit labels.
    bar=Image.new('RGB',(1180,605),(245,243,233));p=ImageDraw.Draw(bar)
    p.text((36,22),'P4-H / ДЛИННЫЕ ПРЯМЫЕ СЕГМЕНТЫ',font=_font(29),fill=(46,48,45))
    p.text((36,69),'Часть всех рёбер в максимальных цепочках одного направления, длина от 8 ячеек',font=_font(17),fill=(52,53,50))
    for i,m in enumerate(report['metrics']):
        yy=130+i*92;val=m['edges_in_straight_runs_ge_8_fraction'];strength=m['relief_strength']
        label='Контроль: только parent' if strength==0 else f'relief_strength={strength:g}'
        p.text((35,yy-2),label,font=_font(20),fill=(47,52,49))
        width=int(630*val);col=(125,80,81) if strength==0 else (43,82,120)
        p.rectangle((340,yy,340+630,yy+32),fill=(225,225,214))
        if width:p.rectangle((340,yy,340+width,yy+32),fill=col)
        p.text((990,yy),f'{val:.1%}',font=_font(22),fill=(46,54,54))
    p.text((35,530),'Сравнение не подтверждает физические реки. Parent-only — диагностический контрфакт.',font=_font(17),fill=(85,65,65))
    bar.save(out/'p4h-directional-straight-run-metrics.png',compress_level=3)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('macro-npz','baseline-child-npz','child-manifest','variant-0p5-npz','variant-1p25-npz',
                 'archived-0p5-npz','archived-1p25-npz','archived-2p0-npz',
                 'p4f-audit-json','p4g-audit-json','terrain-0p5-png','terrain-1p25-png','terrain-2p0-png'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise DirectionBiasError('output exists: no overwrite')
    f=json.loads(a.p4f_audit_json.read_text('utf8'))
    g=json.loads(a.p4g_audit_json.read_text('utf8'))
    fsrc=f.get('source_sha256',{});gsrc=g.get('input_sha256',{})
    paths={
      'macro_npz':a.macro_npz,'baseline_child_npz':a.baseline_child_npz,'child_manifest':a.child_manifest,
      'variant_0p5_npz':a.variant_0p5_npz,'variant_1p25_npz':a.variant_1p25_npz,
      'baseline_projection_npz':a.archived_2p0_npz,
      'p4f_projection_0.5':a.archived_0p5_npz,'p4f_projection_1.25':a.archived_1p25_npz,
    }
    for key,path in paths.items():
        expected=gsrc.get(key)
        if key in fsrc and fsrc[key]!=expected:raise DirectionBiasError('P4-F/P4-G source audit disagreement: '+key)
        if _sha(path)!=expected:raise DirectionBiasError('P4-G source SHA mismatch: '+key)
    if _sha(a.p4f_audit_json)!=gsrc.get('p4f_audit_json'):
        raise DirectionBiasError('prior P4-F audit source mismatch')
    macro=_npz(a.macro_npz);base=_npz(a.baseline_child_npz)
    children={0.0:{k:v.copy() for k,v in base.items()},
              .5:_npz(a.variant_0p5_npz),1.25:_npz(a.variant_1p25_npz),2.:base}
    children[0.0]['child_elevation_m']=base['parent_interpolated_m'].copy()
    a30={.5:_npz(a.archived_0p5_npz),1.25:_npz(a.archived_1p25_npz),2.:_npz(a.archived_2p0_npz)}
    outputs,angles,report=inspect_directional_bias(children,macro,json.loads(a.child_manifest.read_text('utf8')),a30,f,g)
    backgrounds={.5:a.terrain_0p5_png,1.25:a.terrain_1p25_png,2.:a.terrain_2p0_png}
    render_report(outputs,angles,report,backgrounds,a.output)
    report['source_sha256']={k:_sha(v) for k,v in paths.items()}
    report['source_sha256'].update({'p4f_audit_json':_sha(a.p4f_audit_json),'p4g_audit_json':_sha(a.p4g_audit_json)})
    report['P4G_parent_and_variant_source_sha_checked']=True
    (a.output/'p4h-directional-bias-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    with (a.output/'p4h-directional-bias-metrics.csv').open('w',encoding='utf8',newline='') as c:
        keys=list(report['metrics'][0]);writer=csv.DictWriter(c,fieldnames=keys);writer.writeheader();writer.writerows(report['metrics'])
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
