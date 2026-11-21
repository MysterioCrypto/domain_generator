"""P4-C1 historical A8 inlet / Core MFD route evidence — toy-only tests."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

from scripts.reconcile_region_boundary_corridors_v02 import (
    BoundaryCorridorError, reconcile_boundary, render_evidence,
)


def toy():
    size=7
    z=np.array([[120.-2*c+3*r for c in range(size)] for r in range(size)],dtype='float32')
    child={'child_elevation_m':z,'east_km':np.arange(-3,4,dtype=float),
           'north_km_north_first':np.arange(3,-4,-1,dtype=float)}
    cm={'status':'NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON',
        'is_accepted_Core_DomainData':False,'detail_coordinate_system':'spherical_xyz_v1',
        'planet_radius_km':180/np.pi,'center_lat_lon_deg':[0.,0.]}
    river=np.zeros((5,5),dtype=np.uint8)
    next_index=np.full((5,5),-1,dtype='int32')
    river[2,0]=1;next_index[2,0]=2*5+1
    river[2,3]=1;next_index[2,3]=2*5+4
    macro={'latitude_deg_north_first':np.array([4,2,0,-2,-4],dtype=float),
           'longitude_deg_west_to_east':np.array([-4,-2,0,2,4],dtype=float),
           'source_river_mask_D8':river,
           'local_downstream_index':next_index,
           'source_catchment_km2_D8':np.full((5,5),90.,dtype='float64')}
    mask=np.zeros((size,size),dtype='uint8');mask[3,1:7]=1
    receiver=np.full((size,size),-1,dtype='int32')
    edges=[]
    for c in range(1,6):
        source=3*size+c;dest=source+1
        edges.append([source,dest]);receiver[3,c]=dest
    edges=np.asarray(edges,dtype='int32')
    projection={'channel_mask':mask,
                'Core_dominant_receiver_index':receiver,
                'channel_edge_flat_from_to':edges,
                'lake_proxy_jumps_flat_from_to':np.empty((0,2),dtype='int32')}
    from scripts.compare_planetary_child_mfd_outlets_v02 import macro_outlet_candidates
    oldexit=macro_outlet_candidates(macro, child, cm)[0][0]
    report={'status':'P2_B2_4_REFERENCE_EXIT_ALIGNMENT_NOT_ACCEPTED_HYDROLOGY',
            'is_author_approved_local_river_map':False,
            'external_area_auto_injected_km2':0.,
            'source_macro_A8_outlets':[oldexit],
            'child_core_dominant_channel_ledger':{
                'status':'CONNECTED_CORE_DOMINANT_MFD_CHANNEL_PROJECTION_NOT_REAL_RIVERS',
                'is_physical_discharge_or_approved_river':False,
                'no_external_A8_source_area_auto_injected':True,
                'connected_boundary_endpoints':[{'child_edge_cell_row_col':[3,6]}],
                'lake_topology_status':'NO_LAKES_QUALIFIED'}}
    masks={'all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS':edges[[0,1,3,4]],
           'withheld_ordinary_edges_NOT_DISPLAYED':edges[[2]],
           'lake_proxy_jumps_NOT_RIVERS':np.empty((0,2),dtype='int32')}
    audit={'status':'P4B_CONSERVATIVE_DRAINAGE_EVIDENCE_NOT_CANONICAL_RIVERS',
           'is_accepted_hydrology':False,'is_water_occupancy_or_discharge':False,
           'source_external_inflow_km2_applied':0.,
           'p4a_child_npz_sha256_lineage_verified':True,
           'all_strictly_downhill_edges':4,
           'withheld_unsafe_ordinary_edges':1,
           'undrawn_geometric_lake_proxy_jumps':0}
    return macro,child,cm,projection,report,masks,audit


def test_one_macro_entry_matches_one_child_route_with_a_withheld_gap(tmp_path):
    data=toy()
    saved=copy.deepcopy(data)
    audit,paths=reconcile_boundary(*data,boundary_band_km=2,crossing_radius_km=5,
                                   outlet_radius_km=5)
    assert audit['source_macro_inlet_count']==1
    assert audit['source_macro_exit_count']==1
    assert audit['inlets_with_candidate_internal_graph']==1
    assert not audit['same_macro_to_child_basin_identity_established']
    assert audit['external_inflow_area_injected_km2']==0
    inlet=audit['inlet_results'][0]
    assert inlet['status']=='ONE_GEOMETRIC_CHILD_ROUTE_HINT_NOT_VERIFIED'
    assert inlet['nearby_strict_inward_edges'] == 2
    assert inlet['distinct_child_terminals_reachable']==1
    assert inlet['A8_upstream_area_km2_UNSAFE_NOT_INJECTED']==90
    chosen=inlet['selected_candidate']
    assert chosen['child_start_row_col']==[3,1]
    assert chosen['terminal_row_col']==[3,6]
    assert chosen['path_length_edges']==5
    assert chosen['strict_downhill_edges']==4
    assert chosen['withheld_unsafe_edges']==1
    assert chosen['same_side_macro_exit_near_only']['distance_km']==0
    assert not chosen['full_continuity_as_physical_river_verified']
    for value,old in zip(data,saved):
        if isinstance(value,dict):
            for key,x in value.items():
                if isinstance(x,np.ndarray):np.testing.assert_array_equal(x,old[key])
                else:assert x==old[key]
    render_evidence(data[1],Image.new('RGB',(7*12,7*12),'#63795c'),
                    audit,paths,tmp_path/'out')
    assert (tmp_path/'out/boundary-corridor-evidence-sheet.png').exists()


def test_not_enough_inward_routing_stays_unresolved():
    data=list(toy())
    data[3]['channel_edge_flat_from_to']=np.empty((0,2),dtype='int32')
    data[5]['all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS']=np.empty((0,2),dtype='int32')
    data[5]['withheld_ordinary_edges_NOT_DISPLAYED']=np.empty((0,2),dtype='int32')
    data[6]['all_strictly_downhill_edges']=0
    data[6]['withheld_unsafe_ordinary_edges']=0
    audit,paths=reconcile_boundary(*data)
    assert audit['source_macro_inlet_count']==1
    assert audit['inlets_with_candidate_internal_graph']==0
    assert audit['inlet_results'][0]['status']=='NO_INWARD_CHILD_GRAPH_CANDIDATE'
    assert paths['selected_paths']==[]


@pytest.mark.parametrize('failure',["accepted_river", "injected_area", "graph_mismatch",
                                    "receiver_mismatch", "cycle", "duplicate",
                                    "wrong_edges", "nan_grid", "bad_spacing"])
def test_fail_closed_on_inconsistent_evidence(failure):
    data=list(toy())
    if failure=='accepted_river':data[4]['is_author_approved_local_river_map']=True
    elif failure=='injected_area':data[4]['external_area_auto_injected_km2']=42.
    elif failure=='graph_mismatch':data[5]['all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS'][0]=[10,11]
    elif failure=='receiver_mismatch':data[3]['Core_dominant_receiver_index'][3,2]=-1
    elif failure=='cycle':
        data[3]['Core_dominant_receiver_index'][3,5]=3*7+1
        data[3]['channel_edge_flat_from_to'][-1]=[3*7+5,3*7+1]
        data[5]['all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS'][-1]=[3*7+5,3*7+1]
    elif failure=='duplicate':
        data[5]['all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS'][1]=data[5]['all_strictly_downhill_edges_NOT_CONFIRMED_RIVERS'][0]
    elif failure=='wrong_edges':data[6]['all_strictly_downhill_edges']=55
    elif failure=='nan_grid':data[1]['child_elevation_m'][0,0]=float('nan')
    elif failure=='bad_spacing':data[1]['north_km_north_first']=np.arange(-3,4,dtype=float)
    with pytest.raises(BoundaryCorridorError):reconcile_boundary(*data)


def test_empty_macro_entries_is_not_hallucinated():
    data=list(toy())
    data[0]['source_river_mask_D8'][2,0]=0
    a,g=reconcile_boundary(*data)
    assert a['source_macro_inlet_count']==0
    assert a['inlets_with_candidate_internal_graph']==0
    assert g['selected_paths']==[]


def test_cli_hash_guard_and_bitwise_replay(tmp_path):
    data=toy()
    folder=tmp_path/'inputs';folder.mkdir()
    np.savez_compressed(folder/'macro.npz',**data[0]);np.savez_compressed(folder/'child.npz',**data[1]);
    np.savez_compressed(folder/'projection.npz',**data[3]);np.savez_compressed(folder/'masks.npz',**data[5]);
    for nm,v in [('cm',data[2]),('projection',data[4])]:
        (folder/(nm+'.json')).write_text(json.dumps(v),encoding='utf8')
    audit=data[6].copy()
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    Image.new('RGB',(140,140),'#5c7659').save(folder/'p4a.png')
    audit['input_sha256']={'child_npz':sha(folder/'child.npz'),
                           'projection_npz':sha(folder/'projection.npz'),
                           'p4a_image':sha(folder/'p4a.png')}
    (folder/'p4b.json').write_text(json.dumps(audit),encoding='utf8')
    cmd=[sys.executable,'-m','scripts.reconcile_region_boundary_corridors_v02']
    for name,path in [('macro-npz','macro.npz'),('child-npz','child.npz'),
                      ('child-manifest','cm.json'),('projection-npz','projection.npz'),
                      ('projection-manifest','projection.json'),('p4b-masks-npz','masks.npz'),
                      ('p4b-audit-json','p4b.json'),('p4a-map-image','p4a.png')]:
        cmd+=['--'+name,str(folder/path)]
    root=Path(__file__).resolve().parents[1]
    def call(name):
        return subprocess.run(cmd+['--output',str(tmp_path/name)],
                              cwd=root,capture_output=True,text=True)
    a=call('a');b=call('b')
    assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
    for item in ['boundary-corridor-audit.json','boundary-corridor-evidence-map.png',
                 'boundary-corridor-evidence-sheet.png']:
        assert sha(tmp_path/'a'/item)==sha(tmp_path/'b'/item)
    assert call('a').returncode!=0
    with np.load(folder/'child.npz') as z:altered={k:z[k].copy() for k in z.files}
    altered['child_elevation_m'][0,0]+=4
    np.savez_compressed(folder/'child.npz',**altered)
    result=call('wrong-hash')
    assert result.returncode!=0 and 'hash lineage mismatch' in result.stderr
    np.savez_compressed(folder/'child.npz', **data[1])
    Image.new('RGB',(140,140),'#707070').save(folder/'p4a.png')
    result=call('wrong-map-hash')
    assert result.returncode!=0 and 'hash lineage mismatch' in result.stderr


def test_macro_outlets_must_match_prior_projection_source():
    data=list(toy())
    data[0]['source_river_mask_D8'][2,3]=0
    with pytest.raises(BoundaryCorridorError,match='macro does not reproduce'):
        reconcile_boundary(*data)
