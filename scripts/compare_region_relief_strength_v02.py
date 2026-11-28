from __future__ import annotations

"""P4-E read-only, source-anchored alternate child relief; NOT approved geography.

Hold A8 source, center, seed, P3 cover colors and 1-km raster fixed. Only
change the EXPLICIT child-detail relief_strength setting. Reference the SAME
historic P4-D edge coordinates to measure gradients (NOT revised MFD routing).
A fixed P3 color field is for visual comparability; it is NOT regenerated
vegetation, hydrology or water under the new elevations.
"""

import argparse
import csv
from dataclasses import replace
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.condition_planetary_child_terrain_v02 import (ChildTerrainSettings,
                                                             generate_child)
from scripts.render_region_cartographic_base_v02 import (_base_pixels,
                                                           _with_model_contours)


class ReliefComparisonError(ValueError):
    pass


DEFAULT_STRENGTHS = (0.5, 1.25, 2.0)


def _font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _sha(path: Path) -> str:
    with path.open('rb') as f:
        return file_digest(f, 'sha256').hexdigest()


def _gradient_edges(z: np.ndarray, edge_rows: list[dict]):
    n,m=z.shape
    bad=[]
    last=None
    for i,e in enumerate(edge_rows):
        try:
            idx=int(e['edge_index'])
            a=(int(e['source_row']),int(e['source_col']))
            b=(int(e['target_row']),int(e['target_col']))
        except (ValueError,TypeError,KeyError) as exc:
            raise ReliefComparisonError('invalid P4-D edge fields') from exc
        if idx!=i or not all(0<=r<n and 0<=c<m for r,c in (a,b)):
            raise ReliefComparisonError('bad row ordering or coordinate outside child')
        if max(abs(a[0]-b[0]),abs(a[1]-b[1]))!=1:
            raise ReliefComparisonError('edge must connect adjacent child samples')
        if last is not None and a!=last:
            raise ReliefComparisonError('disconnected historical reference corridor')
        last=b
        bad.append(float(z[b]-z[a])>=0.0)
    return np.asarray(bad,dtype=bool)


def _local_minima(z: np.ndarray) -> int:
    # Strictly no LOWER raw neighbor: mathematical micro-pit, never lake water.
    interior=z[1:-1,1:-1]
    if min(z.shape)<3:return 0
    lows=np.ones(interior.shape,dtype=bool)
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr or dc:
                neighbor=z[1+dr:z.shape[0]-1+dr,1+dc:z.shape[1]-1+dc]
                lows &= interior<=neighbor
    return int(np.sum(lows))


def _parent_anchor_check(macro, fields, metadata, tolerance_m=1e-6):
    """generate_child uses continuous geographic parent station evaluation."""
    if metadata['max_parent_anchor_error_m']>tolerance_m:
        raise ReliefComparisonError('source parent DEM height anchors changed')
    if fields['child_elevation_m'].shape!=tuple(metadata['child_shape']):
        raise ReliefComparisonError('child size metadata contradictory')
    return {'parent_stations_count':metadata['source_elevation_anchors_in_child'],
            'max_parent_station_error_m':metadata['max_parent_anchor_error_m']}


