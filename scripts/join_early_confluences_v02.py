"""P4-R: bounded same-target first-contact joining, geometry-only candidate.

No routing, catchment properties, water raster or Strahler values are generated.
Never use the returned graph as a canonical RiverNetwork/DomainData.
"""
import argparse
import hashlib
import json
from pathlib import Path
from domain_generator.hydrology.early_joining import run, terminals, line, point, xy

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

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
