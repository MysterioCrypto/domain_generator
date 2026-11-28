"""Public synthetic tests for P4-M, without private geography."""
import copy,json,subprocess,sys
from pathlib import Path
import numpy as np
import pytest
from scripts.condition_planetary_child_terrain_v02 import ChildTerrainSettings,generate_child
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection
from scripts.compare_region_resolution_v02 import nested_terrain,physical_runs,outlet_distances,run,sha


def toy():
    lat=np.arange(36.,-37.,-12.);lon=np.arange(-36.,37.,12.);yy,xx=np.meshgrid(lat,lon,indexing='ij');z=(400+4*xx+2*yy+3*np.sin(yy/12)*np.cos(xx/12)).astype(np.float32)
    m={'latitude_deg_north_first':lat,'longitude_deg_west_to_east':lon,'elevation_m':z,'land_mask':np.ones(z.shape,np.uint8),'source_river_mask_D8':np.zeros(z.shape,np.uint8),'local_downstream_index':np.full(z.shape,-1,np.int32),'source_catchment_km2_D8':np.ones(z.shape,np.float32)}
    s=ChildTerrainSettings(center_lat_deg=0.,center_lon_deg=0.,half_width_km=24.,half_height_km=24.,planet_radius_km=180/np.pi,planetary_year_earth_days=200.,seed=1406,relief_strength=2.,detail_coordinate_system='spherical_xyz_v1')
    c,meta=generate_child(m,s);return m,c,meta


def test_nested_samples_and_source_immutability():
    m,c,meta=toy();old=copy.deepcopy(c);f,fm,r=nested_terrain(m,c,meta)
    assert f['child_elevation_m'].shape==(97,97) and r['anchor_count']==25
    assert r['nested_all_six_arrays_exact'] and max(r['anchor_error_m'])<=1e-6
    for k,v in c.items():
        np.testing.assert_array_equal(v,old[k]);np.testing.assert_array_equal(v,f[k][::2] if v.ndim==1 else f[k][::2,::2])


@pytest.mark.parametrize('key',['child_elevation_m','new_local_relief_m','land_mask','east_km'])
def test_changed_source_rejected(key):
    m,c,meta=toy();c[key].flat[1]+=1
    with pytest.raises(ValueError):nested_terrain(m,c,meta)


def test_physical_length_not_edge_count():
    # Same horizontal segment at different resolutions plus diagonal case.
    for s,n in [(1.,8),(.5,16)]:
        e=np.array([[i,i+1] for i in range(n)],dtype=np.int32)
        a=physical_runs(e,(20,20),s);assert a['max_run_km']==8 and a['length_fraction_ge8km']==1 and a['length_fraction_ge16km']==0
    e=np.array([[i*21,(i+1)*21] for i in range(6)],dtype=np.int32)
    a=physical_runs(e,(20,20),1.);assert a['max_run_km']==pytest.approx(6*np.sqrt(2)) and a['length_fraction_ge8km']==1


def test_cycle_rejected():
    with pytest.raises(ValueError):physical_runs(np.array([[0,1],[1,0]]),(3,3),1.)


def test_outlet_nearest_not_bijective():
    a=outlet_distances([[0,0],[0,2]],[[0,0]])
    assert a['exact_common_locations']==1 and a['baseline_to_fine']['max_km']==2 and a['fine_to_baseline']['max_km']==0


def test_independent_projection_and_ledger():
    m,c,meta=toy();archive,_=connected_mfd_channel_projection(c,m,meta,stream_threshold_km2=30.)
    f,fm,g,r=run(m,c,meta,archive)
    assert r['original_projection_exact_replay'] and not r['approved_geography']
    assert r['fine']['mass_balance']['local_source_area_km2']==97**2*.25
    assert r['baseline']['mass_balance']['local_source_area_km2']==49**2
    for k in ('baseline','fine'):assert abs(r[k]['mass_balance']['balance_error_km2'])<1e-6
    archive['channel_mask'].flat[0]^=1
    with pytest.raises(ValueError,match='projection replay mismatch'):run(m,c,meta,archive)


def test_cli_replay_and_sha_guard(tmp_path):
    m,c,meta=toy();f,_=connected_mfd_channel_projection(c,m,meta,stream_threshold_km2=30.)
    paths={k:tmp_path/(k+'.npz') for k in ('macro','child','projection')}
    for k,v in [('macro',m),('child',c),('projection',f)]:np.savez_compressed(paths[k],**v)
    paths['manifest']=tmp_path/'manifest.json';paths['manifest'].write_text(json.dumps(meta));paths['prior']=tmp_path/'prior.json';paths['prior'].write_text(json.dumps({'status':'P4_L_ANISOTROPIC_DETAIL_COUNTERFACTUAL_NOT_RIVERS','original_projection_exact_replay':True,'approved_geography':False,'source_sha256':{k:sha(v) for k,v in paths.items() if k!='prior'}}))
    cmd=[sys.executable,'-m','scripts.compare_region_resolution_v02']
    for k,v in paths.items():cmd+=['--'+k,str(v)]
    def call(n):return subprocess.run(cmd+['--output',str(tmp_path/n)],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
    a,b=call('one'),call('two');assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
    for f in (tmp_path/'one').iterdir():assert sha(f)==sha(tmp_path/'two'/f.name)
    paths['manifest'].write_bytes(paths['manifest'].read_bytes()+b' ');bad=call('bad');assert bad.returncode!=0 and 'SHA mismatch' in bad.stderr