def compare(macro, original, child_meta, cover, p4d, edge_rows,
            strengths=DEFAULT_STRENGTHS):
    if (child_meta.get('status')!='NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON'
            or child_meta.get('is_accepted_Core_DomainData') is not False
            or p4d.get('status')!='P4_D_ANCHOR_AND_RAW_DESCENT_NEGATIVE_CONTROL_NOT_RIVERS'
            or p4d.get('prior_P4C2_source_file_hashes_verified') is not True
            or p4d.get('physical_basin_identity_or_river_verified') is not False
            or p4d.get('macro_A8_upstream_area_injected_km2')!=0):
        raise ReliefComparisonError('requires explicit unaccepted child and P4-D evidence')
    strengths=tuple(float(s) for s in strengths)
    baseline=float(child_meta['relief_strength'])
    if (len(strengths)!=3 or tuple(sorted(strengths))!=strengths or len(set(strengths))!=3
            or any(not np.isfinite(s) or not 0<=s<=2.5 for s in strengths)
            or baseline!=strengths[-1]):
        raise ReliefComparisonError('require three ascending strengths within [0,2.5], baseline last')
    axes_x=np.asarray(original['east_km']);axes_y=np.asarray(original['north_km_north_first'])
    z_original=np.asarray(original['child_elevation_m'])
    cls=np.asarray(cover['cover_class_candidate'])
    if (z_original.shape!=(len(axes_y),len(axes_x)) or z_original.shape!=cls.shape
            or min(z_original.shape)<3 or np.any(~np.isfinite(z_original))
            or np.any(~np.isin(cls,range(6)))
            or not np.allclose(np.diff(axes_x),axes_x[1]-axes_x[0])
            or not np.allclose(-np.diff(axes_y),axes_x[1]-axes_x[0])
            or not np.all(np.diff(axes_x)>0) or not np.all(np.diff(axes_y)<0)):
        raise ReliefComparisonError('child grid or fixed P3 cover inconsistent')
    if (not edge_rows or len(edge_rows)!=p4d['raw_uphill_or_flat_edges']+p4d['complete_P4C2_partition']['strict']
            +p4d['complete_P4C2_partition']['fill_only']):
        raise ReliefComparisonError('P4-D reference corridor length inconsistent')
    original_bad=_gradient_edges(z_original.astype(float),edge_rows)
    if int(np.sum(original_bad))!=p4d['raw_uphill_or_flat_edges']:
        raise ReliefComparisonError('source P4-D raw-gradient count cannot be reproduced')
    for i,e in enumerate(edge_rows):
        source=(int(e['source_row']),int(e['source_col']))
        target=(int(e['target_row']),int(e['target_col']))
        dz=float(z_original[target])-float(z_original[source])
        if (not np.isclose(dz,float(e['raw_delta_m']),rtol=0,atol=1e-8)
                or original_bad[i]!=(str(e['raw_uphill_or_flat']).lower()=='true')):
            raise ReliefComparisonError('P4-D edge has been altered')
    cfg=ChildTerrainSettings(center_lat_deg=float(child_meta['center_lat_lon_deg'][0]),
       center_lon_deg=float(child_meta['center_lat_lon_deg'][1]),
       half_width_km=float(max(abs(axes_x[0]),abs(axes_x[-1]))),
       half_height_km=float(max(abs(axes_y[0]),abs(axes_y[-1]))),
       planet_radius_km=float(child_meta['planet_radius_km']),
       planetary_year_earth_days=float(child_meta['planet_year_earth_days']),
       spacing_km=float(axes_x[1]-axes_x[0]),
       seed=int(child_meta['seed']),relief_strength=baseline,
       detail_coordinate_system=child_meta['detail_coordinate_system'])
    variants={};metrics=[]
    for strength in strengths:
        generated,meta=generate_child(macro,replace(cfg,relief_strength=strength))
        if generated['child_elevation_m'].shape!=z_original.shape:
            raise ReliefComparisonError('regenerated child shape mismatch')
        if not np.array_equal(generated['east_km'],axes_x) or not np.array_equal(generated['north_km_north_first'],axes_y):
            raise ReliefComparisonError('regenerated local coordinates drifted')
        if not np.array_equal(generated['parent_interpolated_m'],original['parent_interpolated_m']):
            raise ReliefComparisonError('a proposed alternative changed macro-parent interpolation')
        if not np.array_equal(generated['land_mask'],original['land_mask']):
            raise ReliefComparisonError('an alternative changed original land sign')
        anchors=_parent_anchor_check(macro,generated,meta)
        if anchors['parent_stations_count']!=child_meta['source_elevation_anchors_in_child']:
            raise ReliefComparisonError('original parent station count drifted')
        if strength==baseline and not all(np.array_equal(generated[k],original[k]) for k in original):
            raise ReliefComparisonError('original source cannot reproduce BIT-EXACT at original strength')
        z=np.asarray(generated['child_elevation_m'],float)
        bad=_gradient_edges(z,edge_rows)
        # This is explicitly the old reference route, NOT a recomputed route.
        newly=int(np.sum(bad&~original_bad));fixed=int(np.sum(~bad&original_bad))
        if int(np.sum(bad))!=int(np.sum(original_bad))+newly-fixed:
            raise ReliefComparisonError('gradient-change accounting mismatch')
        metrics.append({
            'relief_strength':strength,
            'parent_anchor_count':anchors['parent_stations_count'],
            'maximum_parent_anchor_error_m':anchors['max_parent_station_error_m'],
            'baseline_bit_exact_replay':bool(strength==baseline),
            'reference_fixed_edge_count':len(edge_rows),
            'reference_non_downhill_raw_edges':int(np.sum(bad)),
            'baseline_blocked_edges_now_downhill':fixed,
            'baseline_downhill_edges_now_blocked':newly,
            'full_grid_interior_raw_local_minima_NOT_LAKES':_local_minima(z),
            'effective_fine_relief_std_m':float(np.std(z-generated['parent_interpolated_m'])),
            'raw_elevation_min_m':float(np.min(z)),
            'raw_elevation_max_m':float(np.max(z)),
            'fixed_land_cells':int(np.sum(generated['land_mask'])),
        })
        variants[strength]=generated
    audit={
       'status':'P4_E_ANCHOR_PRESERVING_CHILD_RELIEF_STRENGTH_ALTERNATIVES_NOT_CANON',
       'accepted_geography_or_rivers':False,
       'approved_hydrology':False,
       'accepted_Core_MFD_or_P4C1_route_recomputed':False,
       'fixed_historical_edge_route_only':True,
       'variant_cover_colors_reuse_baseline_P3_NOT_RECOMPUTED':True,
       'true_alternative_basin_or_dendricity_computed':False,
       'A8_outside_only_catchment_area_injected_km2':0.,
       'orig_source_relief_strength':baseline,
       'source_parent_station_count':child_meta['source_elevation_anchors_in_child'],
       'source_child_grid_shape':list(z_original.shape),
       'variant_scores':metrics,
       'needs_followup':['Visual author review of three terrain alternatives; none auto-accepted',
                         'For any selected candidate, recompute P2 Core-MFD graph and basin connectivity',
                         'Recompute P3 candidate land cover if author chooses a terrain variant',
                         'Verify external catchment without copying historic D8 cumulative area'],
    }
    return variants,audit


