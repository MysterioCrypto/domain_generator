"""P4-J public toy maps only: graph topology, SHA, spatial display invariants."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

from scripts.generalize_region_model_channel_geometry_v02 import (
    GeometryDisplayError, generalize_model_edges, render_comparison,
)


def toy():
    shape=(9,9);e=np.array([[30,31],[31,32],[23,32],[32,42],[42,51],[51,52],[52,53]],dtype=np.int32)
    mask=np.zeros(shape,dtype='uint8');mask.ravel()[np.unique(e)]=1
    receiver=np.full(shape,-1,dtype='int32');receiver.ravel()[e[:,0]]=e[:,1]
    fields={'channel_mask':mask,'Core_dominant_receiver_index':receiver,
        'channel_edge_flat_from_to':e,'lake_proxy_jumps_flat_from_to':np.zeros((0,2),dtype='int32'),
        'Core_dominant_channel_area_km2_NOT_Q':np.where(mask,100.,0.).astype('float32')}
    child={'east_km':np.arange(9,dtype='float64'),
           'north_km_north_first':np.arange(8,-1,-1,dtype='float64')}
    return fields,child


def test_preserve_all_nodes_edges_branching_endpoints_and_audit():
    data,child=toy();original=copy.deepcopy(data)
    xy,audit=generalize_model_edges(data,child['east_km'],child['north_km_north_first'])
    assert xy.shape==(7,9,2)
    assert audit['source_edge_count']==7
    assert audit['original_node_ids_and_edge_order_preserved']
    assert audit['all_original_node_positions_exact']
    assert not audit['channel_graph_topology_mutated']
    assert not audit['is_approved_river_geometry']
    assert audit['independent_original_crossing_count']==audit['independent_display_crossing_count']==0
    assert audit['maximum_hausdorff_offset_km']<=.2
    assert audit['edges_with_geometric_change_gt_0p02_km']>0
    e=data['channel_edge_flat_from_to']
    np.testing.assert_array_equal(xy[:,0,0],child['east_km'][e[:,0]%9])
    np.testing.assert_array_equal(xy[:,-1,1],child['north_km_north_first'][e[:,1]//9])
    for k,v in original.items():np.testing.assert_array_equal(data[k],v)


@pytest.mark.parametrize('bad',['empty','repeated_source','nonadjacent','wrong_receiver','unmasked_source','unmasked_target','bounds','proxy','cycle','bad_x_axis','bad_y_axis','bad_shape','bad_tolerance'])
def test_illegal_graph_or_grid_rejected(bad):
    f,c=toy()
    if bad=='empty':f['channel_edge_flat_from_to']=np.zeros((0,2),dtype=np.int32)
    if bad=='repeated_source':f['channel_edge_flat_from_to'][1,0]=30
    if bad=='nonadjacent':f['channel_edge_flat_from_to'][0,1]=40
    if bad=='wrong_receiver':f['Core_dominant_receiver_index'][3,3]=-1
    if bad=='unmasked_source':f['channel_mask'][3,3]=0
    if bad=='unmasked_target':f['channel_mask'][4,6]=0
    if bad=='bounds':f['channel_edge_flat_from_to'][0,1]=999
    if bad=='proxy':f['lake_proxy_jumps_flat_from_to']=np.array([[30,44]],dtype=np.int32)
    if bad=='cycle':
        f['channel_edge_flat_from_to']=np.array([[30,31],[31,30]],dtype=np.int32)
        f['Core_dominant_receiver_index'].fill(-1)
        f['Core_dominant_receiver_index'].ravel()[[30,31]]=[31,30]
    if bad=='bad_x_axis':c['east_km'][5]+=2
    if bad=='bad_y_axis':c['north_km_north_first'][5]+=2
    if bad=='bad_shape':c['east_km']=c['east_km'][:6]
    kwargs={'max_offset_km':.5} if bad=='bad_tolerance' else {}
    with pytest.raises(GeometryDisplayError):generalize_model_edges(f,c['east_km'],c['north_km_north_first'],**kwargs)


def test_non_connected_crossing_is_not_silently_smoothed():
    f,c=toy();e=np.array([[10,20],[11,19]],dtype=np.int32)
    f['channel_edge_flat_from_to']=e
    f['channel_mask'][:]=0;f['channel_mask'].ravel()[np.unique(e)]=1
    f['Core_dominant_receiver_index'].fill(-1);f['Core_dominant_receiver_index'].ravel()[e[:,0]]=e[:,1]
    with pytest.raises(GeometryDisplayError,match='crosses'):
        generalize_model_edges(f,c['east_km'],c['north_km_north_first'])


def test_render_two_identical_outputs_without_mutation(tmp_path):
    f,c=toy();xy,audit=generalize_model_edges(f,c['east_km'],c['north_km_north_first'])
    audit['origin_xy_km']=[0.,8.]
    img=tmp_path/'terrain.png';Image.new('RGB',(45,45),(84,106,83)).save(img)
    for out in (tmp_path/'one',tmp_path/'two'):
        render_comparison(f,xy,copy.deepcopy(audit),img,out)
    for name in ('p4j-overview-original-vs-bounded-curves.png','p4j-zoom-original-vs-bounded-curves.png'):
        assert (tmp_path/'one'/name).read_bytes()==(tmp_path/'two'/name).read_bytes()
    with pytest.raises(GeometryDisplayError):render_comparison(f,xy,audit,img,tmp_path/'one')


def test_full_cli_source_sha_and_deterministic_replay(tmp_path):
    f,child=toy();src=tmp_path/'sources';src.mkdir()
    np.savez_compressed(src/'source.npz',**f)
    np.savez_compressed(src/'child.npz',**child)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    prior={'status':'P4_I_HERMITE_VS_BILINEAR_PARENT_ANCHOR_CONTROL_NOT_RIVERS',
           'not_author_accepted_geography_or_rivers':True,
           'P4F_archived_3_original_model_fields_exact_replay':True,
           'accepted_Core_changed':False,
           'source_sha256':{'baseline_projection_npz':sha(src/'source.npz'),'baseline_child_npz':sha(src/'child.npz')}}
    (src/'prior.json').write_text(json.dumps(prior))
    Image.new('RGB',(45,45),(84,106,83)).save(src/'terrain.png')
    args=[sys.executable,'-m','scripts.generalize_region_model_channel_geometry_v02',
        '--baseline-projection-npz',str(src/'source.npz'),
        '--baseline-child-npz',str(src/'child.npz'),
        '--p4i-audit-json',str(src/'prior.json'),
        '--terrain-png',str(src/'terrain.png')]
    root=Path(__file__).resolve().parents[1]
    def run(name):return subprocess.run(args+['--output',str(tmp_path/name)],cwd=root,capture_output=True,text=True)
    a,b=run('one'),run('two');assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
    for file in (tmp_path/'one').iterdir():assert sha(file)==sha(tmp_path/'two'/file.name)
    with np.load(tmp_path/'one'/'p4j-display-only-channel-curves.npz') as z:
        np.testing.assert_array_equal(z['source_target_flat'],f['channel_edge_flat_from_to'])
    assert run('one').returncode!=0
    with np.load(src/'source.npz') as z:broken={k:z[k].copy() for k in z.files}
    broken['Core_dominant_channel_area_km2_NOT_Q'][3,3]+=1
    np.savez_compressed(src/'source.npz',**broken)
    failed=run('altered')
    assert failed.returncode!=0 and 'SHA mismatch' in failed.stderr
