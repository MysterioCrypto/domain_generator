from __future__ import annotations

"""P4-I source-anchored parent DEM interpolation counterfactual, NOT rivers.

Experimental change: accepted adapter's C1 Hermite parent interpolation is
replaced with a bilinear parent surface, while EXISTING local detail is copied
bit-for-bit. Both hold the same source-station heights. All 1D channel networks
are independently rerouted under unchanged accepted Core code, not morphed.
"""

import argparse
import csv
from hashlib import file_digest
import json
from math import cos, pi, radians
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.condition_planetary_child_terrain_v02 import _bilinear, _c1_cubic, _source_fields
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection
from scripts.compare_region_mfd_variant_basins_v02 import terminal_ids, terminal_sides
from scripts.diagnose_region_directional_bias_v02 import straight_chain_runs


class InterpolationCounterfactualError(ValueError):
    pass


STRENGTHS = (0.0, .5, 1.25, 2.0)


def _npz(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as z:
        return {k:z[k].copy() for k in z.files}


def _sha(path:Path)->str:
    with path.open('rb') as stream:return file_digest(stream,'sha256').hexdigest()


def _font(size:int):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(path).is_file():return ImageFont.truetype(path,size)
    return ImageFont.load_default()


def anchored_parent_alternatives(macro:dict,baseline:dict,meta:dict,*,anchor_tol=1e-6):
    """Rebuild 2 parent surfaces using original *source nodes*, not child anchors."""
    lat_src,lon_src,z_src,_=_source_fields(macro)
    try:
        lat0,lon0=map(float,meta['center_lat_lon_deg'])
        kpd=pi*float(meta['planet_radius_km'])/180
        if not np.isfinite(kpd) or kpd<=0:raise ValueError('radius')
        xx,yy=np.meshgrid(baseline['east_km'],baseline['north_km_north_first'])
        lat=lat0+yy/kpd;lon=lon0+xx/(kpd*cos(radians(lat0)))
        linear=_bilinear(lon,lat,lon_src,lat_src,z_src)
        cubic=_c1_cubic(lon,lat,lon_src,lat_src,z_src)
        cubic=np.where(linear>=0,np.maximum(0,cubic),np.minimum(0,cubic))
    except (ValueError,KeyError,IndexError) as error:
        raise InterpolationCounterfactualError('source coordinate alignment failed') from error
    if linear.shape!=baseline['child_elevation_m'].shape:
        raise InterpolationCounterfactualError('child surface shape mismatch')
    # Original construction stored float32 parent, so floating-point tolerance is
    # for re-evaluation only, not an accepted source-station error.
    parent=np.asarray(baseline['parent_interpolated_m'],dtype=np.float64)
    maximum_cubic_raster_difference=float(np.max(np.abs(parent-cubic)))
    if maximum_cubic_raster_difference>2e-4:
        raise InterpolationCounterfactualError('archived parent DEM not Hermite C1 source')
    parent_e=(lon_src-lon0)*kpd*cos(radians(lat0))
    parent_n=(lat_src-lat0)*kpd
    rows=np.flatnonzero((parent_n>=baseline['north_km_north_first'][-1]-1e-8)&
                           (parent_n<=baseline['north_km_north_first'][0]+1e-8))
    cols=np.flatnonzero((parent_e>=baseline['east_km'][0]-1e-8)&
                           (parent_e<=baseline['east_km'][-1]+1e-8))
    count=len(rows)*len(cols)
    if not count or count!=meta['source_elevation_anchors_in_child']:
        raise InterpolationCounterfactualError('source station count changed')
    node_lon,node_lat=np.meshgrid(lon_src[cols],lat_src[rows])
    bil_nodes=_bilinear(node_lon,node_lat,lon_src,lat_src,z_src)
    cubic_nodes=_c1_cubic(node_lon,node_lat,lon_src,lat_src,z_src)
    reference=z_src[np.ix_(rows,cols)]
    e_bil=float(np.max(np.abs(bil_nodes-reference)))
    e_cubic=float(np.max(np.abs(cubic_nodes-reference)))
    if max(e_bil,e_cubic)>anchor_tol:
        raise InterpolationCounterfactualError('parent source-station height changed')
    if not np.isfinite(linear).all() or not np.isfinite(cubic).all():
        raise InterpolationCounterfactualError('nonfinite interpolated height')
    d=linear-parent
    return linear,{'actual_original_parent_stations':count,
        'hermite_original_replay_max_error_m':maximum_cubic_raster_difference,
        'source_node_bilinear_max_absolute_error_m':e_bil,
        'source_node_hermite_max_absolute_error_m':e_cubic,
        'bilinear_minus_hermite_raster_min_m':float(d.min()),
        'bilinear_minus_hermite_raster_max_m':float(d.max()),
        'bilinear_minus_hermite_raster_RMS_m':float(np.sqrt(np.mean(d*d))),
        'original_parent_source_sign_equal_bilinear':bool(np.array_equal(linear>=0,parent>=0))}


def _checked_source(children,baseline):
    for s,child in children.items():
        for key in ('east_km','north_km_north_first','parent_interpolated_m','land_mask'):
            if not np.array_equal(baseline[key],child[key]):
                raise InterpolationCounterfactualError('a candidate moved parent, axes or coastline')
        if (child['child_elevation_m'].shape!=baseline['child_elevation_m'].shape or
            not np.isfinite(child['child_elevation_m']).all() or
            not np.array_equal(np.asarray(child['land_mask'],bool),np.asarray(child['child_elevation_m'])>=0)):
            raise InterpolationCounterfactualError('source coastline, dimensions or finite heights broken')
        if s and np.max(np.abs(child['child_elevation_m']-(child['parent_interpolated_m']+child['new_local_relief_m'])))>2e-4:
            raise InterpolationCounterfactualError('source local detail cannot be isolated')


def compare_interpolants(children:dict,macro:dict,meta:dict,archived:dict,p4f:dict,p4h:dict):
    if (tuple(children)!=STRENGTHS or tuple(archived)!=(.5,1.25,2.) or
        p4f.get('status')!='P4_F_INDEPENDENT_CORE_MFD_TERRAIN_VARIANT_TOPOLOGY_NOT_RIVERS' or
        p4h.get('status')!='P4_H_PARENT_ONLY_NEGATIVE_CONTROL_AND_DIRECTIONAL_BIAS_NOT_RIVERS' or
        not p4h.get('prior_P4F_and_P4G_model_archives_bit_exact_replayed') or
        p4f.get('geography_or_rivers_approved') is not False or
        p4h.get('operator_accepted_geography') is not False or
        p4h.get('physical_river_or_discharge_verified') is not False or
        p4f.get('no_A8_external_inflow_injected_km2')!=0 or
        p4h.get('A8_external_area_autoinjected_km2')!=0):
        raise InterpolationCounterfactualError('P4-F/P4-H noncanonical provenance invalid')
    baseline=children[2.]
    _checked_source(children,baseline)
    parent=baseline['parent_interpolated_m']
    if not np.array_equal(children[0.]['child_elevation_m'],parent) or np.any(children[0.]['new_local_relief_m']):
        raise InterpolationCounterfactualError('zero-detail parent control not pure Hermite')
    new_parent,anchor_audit=anchored_parent_alternatives(macro,baseline,meta)
    if p4f.get('original_parent_stations_preserved')!=anchor_audit['actual_original_parent_stations'] or p4h.get('baseline_anchored_station_count')!=anchor_audit['actual_original_parent_stations']:
        raise InterpolationCounterfactualError('original anchor count provenance inconsistency')
    if not anchor_audit['original_parent_source_sign_equal_bilinear']:
        raise InterpolationCounterfactualError('parent terrain land/sea changed')
    # Baseline original already archived (except 0-detail control); independent
    # full numerical replay verifies old source before any difference is reported.
    scores=[];outputs={};source_sample=(220,224)
    for i,s in enumerate(STRENGTHS):
        child=children[s]
        detail=np.zeros_like(parent) if s==0 else child['new_local_relief_m']
        new_height=np.asarray(new_parent,dtype=np.float64)+np.asarray(detail,dtype=np.float64)
        if not np.array_equal(new_height>=0,child['land_mask'].astype(bool)):
            raise InterpolationCounterfactualError('counterfactual would move coastline: no implicit clipping')
        candidate={k:v.copy() for k,v in child.items()}
        candidate['parent_interpolated_m']=new_parent.astype('float32')
        candidate['child_elevation_m']=new_height.astype('float32')
        candidate['new_local_relief_m']=detail.copy()
        orig_fields,orig_ledger=connected_mfd_channel_projection(child,macro,meta,stream_threshold_km2=30.)
        alt_fields,alt_ledger=connected_mfd_channel_projection(candidate,macro,meta,stream_threshold_km2=30.)
        if s:
            record=archived[s]
            if set(orig_fields)!=set(record) or any(not np.array_equal(orig_fields[k],record[k]) for k in record):
                raise InterpolationCounterfactualError('previous P4-F model not bit-exact')
            existing=p4f['variant_comparison'][i-1]
            if (int(orig_fields['channel_mask'].sum())!=existing['channel_mask_cells_NOT_WATER'] or
                len(orig_ledger['connected_boundary_endpoints'])!=existing['connected_channel_terminal_count']):
                raise InterpolationCounterfactualError('previous P4-F model count mismatch')
        for mode,ledger in (('original',orig_ledger),('bilinear',alt_ledger)):
            a=ledger['internal_mfd_mass_ledger']
            if (a['explicit_external_area_km2']!=0 or abs(a['balance_error_km2'])>1e-6 or
                    not ledger['no_external_A8_source_area_auto_injected'] or
                    ledger['is_physical_discharge_or_approved_river'] is not False):
                raise InterpolationCounterfactualError('MFD mass balance/physical claim failed in '+mode)
        mask_a=orig_fields['channel_mask'].astype(bool)
        mask_b=alt_fields['channel_mask'].astype(bool)
        union=int(np.count_nonzero(mask_a|mask_b))
        root_a=terminal_ids(orig_fields['Core_dominant_receiver_index'],orig_fields['lake_proxy_jumps_flat_from_to'])
        root_b=terminal_ids(alt_fields['Core_dominant_receiver_index'],alt_fields['lake_proxy_jumps_flat_from_to'])
        outlet_original={tuple(x['child_edge_cell_row_col']) for x in orig_ledger['connected_boundary_endpoints']}
        outlet_bilinear={tuple(x['child_edge_cell_row_col']) for x in alt_ledger['connected_boundary_endpoints']}
        score={'relief_strength':s,
            'original_model_channel_cells':int(mask_a.sum()),
            'bilinear_model_channel_cells':int(mask_b.sum()),
            'original_channel_outlet_count':len(outlet_original),
            'bilinear_channel_outlet_count':len(outlet_bilinear),
            'model_channel_mask_IoU':float(np.count_nonzero(mask_a&mask_b)/union) if union else 1.,
            'same_model_channel_outlet_set':outlet_original==outlet_bilinear,
            'model_channel_outlet_intersection_count':len(outlet_original&outlet_bilinear),
            'same_dominant_model_terminal_pixel_all_cells_fraction':float(np.mean(root_a==root_b)),
            'same_dominant_model_terminal_side_all_cells_fraction':float(np.mean(terminal_sides(root_a)==terminal_sides(root_b))),
            'sample_historical_source_row_col':list(source_sample) if max(source_sample)<min(parent.shape) else None,
            'model_straight_chain_ge_8_original_fraction':straight_chain_runs(orig_fields['channel_edge_flat_from_to'],parent.shape)['edges_in_straight_runs_ge_8_fraction'],
            'model_straight_chain_ge_8_bilinear_fraction':straight_chain_runs(alt_fields['channel_edge_flat_from_to'],parent.shape)['edges_in_straight_runs_ge_8_fraction'],
            'source_detail_grid_exactly_frozen':bool(np.array_equal(candidate['new_local_relief_m'],detail)),
            'child_land_mask_unchanged':bool(np.array_equal(candidate['land_mask'],child['land_mask'])),
            'original_MFD_area_conservation_error_km2':orig_ledger['internal_mfd_mass_ledger']['balance_error_km2'],
            'bilinear_MFD_area_conservation_error_km2':alt_ledger['internal_mfd_mass_ledger']['balance_error_km2']}
        if score['sample_historical_source_row_col']:
            row,col=source_sample
            score['same_historical_model_source_terminal_pixel']=bool(root_a[row,col]==root_b[row,col])
            score['historical_model_source_terminal_original_row_col']=list(divmod(int(root_a[row,col]),parent.shape[1]))
            score['historical_model_source_terminal_bilinear_row_col']=list(divmod(int(root_b[row,col]),parent.shape[1]))
        scores.append(score)
        outputs[s]={'original':orig_fields,'bilinear':alt_fields,'candidate':candidate,'source_parent':child['parent_interpolated_m'].copy()}
    report={'status':'P4_I_HERMITE_VS_BILINEAR_PARENT_ANCHOR_CONTROL_NOT_RIVERS',
        'source_macro_A8_or_interpolator_uniquely_attributed':False,
        'not_author_accepted_geography_or_rivers':True,
        'accepted_Core_changed':False,'accepted_child_source_modified':False,
        'P4F_archived_3_original_model_fields_exact_replay':True,
        'original_source_anchor_heights_both_interpolants_exact':True,
        'A8_external_area_auto_injected_km2':0.,
        'source_child_grid_shape':list(parent.shape),
        'interpolation_control':'C1 Hermite vs bilinear, same source macro station heights and EXACT original per-strength local relief',
        'source_stations':anchor_audit,
        'model_topology_original_vs_alt':scores,
        'cannot_promote_alternative_to_accepted_map_without_author_and_outlet_gate':True,
        'limitations':['different interpolation changes interior slopes AND independent model receiver topology',
            'preserving parent stations does NOT guarantee preservation of channel nodes/outlets',
            'bilinear is C0 with derivative discontinuities at macro grid boundaries',
            'single 231x231 real region and 3 candidate strengths do not prove geological realism or global applicability',
            'cannot isolate macro source spatial structure from interpolation mathematically without independent source observations',
            'no physical river Q, water permanence, external-only A8 flux, POIs or accepted map claimed'],
        'next_bounded_step':'P4-J topology-preserving vector drawing/generalization on fixed and approved existing model channel graph, compare map readability, no hidden geometry mutation'}
    return outputs,report


def render_comparison(outputs, report, background_paths:dict, dest:Path):
    if dest.exists():raise InterpolationCounterfactualError('no overwrite')
    nr,nc=report['source_child_grid_shape'];scale=4;pw=nc*scale;ph=nr*scale
    mx=42;top=110;bottom=90;gap=20;rgap=47
    pic=Image.new('RGB',(2*pw+2*mx+gap,3*ph+top+bottom+2*rgap),(237,234,224))
    draw=ImageDraw.Draw(pic)
    draw.text((mx,11),'ОСВЕРА / P4-I — ИНТЕРПОЛЯТОР РОДИТЕЛЬСКОГО РЕЛЬЕФА',font=_font(26),fill=(42,48,47))
    draw.text((mx,47),'Левый столбец: Hermite C1  |  Правый: bilinear  |  Исходная мелкая деталь не меняется',font=_font(19),fill=(61,68,63))
    for i,s in enumerate((.5,1.25,2.)):
        with Image.open(background_paths[s]) as im: bg=im.convert('RGB').resize((pw,ph),Image.Resampling.BILINEAR)
        for j,kind in enumerate(('original','bilinear')):
            x=mx+j*(pw+gap);y=top+i*(ph+rgap)
            layer=Image.new('RGBA',(pw,ph),(0,0,0,0));p=ImageDraw.Draw(layer)
            fields=outputs[s][kind];edges=fields['channel_edge_flat_from_to'];area=fields['Core_dominant_channel_area_km2_NOT_Q'].ravel()
            for a,b in edges:
                ra,ca=divmod(int(a),nc);rb,cb=divmod(int(b),nc)
                thick=3 if area[int(a)]>=200 else 1
                color=(22,67,123,232) if thick==3 else (50,90,138,155)
                p.line(((ca+.5)*scale,(ra+.5)*scale,(cb+.5)*scale,(rb+.5)*scale),fill=color,width=thick)
            pic.paste(Image.alpha_composite(bg.convert('RGBA'),layer).convert('RGB'),(x,y))
            draw.rectangle((x,y,x+pw-1,y+ph-1),outline=(104,105,92),width=2)
            score=report['model_topology_original_vs_alt'][i+1]
            draw.text((x,y+ph+9),f'{s:g}: {kind}  ·  {int(fields["channel_mask"].sum()):,} model cells',font=_font(17),fill=(45,49,49))
            if j==1:draw.text((x+450,y+ph+9),f'IoU {score["model_channel_mask_IoU"]:.1%}',font=_font(17),fill=(50,56,54))
    draw.text((mx,top+3*ph+2*rgap+28),'Порог 30 км². Это модельные линии, НЕ принятые реки. Фон P4-E остался старым для сопоставимости.',font=_font(16),fill=(65,59,58))
    dest.mkdir(parents=True)
    pic.save(dest/'p4i-interpolator-model-channel-review-2x3.png',compress_level=3)
    # Compact heat map of interpolation-only change; visual not an elevation field replacement.
    diff=outputs[2.]['candidate']['parent_interpolated_m']-outputs[2.]['source_parent']
    vmax=max(abs(float(diff.min())),abs(float(diff.max())),1e-6)
    z=np.clip(diff/vmax,-1,1)
    rgb=np.zeros((nr,nc,3),dtype=np.uint8)
    rgb[:,:,0]=(240*np.maximum(z,0)+220*(1-np.abs(z))).astype('uint8')
    rgb[:,:,1]=(218*(1-np.abs(z))+120*np.abs(z)).astype('uint8')
    rgb[:,:,2]=(240*np.maximum(-z,0)+215*(1-np.abs(z))).astype('uint8')
    Image.fromarray(rgb,'RGB').resize((nc*4,nr*4),Image.Resampling.NEAREST).save(dest/'p4i-bilinear-minus-hermite-parent-height-difference.png',compress_level=3)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('macro-npz','baseline-child-npz','child-manifest','variant-0p5-npz','variant-1p25-npz',
              'archived-0p5-npz','archived-1p25-npz','archived-2p0-npz','p4f-audit-json','p4h-audit-json',
              'terrain-0p5-png','terrain-1p25-png','terrain-2p0-png'):
        parser.add_argument('--'+n,required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.output.exists():raise InterpolationCounterfactualError('no overwrite')
    p4f=json.loads(args.p4f_audit_json.read_text('utf8'))
    p4h=json.loads(args.p4h_audit_json.read_text('utf8'))
    sources={'macro_npz':args.macro_npz,'baseline_child_npz':args.baseline_child_npz,
       'child_manifest':args.child_manifest,'variant_0p5_npz':args.variant_0p5_npz,
       'variant_1p25_npz':args.variant_1p25_npz,'baseline_projection_npz':args.archived_2p0_npz,
       'p4f_projection_0.5':args.archived_0p5_npz,'p4f_projection_1.25':args.archived_1p25_npz,
       'p4f_audit_json':args.p4f_audit_json}
    known=p4h.get('source_sha256',{})
    for k,path in sources.items():
        if _sha(path)!=known.get(k):raise InterpolationCounterfactualError('P4-H input source SHA mismatch: '+k)
    child={2.:_npz(args.baseline_child_npz),.5:_npz(args.variant_0p5_npz),1.25:_npz(args.variant_1p25_npz)}
    child[0.]={k:v.copy() for k,v in child[2.].items()}
    child[0.]['child_elevation_m']=child[0.]['parent_interpolated_m'].copy()
    child[0.]['new_local_relief_m']=np.zeros_like(child[0.]['child_elevation_m'])
    meta=json.loads(args.child_manifest.read_text('utf8'))
    out,report=compare_interpolants({s:child[s] for s in STRENGTHS},_npz(args.macro_npz),meta,
      {.5:_npz(args.archived_0p5_npz),1.25:_npz(args.archived_1p25_npz),2.:_npz(args.archived_2p0_npz)},p4f,p4h)
    maps={.5:args.terrain_0p5_png,1.25:args.terrain_1p25_png,2.:args.terrain_2p0_png}
    render_comparison(out,report,maps,args.output)
    report['P4H_source_sha256_all_input_verified']=True
    report['source_sha256']={k:_sha(v) for k,v in sources.items()}
    report['source_sha256']['p4h_audit_json']=_sha(args.p4h_audit_json)
    (args.output/'p4i-parent-interpolant-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    with (args.output/'p4i-parent-interpolant-metrics.csv').open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(report['model_topology_original_vs_alt'][0]))
        writer.writeheader();writer.writerows(report['model_topology_original_vs_alt'])
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
