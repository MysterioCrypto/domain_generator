"""P4-Q experimental imported DEM lake continuation, not approved geography."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from domain_generator.terrain.state import TerrainState
from domain_generator.hydrology.continuous import generate_hydrology_v02,validate_hydrology_v02
from scripts.evaluate_imported_dem_native_network_v02 import make_plan
from scripts.audit_native_network_spatial_v02 import audit_network


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('child','prior','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();prior=json.loads(a.prior.read_text())
    if prior['status']!='P4_M_NESTED_SAME_ANALYTIC_TERRAIN_RESOLUTION_NOT_RIVERS' or sha(a.child)!=prior['derived_sha256']['p4m-fine-terrain.npz']:raise ValueError('P4-M SHA mismatch')
    with np.load(a.child,allow_pickle=False) as f:
        z=f['child_elevation_m'];origin=[float(f['east_km'][0]-.25),float(f['north_km_north_first'][-1]-.25)]
        if not np.all(f['land_mask']) or not np.all(np.diff(f['east_km'])==.5) or not np.all(np.diff(f['north_km_north_first'])==-.5):raise ValueError('inland 500 m only')
    plan=make_plan(z.shape);t=TerrainState(elevation_m=z.copy());h=generate_hydrology_v02(plan,t,experimental_network_assembly=True);v=validate_hydrology_v02(plan,t,h,attempt_index=0)
    if not v.engine_invariants.passed or not np.array_equal(t.elevation_m,z):raise ValueError('failed native validation or mutated source')
    a.output.mkdir(parents=True,exist_ok=False)
    r={'status':'P4_Q_EXPERIMENTAL_LAKE_CONTINUATION_NOT_CANON','validation_checks':len(v.engine_invariants.results),'approved_geography':False,'chapter1_compatibility_verified':False,'source_sha256':{'child':sha(a.child),'prior':sha(a.prior)},'origin_east_north_km':origin,'networks':{}}
    for name,net in [('regional',h.river_network),('potential',h.potential_river_network)]:
        n=net.model_dump(mode='json',by_alias=True);(a.output/(name+'.json')).write_text(json.dumps(n)+'\n');audit=audit_network(n);r['networks'][name]=audit
        if audit['same_lake_outlet_to_inflow_ids']:raise ValueError('same-lake return')
        outgoing={s.from_node:s for s in net.segments.values()};paths=[]
        for k,node in net.nodes.items():
            if node.kind.value!='lake_outlet':continue
            keys=[];start=k
            while k in outgoing:
                s=outgoing[k];keys.append(k);k=s.to_node
            paths.append({'feature_id':node.feature_id,'start_node':start,'terminal_node':k,'terminal_kind':net.nodes[k].kind.value,'segments_to_first_terminal':len(keys)})
        r['networks'][name]['lake_paths']=paths
    (a.output/'lakes.json').write_text(json.dumps({k:v.model_dump(mode='json') for k,v in h.lake_features.items()})+'\n');r['derived_sha256']={f.name:sha(f) for f in sorted(a.output.iterdir())};(a.output/'p4q-audit.json').write_text(json.dumps(r,indent=2)+'\n')
    print({k:{x:y for x,y in n.items() if x!='defects'} for k,n in r['networks'].items()},flush=True)
if __name__=='__main__':main()
