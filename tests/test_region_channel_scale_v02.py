"""P4-G public toy worlds, never PRIVATE Освера grids."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

from scripts.compare_region_channel_scale_v02 import (
    ChannelScaleError, THRESHOLDS, STRENGTHS, channel_morphology,
    compare_channel_scale, iou, render_maps,
)
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection


def toy():
    n=9
    r,c=np.indices((n,n))
    field=(200+5*(n-1-c)+.6*r).astype('float32')
    children={}
    for strength in STRENGTHS:
        child=(field+strength*.5*np.sin((r+1)*(c+2))).astype('float32')
        children[strength]={
           'child_elevation_m':child,'parent_interpolated_m':field.copy(),
           'land_mask':np.ones((n,n),dtype=np.uint8),
           'east_km':np.arange(-4,5,dtype=np.float64),
           'north_km_north_first':np.arange(4,-5,-1,dtype=np.float64),
        }
    macro={'latitude_deg_north_first':np.array([6.,0.,-6.]),
           'longitude_deg_west_to_east':np.array([-6.,0.,6.]),
           'source_river_mask_D8':np.zeros((3,3),dtype='uint8'),
           'local_downstream_index':np.full((3,3),-1,dtype='int32'),
           'source_catchment_km2_D8':np.ones((3,3),dtype='float32')}
    meta={'planet_radius_km':180/np.pi,'center_lat_lon_deg':[0.,0.],
          'status':'NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON',
          'is_accepted_Core_DomainData':False}
    archived={};scores=[]
    for strength in STRENGTHS:
        data,rep=connected_mfd_channel_projection(children[strength],macro,meta,stream_threshold_km2=30.)
        archived[strength]=data
        scores.append({'relief_strength':strength,
                       'channel_mask_cells_NOT_WATER':int(data['channel_mask'].sum()),
                       'connected_channel_terminal_count':len(rep['connected_boundary_endpoints'])})
    previous={'status':'P4_F_INDEPENDENT_CORE_MFD_TERRAIN_VARIANT_TOPOLOGY_NOT_RIVERS',
              'source_existing_P4E_and_P4C1_SHA_checked':True,
              'baseline_P2B2p4_exact_replay_verified':True,
              'geography_or_rivers_approved':False,
              'no_A8_external_inflow_injected_km2':0,
              'original_parent_stations_preserved':1,
              'independently_recomputed_for_each_variant':True,
              'variant_comparison':scores}
    return children,macro,meta,previous,archived


def test_real_accepted_core_comparison_on_three_toy_variants():
    args=toy();copies=copy.deepcopy(args)
    results,audit=compare_channel_scale(*args)
    assert list(results)==[(s,t) for s in STRENGTHS for t in THRESHOLDS]
    assert len(audit['morphology'])==9
    assert len(audit['cross_strength_at_fixed_threshold'])==9
    assert not audit['is_accepted_Core_change'] and not audit['is_approved_physical_river_or_Q']
    assert audit['A8_old_D8_flow_imported_km2']==0
    for s in STRENGTHS:
        for t in THRESHOLDS:
            score=next(q for q in audit['morphology'] if q['relief_strength']==s and q['stream_threshold_km2_NOT_Q']==t)
            assert score['local_area_km2_NOT_WATER']==81
            assert abs(score['conservation_error_km2'])<1e-7
            assert score['ordinary_edge_length_km']>=score['ordinary_edges']
            assert 0<=score['diagonal_edge_fraction']<=1
        for key in args[4][s]:
            np.testing.assert_array_equal(results[(s,30.)][0][key],args[4][s][key])
        for key in args[0][s]:np.testing.assert_array_equal(args[0][s][key],copies[0][s][key])


@pytest.mark.parametrize('problem',['unknown_threshold','missing_strength','bad_status',
 'not_verified','accepted_rivers','external_flow','different_parent','different_coast','different_axis',
 'damaged_archive','wrong_score','bad_mass'])
def test_provenance_and_thresholds_fail_closed(problem):
    data=list(toy());kw={}
    if problem=='unknown_threshold':kw['thresholds']=(10.,30.,60.)
    elif problem=='missing_strength':data[0].pop(.5)
    elif problem=='bad_status':data[3]['status']='AUTHOR_APPROVED'
    elif problem=='not_verified':data[3]['source_existing_P4E_and_P4C1_SHA_checked']=False
    elif problem=='accepted_rivers':data[3]['geography_or_rivers_approved']=True
    elif problem=='external_flow':data[3]['no_A8_external_inflow_injected_km2']=12
    elif problem=='different_parent':data[0][.5]['parent_interpolated_m'][1,1]+=1
    elif problem=='different_coast':data[0][1.25]['land_mask'][0,0]=0
    elif problem=='different_axis':data[0][.5]['east_km']+=.1
    elif problem=='damaged_archive':data[4][2.]['channel_mask'][2,2]^=1
    elif problem=='wrong_score':data[3]['variant_comparison'][1]['connected_channel_terminal_count']+=1
    elif problem=='bad_mass':data[3]['baseline_P2B2p4_exact_replay_verified']=False
    with pytest.raises(ChannelScaleError):compare_channel_scale(*data,**kw)


def test_channel_graph_validation_and_metric_semantics():
    data={'channel_mask':np.zeros((5,5),dtype='uint8'),
          'channel_edge_flat_from_to':np.array([[6,7],[7,8],[11,7]],dtype='int32'),
          'lake_proxy_jumps_flat_from_to':np.zeros((0,2),dtype='int32')}
    data['channel_mask'].ravel()[[6,7,11]]=1
    ledger={'routed_ordinary_channel_cells':3,'ordinary_adjacent_channel_edges':3,
            'nonphysical_proxy_links_NOT_RIVERS':0,
            'connected_boundary_endpoints':[],'headwater_seed_cells':3}
    result=channel_morphology(data,ledger)
    assert result['model_confluence_nodes_with_2_or_more_incoming']==1
    assert result['model_topological_headwater_nodes']==2
    assert result['ordinary_edges']==3
    bad=copy.deepcopy(data);bad['channel_edge_flat_from_to'][0,1]=24
    with pytest.raises(ChannelScaleError):channel_morphology(bad,ledger)
    bad=copy.deepcopy(data);bad['channel_edge_flat_from_to'][2,0]=6
    with pytest.raises(ChannelScaleError):channel_morphology(bad,ledger)
    ledger['ordinary_adjacent_channel_edges']=1
    with pytest.raises(ChannelScaleError):channel_morphology(data,ledger)


def test_iou_exact_empty_and_shape_rejection():
    assert iou(np.zeros((3,3)),np.zeros((3,3)))==1
    assert iou(np.ones((3,3)),np.zeros((3,3)))==0
    assert iou(np.eye(3),np.eye(3))==1
    with pytest.raises(ChannelScaleError):iou(np.zeros((3,3)),np.zeros((4,4)))


def test_render_two_complete_comparisons_are_byte_identical(tmp_path):
    args=toy();outputs,summary=compare_channel_scale(*args)
    back={}
    for s in STRENGTHS:
        f=tmp_path/(str(s)+'-map.png');Image.new('RGB',(9*5,9*5),(63,91,65)).save(f);back[s]=f
    render_maps(outputs,summary,back,tmp_path/'one')
    render_maps(outputs,summary,back,tmp_path/'two')
    for name in ['region-model-network-threshold-3x3.png','region-network-map-review-3variants.png']:
        assert (tmp_path/'one'/name).read_bytes()==(tmp_path/'two'/name).read_bytes()
    with pytest.raises(ChannelScaleError):render_maps(outputs,summary,back,tmp_path/'one')


def test_cli_replays_real_core_toy_and_sha_rejects_corruption(tmp_path):
    children,macro,meta,p4f,baseline=toy();directory=tmp_path/'sources';directory.mkdir()
    def save(n,z):np.savez_compressed(directory/n,**z)
    save('macro.npz',macro);save('child05.npz',children[.5]);save('child125.npz',children[1.25]);save('child20.npz',children[2.])
    save('p4f05.npz',baseline[.5]);save('p4f125.npz',baseline[1.25]);save('p4f20.npz',baseline[2.])
    (directory/'manifest.json').write_text(json.dumps(meta))
    def sh(f):return hashlib.sha256(f.read_bytes()).hexdigest()
    audit_e={'status':'P4_E_ANCHOR_PRESERVING_CHILD_RELIEF_STRENGTH_ALTERNATIVES_NOT_CANON',
             'source_parent_station_count':1,'P4A_and_P4D_source_bytes_verified':True}
    (directory/'e.json').write_text(json.dumps(audit_e))
    p4f['source_sha256']={
        'macro_npz':sh(directory/'macro.npz'),'baseline_child_npz':sh(directory/'child20.npz'),
        'child_manifest':sh(directory/'manifest.json'),'variant_0p5_npz':sh(directory/'child05.npz'),
        'variant_1p25_npz':sh(directory/'child125.npz'),'p4e_audit_json':sh(directory/'e.json'),
        'baseline_projection_npz':sh(directory/'p4f20.npz')}
    (directory/'f.json').write_text(json.dumps(p4f))
    for s in ('05','125','20'):Image.new('RGB',(9*5,9*5),(63,91,65)).save(directory/(s+'.png'))
    args=[sys.executable,'-m','scripts.compare_region_channel_scale_v02']
    mapping={'macro-npz':'macro.npz','child-manifest':'manifest.json',
      'child-0p5-npz':'child05.npz','child-1p25-npz':'child125.npz','child-2p0-npz':'child20.npz',
      'p4e-audit-json':'e.json','p4f-audit-json':'f.json',
      'p4f-0p5-npz':'p4f05.npz','p4f-1p25-npz':'p4f125.npz','p4f-2p0-npz':'p4f20.npz',
      'terrain-0p5-png':'05.png','terrain-1p25-png':'125.png','terrain-2p0-png':'20.png'}
    for key,name in mapping.items():args.extend(['--'+key,str(directory/name)])
    root=Path(__file__).resolve().parents[1]
    def run(folder):return subprocess.run(args+['--output',str(tmp_path/folder)],cwd=root,capture_output=True,text=True)
    one,two=run('one'),run('two')
    assert one.returncode==0,(one.stderr,one.stdout[-1000:])
    assert two.returncode==0,(two.stderr,two.stdout[-1000:])
    for file in (tmp_path/'one').iterdir():assert sh(file)==sh(tmp_path/'two'/file.name)
    assert run('one').returncode!=0
    with np.load(directory/'child05.npz') as source:
        damaged={k:source[k].copy() for k in source.files}
    damaged['child_elevation_m'][0,0]+=1
    save('child05.npz',damaged)
    failed=run('tampered')
    assert failed.returncode!=0 and 'SHA mismatch' in failed.stderr


def test_rectangular_synthetic_map_composition(tmp_path):
    # The synthetic CI domain is not required to be square. Renderer must
    # respect native row/col dimensions instead of cropping or stretching.
    shape=(5,9)
    outputs={}
    morphology=[]
    for strength in STRENGTHS:
        for threshold in THRESHOLDS:
            fields={'channel_edge_flat_from_to':np.zeros((0,2),dtype=np.int32),
                    'Core_dominant_channel_area_km2_NOT_Q':np.ones(shape,dtype='float32')}
            outputs[(strength,threshold)]=(fields,{})
            morphology.append({'relief_strength':strength,'stream_threshold_km2_NOT_Q':threshold,
                   'ordinary_skeleton_cells':0,'model_confluence_nodes_with_2_or_more_incoming':0,
                   'ordinary_edge_length_km':0,'model_terminal_count':0})
    audit={'source_grid_shape':list(shape),'morphology':morphology}
    backgrounds={}
    for strength in STRENGTHS:
        f=tmp_path/(str(strength)+'-rect.png')
        Image.new('RGB',(shape[1]*5,shape[0]*5),(64,93,70)).save(f)
        backgrounds[strength]=f
    render_maps(outputs,audit,backgrounds,tmp_path/'rect')
    with Image.open(tmp_path/'rect'/'region-model-network-threshold-3x3.png') as im:
        assert im.size==(36*2+3*shape[1]*5+2*22,85+3*shape[0]*5+2*22+116)
    with Image.open(tmp_path/'rect'/'region-network-map-review-3variants.png') as im:
        assert im.size==(52*2+3*shape[1]*5+2*26,91+shape[0]*5+130)
