import copy
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from scripts.generalize_semantic_channel_reaches_v02 import split_reaches, process, sha


def toy():
    n=12; shape=(n,n); rr,cc=np.indices(shape)
    # two merging branches and an interior bend; terminal at eastern boundary
    seqs=[[25,26,39,40,53,54,55,56,57,58,59],[16,28,40]]
    e=np.array([edge for p in seqs for edge in zip(p,p[1:])],dtype=np.int32)
    mask=np.zeros(shape,dtype=np.uint8);mask.ravel()[np.unique(e)]=1
    rec=np.full(shape,-1,dtype=np.int32);rec.ravel()[e[:,0]]=e[:,1]
    f={'channel_mask':mask,'lake_proxy_mask':np.zeros(shape,dtype=np.uint8),'channel_edge_flat_from_to':e,'lake_proxy_jumps_flat_from_to':np.empty((0,2),np.int32),'Core_dominant_receiver_index':rec,'Core_dominant_channel_area_km2_NOT_Q':mask.astype(float)*100}
    z=200.-cc+rr*.1
    c={'east_km':np.arange(n,dtype=float),'north_km_north_first':np.arange(n-1,-1,-1,dtype=float),'child_elevation_m':z,'parent_interpolated_m':z.copy(),'land_mask':np.ones(shape,np.uint8)}
    return f,c


def test_partition_exact_and_endpoints():
    f,c=toy();snapshot=copy.deepcopy((f,c));paths,fixed,raw,out,r=process(f,c)
    reconstructed=[(int(a),int(b)) for p in paths for a,b in zip(p,p[1:])]
    assert sorted(reconstructed)==sorted(map(tuple,f['channel_edge_flat_from_to']))
    assert set(fixed)=={25,16,40,59}
    assert len(paths)==3
    for a,b in zip(raw,out):np.testing.assert_array_equal(a[[0,-1]],b[[0,-1]])
    assert r['max_hausdorff_km']<=.75 and r['new_crossings']==0
    assert r['changed_reaches_gt_20m']>0
    assert r['is_approved_river_geometry'] is False
    for obj,orig in zip((f,c),snapshot):
        for k in obj:np.testing.assert_array_equal(obj[k],orig[k])


@pytest.mark.parametrize('edges',[[[13,14],[14,13]],[[13,14],[13,25]],[[13,16]],[[13,999]],[[13,13]]])
def test_reject_invalid_graph(edges):
    with pytest.raises(ValueError):split_reaches(np.array(edges,dtype=int),(12,12))


def test_boundary_nodes_fixed():
    p,f=split_reaches(np.array([[0,1],[1,2],[2,14]]),(12,12))
    assert set(f)=={0,1,2,14} and len(p)==3


@pytest.mark.parametrize('key',['lake','receiver','coast','axis','nan'])
def test_bad_inputs(key):
    f,c=toy()
    if key=='lake':f['lake_proxy_mask'][0,0]=1
    if key=='receiver':f['Core_dominant_receiver_index'].ravel()[25]=-1
    if key=='coast':c['land_mask'].ravel()[25]=0
    if key=='axis':c['east_km'][1]+=.1
    if key=='nan':c['child_elevation_m'][0,0]=np.nan
    with pytest.raises(ValueError):process(f,c)


def test_original_unconnected_crossing():
    f,c=toy();e=np.array([[13,26],[14,25]],np.int32);f['channel_edge_flat_from_to']=e;f['channel_mask'][:]=0;f['channel_mask'].ravel()[np.unique(e)]=1;f['Core_dominant_receiver_index'][:]=-1;f['Core_dominant_receiver_index'].ravel()[e[:,0]]=e[:,1]
    with pytest.raises(ValueError,match='original geometry'):process(f,c)


def test_straight_reach_does_not_invent_meanders():
    f,c=toy();e=np.array([[i,i+1] for i in range(25,32)],np.int32);f['channel_edge_flat_from_to']=e;f['channel_mask'][:]=0;f['channel_mask'].ravel()[np.unique(e)]=1;f['Core_dominant_receiver_index'][:]=-1;f['Core_dominant_receiver_index'].ravel()[e[:,0]]=e[:,1]
    *_,r=process(f,c);assert r['max_hausdorff_km']==0 and r['changed_reaches_gt_20m']==0


def test_cli_reproducibility_and_sha_guard(tmp_path):
    f,c=toy();a=tmp_path/'f.npz';b=tmp_path/'c.npz';bg=tmp_path/'bg.png';prior=tmp_path/'j.json'
    np.savez_compressed(a,**f);np.savez_compressed(b,**c);Image.new('RGB',(60,60),(100,110,90)).save(bg)
    prior.write_text(json.dumps({'status':'P4_J_TOPOLOGY_PRESERVING_DISPLAY_GEOMETRY_ONLY_NOT_RIVERS','channel_graph_topology_mutated':False,'is_approved_river_geometry':False,'source_sha256':{'baseline_projection_npz':sha(a),'baseline_child_npz':sha(b),'terrain_p4e_png':sha(bg)}}))
    cmd=[sys.executable,'-m','scripts.generalize_semantic_channel_reaches_v02','--projection',str(a),'--child',str(b),'--background',str(bg),'--prior',str(prior)]
    def run(name):return subprocess.run(cmd+['--output',str(tmp_path/name)],capture_output=True,text=True,cwd=Path(__file__).resolve().parents[1])
    u,v=run('one'),run('two');assert u.returncode==v.returncode==0,(u.stderr,v.stderr)
    for file in (tmp_path/'one').iterdir():assert sha(file)==sha(tmp_path/'two'/file.name)
    assert run('one').returncode!=0
    bg.write_bytes(bg.read_bytes()+b'changed');bad=run('bad');assert bad.returncode!=0 and 'SHA mismatch' in bad.stderr