def _residual_panel(z: np.ndarray, parent: np.ndarray, width: int):
    """Explicit signed residual tint at constant ±35 m across all candidates."""
    residual=np.clip((z-parent)/35.,-1.,1.)
    # neutral grey for zero, muted teal for negative, amber for positive
    zero=np.array([187.,185.,167.]);neg=np.array([66.,119.,130.]);pos=np.array([186.,111.,61.])
    signed=np.where(residual[...,None]>=0,residual[...,None]*(pos-zero),-residual[...,None]*(neg-zero))
    rgb=np.uint8(np.clip(np.rint(zero+signed),0,255))
    return Image.fromarray(rgb,'RGB').resize((width,width),Image.Resampling.BILINEAR)


def render_contact_sheet(variants,original,cover,audit,output:Path,*,pixels_per_cell=5):
    if pixels_per_cell not in (4,5,6,7,8,9):
        raise ReliefComparisonError('unsupported comparison pixel scale')
    scores=audit['variant_scores'];axes_x=np.asarray(original['east_km']);axes_y=np.asarray(original['north_km_north_first'])
    cls=np.asarray(cover['cover_class_candidate'])
    dim=len(axes_x)*pixels_per_cell
    margin=50;gap=24;label_top=83;between=80;bottom=155
    w=margin*2+dim*3+gap*2;h=label_top+dim*2+between+bottom
    page=Image.new('RGB',(w,h),(236,234,222));d=ImageDraw.Draw(page)
    d.text((margin,15),'ОСВЕРА / P4-E — ТРИ ВАРИАНТА ЛОКАЛЬНОГО РЕЛЬЕФА',font=_font(26),fill=(40,48,42))
    for i,score in enumerate(scores):
        key=score['relief_strength'];field=variants[key];z=np.asarray(field['child_elevation_m'],float)
        x=margin+i*(dim+gap)
        color=_base_pixels(z,cls,axes_x,axes_y).resize((dim,dim),Image.Resampling.BICUBIC)
        color,step=_with_model_contours(color,z,axes_x,axes_y)
        color.save(output/f'region-relief-strength-{str(key).replace(".","p")}.png',optimize=True)
        page.paste(color,(x,label_top))
        d.rectangle((x-1,label_top-1,x+dim,label_top+dim),outline=(105,106,92),width=2)
        d.text((x,label_top+dim+10),f'Сила рельефа {key:g}    |    без спуска: {score["reference_non_downhill_raw_edges"]}/253',font=_font(17),fill=(54,57,45))
        detail=_residual_panel(z,field['parent_interpolated_m'].astype(float),dim)
        page.paste(detail,(x,label_top+dim+between))
        d.rectangle((x-1,label_top+dim+between-1,x+dim,label_top+dim+between+dim),outline=(109,105,91),width=2)
        d.text((x,label_top+dim*2+between+10),f'Микровпадины: {score["full_grid_interior_raw_local_minima_NOT_LAKES"]}',font=_font(17),fill=(54,57,45))
    y=label_top+2*dim+between+53
    for i,text in enumerate((
        'ВЕРХ: одинаковая гипотетическая P3-окраска, изменяется только DEM (теневой рельеф и горизонтали).',
        'НИЗ: отличия DEM от родительской поверхности. Бирюзовый = ниже, коричневый = выше; одна шкала ±35 м.',
        '63 исходные опоры неизменны. Старая MFD-сеть НЕ пересчитана; показанные показатели НЕ подтверждают реку.',
    )):
        d.text((margin,y+i*29),text,font=_font(17),fill=(71,74,61))
    page.save(output/'region-relief-comparison-sheet.png',optimize=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('macro-npz','child-npz','child-manifest','cover-npz','p4a-audit-json',
              'p4d-audit-json','p4d-edges-csv'):
        p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--strengths',nargs=3,type=float,default=list(DEFAULT_STRENGTHS))
    p.add_argument('--pixels-per-cell',type=int,default=5)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise ReliefComparisonError('output directory must not already exist')
    def arrays(path):
        with np.load(path,allow_pickle=False) as a:return {k:a[k].copy() for k in a.files}
    macro=arrays(args.macro_npz);original=arrays(args.child_npz);cover=arrays(args.cover_npz)
    cm=json.loads(args.child_manifest.read_text(encoding='utf8'))
    p4a=json.loads(args.p4a_audit_json.read_text(encoding='utf8'))
    p4d=json.loads(args.p4d_audit_json.read_text(encoding='utf8'))
    for key,path in [('macro_npz',args.macro_npz),('child_npz',args.child_npz),
                     ('child_manifest',args.child_manifest)]:
        if _sha(path)!=p4d.get('input_sha256',{}).get(key):
            raise ReliefComparisonError('upstream P4-D SHA lineage mismatch: '+key)
    if (p4a.get('status')!='P4A_NONCANONICAL_CARTOGRAPHIC_BASE'
            or p4a.get('is_author_canon') is not False
            or p4a.get('is_measured_landcover') is not False
            or p4a.get('input_sha256',{}).get('cover_npz')!=_sha(args.cover_npz)
            or p4a.get('input_sha256',{}).get('child_npz')!=_sha(args.child_npz)):
        raise ReliefComparisonError('P4-A fixed cover not from the same baseline child')
    with args.p4d_edges_csv.open('r',encoding='utf8',newline='') as f:edges=list(csv.DictReader(f))
    fields,audit=compare(macro,original,cm,cover,p4d,edges,args.strengths)
    args.output.mkdir(parents=True,exist_ok=False)
    render_contact_sheet(fields,original,cover,audit,args.output,pixels_per_cell=args.pixels_per_cell)
    audit['source_sha256']={k:_sha(getattr(args,k)) for k in (
        'macro_npz','child_npz','child_manifest','cover_npz','p4a_audit_json',
        'p4d_audit_json','p4d_edges_csv')}
    audit['P4A_and_P4D_source_bytes_verified']=True
    for score in audit['variant_scores']:
        strength=score['relief_strength']
        if strength!=audit['orig_source_relief_strength']:
            filename=f'relief-strength-{str(strength).replace(".","p")}-derived.npz'
            np.savez_compressed(args.output/filename,**fields[strength])
            score['derived_variant_npz_sha256']=_sha(args.output/filename)
            score['derived_variant_npz_file']=filename
    (args.output/'region-relief-comparison-audit.json').write_text(
        json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
