"""P4-P: exact polyline intersection audit; not a geometry repair or water claim."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


from domain_generator.hydrology.early_joining import audit_network

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
