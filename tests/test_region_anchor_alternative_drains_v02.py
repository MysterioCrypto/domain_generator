"""P4-D TOY ONLY. No actual Osvera data in public test fixtures."""

import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

from domain_generator.hydrology.routing import priority_flood_surfaces
from scripts.audit_region_corridor_sensitivity_v02 import audit_route_sensitivity
from scripts.audit_region_anchor_alternative_drains_v02 import (
    AnchorDrainEvidenceError, audit_anchor_alternatives, parent_stations,
    render_diagnostic,
)


def toy():
    parent=np.vstack([np.full(7,30.), [20.,19.,18.,17.,18.,17.,16.],np.full(7,30.)])
    raw=parent.copy()
    raw[1,3]=19.
    raw[1,4]=20.
    macro={
        'latitude_deg_north_first':np.array([2.,0.,-2.]),
        'longitude_deg_west_to_east':np.array([-4.,0.,4.]),
        'elevation_m':np.full((3,3),15.),
        'land_mask':np.ones((3,3),dtype='uint8'),
    }
    child={'child_elevation_m':raw.astype('float32'),
           'parent_interpolated_m':parent.astype('float32'),
           'new_local_relief_m':(raw-parent).astype('float32'),
           'east_km':np.arange(-3,4,dtype='float64'),
           'north_km_north_first':np.array([1.,0.,-1.])}
    cm={'status':'NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON',
        'is_accepted_Core_DomainData':False,
        'detail_coordinate_system':'spherical_xyz_v1',
        'planet_radius_km':180/np.pi,
        'center_lat_lon_deg':[0.,0.],
        'max_parent_anchor_error_m':0.,
        'source_elevation_anchors_in_child':1}
    fill=np.maximum(0,priority_flood_surfaces(raw).fill_elevation_m-raw)
    route=[];strict=set();hidden=set()
    for col in (1,2,3,4):
        a=7+col;b=a+1
        tag='safe' if raw[1,col+1]<raw[1,col] and max(fill[1,col],fill[1,col+1])<=2 else 'withheld'
        route.append((a,b,tag))
        (strict if tag=='safe' else hidden).add((a,b))
    rec,rows=audit_route_sensitivity(raw,fill,route,strict,hidden,set(),thresholds=(0,2,10))
    p4c2={'status':'P4_C2_RAW_DEM_ROUTE_SENSITIVITY_NOT_RIVERS',
          'P4C1_exact_file_lineage_verified':True,
          'accepted_water_or_same_basin_identity':False,
          'A8_D8_cumulative_area_not_imported_km2':0.,
          'per_route':[rec]}
    return macro,child,cm,p4c2,rows


def test_fine_residual_and_parent_uphill_are_separate_categories():
    args=toy();original=copy.deepcopy(args)
    audit,edges=audit_anchor_alternatives(*args)
    assert audit['original_parent_stations_continuous_not_child_pixels']==1
    assert audit['raw_uphill_or_flat_edges']==2
    assert audit['fine_residual_reversals_of_descending_parent']==1
    assert audit['parent_gradient_already_non_downhill']==1
    assert audit['blocked_sources_with_immediate_alternative_raw_downhill']==1
    assert audit['blocked_sources_without_immediate_raw_downhill']==1
    assert audit['greedy_raw_descent_ends_at_local_sinks_NOT_LAKES']==2
    assert audit['greedy_raw_descent_reaches_boundary']==0
    assert audit['raw_bad_runs_count']==1
    assert audit['max_consecutive_raw_bad_edges']==2
    assert audit['physical_basin_identity_or_river_verified'] is False
    assert audit['macro_A8_upstream_area_injected_km2']==0
    assert (edges[1]['raw_delta_m']==1. and edges[1]['parent_delta_m']==-1.
            and edges[1]['effective_fine_residual_delta_m']==2.)
    assert (edges[2]['raw_delta_m']==1. and edges[2]['parent_delta_m']==1.)
    assert np.array_equal(args[1]['child_elevation_m'],original[1]['child_elevation_m'])
    assert args[4]==original[4]


def test_parent_stations_are_geographic_not_rounded_to_pixels():
    macro,child,cm,_,_=toy()
    macro['longitude_deg_west_to_east']=np.array([-4.,.25,4.])
    stations=parent_stations(macro,child,cm)
    assert stations.shape==(1,2)
    assert abs(stations[0,0]-.25)<1e-8


@pytest.mark.parametrize('kind',[ 'wrong_coord_mode','bad_anchor_count','bad_anchor_error',
                                  'nonfinite_dem','short_p4c2','rejected_canon','tampered_row',
                                  'tampered_height','tampered_fill','disconnected',
                                  'bad_spacing','bad_threshold'])
