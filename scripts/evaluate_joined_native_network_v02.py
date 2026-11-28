"""P4-S: evaluate experimental native joining; no author-map acceptance."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from domain_generator.grid import GridAdapter
from domain_generator.terrain.state import TerrainState
from domain_generator.hydrology.continuous import generate_hydrology_v02, validate_hydrology_v02
from domain_generator.hydrology.early_joining import audit_network, traversed_geometry_cells
from scripts.evaluate_imported_dem_native_network_v02 import make_plan


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def geometry_signature(n):
    def node(k):
        v=n['nodes'][k];return (v['kind'],v['position']['x_km'],v['position']['y_km'],v.get('feature_id'),v.get('boundary_side'))
    return Counter(node(k) for k in n['nodes']),Counter((node(s['from']),node(s['to']),tuple((p['x_km'],p['y_km']) for p in s['centerline'])) for s in n['segments'].values())


def coverage(adapter,n,excluded):
    result=np.zeros((adapter.rows,adapter.columns),bool)
    for s in n['segments'].values():
        for c in traversed_geometry_cells(adapter,[(p['x_km'],p['y_km']) for p in s['centerline']]):
            if c not in excluded:result[c]=True
    return result


def compare_baseline_coverage(adapter, excluded, masks, baseline):
    prior=json.loads((baseline/'p4q-audit.json').read_text())
    if prior['status']!='P4_Q_EXPERIMENTAL_LAKE_CONTINUATION_NOT_CANON' or prior['approved_geography'] is not False:
        raise ValueError('unexpected P4-Q provenance')
    old={}
    for name in ('regional','potential'):
        f=baseline/(name+'.json')
        if sha(f)!=prior['derived_sha256'][f.name]:raise ValueError('P4-Q SHA mismatch')
        old[name]=coverage(adapter,json.loads(f.read_text()),excluded)
    return {'baseline_audit_sha256':sha(baseline/'p4q-audit.json'),
            'regional_coverage_equal':bool(np.array_equal(old['regional'],masks['regional'])),
            'potential_coverage_equal':bool(np.array_equal(old['potential'],masks['potential'])),
            'baseline_regional_cells_missing_from_potential':int(np.count_nonzero(old['regional']&~old['potential']))}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('child','prior','geometry-archive','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--baseline-archive',type=Path)
    a=p.parse_args();prior=json.loads(a.prior.read_text());g=json.loads((a.geometry_archive/'p4r-audit.json').read_text())
    if prior['status']!='P4_M_NESTED_SAME_ANALYTIC_TERRAIN_RESOLUTION_NOT_RIVERS' or sha(a.child)!=prior['derived_sha256']['p4m-fine-terrain.npz']:raise ValueError('P4-M SHA mismatch')
    if g['status']!='P4_R_EARLY_CONFLUENCE_GEOMETRY_CANDIDATE_NOT_CANON' or g['approved_geography'] is not False:raise ValueError('unexpected P4-R provenance')
    with np.load(a.child,allow_pickle=False) as f:
        z=f['child_elevation_m'];origin=[float(f['east_km'][0]-.25),float(f['north_km_north_first'][-1]-.25)]
        if not np.all(f['land_mask']) or not np.all(np.diff(f['east_km'])==.5) or not np.all(np.diff(f['north_km_north_first'])==-.5):raise ValueError('inland 500 m only')
    plan=make_plan(z.shape);t=TerrainState(elevation_m=z.copy());adapter=GridAdapter.from_plan(plan)
    h=generate_hydrology_v02(plan,t,experimental_network_assembly=True,experimental_early_joining=True)
    print('generated joined state',flush=True)
    v=validate_hydrology_v02(plan,t,h,attempt_index=0)
    if not v.engine_invariants.passed:raise ValueError(v.model_dump_json())
    excluded={c for l in h.lake_candidates for c in l.cells};a.output.mkdir(parents=True,exist_ok=False)
    report={'status':'P4_S_EXPERIMENTAL_NATIVE_JOINING_NOT_CANON','approved_geography':False,'chapter1_compatibility_verified':False,'validation_checks':len(v.engine_invariants.results),'origin_east_north_km':origin,'networks':{},'source_sha256':{'child':sha(a.child),'prior':sha(a.prior),'geometry_audit':sha(a.geometry_archive/'p4r-audit.json')},'limitations':['MFD max on retained land-cell geometry, not additive area or discharge','segment order is max raster skeleton order intersected (plus lake outlet order), not recomputed graph Strahler','regional/potential geometries independently assembled; cell coverage is a diagnostic, not proof of cross-layer nesting','internal experimental opt-in, not full public DomainData pipeline or canonical map']}
    masks={}
    for name,net in [('regional',h.river_network),('potential',h.potential_river_network)]:
        n=net.model_dump(mode='json',by_alias=True);f=a.geometry_archive/(name+'-geometry-only.json')
        if sha(f)!=g['derived_sha256'][f.name]:raise ValueError('P4-R SHA mismatch')
        old=json.loads(f.read_text());same=geometry_signature(n)==geometry_signature(old)
        audit=audit_network(n)
        if audit['defective_pairs'] or audit['degenerate_segment_ids'] or audit['non_simple_segments']:raise ValueError('spatial defects')
        masks[name]=coverage(adapter,n,excluded);errors=0
        for s in n['segments'].values():
            cells=[c for c in traversed_geometry_cells(adapter,[(p['x_km'],p['y_km']) for p in s['centerline']]) if c not in excluded]
            errors+=s['properties']['catchment_area_km2']!=max(float(h.flow_accumulation_km2[c]) for c in cells)
        report['networks'][name]={'geometry_equals_p4r':same,'nodes':len(n['nodes']),'segments':len(n['segments']),'spatial_defective_pairs':audit['defective_pairs'],'area_mismatch_segments':errors,'coverage_cells':int(masks[name].sum()),'min_catchment_km2':min(s['properties']['catchment_area_km2'] for s in n['segments'].values()),'max_catchment_km2':max(s['properties']['catchment_area_km2'] for s in n['segments'].values())}
        (a.output/(name+'.json')).write_text(json.dumps(n)+'\n')
    report['regional_stream_mask_equals_geometry']=bool(np.array_equal(h.stream_mask,masks['regional']));report['regional_cells_missing_from_potential_geometry']=int(np.count_nonzero(masks['regional']&~masks['potential']));report['regional_skeleton_subset_of_potential']=bool(np.all(~h.channel_skeleton_mask|h.potential_channel_skeleton_mask));report['potential_order_histogram']=dict(sorted(Counter(h.potential_segment_strahler_order.values()).items()));report['terrain_unchanged']=bool(np.array_equal(z,t.elevation_m))
    if a.baseline_archive:report['baseline_geometry_coverage']=compare_baseline_coverage(adapter,excluded,masks,a.baseline_archive)
    (a.output/'potential-segment-orders.json').write_text(json.dumps(h.potential_segment_strahler_order,sort_keys=True)+'\n');(a.output/'lakes.json').write_text(json.dumps({k:v.model_dump(mode='json') for k,v in h.lake_features.items()})+'\n');np.savez_compressed(a.output/'fields.npz',flow_accumulation_km2=h.flow_accumulation_km2,regional_stream_mask=h.stream_mask,potential_geometry_mask=masks['potential'],water_depth_m=h.water_depth_m,channel_strahler_order=h.channel_strahler_order,regional_skeleton=h.channel_skeleton_mask,potential_skeleton=h.potential_channel_skeleton_mask)
    report['derived_sha256']={f.name:sha(f) for f in sorted(a.output.iterdir())};(a.output/'p4s-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
