"""P4-P: exact polyline intersection audit; not a geometry repair or water claim."""
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
import numpy as np
import shapely
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    prior=json.loads((a.archive_dir/'p4o-audit.json').read_text());names=['native-regional','normalized-regional','potential'];r={}
    if prior['status']!='P4_O_IMPORTED_DEM_NATIVE_NETWORK_EXPERIMENT_NOT_CANON' or prior['approved_geography'] is not False:raise ValueError('unexpected provenance')
    for name in names:
        f=a.archive_dir/(name+'.json')
        if sha(f)!=prior['derived_sha256'][f.name]:raise ValueError('source SHA mismatch')
        r[name]=audit_network(json.loads(f.read_text()))
    report={'status':'P4_P_SPATIAL_DIAGNOSTIC_NOT_CANON','source_audit_sha256':sha(a.archive_dir/'p4o-audit.json'),'networks':r,'shared_node_tolerance_km':1e-8,'limitations':['exact GEOS intersections of piecewise linear geometry; not near-overlap audit','point components are not independent hydrological events','zero-length segments reported separately and excluded from pair tests','no inter-layer intersection test or repair','no physical water or geographic acceptance']}
    with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')

if __name__=='__main__':main()