def test_provenance_and_bad_geometry_fail_closed(kind):
    data=list(toy())
    if kind=='wrong_coord_mode':data[2]['detail_coordinate_system']='invalid_detail_coordinate_mode'
    if kind=='bad_anchor_count':data[2]['source_elevation_anchors_in_child']=8
    if kind=='bad_anchor_error':data[2]['max_parent_anchor_error_m']=3
    if kind=='nonfinite_dem':data[1]['child_elevation_m'][0,0]=float('nan')
    if kind=='short_p4c2':data[3]['status']='GIVEN_WATER'
    if kind=='rejected_canon':data[3]['accepted_water_or_same_basin_identity']=True
    if kind=='tampered_row':data[4][1]['target_col']=1
    if kind=='tampered_height':data[4][0]['raw_delta_m_target_minus_source']=-999.
    if kind=='tampered_fill':data[4][0]['max_endpoint_virtual_fill_m_NOT_WATER']=100.
    if kind=='disconnected':data[4][2]['source_col']=0
    if kind=='bad_spacing':data[1]['north_km_north_first'][1]=-.25
    if kind=='bad_threshold':data[3]['per_route'][0]['baseline_fill_limit_m']=200.
    with pytest.raises((AnchorDrainEvidenceError, KeyError, ValueError)):
        audit_anchor_alternatives(*data)


def test_empty_and_partially_deleted_route_rejected():
    data=list(toy())
    data[4]=[]
    with pytest.raises(AnchorDrainEvidenceError):audit_anchor_alternatives(*data)
    data=list(toy());data[4]=data[4][:-1]
    with pytest.raises(AnchorDrainEvidenceError):audit_anchor_alternatives(*data)


def test_renderer_both_layers_and_refuses_overwriting(tmp_path):
    macro,child,cm,p4c2,source=toy()
    audit,rows=audit_anchor_alternatives(macro,child,cm,p4c2,source)
    base=Image.new('RGB',(7*30,3*30),(93,118,95))
    for name in ('a','b'):
        render_diagnostic(base,child,macro,cm,rows,audit,tmp_path/name)
    for name in ('anchor-gradient-evidence-map.png','anchor-gradient-evidence-sheet.png'):
        a=(tmp_path/'a'/name).read_bytes();b=(tmp_path/'b'/name).read_bytes()
        assert hashlib.sha256(a).digest()==hashlib.sha256(b).digest()
    with pytest.raises(FileExistsError):
        render_diagnostic(base,child,macro,cm,rows,audit,tmp_path/'a')


def test_cli_hash_lineage_and_bitwise_replay(tmp_path):
    macro,child,cm,p4c2,rows=toy();data=tmp_path/'inputs';data.mkdir()
    np.savez_compressed(data/'macro.npz',**macro);np.savez_compressed(data/'child.npz',**child)
    (data/'cm.json').write_text(json.dumps(cm),encoding='utf8')
    with (data/'edges.csv').open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    Image.new('RGB',(210,90),(104,123,101)).save(data/'map.png')
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    p4c2['input_sha256']={k:sha(data/n) for k,n in (
        ('macro_npz','macro.npz'),('child_npz','child.npz'),
        ('child_manifest','cm.json'),('p4a_map_image','map.png'))}
    (data/'p4c2.json').write_text(json.dumps(p4c2),encoding='utf8')
    args=[sys.executable,'-m','scripts.audit_region_anchor_alternative_drains_v02']
    for key,name in [('macro-npz','macro.npz'),('child-npz','child.npz'),
                     ('child-manifest','cm.json'),('p4c2-audit-json','p4c2.json'),
                     ('p4c2-edges-csv','edges.csv'),('p4a-map-image','map.png')]:
        args.extend(('--'+key,str(data/name)))
    root=Path(__file__).resolve().parents[1]
    def run(target):return subprocess.run(args+['--output',str(tmp_path/target)],cwd=root,capture_output=True,text=True)
    a,b=run('a'),run('b')
    assert a.returncode==0,(a.stderr,a.stdout[-1000:])
    assert b.returncode==0,(b.stderr,b.stdout[-1000:])
    for p in ('anchor-gradient-evidence-map.png','anchor-gradient-evidence-sheet.png',
              'anchor-gradient-audit.json','anchor-gradient-all-edges.csv'):
        assert sha(tmp_path/'a'/p)==sha(tmp_path/'b'/p)
    assert run('a').returncode!=0
    with np.load(data/'child.npz') as z:changed={k:z[k].copy() for k in z.files}
    changed['child_elevation_m'][0,0]+=1
    np.savez_compressed(data/'child.npz',**changed)
    failure=run('corrupt')
    assert failure.returncode!=0 and 'SHA lineage mismatch' in failure.stderr
