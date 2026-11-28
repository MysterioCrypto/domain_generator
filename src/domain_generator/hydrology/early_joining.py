"""Experimental same-target joining and exact spatial diagnostics.

Geometry only; the caller owns MFD and raster-derived properties.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from math import floor, ceil
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import substring
from shapely.strtree import STRtree

def audit_network(net, tolerance_km=1e-8):
    if not np.isfinite(tolerance_km) or tolerance_km < 0:
        raise ValueError('invalid tolerance')
    ids = sorted(net['segments'])
    segs = [net['segments'][i] for i in ids]
    lines = np.array([LineString([(p['x_km'], p['y_km']) for p in s['centerline']]) for s in segs], dtype=object)
    degenerate = [ids[i] for i,g in enumerate(lines) if g.is_empty or g.length <= 0]
    if any(not g.is_valid and g.length > 0 for g in lines):
        raise ValueError('invalid nondegenerate segment')
    active = np.array([i for i,g in enumerate(lines) if g.length > 0],dtype=int)
    ii, jj = STRtree(lines[active]).query(lines[active], predicate='intersects') if len(active) else ([], [])
    ii,jj=active[np.asarray(ii,dtype=int)],active[np.asarray(jj,dtype=int)]
    pairs = sorted((int(i),int(j)) for i,j in zip(ii,jj) if i<j)
    count = Counter(); defects = []
    for i,j in pairs:
        intersection = lines[i].intersection(lines[j])
        shared = set((segs[i]['from'],segs[i]['to'])) & set((segs[j]['from'],segs[j]['to']))
        allowed = [Point(net['nodes'][k]['position']['x_km'],net['nodes'][k]['position']['y_km']) for k in sorted(shared)]
        points=[]; lengths=[]
        def collect(g):
            if g.is_empty:return
            if g.geom_type=='Point':points.append(g)
            elif g.geom_type in ('LineString','LinearRing'):lengths.append(g.length)
            elif g.geom_type in ('MultiPoint','MultiLineString','GeometryCollection'):
                for child in g.geoms:collect(child)
            else:raise ValueError('unexpected intersection geometry '+g.geom_type)
        collect(intersection)
        bad=[p for p in points if not any(p.distance(q)<=tolerance_km for q in allowed)]
        overlap=float(sum(lengths));count['intersecting_pairs']+=1
        if not bad and overlap==0:
            count['shared_node_only_pairs']+=1;continue
        count['defective_pairs']+=1;count['unauthorized_point_components']+=len(bad)
        count['positive_length_overlap_pairs']+=int(overlap>0)
        count['crosses_predicate_pairs']+=int(lines[i].crosses(lines[j]))
        defects.append({'segments':[ids[i],ids[j]],'shared_nodes':sorted(shared),'unauthorized_points_sw_km':sorted([[p.x,p.y] for p in bad]),'overlap_km':overlap,'crosses_predicate':bool(lines[i].crosses(lines[j]))})
    keys=('intersecting_pairs','shared_node_only_pairs','defective_pairs','unauthorized_point_components','positive_length_overlap_pairs','crosses_predicate_pairs')
    return {'segments':len(lines),'degenerate_segment_ids':degenerate,'same_lake_outlet_to_inflow_ids':[ids[i] for i,s in enumerate(segs) if net['nodes'][s['from']]['kind']=='lake_outlet' and net['nodes'][s['to']]['kind']=='lake_inflow' and net['nodes'][s['from']].get('feature_id')==net['nodes'][s['to']].get('feature_id')],'non_simple_segments':sum(not g.is_simple for g in lines),**{k:count[k] for k in keys},'overlap_km':sum(d['overlap_km'] for d in defects),'defects':defects}

EPS = 1e-8
TERMINALS = {'domain_outlet','marine_outlet','lake_inflow'}


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



def traversed_geometry_cells(adapter, points):
    """Positive-length cell intervals plus semantic endpoints, canonical grid ties.

    Intersect each straight piece with vertical/horizontal grid lines; midpoint
    sampling each resulting interval is exact in the piecewise-linear model.
    A corner-only contact does not add a cell unless it is a semantic endpoint.
    """
    if len(points) < 2:
        raise ValueError("segment has fewer than two points")
    size = adapter.cell_size_km
    cells = [adapter.containing_cell(*points[0])]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 == x1 and y0 == y1:
            continue
        ts = [0., 1.]
        for a, b in ((x0,x1),(y0,y1)):
            if a == b:
                continue
            for k in range(floor(min(a,b)/size)+1, ceil(max(a,b)/size)):
                t = (k*size-a)/(b-a)
                if 0 < t < 1:
                    ts.append(t)
        ts = sorted(set(ts))
        for a,b in zip(ts,ts[1:]):
            if b-a <= 1e-14:
                continue
            t = (a+b)/2
            x = x0+(x1-x0)*t; y=y0+(y1-y0)*t
            cells.append(adapter.containing_cell(x,y))
    cells.append(adapter.containing_cell(*points[-1]))
    return tuple(dict.fromkeys(cells))
