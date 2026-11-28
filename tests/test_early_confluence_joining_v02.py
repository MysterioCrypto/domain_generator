"""P4-R geometry-only joining: synthetic public inputs, no private geography."""
from copy import deepcopy
import pytest
from scripts.join_early_confluences_v02 import run,terminals,line,point


def network(lines):
    nodes={};segments={}
    for k,a,b,coords,area in lines:
        for n,p in ((a,coords[0]),(b,coords[-1])):
            nodes.setdefault(n,{'position':point(p),'kind':'source','feature_id':None,'boundary_side':None})
        segments[k]={'from':a,'to':b,'centerline':[point(p) for p in coords],'properties':{'catchment_area_km2':area}}
    for k,n in nodes.items():
        ins=sum(s['to']==k for s in segments.values());outs=sum(s['from']==k for s in segments.values())
        n['kind']='domain_outlet' if not outs else 'confluence' if ins else 'source'
    return {'nodes':nodes,'segments':segments}


def branches():
    return [('a','s1','c',[(0,2),(2,.5),(4,1)],100),('b','s2','c',[(0,0),(2,1.5),(4,1)],80),('out','c','o',[(4,1),(5,1)],100)]


def test_first_contact_and_unary_collapse():
    n=network(branches());old=deepcopy(n);c,r=run(n)
    assert n==old and terminals(c)==terminals(n)
    assert r['before']['defective_pairs']==1 and r['after']['defective_pairs']==0
    assert len(r['joins'])==1 and r['collapsed_unary_nodes']==['c']
    assert r['candidate_segments']==r['original_segments']==3
    assert r['discarded_suffix_km']>0
    assert r['original_length_km']-r['candidate_length_km']==pytest.approx(r['discarded_suffix_km'])
    assert all('properties' not in s for s in c['segments'].values())
    assert c['status']=='GEOMETRY_ONLY_NOT_RIVER_NETWORK'


def test_three_branches_joint_processing_and_determinism():
    n=network(branches()+[('third','s3','c',[(0,3),(2.1,-.5),(4,1)],60)])
    c,r=run(n);assert r['before']['defective_pairs']>1 and r['after']['defective_pairs']==0
    assert len(r['joins'])==2 and terminals(c)==terminals(n)
    rev={'nodes':dict(reversed(list(n['nodes'].items()))),'segments':dict(reversed(list(n['segments'].items())))}
    assert run(rev)==(c,r)


def test_clean_graph_and_isolated_boundary_unchanged():
    n=network([('a','s1','c',[(0,0),(2,1)],10),('b','s2','c',[(0,2),(2,1)],20),('o','c','o',[(2,1),(3,1)],30)])
    n['nodes']['isolated']={'kind':'domain_outlet','position':point((3,4)),'feature_id':None,'boundary_side':'east'}
    c,r=run(n);assert c['nodes']==n['nodes'] and not r['joins'] and r['isolated_domain_outlets_preserved']==1
    assert sorted((s['centerline'] for s in c['segments'].values()),key=str)==sorted((s['centerline'] for s in n['segments'].values()),key=str)


def test_cross_target_rejected():
    n=network([('a','s1','o1',[(0,0),(2,2)],10),('b','s2','o2',[(0,2),(2,0)],20)])
    with pytest.raises(ValueError,match='cross-target'):run(n)


def test_positive_length_overlap_rejected():
    n=network([('a','s1','c',[(0,0),(1,1),(2,1)],10),('b','s2','c',[(0,2),(1,1),(2,1)],20),('o','c','o',[(2,1),(3,1)],30)])
    with pytest.raises(ValueError,match='unsupported input geometry'):run(n)


def test_lake_terminal_preservation():
    n=network(branches());n['nodes']['s1'].update(kind='lake_outlet',feature_id='lake')
    c,r=run(n);assert c['nodes']['s1']==n['nodes']['s1'] and terminals(c)['s1']=='o'
    n['nodes']['o'].update(kind='lake_inflow',feature_id='lake')
    with pytest.raises(ValueError,match='lake cycle'):run(n)
