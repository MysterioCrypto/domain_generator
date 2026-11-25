"""Public-only P4-L controls; no private planetary data."""
import copy,json,subprocess,sys
from pathlib import Path
import numpy as np
import pytest
from scripts.condition_planetary_child_terrain_v02 import ChildTerrainSettings, generate_child
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection
from scripts.compare_region_anisotropic_detail_v02 import candidate_surface, run, sha


def fixture():
    lat=np.arange(36.,-37.,-12.);lon=np.arange(-36.,37.,12.);yy,xx=np.meshgrid(lat,lon,indexing='ij');z=(400.+4*xx+2*yy+3*np.sin(yy/12)*np.cos(xx/12)).astype(np.float32)
    m={'latitude_deg_north_first':lat,'longitude_deg_west_to_east':lon,'elevation_m':z,'land_mask':np.ones(z.shape,np.uint8),'source_river_mask_D8':np.zeros(z.shape,np.uint8),'local_downstream_index':np.full(z.shape,-1,np.int32),'source_catchment_km2_D8':np.ones(z.shape,np.float32)}
    s=ChildTerrainSettings(center_lat_deg=0.,center_lon_deg=0.,half_width_km=24.,half_height_km=24.,planet_radius_km=180/np.pi,planetary_year_earth_days=200.,seed=1406,relief_strength=2.,detail_coordinate_system='spherical_xyz_v1')
    c,meta=generate_child(m,s);return m,c,meta


def test_anchored_boundary_rms_immutable():
    m,c,meta=fixture();before=copy.deepcopy(c);alt,r=candidate_surface(m,c,meta)
    assert r['anchor_count']==25 and r['continuous_anchor_max_error_m']<=1e-6
    assert r['boundary_exact'] and r['land_mask_exact']
    assert r['detail_rms_candidate_m']==pytest.approx(r['detail_rms_original_m'],abs=1e-8)
    assert 0<r['max_height_change_m']<=60
    for k in c:np.testing.assert_array_equal(c[k],before[k])
    for k in ('east_km','north_km_north_first','parent_interpolated_m','land_mask'):np.testing.assert_array_equal(alt[k],c[k])
    alt2,r2=candidate_surface(m,c,meta);assert r==r2
    for k in alt:np.testing.assert_array_equal(alt[k],alt2[k])


@pytest.mark.parametrize('key',['child_elevation_m','new_local_relief_m','parent_interpolated_m','land_mask','east_km'])
def test_reject_changed_source(key):
    m,c,meta=fixture();c[key].flat[1]+=1
    with pytest.raises(ValueError):candidate_surface(m,c,meta)


def test_independent_core_and_replay_guard():
    m,c,meta=fixture();a,_=connected_mfd_channel_projection(c,m,meta,stream_threshold_km2=30)
    alt,b,r=run(m,c,meta,a)
    assert r['original_projection_exact_replay'] and not r['accepted_core_changed'] and not r['approved_geography']
    assert r['baseline']['mass_balance']['explicit_external_area_km2']==r['candidate']['mass_balance']['explicit_external_area_km2']==0
    assert 0<=r['channel_mask_iou']<=1
    a['channel_mask'].flat[0]^=1
    with pytest.raises(ValueError,match='projection replay mismatch'):run(m,c,meta,a)


def test_cli_reproducibility_and_sha_guard(tmp_path):
    m,c,meta=fixture();a,_=connected_mfd_channel_projection(c,m,meta,stream_threshold_km2=30)
    p={k:tmp_path/(k+'.npz') for k in ('macro','child','projection')}
    for k,v in [('macro',m),('child',c),('projection',a)]:np.savez_compressed(p[k],**v)
    p['manifest']=tmp_path/'meta.json';p['manifest'].write_text(json.dumps(meta));p['prior']=tmp_path/'prior.json';p['prior'].write_text(json.dumps({'status':'P4_K_SEMANTIC_REACH_DISPLAY_ONLY_NOT_RIVERS','unchanged_source_graph':True,'source_sha256':{'baseline_child_npz':sha(p['child']),'baseline_projection_npz':sha(p['projection'])}}))
    cmd=[sys.executable,'-m','scripts.compare_region_anisotropic_detail_v02']
    for k,v in p.items():cmd+=['--'+k,str(v)]
    def call(n):return subprocess.run(cmd+['--output',str(tmp_path/n)],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
    a,b=call('a'),call('b');assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
    for f in (tmp_path/'a').iterdir():assert sha(f)==sha(tmp_path/'b'/f.name)
    p['projection'].write_bytes(p['projection'].read_bytes()+b'x');bad=call('bad');assert bad.returncode!=0 and 'SHA/provenance mismatch' in bad.stderr
