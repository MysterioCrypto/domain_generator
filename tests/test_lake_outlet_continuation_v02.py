"""Public P4-Q regressions: opt-in lake continuation and feature graph semantics."""
import numpy as np
import pytest
from domain_generator.contracts.data import RiverNetwork
from domain_generator.terrain.state import TerrainState
from domain_generator.hydrology.continuous import generate_hydrology_v02, validate_hydrology_v02, _validate_lake_continuations, HydrologyCapabilityError
from scripts.evaluate_imported_dem_native_network_v02 import make_plan
from scripts.audit_native_network_spatial_v02 import audit_network


def surface(seed):
    rr,cc=np.indices((61,61));r=np.random.default_rng(seed)
    return 400-cc*1.5-60*np.exp(-((rr-30)**2+(cc-30)**2)/90)+sum(r.uniform(1,8)*np.sin(rr*r.uniform(.07,.45)+cc*r.uniform(.07,.45)+r.uniform(0,6)) for _ in range(8))


def self_returns(net):
    return [s for s in net.segments.values() if net.nodes[s.from_node].kind.value=='lake_outlet' and net.nodes[s.to_node].kind.value=='lake_inflow' and net.nodes[s.from_node].feature_id==net.nodes[s.to_node].feature_id]


@pytest.mark.parametrize('seed,expected_returns',[(0,1),(1,0)])
def test_lake_continuation_real_dem(seed,expected_returns):
    z=surface(seed);p=make_plan(z.shape);t=TerrainState(elevation_m=z.copy())
    old=generate_hydrology_v02(p,t);new=generate_hydrology_v02(p,t,experimental_network_assembly=True)
    assert len(old.lake_candidates)==1
    assert old.lake_outlets==new.lake_outlets and old.lake_candidates==new.lake_candidates
    for key in ('routing_elevation_m','fill_elevation_m','flow_accumulation_km2','channel_skeleton_mask','potential_channel_skeleton_mask'):
        np.testing.assert_array_equal(getattr(old,key),getattr(new,key))
    np.testing.assert_array_equal(t.elevation_m,z)
    for a,b in ((old.river_network,new.river_network),(old.potential_river_network,new.potential_river_network)):
        assert len(self_returns(a))==expected_returns and not self_returns(b)
        _validate_lake_continuations(b)
        report=audit_network(b.model_dump(mode='json',by_alias=True))
        assert not report['degenerate_segment_ids']
        def outlet(net):return next(n for n in net.nodes.values() if n.kind.value=='lake_outlet')
        assert outlet(a)==outlet(b)
    assert validate_hydrology_v02(p,t,new,attempt_index=0).engine_invariants.passed


def test_feature_level_cycle_through_confluence():
    def point(x):return dict(x_km=float(x),y_km=1.)
    def node(kind,x,**kw):return dict(kind=kind,position=point(x),**kw)
    def seg(a,b,x,y):return {'from':a,'to':b,'centerline':[point(x),point(y)],'properties':{'catchment_area_km2':10.}}
    nodes={'a':node('lake_outlet',0,feature_id='lake-0001'),'b':node('confluence',1),'c':node('lake_inflow',2,feature_id='lake-0001')}
    segments={'s1':seg('a','b',0,1),'s2':seg('b','c',1,2)}
    with pytest.raises(HydrologyCapabilityError,match='cyclic lake'):_validate_lake_continuations(RiverNetwork.model_validate(dict(nodes=nodes,segments=segments)))
    nodes['c']=node('marine_outlet',2,feature_id='marine-0001')
    _validate_lake_continuations(RiverNetwork.model_validate(dict(nodes=nodes,segments=segments)))
