"""P4-P regression: native normalization fixes a real false merge, not just a mock."""
import json
from pathlib import Path
import numpy as np
import pytest
import domain_generator
from domain_generator.contracts.spec import DomainSpec
from domain_generator.presets.registry import PresetRegistry
from domain_generator.compiler import compile_domain_spec
from domain_generator.terrain.state import TerrainState
import domain_generator.hydrology.continuous as core
from scripts.audit_native_network_spatial_v02 import audit_network


def plan():
    root=Path(__file__).resolve().parents[1]
    s=json.loads((root/'examples/terrain-v02/checkpoint/request.json').read_text())['domain_spec']
    s.update(id='p4p-test',features=[],constraints=[],seed=1406,domain={'size':{'width_km':30.5,'height_km':30.5}},simulation={'cell_size_km':.5})
    s['hydrology'].update(stream_threshold_km2=30.,lake_min_area_km2=16.,lake_min_depth_m=10.)
    return compile_domain_spec(DomainSpec.model_validate(s),registry=PresetRegistry([],operator_ids=[]),generator_version=domain_generator.__version__)


@pytest.mark.parametrize('seed,legacy_valid',[(0,True),(3,False)])
def test_native_regional_normalization(seed,legacy_valid,monkeypatch):
    rr,cc=np.indices((61,61));r=np.random.default_rng(seed)
    z=400-cc*1.5+sum(r.uniform(1,8)*np.sin(rr*r.uniform(.07,.45)+cc*r.uniform(.07,.45)+r.uniform(0,6)) for _ in range(8))
    p=plan();t=TerrainState(elevation_m=z.copy());original=core.build_continuous_river_network;calls=[]
    def legacy(*args,**kwargs):
        calls.append(1)
        if len(calls)==1:kwargs['normalize_false_confluences']=False
        return original(*args,**kwargs)
    with monkeypatch.context() as m:
        m.setattr(core,'build_continuous_river_network',legacy);old=core.generate_hydrology_v02(p,t)
    new=core.generate_hydrology_v02(p,t,experimental_network_assembly=True)
    assert core._network_invariants(old.river_network)==legacy_valid
    assert core.validate_hydrology_v02(p,t,new,attempt_index=0).engine_invariants.passed
    assert new.potential_river_network==old.potential_river_network
    for key in ('routing_elevation_m','fill_elevation_m','flow_accumulation_km2','channel_skeleton_mask','potential_channel_skeleton_mask'):
        np.testing.assert_array_equal(getattr(old,key),getattr(new,key))
    np.testing.assert_array_equal(t.elevation_m,z)
    if legacy_valid:
        assert old.river_network==new.river_network
        np.testing.assert_array_equal(old.water_depth_m,new.water_depth_m)
        np.testing.assert_array_equal(old.stream_mask,new.stream_mask)
    else:
        assert len(new.river_network.segments)<len(old.river_network.segments)


def network(lines):
    nodes={};segments={}
    for id,a,b,coords in lines:
        def point(p):return dict(x_km=p[0],y_km=p[1])
        for k,p in ((a,coords[0]),(b,coords[-1])):
            nodes.setdefault(k,dict(kind='source',position=point(p)))
        segments[id]={'from':a,'to':b,'centerline':[point(p) for p in coords]}
    return {'nodes':nodes,'segments':segments}


def test_shared_endpoint_is_allowed():
    a=audit_network(network([('a','x','c',[(0,0),(1,1)]),('b','y','c',[(2,0),(1,1)])]));assert a['shared_node_only_pairs']==1 and a['defective_pairs']==0


def test_crossing_and_overlap_are_not_allowed():
    a=audit_network(network([('a','x','y',[(0,0),(2,2)]),('b','u','v',[(0,2),(2,0)])]));assert a['defective_pairs']==a['crosses_predicate_pairs']==1 and a['unauthorized_point_components']==1
    b=audit_network(network([('a','x','y',[(0,0),(2,0)]),('b','u','v',[(1,0),(3,0)])]));assert b['positive_length_overlap_pairs']==1 and b['overlap_km']==1


def test_same_location_is_not_same_node_and_degenerate_reported():
    a=network([('a','x','y',[(0,0),(1,0)]),('b','u','v',[(1,0),(2,0)]),('lake','out','in',[(4,4),(4,4)])])
    a['nodes']['out'].update(kind='lake_outlet',feature_id='lake1');a['nodes']['in'].update(kind='lake_inflow',feature_id='lake1')
    r=audit_network(a);assert r['defective_pairs']==1 and r['degenerate_segment_ids']==['lake'] and r['same_lake_outlet_to_inflow_ids']==['lake']
