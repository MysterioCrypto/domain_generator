"""P4-F toy-only diagnostic tests; real/private DEM is NOT a fixture."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

from scripts.compare_region_mfd_variant_basins_v02 import (
    VariantRoutingError, terminal_ids, terminal_sides,
    fractional_terminal_area_sides, iou, compare_results, render_sheet,
)
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection


def _receivers():
    # Every interior model cell goes west; boundary is a terminal.
    f=np.full((5,5),-1,dtype=np.int32)
    for r in range(1,4):
        for c in range(1,4):f[r,c]=r*5+(c-1)
    return f


def test_dominant_terminal_resolution_and_side_identity():
    rec=_receivers()
    ids=terminal_ids(rec)
    assert ids[1,3]==5 and ids[2,3]==10
    assert np.all(terminal_sides(ids)[1,1:-1]==3)
    assert len(np.unique(ids))>=12
    np.testing.assert_array_equal(ids,terminal_ids(rec.copy()))


@pytest.mark.parametrize('bad',["cycle","premature","bad_outside","nonlocal","edge_routes","non_integer","narrow"])
def test_terminal_graph_fails_closed(bad):
    f=_receivers()
    if bad=='cycle':f[2,1]=2*5+2
    elif bad=='premature':f[2,1]=-1
    elif bad=='bad_outside':f[2,1]=99
    elif bad=='nonlocal':f[2,2]=2*5+0
    elif bad=='edge_routes':f[0,0]=1
    elif bad=='non_integer':f=f.astype('float64')
    elif bad=='narrow':f=f[:2]
    with pytest.raises(VariantRoutingError):terminal_ids(f)


def test_proxy_nonlocal_must_be_explicit_and_does_not_assert_water():
    rec=_receivers();rec[2,2]=2*5+0
    with pytest.raises(VariantRoutingError):terminal_ids(rec)
    result=terminal_ids(rec,np.asarray([[12,10]],dtype=np.int32))
    assert result[2,2]==10
    assert iou(np.zeros((3,3)),np.zeros((3,3)))==1.0
    assert iou(np.eye(3),np.rot90(np.eye(3)))==pytest.approx(.2)
    assert iou(np.eye(3),np.zeros((3,3)))==0.


def test_fractional_terminal_sides_disjoint_counting():
    a=np.arange(25,dtype=float).reshape((5,5))
    d=fractional_terminal_area_sides(a)
    assert sum(d.values())==sum(a.ravel()[np.array([0,1,2,3,4,5,9,10,14,15,19,20,21,22,23,24])])
    assert d['west']==a[1:-1,0].sum()
    with pytest.raises(VariantRoutingError):fractional_terminal_area_sides(np.full((5,5),np.nan))


def fake_data():
    # A fully synthetic, gently sloping 9x9 grid with fixed macropoints.
    n=9
    row,col=np.indices((n,n))
    fields={}
    for s in (.5,1.25,2.):
        z=(200.+6*(n-1-col)+.4*row+s*.23*np.sin((row+2)*(col+1))).astype('float32')
        fields[s]={"child_elevation_m":z,"parent_interpolated_m":(200.+6*(n-1-col)+.4*row).astype('float32'),
                   "land_mask":np.ones((n,n),dtype='uint8'),"east_km":np.arange(-4,5,dtype='float64'),
                   "north_km_north_first":np.arange(4,-5,-1,dtype='float64')}
    m={"latitude_deg_north_first":np.array([6.,0.,-6.]),"longitude_deg_west_to_east":np.array([-6.,0.,6.]),
       "source_river_mask_D8":np.zeros((3,3),dtype='uint8'),
       "local_downstream_index":np.full((3,3),-1,dtype='int32'),"source_catchment_km2_D8":np.ones((3,3),dtype='float32')}
    cm={"planet_radius_km":180/np.pi,"center_lat_lon_deg":[0.,0.],"status":"NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData":False}
    old_projection,old_ledger=connected_mfd_channel_projection(fields[2.],m,cm)
    root=terminal_ids(old_projection['Core_dominant_receiver_index'],old_projection['lake_proxy_jumps_flat_from_to'])
    rr,cc=divmod(int(root[4,4]),9)
    c1={'audit':{'status':'P4_C1_COARSE_INLET_TO_CHILD_DOMINANT_GRAPH_HINTS_NOT_RIVERS',
                'is_approved_river_map':False,'external_inflow_area_injected_km2':0.,
                'source_macro_inlet_count':1,
                'inlet_results':[{'selected_candidate':{'child_start_row_col':[4,4],
                                                       'terminal_row_col':[rr,cc]}}]}}
    e={'status':'P4_E_ANCHOR_PRESERVING_CHILD_RELIEF_STRENGTH_ALTERNATIVES_NOT_CANON',
       'P4A_and_P4D_source_bytes_verified':True,'accepted_geography_or_rivers':False,
       'A8_outside_only_catchment_area_injected_km2':0,
       'source_child_grid_shape':[9,9],'source_parent_station_count':1,
       'variant_scores':[{'relief_strength':s,'parent_anchor_count':1,
                          'maximum_parent_anchor_error_m':0.,'fixed_land_cells':81} for s in (.5,1.25,2.)]}
    return fields,m,cm,c1,e,old_projection,old_ledger


def test_real_core_algorithm_recalculates_3_synthetic_candidates_without_water():
    children,macro,meta,c1,prev,old_proj,old_ledger=fake_data()
    untouched={s:{k:np.copy(v) for k,v in child.items()} for s,child in children.items()}
    data,report=compare_results(children,macro,meta,c1,prev)
    assert report['status']=='P4_F_INDEPENDENT_CORE_MFD_TERRAIN_VARIANT_TOPOLOGY_NOT_RIVERS'
    assert report['no_A8_external_inflow_injected_km2']==0
    assert not report['geography_or_rivers_approved']
    assert not report['P4C1_coarse_A8_to_new_MFD_basin_identity_proved']
    assert report['dominant_root_is_model_only_not_fractional_MFD_basin']
    assert len(report['variant_comparison'])==3
    for a in report['variant_comparison']:
        assert a['area_local_source_km2']==81
        assert abs(a['area_balance_error_km2'])<1e-8
        assert a['lake_proxy_jumps_NOT_WATER']==0
    for key in old_proj:
        np.testing.assert_array_equal(data['outputs'][2.][0][key],old_proj[key])
    for s in children:
        for k in children[s]:np.testing.assert_array_equal(children[s][k],untouched[s][k])


@pytest.mark.parametrize('mutate',["strength","anchors","parent","land","grid","extent","c1water","c1badterminal","p4ewater","invalidthreshold"])
def test_comparison_rejects_inconsistent_models_or_identity(mutate):
    children,macro,meta,c1,e,_,_=fake_data();kwargs={}
    if mutate=='strength':e['variant_scores'][1]['relief_strength']=.8
    elif mutate=='anchors':e['variant_scores'][0]['parent_anchor_count']=5
    elif mutate=='parent':children[.5]['parent_interpolated_m'][2,2]+=1
    elif mutate=='land':children[1.25]['land_mask'][2,2]=0
    elif mutate=='grid':children[.5]['east_km'][1]=4
    elif mutate=='extent':e['source_child_grid_shape']=[10,10]
    elif mutate=='c1water':c1['audit']['external_inflow_area_injected_km2']=5
    elif mutate=='c1badterminal':c1['audit']['inlet_results'][0]['selected_candidate']['terminal_row_col']=[2,2]
    elif mutate=='p4ewater':e['accepted_geography_or_rivers']=True
    elif mutate=='invalidthreshold':kwargs['stream_threshold_km2']=0
    with pytest.raises((VariantRoutingError,ValueError)):
        compare_results(children,macro,meta,c1,e,**kwargs)


def test_consistent_visual_sheet_and_immutable_original(tmp_path):
    children,macro,meta,c1,e,_,_=fake_data();analysis,report=compare_results(children,macro,meta,c1,e)
    backgrounds={}
    for s in (.5,1.25,2.):
        f=tmp_path/('s'+str(s)+'.png');Image.new('RGB',(9*10,9*10),(86,99,74)).save(f);backgrounds[s]=f
    for name in ('first','second'):
        render_sheet(analysis,report,backgrounds,tmp_path/name)
    assert (tmp_path/'first/region-mfd-variant-topology-sheet.png').read_bytes()==(
            tmp_path/'second/region-mfd-variant-topology-sheet.png').read_bytes()
    with pytest.raises(FileExistsError):render_sheet(analysis,report,backgrounds,tmp_path/'first')


def test_missing_macro_source_rejected():
    children,macro,meta,c1,e,_,_=fake_data();macro.pop('source_river_mask_D8')
    with pytest.raises((ValueError,KeyError)):
        compare_results(children,macro,meta,c1,e)


def test_cli_exact_source_sha_replay_and_tampering(tmp_path):
    children,macro,meta,c1,e,baseline,bl= fake_data()
    source=tmp_path/'sources';source.mkdir()
    def dump(path,d):np.savez_compressed(path,**d)
    dump(source/'macro.npz',macro)
    dump(source/'base.npz',children[2.])
    dump(source/'p05.npz',children[.5]);dump(source/'p125.npz',children[1.25])
    dump(source/'baseline_proj.npz',baseline)
    (source/'base_manifest.json').write_text(json.dumps(meta))
    (source/'old_report.json').write_text(json.dumps({'child_core_dominant_channel_ledger':bl}))
    def sh(p):return sha256(p.read_bytes()).hexdigest()
    c1['audit']['input_sha256']={
        'macro_npz':sh(source/'macro.npz'),'child_npz':sh(source/'base.npz'),
        'child_manifest':sh(source/'base_manifest.json'),
        'projection_npz':sh(source/'baseline_proj.npz'),
        'projection_manifest':sh(source/'old_report.json')}
    e['source_sha256']={k:v for k,v in c1['audit']['input_sha256'].items() if k in ('macro_npz','child_npz','child_manifest')}
    e['variant_scores'][0]['derived_variant_npz_sha256']=sh(source/'p05.npz')
    e['variant_scores'][1]['derived_variant_npz_sha256']=sh(source/'p125.npz')
    (source/'c1.json').write_text(json.dumps(c1))
    (source/'e.json').write_text(json.dumps(e))
    for k in ('0p5','1p25','2p0'):Image.new('RGB',(9*10,9*10),(91,105,88)).save(source/(k+'.png'))
    args=[sys.executable,'-m','scripts.compare_region_mfd_variant_basins_v02']
    for arg,file in [('macro-npz','macro.npz'),('baseline-child-npz','base.npz'),
        ('child-manifest','base_manifest.json'),('baseline-projection-npz','baseline_proj.npz'),
        ('baseline-projection-manifest','old_report.json'),('variant-0p5-npz','p05.npz'),
        ('variant-1p25-npz','p125.npz'),('p4e-audit-json','e.json'),
        ('p4c1-audit-json','c1.json'),('terrain-0p5-png','0p5.png'),
        ('terrain-1p25-png','1p25.png'),('terrain-2p0-png','2p0.png')]:
        args+=['--'+arg,str(source/file)]
    root=Path(__file__).resolve().parents[1]
    def run(name):return subprocess.run(args+['--output',str(tmp_path/name)],cwd=root,capture_output=True,text=True)
    a,b=run('first'),run('second')
    assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
    for file in (tmp_path/'first').iterdir():
        assert sh(file)==sh(tmp_path/'second'/file.name)
    assert run('first').returncode!=0
    with np.load(source/'p05.npz') as z:modified={key:z[key].copy() for key in z.files}
    modified['child_elevation_m'][2,3]+=10.
    dump(source/'p05.npz',modified)
    bad=run('tampered')
    assert bad.returncode!=0 and 'SHA mismatch' in bad.stderr
