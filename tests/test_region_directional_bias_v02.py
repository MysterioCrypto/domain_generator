"""P4-H synthetic worlds only: model direction controls and SHA tamper guards."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest
from scripts.diagnose_region_directional_bias_v02 import (DirectionBiasError,angular_gap_rad,direction_from_elevation,snap_fraction,straight_chain_runs,inspect_directional_bias,render_report)
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection


def fixture():
    n=13;rr,cc=np.indices((n,n));parent=(320+2*(n-1-cc)+1.5*np.abs(rr-(n//2))).astype('float32')
    child={}
    for s in (0.,.5,1.25,2.):
        z=(parent+s*.18*np.sin((rr+2)*(cc+1))).astype('float32') if s else parent.copy()
        child[s]={'child_elevation_m':z,'parent_interpolated_m':parent.copy(),
                  'land_mask':np.ones((n,n),dtype=np.uint8),
                  'east_km':np.arange(n,dtype='float64'),
                  'north_km_north_first':np.arange(n-1,-1,-1,dtype='float64')}
    macro={'latitude_deg_north_first':np.array([6.,0.,-6.]),'longitude_deg_west_to_east':np.array([-6.,0.,6.]),
           'source_river_mask_D8':np.zeros((3,3),dtype='uint8'),
           'local_downstream_index':np.full((3,3),-1,dtype='int32'),
           'source_catchment_km2_D8':np.ones((3,3),dtype='float32')}
    meta={'planet_radius_km':180/np.pi,'center_lat_lon_deg':[0.,0.],
          'status':'NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON','is_accepted_Core_DomainData':False}
    arch={};scores=[]
    for s in (.5,1.25,2.):
        fields,ledger=connected_mfd_channel_projection(child[s],macro,meta,stream_threshold_km2=30.)
        arch[s]=fields;scores.append({'relief_strength':s,'channel_mask_cells_NOT_WATER':int(fields['channel_mask'].sum()),
                   'connected_channel_terminal_count':len(ledger['connected_boundary_endpoints'])})
    f={'status':'P4_F_INDEPENDENT_CORE_MFD_TERRAIN_VARIANT_TOPOLOGY_NOT_RIVERS',
       'geography_or_rivers_approved':False,'baseline_P2B2p4_exact_replay_verified':True,
       'original_parent_stations_preserved':1,'variant_comparison':scores}
    g={'status':'P4_G_THREE_THRESHOLD_MODEL_CHANNEL_MORPHOLOGY_NOT_RIVERS',
       'is_approved_physical_river_or_Q':False,'P4F_threshold_30_bit_exact_all_3_variants':True,
       'P4F_original_63_parent_stations_preserved':1}
    return child,macro,meta,arch,f,g


def test_circular_direction_wrapping_and_snap():
    a=np.deg2rad([359.,1.,44.,46.,90.,125.])
    assert np.rad2deg(angular_gap_rad(a[:1],a[1:2]))[0]==pytest.approx(2.)
    assert snap_fraction(a,np.ones(6,dtype=bool))==pytest.approx(5/6)
    assert snap_fraction(np.deg2rad([22.5]),np.array([True]))==0.


def test_metric_gradient_east_and_north():
    rr,cc=np.indices((5,5))
    assert float(direction_from_elevation((500-5*cc).astype(float),1)[2,2])==pytest.approx(0)
    assert float(direction_from_elevation((500+5*rr).astype(float),1)[2,2])==pytest.approx(np.pi/2)
    with pytest.raises(DirectionBiasError):direction_from_elevation(np.full((5,5),np.nan),1)


def test_merges_and_straight_run_no_double_count():
    e=np.array([[6,7],[7,8],[11,7],[8,9]],dtype=np.int32)
    s=straight_chain_runs(e,(5,5));assert s['edge_count']==4 and s['number_of_maximal_same_heading_runs']==2
    assert s['maximum_same_heading_run_cells']==3 and s['diagonal_edges_fraction']==pytest.approx(.25)
    assert s['edges_in_straight_runs_ge_8_fraction']==0
    e2=np.array([[6,7],[7,8],[8,9]],dtype=np.int32)
    assert straight_chain_runs(e2,(5,5),min_run=3)['edges_in_straight_runs_ge_8_fraction']==1


@pytest.mark.parametrize('bad',['empty','nonadjacent','outofbounds','duplicate','cycle'])
def test_bad_model_graph_fails_closed(bad):
    e={'empty':np.empty((0,2),dtype=np.int32),'nonadjacent':np.array([[6,8]]),
       'outofbounds':np.array([[6,100]]),'duplicate':np.array([[6,7],[6,11]]),
       'cycle':np.array([[6,7],[7,6]])}[bad]
    with pytest.raises(DirectionBiasError):straight_chain_runs(e,(5,5))


def test_four_full_accepted_core_projections_and_immutable_inputs():
    arg=fixture();snapshot=copy.deepcopy(arg)
    out,_,report=inspect_directional_bias(*arg)
    assert list(out)==[0.,.5,1.25,2.]
    assert len(report['metrics'])==4
    assert not report['parent_only_is_valid_natural_terrain']
    assert not report['operator_accepted_geography']
    assert report['prior_P4F_and_P4G_model_archives_bit_exact_replayed']
    assert report['A8_external_area_autoinjected_km2']==0
    for row in report['metrics']:
        assert row['model_channel_cells']>0
        assert 0<=row['parent_continuous_raw_gradient_octant_snap_on_fixed_sample']<=1
        assert row['source_parent_samples_on_fixed_original_channel']>0
    for s in arg[0]:
        for k in arg[0][s]:np.testing.assert_array_equal(arg[0][s][k],snapshot[0][s][k])
    for s in (.5,1.25,2.):
        for k in arg[3][s]:np.testing.assert_array_equal(out[s][0][k],arg[3][s][k])


@pytest.mark.parametrize('bad',['status','approved','baseline','parent','land','axis','projection','stations'])
def test_false_provenance_rejected(bad):
    arg=list(fixture())
    if bad=='status':arg[4]['status']='APPROVED'
    if bad=='approved':arg[5]['is_approved_physical_river_or_Q']=True
    if bad=='baseline':arg[4]['baseline_P2B2p4_exact_replay_verified']=False
    if bad=='parent':arg[0][.5]['parent_interpolated_m'][1,1]+=2
    if bad=='land':arg[0][2.]['land_mask'][1,1]=0
    if bad=='axis':arg[0][1.25]['east_km'][3]+=1
    if bad=='projection':arg[3][.5]['channel_mask'][4,4]^=1
    if bad=='stations':arg[5]['P4F_original_63_parent_stations_preserved']=4
    with pytest.raises(DirectionBiasError):inspect_directional_bias(*arg)


def test_png_determinism_and_no_overwrite(tmp_path):
    out,angles,report=inspect_directional_bias(*fixture());backgrounds={}
    for s in (.5,1.25,2.):
        f=tmp_path/f'{s}.png';Image.new('RGB',(45,45),(60,92,72)).save(f);backgrounds[s]=f
    for name in ('a','b'):render_report(out,angles,report,backgrounds,tmp_path/name)
    for n in ('p4h-parent-vs-detail-directional-run-review.png','p4h-directional-straight-run-metrics.png'):
        assert (tmp_path/'a'/n).read_bytes()==(tmp_path/'b'/n).read_bytes()
    with pytest.raises(DirectionBiasError):render_report(out,angles,report,backgrounds,tmp_path/'a')


def test_full_cli_source_hash_and_tamper(tmp_path):
    children,macro,meta,archive,f,g=fixture();p=tmp_path/'in';p.mkdir()
    maps={'macro_npz':('macro.npz',macro),'baseline_child_npz':('base.npz',children[2.]),
      'variant_0p5_npz':('alt05.npz',children[.5]),'variant_1p25_npz':('alt125.npz',children[1.25]),
      'baseline_projection_npz':('arch20.npz',archive[2.]),
      'p4f_projection_0.5':('arch05.npz',archive[.5]),'p4f_projection_1.25':('arch125.npz',archive[1.25])}
    for name,data in maps.values():np.savez_compressed(p/name,**data)
    (p/'manifest.json').write_text(json.dumps(meta))
    def sh(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    maps['child_manifest']=('manifest.json',None)
    g['input_sha256']={k:sh(p/v[0]) for k,v in maps.items()}
    f['source_sha256']={k:v for k,v in g['input_sha256'].items() if not k.startswith('p4f_projection_')}
    (p/'f.json').write_text(json.dumps(f));g['input_sha256']['p4f_audit_json']=sh(p/'f.json')
    (p/'g.json').write_text(json.dumps(g))
    for v in ('05','125','20'):Image.new('RGB',(45,45),(65,97,73)).save(p/f'{v}.png')
    names={'macro-npz':'macro.npz','baseline-child-npz':'base.npz','child-manifest':'manifest.json',
       'variant-0p5-npz':'alt05.npz','variant-1p25-npz':'alt125.npz',
       'archived-0p5-npz':'arch05.npz','archived-1p25-npz':'arch125.npz','archived-2p0-npz':'arch20.npz',
       'p4f-audit-json':'f.json','p4g-audit-json':'g.json',
       'terrain-0p5-png':'05.png','terrain-1p25-png':'125.png','terrain-2p0-png':'20.png'}
    args=[sys.executable,'-m','scripts.diagnose_region_directional_bias_v02']
    for opt,n in names.items():args.extend(['--'+opt,str(p/n)])
    root=Path(__file__).resolve().parents[1]
    def run(dest):return subprocess.run(args+['--output',str(tmp_path/dest)],cwd=root,text=True,capture_output=True)
    a,b=run('one'),run('two');assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
    for file in (tmp_path/'one').iterdir():assert sh(file)==sh(tmp_path/'two'/file.name)
    assert run('one').returncode!=0
    with np.load(p/'alt05.npz') as z:corrupt={k:z[k].copy() for k in z.files}
    corrupt['child_elevation_m'][2,2]+=30;np.savez_compressed(p/'alt05.npz',**corrupt)
    bad=run('tamper');assert bad.returncode!=0 and 'source SHA mismatch' in bad.stderr
