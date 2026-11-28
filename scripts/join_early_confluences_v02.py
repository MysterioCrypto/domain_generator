"""P4-R: bounded same-target first-contact joining, geometry-only candidate.

No routing, catchment properties, water raster or Strahler values are generated.
Never use the returned graph as a canonical RiverNetwork/DomainData.
"""
import argparse
from collections import defaultdict, Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from shapely.geometry import LineString, Point
from shapely.ops import substring
from scripts.audit_native_network_spatial_v02 import audit_network

EPS = 1e-8
TERMINALS = {'domain_outlet','marine_outlet','lake_inflow'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def xy(p):
    return (p['x_km'],p['y_km'])


def point(p):
    return {'x_km':float(p[0]),'y_km':float(p[1])}


def line(s):
    return LineString([xy(p) for p in s['centerline']])


def terminals(net):
    """Require directed merge-only forest; compare every source and lake outlet."""
    nodes=net['nodes']; out={}; inc=Counter()
    for s in net['segments'].values():
        a,b=s['from'],s['to']
        if a not in nodes or b not in nodes or a in out or a==b:
            raise ValueError('invalid directed graph')
        if xy(s['centerline'][0])!=xy(nodes[a]['position']) or xy(s['centerline'][-1])!=xy(nodes[b]['position']):
            raise ValueError('endpoint mismatch')
        out[a]=b;inc[b]+=1
    for k,n in nodes.items():
        kind=n['kind']
        if kind in TERMINALS:
            # Preserve existing isolated boundary descriptors; do not invent inflows.
            ok=k not in out and (inc[k]>=1 or kind=='domain_outlet')
        elif kind in {'source','lake_outlet'}:
            ok=k in out and inc[k]==0
        elif kind=='confluence':
            ok=k in out and inc[k]>=2
        else:ok=False
        if not ok:raise ValueError('invalid node degree '+k)
    end={}
    for k in sorted(nodes):
        trail=[];cur=k;seen=set()
        while cur not in end and cur in out:
            if cur in seen:raise ValueError('cycle')
            trail.append(cur);seen.add(cur);cur=out[cur]
        terminal=end.get(cur,cur)
        for v in trail+[cur]:end[v]=terminal
    # Check feature-level lake continuations, not only the ordinary DAG.
    outlets={n['feature_id']:k for k,n in nodes.items() if n['kind']=='lake_outlet'}
    if len(outlets)!=sum(n['kind']=='lake_outlet' for n in nodes.values()):raise ValueError('duplicate lake outlet')
    for k in outlets.values():
        seen=set()
        while True:
            if k in seen:raise ValueError('lake cycle')
            seen.add(k);n=nodes[end[k]]
            if n['kind']!='lake_inflow':break
            if n['feature_id'] not in outlets:raise ValueError('missing lake continuation')
            k=outlets[n['feature_id']]
    return {k:end[k] for k,n in nodes.items() if n['kind'] in {'source','lake_outlet'}}


def intersection_points(g):
    if g.is_empty:return []
    if g.geom_type=='Point':return [g]
    if g.geom_type in ('MultiPoint','GeometryCollection'):
        return [p for v in g.geoms for p in intersection_points(v)]
    raise ValueError('positive length intersection: unsupported')


def fragment(s,lo,hi,start,end,nodes):
    """Clip one original segment; only shared endpoint roundoff is adjusted."""
    g=line(s);p=substring(g,lo,hi)
    if p.geom_type!='LineString' or p.length<=EPS:raise ValueError('degenerate fragment')
    coords=list(p.coords);a=xy(nodes[start]['position']);b=xy(nodes[end]['position'])
    if Point(coords[0]).distance(Point(a))>EPS or Point(coords[-1]).distance(Point(b))>EPS:raise ValueError('off-trace join')
    coords[0]=a;coords[-1]=b
    coords=[v for i,v in enumerate(coords) if i==0 or v!=coords[i-1]]
    if len(coords)<2:raise ValueError('degenerate fragment')
    src=s['source_fragments']
    if len(src)!=1:raise ValueError('fragment of merged provenance')
    offset=src[0]['start_km']
    return {'from':start,'to':end,'centerline':[point(v) for v in coords],'source_fragments':[{'segment_id':src[0]['segment_id'],'start_km':offset+lo,'end_km':offset+hi}]}


def run(net):
    old_end=terminals(net);before=audit_network(net)
    if before['degenerate_segment_ids'] or before['non_simple_segments'] or before['same_lake_outlet_to_inflow_ids'] or before['positive_length_overlap_pairs']:
        raise ValueError('unsupported input geometry')
    groups=defaultdict(list); affected=set()
    for k,s in net['segments'].items():groups[s['to']].append(k)
    for d in before['defects']:
        a,b=[net['segments'][k] for k in d['segments']]
        if a['to']!=b['to'] or net['nodes'][a['to']]['kind']!='confluence':
            raise ValueError('cross-target intersection: unsupported')
        affected.add(a['to'])
    nodes=deepcopy(net['nodes']); edges={};joins=[];removed=[]
    def new_id(prefix,used):
        i=len(used)+1
        while f'{prefix}{i:06d}' in used:i+=1
        return f'{prefix}{i:06d}'
    def add(s):
        k=new_id('p4r-edge-',edges);edges[k]=s;return k
    def base(k):
        s=net['segments'][k];g=line(s)
        return {'from':s['from'],'to':s['to'],'centerline':deepcopy(s['centerline']),'source_fragments':[{'segment_id':k,'start_km':0.,'end_km':g.length}]}
    for target,keys in sorted(groups.items()):
        if target not in affected:
            for k in sorted(keys):add(base(k))
            continue
        # Stable priority: existing maximum area descriptor, then length, then ID.
        # Area is NOT summed, transferred or interpreted as a local discharge.
        keys.sort(key=lambda k:(-net['segments'][k]['properties']['catchment_area_km2'],-line(net['segments'][k]).length,k))
        tree=[add(base(keys[0]))]
        for k in keys[1:]:
            s=base(k);g=line(s);contacts=[]
            for e in tree:
                h=line(edges[e])
                for p in intersection_points(g.intersection(h)):
                    contacts.append((g.project(p),e,h.project(p),p))
            if not contacts:raise ValueError('missing original shared endpoint')
            ds,e,dr,p=min(contacts,key=lambda v:(v[0],v[1],v[2]))
            if ds>=g.length-EPS:
                tree.append(add(s));continue
            if ds<=EPS:raise ValueError('join at donor source: unsupported')
            rec=edges[e];h=line(rec)
            if dr<=EPS:
                join=rec['from']
            elif dr>=h.length-EPS:
                join=rec['to']
            else:
                join=new_id('p4r-join-',nodes)
                nodes[join]={'kind':'confluence','position':point((p.x,p.y)),'boundary_side':None,'feature_id':None}
                del edges[e];tree.remove(e)
                tree.extend([add(fragment(rec,0,dr,rec['from'],join,nodes)),add(fragment(rec,dr,h.length,join,rec['to'],nodes))])
            if nodes[join]['kind']!='confluence':raise ValueError('join at non-confluence: unsupported')
            tree.append(add(fragment(s,0,ds,s['from'],join,nodes)))
            joins.append({'original_target':target,'new_target':join,'donor_segment':k,'position':nodes[join]['position'],'discarded_suffix_km':g.length-ds})
    # The old confluence can become unary. Collapse it without changing geometry.
    while True:
        inc=defaultdict(list);out={}
        for k,s in edges.items():inc[s['to']].append(k);out[s['from']]=k
        unary=next((k for k in sorted(nodes) if nodes[k]['kind']=='confluence' and len(inc[k])==1),None)
        if unary is None:break
        i,j=inc[unary][0],out[unary];a,b=edges.pop(i),edges.pop(j)
        add({'from':a['from'],'to':b['to'],'centerline':a['centerline']+b['centerline'][1:],'source_fragments':a['source_fragments']+b['source_fragments']});del nodes[unary];removed.append(unary)
    candidate={'nodes':nodes,'segments':edges,'status':'GEOMETRY_ONLY_NOT_RIVER_NETWORK'}
    if terminals(candidate)!=old_end:raise ValueError('source/outlet terminal changed')
    for k,n in net['nodes'].items():
        if n['kind']!='confluence' and nodes.get(k)!=n:raise ValueError('non-confluence node changed')
    after=audit_network(candidate)
    if after['defective_pairs'] or after['degenerate_segment_ids'] or after['non_simple_segments'] or after['same_lake_outlet_to_inflow_ids']:
        raise ValueError('candidate fails spatial audit: '+str({k:v for k,v in after.items() if k!='defects'}))
    # Verify fragment accounting, including no duplicate original positive-length span.
    spans=defaultdict(list)
    for s in edges.values():
        for f in s['source_fragments']:spans[f['segment_id']].append((f['start_km'],f['end_km']))
    for k,rs in spans.items():
        end=0.
        for a,b in sorted(rs):
            if a<end-EPS or b<=a or b>line(net['segments'][k]).length+EPS:raise ValueError('invalid fragment provenance')
            end=b
    length_before=sum(line(s).length for s in net['segments'].values());length_after=sum(line(s).length for s in edges.values())
    discarded=sum(j['discarded_suffix_km'] for j in joins)
    if abs(length_before-length_after-discarded)>1e-6:raise ValueError('length ledger mismatch')
    incoming_original={s['to'] for s in net['segments'].values()}
    report={'affected_original_confluences':len(affected),'joins':joins,'collapsed_unary_nodes':removed,'original_segments':len(net['segments']),'candidate_segments':len(edges),'original_nodes':len(net['nodes']),'candidate_nodes':len(nodes),'source_and_lake_outlet_terminal_count':len(old_end),'isolated_domain_outlets_preserved':sum(n['kind']=='domain_outlet' and k not in incoming_original for k,n in net['nodes'].items()),'original_length_km':length_before,'candidate_length_km':length_after,'discarded_suffix_km':discarded,'before':before,'after':after}
    return candidate,report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    prior=json.loads((a.archive_dir/'p4q-audit.json').read_text())
    if prior['status']!='P4_Q_EXPERIMENTAL_LAKE_CONTINUATION_NOT_CANON' or prior['approved_geography'] is not False:raise ValueError('unexpected source status')
    result={};candidates={}
    for name in ('regional','potential'):
        f=a.archive_dir/(name+'.json')
        if sha(f)!=prior['derived_sha256'][f.name]:raise ValueError('source SHA mismatch')
        net=json.loads(f.read_text());candidate,r=run(net);candidates[name]=candidate;result[name]=r
    a.output.mkdir(parents=True,exist_ok=False)
    for k,n in candidates.items():(a.output/(k+'-geometry-only.json')).write_text(json.dumps(n)+'\n')
    report={'status':'P4_R_EARLY_CONFLUENCE_GEOMETRY_CANDIDATE_NOT_CANON','source_audit_sha256':sha(a.archive_dir/'p4q-audit.json'),'approved_geography':False,'chapter1_compatibility_verified':False,'canonical_properties_recomputed':False,'networks':result,'limitations':['same-target confluences only; exact intersections, not near misses','first contact is an explicit planar merge-only hypothesis, not hydraulic proof','no new routing, raster masks, catchment values or Strahler; no inter-layer validation','source and lake-outlet terminal invariance is experiment control, not author geography constraint']}
    report['derived_sha256']={f.name:sha(f) for f in sorted(a.output.iterdir())};(a.output/'p4r-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    for k,r in result.items():print(k,{x:v for x,v in r.items() if x not in ('before','after','joins','collapsed_unary_nodes')},'joins',len(r['joins']),'unary',len(r['collapsed_unary_nodes']),'defects',r['before']['defective_pairs'],r['after']['defective_pairs'])

if __name__=='__main__':main()
