from __future__ import annotations

"""P4-G model-channel map scale + topology sensitivity. NOT author rivers.

Nine independently re-calculated Core-based dominant channel projections:
three immutable P4-E DEMs x three *explicit* source thresholds. Reuse only
frozen P4-E P3 color as background. This does not invent river or lake water.
"""

import argparse
import csv
from hashlib import file_digest
import json
from math import hypot
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection


class ChannelScaleError(ValueError):
    pass


STRENGTHS = (0.5, 1.25, 2.0)
THRESHOLDS = (15., 30., 60.)


def _sha(path: Path) -> str:
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def _read_npz(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as source:
        return {name:source[name].copy() for name in source.files}


def _font(size):
    for name in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(name).is_file():
            return ImageFont.truetype(name,size)
    return ImageFont.load_default()


def channel_morphology(fields:dict, ledger:dict, *, spacing_km:float=1.) -> dict:
    """Directed ordinary edge shape only; no lake-proxy gaps called rivers."""
    mask=np.asarray(fields['channel_mask'], dtype=bool)
    edge=np.asarray(fields['channel_edge_flat_from_to'])
    proxy=np.asarray(fields['lake_proxy_jumps_flat_from_to'])
    if (mask.ndim!=2 or min(mask.shape)<3 or edge.ndim!=2 or edge.shape[1]!=2
            or proxy.ndim!=2 or proxy.shape[1]!=2
            or not np.issubdtype(edge.dtype,np.integer)
            or not np.isfinite(spacing_km) or spacing_km<=0):
        raise ChannelScaleError('bad noncanonical channel topology')
    nr,nc=mask.shape;size=mask.size
    if edge.size and (np.any(edge<0) or np.any(edge>=size)):
        raise ChannelScaleError('channel edge out of bounds')
    src=edge[:,0];dst=edge[:,1]
    dr=dst//nc-src//nc;dc=dst%nc-src%nc
    if np.any(np.maximum(abs(dr),abs(dc))!=1):
        raise ChannelScaleError('ordinary edge not adjacent')
    if not np.all(mask.ravel()[src]):
        raise ChannelScaleError('ordinary source not in recorded channel mask')
    if len(np.unique(src))!=len(src):
        raise ChannelScaleError('non-branching 1-receiver graph source duplicated')
    in_degree=np.bincount(dst,minlength=size)
    nodes=np.flatnonzero(mask.ravel())
    diag=(abs(dr)==1)&(abs(dc)==1)
    terminals=ledger['connected_boundary_endpoints']
    if (int(mask.sum())!=int(ledger['routed_ordinary_channel_cells'])
            or len(edge)!=int(ledger['ordinary_adjacent_channel_edges'])
            or len(proxy)!=int(ledger['nonphysical_proxy_links_NOT_RIVERS'])):
        raise ChannelScaleError('ledger and linked channel topology differ')
    return {
        'ordinary_skeleton_cells':int(mask.sum()),
        'ordinary_edges':len(edge),
        'model_terminal_count':len(terminals),
        'model_topological_headwater_nodes':int(np.sum(in_degree[nodes]==0)),
        'model_confluence_nodes_with_2_or_more_incoming':int(np.sum(in_degree[nodes]>=2)),
        'model_confluence_nodes_with_3_or_more_incoming':int(np.sum(in_degree[nodes]>=3)),
        'ordinary_edge_length_km':float(spacing_km*(np.count_nonzero(~diag)+np.count_nonzero(diag)*2**.5)),
        'diagonal_edge_fraction':float(np.mean(diag)) if len(edge) else 0.,
        'geometric_proxy_jumps_not_water':len(proxy),
        'threshold_headwater_eligibility_count_not_proven_springs':ledger['headwater_seed_cells'],
    }


def iou(a,b):
    x=np.asarray(a,dtype=bool);y=np.asarray(b,dtype=bool)
    if x.shape!=y.shape:
        raise ChannelScaleError('channel masks not aligned')
    n=np.count_nonzero(x|y)
    return float(np.count_nonzero(x&y)/n) if n else 1.


def compare_channel_scale(children:dict,macro:dict,meta:dict,previous:dict,
                          archived:dict,*,thresholds=THRESHOLDS):
    if (tuple(children)!=STRENGTHS or tuple(archived)!=STRENGTHS
            or tuple(float(t) for t in thresholds)!=THRESHOLDS):
        raise ChannelScaleError('explicit 3 strengths x 3 threshold comparison required')
    if (previous.get('status')!='P4_F_INDEPENDENT_CORE_MFD_TERRAIN_VARIANT_TOPOLOGY_NOT_RIVERS'
            or previous.get('source_existing_P4E_and_P4C1_SHA_checked') is not True
            or previous.get('baseline_P2B2p4_exact_replay_verified') is not True
            or previous.get('geography_or_rivers_approved') is not False
            or previous.get('no_A8_external_inflow_injected_km2') != 0
            or len(previous.get('variant_comparison',[]))!=3):
        raise ChannelScaleError('unverified earlier P4-F model audit')
    baseline=children[2.0]
    for strength in STRENGTHS:
        c=children[strength]
        if (not np.array_equal(c['east_km'],baseline['east_km'])
                or not np.array_equal(c['north_km_north_first'],baseline['north_km_north_first'])
                or not np.array_equal(c['parent_interpolated_m'],baseline['parent_interpolated_m'])
                or not np.array_equal(c['land_mask'],baseline['land_mask'])
                or c['child_elevation_m'].shape!=baseline['child_elevation_m'].shape):
            raise ChannelScaleError('parents, coastline or grid moved')
    spacing=float(np.median(np.diff(baseline['east_km'])))
    rows=[];outputs={};threshold_masks={}
    for strength in STRENGTHS:
        for threshold in THRESHOLDS:
            fields,ledger=connected_mfd_channel_projection(children[strength],macro,meta,
                stream_threshold_km2=threshold)
            if (ledger['status']!='CONNECTED_CORE_DOMINANT_MFD_CHANNEL_PROJECTION_NOT_REAL_RIVERS'
                    or ledger['is_physical_discharge_or_approved_river'] is not False
                    or ledger['no_external_A8_source_area_auto_injected'] is not True):
                raise ChannelScaleError('nonphysical model output could not be verified')
            balance=ledger['internal_mfd_mass_ledger']
            if (balance['explicit_external_area_km2']!=0
                    or abs(balance['balance_error_km2'])>1e-6
                    or abs(balance['local_source_area_km2']-balance['boundary_terminal_area_km2'])>1e-6):
                raise ChannelScaleError('MFD conservation and no-external-area failed')
            if threshold==30.:
                # The *entire* archived projection and its source bookkeeping
                # must match. A threshold experiment cannot silently rewrite it.
                original=archived[strength]
                if set(fields)!=set(original) or any(not np.array_equal(fields[k],original[k]) for k in fields):
                    raise ChannelScaleError('original P4-F threshold=30 is not bit-exact')
                row_old=previous['variant_comparison'][STRENGTHS.index(strength)]
                if (len(ledger['connected_boundary_endpoints'])!=row_old['connected_channel_terminal_count']
                        or int(fields['channel_mask'].sum())!=row_old['channel_mask_cells_NOT_WATER']):
                    raise ChannelScaleError('P4-F report counts do not replay')
            key=(strength,threshold)
            shape=channel_morphology(fields,ledger,spacing_km=spacing)
            shape.update({'relief_strength':strength,'stream_threshold_km2_NOT_Q':threshold,
                          'local_area_km2_NOT_WATER':balance['local_source_area_km2'],
                          'conservation_error_km2':balance['balance_error_km2']})
            outputs[key]=(fields,ledger)
            threshold_masks[key]=fields['channel_mask'].astype(bool)
            rows.append(shape)
    for shape in rows:
        s,t=shape['relief_strength'],shape['stream_threshold_km2_NOT_Q']
        original=threshold_masks[(s,30.)];current=threshold_masks[(s,t)]
        shape['mask_iou_vs_30km2']=iou(original,current)
        shape['original_30km2_mask_retained_fraction']=float(np.count_nonzero(current&original)/np.count_nonzero(original)) if np.any(original) else 1.
        shape['new_cells_not_on_30km2_mask']=int(np.count_nonzero(current&~original))
        shape['30km2_cells_missing_from_current']=int(np.count_nonzero(original&~current))
    pairwise=[]
    for t in THRESHOLDS:
        for a,b in ((.5,1.25),(.5,2.0),(1.25,2.0)):
            pairwise.append({'threshold_km2':t,'relief_strength_A':a,'relief_strength_B':b,
                             'channel_mask_iou':iou(threshold_masks[(a,t)],threshold_masks[(b,t)])})
    summary={'status':'P4_G_THREE_THRESHOLD_MODEL_CHANNEL_MORPHOLOGY_NOT_RIVERS',
        'is_accepted_Core_change':False,'is_author_accepted_region_map':False,
        'is_approved_physical_river_or_Q':False,'P4F_threshold_30_bit_exact_all_3_variants':True,
        'P4F_original_63_parent_stations_preserved':previous['original_parent_stations_preserved'],
        'unchanged_accepted_Core_routing_called_for_each_of_9_cases':True,
        'source_grid_shape':list(baseline['child_elevation_m'].shape),
        'thresholds_km2_NOT_Q':list(THRESHOLDS),'morphology':rows,
        'cross_strength_at_fixed_threshold':pairwise,
        'P3_frozen_candidate_landcover_visual_background_NOT_RECOMPUTED':True,
        'A8_old_D8_flow_imported_km2':0,
        'limitations':['threshold controls source detection AND dominant receiver preference; no nested-river expectation',
                       'channel graph is single-receiver model geometry, NOT MFD fractional flow or physical discharge',
                       'headwaters/confluences count graph topology, NOT verified springs or permanent rivers',
                       'map-first terrain colors frozen from candidate P3 and do not establish biome',
                       'fixed chart projection and smoothing are visualization only; no authored region acceptance'],
        'next_bounded_step':'P4-H inspect network hierarchy and major trunk cartographic readability before author selection; no auto-merge'}
    return outputs,summary


def _aligned_background(path: Path, shape:tuple[int,int], pixels_per_cell:int) -> Image.Image:
    """P4-E legacy toy render can square-stretch a non-square 1-km grid.

    Correct that visual-only aspect distortion, NEVER resize domain geometry.
    Any other unexpected size must fail rather than silently crop.
    """
    rows,cols=shape
    expected=(cols*pixels_per_cell,rows*pixels_per_cell)
    with Image.open(path) as source:
        rgb=source.convert('RGB')
    if rgb.size==expected:
        return rgb
    if rows!=cols and rgb.size==(expected[0],expected[0]):
        return rgb.resize(expected,Image.Resampling.BICUBIC)
    raise ChannelScaleError('P4-E terrain map size cannot be aligned with child grid')


def _annotate_sheet(outputs:dict,summary:dict, backgrounds:dict, destination:Path,
                   *,pixels_per_cell=5):
    # Exactly 3×3 aligned panels, same scale, only authored numerical differences.
    if pixels_per_cell not in (4,5,6):
        raise ChannelScaleError('unsupported panel scale')
    shape=tuple(summary['source_grid_shape'])
    panel_w=shape[1]*pixels_per_cell
    panel_h=shape[0]*pixels_per_cell
    margin,gap,label,foot=36,22,85,116
    width=margin*2+3*panel_w+2*gap;height=label+3*panel_h+2*gap+foot
    dest=Image.new('RGB',(width,height),(235,230,217))
    d=ImageDraw.Draw(dest)
    d.text((margin,16),'ОСВЕРА / P4-G — ЧУВСТВИТЕЛЬНОСТЬ МОДЕЛЬНОЙ СЕТИ',font=_font(26),fill=(47,50,45))
    d.text((margin,50),'Слева направо — порог 15 / 30 / 60 км²; сверху вниз — relief_strength 0.5 / 1.25 / 2.0',font=_font(17),fill=(51,59,53))
    for i,s in enumerate(STRENGTHS):
        original=_aligned_background(backgrounds[s],shape,pixels_per_cell)
        for j,t in enumerate(THRESHOLDS):
            x=margin+j*(panel_w+gap);y=label+i*(panel_h+gap)
            pane=original.convert('RGBA')
            layer=Image.new('RGBA',pane.size,(0,0,0,0));lines=ImageDraw.Draw(layer)
            fields,_=outputs[(s,t)]
            links=np.asarray(fields['channel_edge_flat_from_to']);ncol=shape[1]
            unique_area=fields['Core_dominant_channel_area_km2_NOT_Q'].ravel()
            for start,end in links:
                a=int(start);b=int(end)
                ar,ac=divmod(a,ncol);br,bc=divmod(b,ncol)
                # Frame line class by accepted model's unique dominant area.
                weight=float(unique_area[a])
                if weight>=700.: col=(29,64,120,242);w=max(3,pixels_per_cell)
                elif weight>=150.:col=(43,90,143,214);w=max(2,pixels_per_cell//2)
                else:col=(68,109,157,175);w=max(1,pixels_per_cell//3)
                lines.line(((ac+.5)*pixels_per_cell,(ar+.5)*pixels_per_cell,
                            (bc+.5)*pixels_per_cell,(br+.5)*pixels_per_cell),fill=col,width=w)
            composite=Image.alpha_composite(pane,layer).convert('RGB')
            dest.paste(composite,(x,y))
            metric=next(a for a in summary['morphology'] if a['relief_strength']==s and a['stream_threshold_km2_NOT_Q']==t)
            d.rectangle((x,y,x+panel_w-1,y+panel_h-1),outline=(97,101,91),width=2)
            d.rectangle((x+7,y+7,x+225,y+54),fill=(235,233,218))
            d.text((x+14,y+11),f'{s:g} / {t:g} км²  ·  {metric["ordinary_skeleton_cells"]} яч.',font=_font(16),fill=(38,49,51))
            d.text((x+14,y+33),f'Слияний: {metric["model_confluence_nodes_with_2_or_more_incoming"]}',font=_font(15),fill=(48,53,51))
    yy=height-100
    d.text((margin,yy),'Тёмно-синий = крупнее модельная dominant-area; светло-синий = менее поддержанная ветвь.',font=_font(17),fill=(58,58,51))
    d.text((margin,yy+27),'P3 цвета и высоты неизменны внутри строки. Топология пересчитана; линии — НЕ доказанные реки.',font=_font(17),fill=(58,58,51))
    dest.save(destination/'region-model-network-threshold-3x3.png',compress_level=2)


def _render_main_maps(outputs:dict,summary:dict,backgrounds:dict,destination:Path,pixels_per_cell=5):
    # Main side-by-side at the same 30 km² threshold, intended for map review.
    shape=tuple(summary['source_grid_shape']);panel_w=shape[1]*pixels_per_cell;panel_h=shape[0]*pixels_per_cell
    margin=52;gap=26;header=91;footer=130
    canvas=Image.new('RGB',(3*panel_w+2*margin+2*gap,panel_h+header+footer),(233,229,217))
    paint=ImageDraw.Draw(canvas)
    paint.text((margin,14),'ОСВЕРА / P4-G — ГЕОГРАФИЯ МОДЕЛЬНЫХ КОРИДОРОВ',font=_font(28),fill=(45,47,45))
    paint.text((margin,49),'Один порог: 30 км² · три независимых варианта рельефа · одинаковая картографическая основа P3',font=_font(18),fill=(57,64,54))
    for i,s in enumerate(STRENGTHS):
        terrain=_aligned_background(backgrounds[s],shape,pixels_per_cell)
        layer=Image.new('RGBA',terrain.size,(0,0,0,0));draw=ImageDraw.Draw(layer)
        fields,ledger=outputs[(s,30.)];nc=shape[1]
        data=fields['channel_edge_flat_from_to'];weight=fields['Core_dominant_channel_area_km2_NOT_Q'].ravel()
        for a,b in data:
            rr,cc=divmod(int(a),nc);tr,tc=divmod(int(b),nc)
            area=weight[a]
            if area>700.:thick=5;rgb=(27,66,120,245)
            elif area>150.:thick=3;rgb=(43,91,144,215)
            else:thick=2;rgb=(73,115,153,180)
            draw.line(((cc+.5)*pixels_per_cell,(rr+.5)*pixels_per_cell,
                       (tc+.5)*pixels_per_cell,(tr+.5)*pixels_per_cell),fill=rgb,width=thick)
        base=Image.alpha_composite(terrain.convert('RGBA'),layer).convert('RGB')
        x=margin+i*(panel_w+gap);y=header
        canvas.paste(base,(x,y));paint.rectangle((x,y,x+panel_w-1,y+panel_h-1),outline=(94,98,89),width=2)
        metric=next(row for row in summary['morphology'] if row['relief_strength']==s and row['stream_threshold_km2_NOT_Q']==30.)
        paint.text((x,y+panel_h+16),f'Микрорельеф: {s:g} · длина модели: {metric["ordinary_edge_length_km"]:,.0f} км',font=_font(18),fill=(51,55,48))
        paint.text((x,y+panel_h+46),f'Ветвлений: {metric["model_confluence_nodes_with_2_or_more_incoming"]} · граничных окончаний: {metric["model_terminal_count"]}',font=_font(17),fill=(51,55,48))
    paint.text((margin,header+panel_h+94),'Линии показывают только геометрию условной сети Core. Это НЕ готовая карта рек или подтверждённая география.',font=_font(17),fill=(73,72,65))
    canvas.save(destination/'region-network-map-review-3variants.png',compress_level=2)


def render_maps(outputs:dict,summary:dict,backgrounds:dict,out:Path,*,pixels_per_cell=5):
    if out.exists():raise ChannelScaleError('output exists: no overwrite')
    if tuple(backgrounds)!=STRENGTHS:raise ChannelScaleError('must supply three aligned source backgrounds')
    if pixels_per_cell not in (4,5,6):raise ChannelScaleError('pixels_per_cell out of range')
    out.mkdir(parents=True)
    _annotate_sheet(outputs,summary,backgrounds,out,pixels_per_cell=pixels_per_cell)
    _render_main_maps(outputs,summary,backgrounds,out,pixels_per_cell=pixels_per_cell)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('macro-npz','child-manifest','child-0p5-npz','child-1p25-npz','child-2p0-npz',
                 'p4e-audit-json','p4f-audit-json','p4f-0p5-npz','p4f-1p25-npz',
                 'p4f-2p0-npz','terrain-0p5-png','terrain-1p25-png','terrain-2p0-png'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--pixels-per-cell',type=int,default=5)
    args=parser.parse_args()
    if args.output.exists():raise ChannelScaleError('output exists: no overwrite')
    previous=json.loads(args.p4f_audit_json.read_text('utf8'))
    p4e=json.loads(args.p4e_audit_json.read_text('utf8'))
    if (p4e.get('status')!='P4_E_ANCHOR_PRESERVING_CHILD_RELIEF_STRENGTH_ALTERNATIVES_NOT_CANON'
            or p4e.get('source_parent_station_count')!=previous.get('original_parent_stations_preserved')
            or p4e.get('P4A_and_P4D_source_bytes_verified') is not True
            or not previous.get('independently_recomputed_for_each_variant',False)):
        raise ChannelScaleError('P4-E/P4-F prior source guard failed')
    input_files={
        'macro_npz':args.macro_npz,
        'child_manifest':args.child_manifest,
        'baseline_child_npz':args.child_2p0_npz,
        'variant_0p5_npz':args.child_0p5_npz,
        'variant_1p25_npz':args.child_1p25_npz,
        'p4e_audit_json':args.p4e_audit_json,
        'baseline_projection_npz':args.p4f_2p0_npz,
    }
    for key,path in input_files.items():
        if _sha(path)!=previous.get('source_sha256',{}).get(key):
            raise ChannelScaleError('P4-F source SHA mismatch '+key)
    children={.5:_read_npz(args.child_0p5_npz),1.25:_read_npz(args.child_1p25_npz),2.:_read_npz(args.child_2p0_npz)}
    archived={.5:_read_npz(args.p4f_0p5_npz),1.25:_read_npz(args.p4f_1p25_npz),2.:_read_npz(args.p4f_2p0_npz)}
    previous_scores=previous['variant_comparison']
    if any(float(previous_scores[i]['relief_strength'])!=strength for i,strength in enumerate(STRENGTHS)):
        raise ChannelScaleError('archived model order altered')
    macro=_read_npz(args.macro_npz)
    metadata=json.loads(args.child_manifest.read_text('utf8'))
    outputs,summary=compare_channel_scale(children,macro,metadata,previous,archived)
    backgrounds={.5:args.terrain_0p5_png,1.25:args.terrain_1p25_png,2.:args.terrain_2p0_png}
    render_maps(outputs,summary,backgrounds,args.output,pixels_per_cell=args.pixels_per_cell)
    summary['P4E_and_P4F_source_SHA256_verified']=True
    summary['input_sha256']={key:_sha(path) for key,path in input_files.items()}
    summary['input_sha256']['p4f_audit_json']=_sha(args.p4f_audit_json)
    for strength in STRENGTHS:
        path={.5:args.p4f_0p5_npz,1.25:args.p4f_1p25_npz,2.:args.p4f_2p0_npz}[strength]
        summary['input_sha256'][f'p4f_projection_{strength:g}']=_sha(path)
    (args.output/'region-channel-scale-audit.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    with (args.output/'region-channel-scale-metrics.csv').open('w',newline='',encoding='utf8') as stream:
        columns=list(summary['morphology'][0])
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(summary['morphology'])
    print(json.dumps({'status':summary['status'],'metrics':summary['morphology'],'pairwise':summary['cross_strength_at_fixed_threshold']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
