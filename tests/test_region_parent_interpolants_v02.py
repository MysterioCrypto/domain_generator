"""P4-I public-only toy source anchors, provenance, independent Core replay."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest
from scripts.condition_planetary_child_terrain_v02 import ChildTerrainSettings,generate_child
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection
from scripts.compare_region_parent_interpolants_v02 import (InterpolationCounterfactualError,anchored_parent_alternatives,compare_interpolants,render_comparison)


def toy():
    lat=np.arange(12,-13,-4,dtype=np.float32);lon=np.arange(-12,13,4,dtype=np.float32)
    rr,cc=np.meshgrid(lat,lon,indexing='ij')
    z=(520+4.4*(12-cc)+1.1*np.abs(rr)+5*np.sin(cc*.35)*np.cos(rr*.25)).astype('float32')
    macro={'latitude_deg_north_first':lat,'longitude_deg_west_to_east':lon,'elevation_m':z,
           'land_mask':np.ones(z.shape,dtype=np.uint8),'source_river_mask_D8':np.zeros(z.shape,dtype='uint8'),
           'local_downstream_index':np.full(z.shape,-1,dtype='int32'),
           'source_catchment_km2_D8':np.ones(z.shape,dtype='float32')}
    children={};meta=None
    for s in (.5,1.25,2.):
        cfg=ChildTerrainSettings(center_lat_deg=0.,center_lon_deg=0.,half_width_km=8.,half_height_km=8.,
            spacing_km=1.,planet_radius_km=180/np.pi,planetary_year_earth_days=200.,seed=1406,
            relief_strength=s,detail_coordinate_system='spherical_xyz_v1')
        child,metadata=generate_child(macro,cfg);children[s]=child
        if s==2.:meta=metadata
    children[0.]={k:v.copy() for k,v in children[2.].items()}
    children[0.]['child_elevation_m']=children[0.]['parent_interpolated_m'].copy()
    children[0.]['new_local_relief_m']=np.zeros_like(children[0.]['child_elevation_m'])
    archived={};scores=[]
    for s in (.5,1.25,2.):
        p,l=connected_mfd_channel_projection(children[s],macro,meta,stream_threshold_km2=30.)
        archived[s]=p;scores.append({'relief_strength':s,'channel_mask_cells_NOT_WATER':int(p['channel_mask'].sum()),'connected_channel_terminal_count':len(l['connected_boundary_endpoints'])})
    f={'status':'P4_F_INDEPENDENT_CORE_MFD_TERRAIN_VARIANT_TOPOLOGY_NOT_RIVERS',
       'geography_or_rivers_approved':False,'no_A8_external_inflow_injected_km2':0,
       'original_parent_stations_preserved':meta['source_elevation_anchors_in_child'],'variant_comparison':scores}
    h={'status':'P4_H_PARENT_ONLY_NEGATIVE_CONTROL_AND_DIRECTIONAL_BIAS_NOT_RIVERS',
       'prior_P4F_and_P4G_model_archives_bit_exact_replayed':True,'operator_accepted_geography':False,
       'physical_river_or_discharge_verified':False,'A8_external_area_autoinjected_km2':0,
       'baseline_anchored_station_count':meta['source_elevation_anchors_in_child']}
    return {s:children[s] for s in (0.,.5,1.25,2.)},macro,meta,archived,f,h


def test_anchor_heights_and_parent_replay():
    a=toy();new,ledger=anchored_parent_alternatives(a[1],a[0][2.],a[2])
    assert ledger['actual_original_parent_stations']==25
    assert ledger['source_node_bilinear_max_absolute_error_m']<=1e-6
    assert ledger['source_node_hermite_max_absolute_error_m']<=1e-6
    assert ledger['hermite_original_replay_max_error_m']<2e-4
    assert np.isfinite(new).all()


def test_independent_core_and_source_immutable():
    a=toy();unchanged=copy.deepcopy(a);models,report=compare_interpolants(*a)
    assert len(models)==4 and report['P4F_archived_3_original_model_fields_exact_replay']
    assert not report['source_macro_A8_or_interpolator_uniquely_attributed']
    assert report['A8_external_area_auto_injected_km2']==0
    for i,s in enumerate((0.,.5,1.25,2.)):
        k=report['model_topology_original_vs_alt'][i]
        assert 0<=k['model_channel_mask_IoU']<=1 and 0<=k['same_dominant_model_terminal_side_all_cells_fraction']<=1
        assert k['source_detail_grid_exactly_frozen'] and k['child_land_mask_unchanged']
        for key in ('east_km','north_km_north_first','new_local_relief_m','land_mask'):
            np.testing.assert_array_equal(models[s]['candidate'][key],a[0][s][key])
        for key in a[0][s]:np.testing.assert_array_equal(a[0][s][key],unchanged[0][s][key])


@pytest.mark.parametrize('failure',['order','parent','anchors','changed_macro','land','axis','projection','scores','approved','external','bad_status'])
def test_fail_closed(failure):
    a=list(toy())
    if failure=='order':a[0]=dict(reversed(list(a[0].items())))
    if failure=='parent':a[0][2.]['parent_interpolated_m'][2,2]+=30
    if failure=='anchors':a[2]['source_elevation_anchors_in_child']+=1
    if failure=='changed_macro':a[1]['elevation_m'][1,1]+=100
    if failure=='land':a[0][1.25]['land_mask'][2,2]=0
    if failure=='axis':a[0][.5]['east_km'][2]+=1
    if failure=='projection':a[3][2.]['channel_mask'][4,4]^=1
    if failure=='scores':a[4]['variant_comparison'][0]['connected_channel_terminal_count']+=1
    if failure=='approved':a[5]['operator_accepted_geography']=True
    if failure=='external':a[4]['no_A8_external_inflow_injected_km2']=5
    if failure=='bad_status':a[5]['status']='CANONICAL'
    with pytest.raises(InterpolationCounterfactualError):compare_interpolants(*a)


def test_render_deterministic_and_no_overwrite(tmp_path):
    outputs,report=compare_interpolants(*toy());backs={}
    for s in (.5,1.25,2.):
        p=tmp_path/f'{s}.png';Image.new('RGB',(17*4,17*4),(78,89,72)).save(p);backs[s]=p
    for name in ('one','two'):render_comparison(outputs,report,backs,tmp_path/name)
    for name in ('p4i-interpolator-model-channel-review-2x3.png','p4i-bilinear-minus-hermite-parent-height-difference.png'):
        assert (tmp_path/'one'/name).read_bytes()==(tmp_path/'two'/name).read_bytes()
    with pytest.raises(InterpolationCounterfactualError):render_comparison(outputs,report,backs,tmp_path/'one')


def test_full_cli_and_sha_tamper(tmp_path):
    children,macro,meta,arch,f,h=toy();source=tmp_path/'s';source.mkdir()
    mapping={'macro_npz':('macro.npz',macro),'baseline_child_npz':('base.npz',children[2.]),
      'variant_0p5_npz':('05.npz',children[.5]),'variant_1p25_npz':('125.npz',children[1.25]),
      'baseline_projection_npz':('arch20.npz',arch[2.]),
      'p4f_projection_0.5':('arch05.npz',arch[.5]),'p4f_projection_1.25':('arch125.npz',arch[1.25])}
    for name,data in mapping.values():np.savez_compressed(source/name,**data)
    (source/'meta.json').write_text(json.dumps(meta))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    h['source_sha256']={k:sha(source/v[0]) for k,v in mapping.items()}
    h['source_sha256']['child_manifest']=sha(source/'meta.json')
    (source/'f.json').write_text(json.dumps(f))
    h['source_sha256']['p4f_audit_json']=sha(source/'f.json')
    (source/'h.json').write_text(json.dumps(h))
    for ss in ('05','125','20'):Image.new('RGB',(68,68),(72,93,66)).save(source/(ss+'.png'))
    opts={'macro-npz':'macro.npz','baseline-child-npz':'base.npz','child-manifest':'meta.json',
       'variant-0p5-npz':'05.npz','variant-1p25-npz':'125.npz','archived-0p5-npz':'arch05.npz',
       'archived-1p25-npz':'arch125.npz','archived-2p0-npz':'arch20.npz','p4f-audit-json':'f.json',
       'p4h-audit-json':'h.json','terrain-0p5-png':'05.png','terrain-1p25-png':'125.png','terrain-2p0-png':'20.png'}
    args=[sys.executable,'-m','scripts.compare_region_parent_interpolants_v02']
    for opt,name in opts.items():args.extend(['--'+opt,str(source/name)])
    root=Path(__file__).resolve().parents[1]
    def run(n):return subprocess.run(args+['--output',str(tmp_path/n)],cwd=root,capture_output=True,text=True)
    one,two=run('one'),run('two')
    assert one.returncode==two.returncode==0,(one.stderr,two.stderr)
    for file in (tmp_path/'one').iterdir():assert sha(file)==sha(tmp_path/'two'/file.name)
    assert run('one').returncode!=0
    with np.load(source/'05.npz') as z:bad={k:z[k].copy() for k in z.files}
    bad['child_elevation_m'][1,1]+=11
    np.savez_compressed(source/'05.npz',**bad)
    result=run('tampered');assert result.returncode!=0 and 'source SHA mismatch' in result.stderr
