"""P4-E generated toy planet tests; no private Osvera grids."""
import copy,csv,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest
from scripts.condition_planetary_child_terrain_v02 import ChildTerrainSettings,generate_child
from scripts.compare_region_relief_strength_v02 import ReliefComparisonError,compare,render_contact_sheet

def fixture():
    v=np.arange(-6.,7.,2.);lat=v[::-1].copy();lon=v.copy();xx,yy=np.meshgrid(lon,lat)
    macro={'latitude_deg_north_first':lat,'longitude_deg_west_to_east':lon,
           'elevation_m':(300+4*xx+3*yy).astype('float32'),'land_mask':np.ones_like(xx,dtype='uint8')}
    s=ChildTerrainSettings(center_lat_deg=0.,center_lon_deg=0.,half_width_km=3.,half_height_km=3.,
        planet_radius_km=180/np.pi,planetary_year_earth_days=365.,spacing_km=1.,seed=1406,
        relief_strength=2.,detail_coordinate_system='spherical_xyz_v1')
    child,cm=generate_child(macro,s)
    cover={'cover_class_candidate':np.ones_like(child['child_elevation_m'],dtype='uint8')}
    edges=[]
    for i,col in enumerate(range(1,5)):
        dz=float(child['child_elevation_m'][3,col+1])-float(child['child_elevation_m'][3,col])
        edges.append({'edge_index':str(i),'source_row':'3','source_col':str(col),
                      'target_row':'3','target_col':str(col+1),'raw_delta_m':str(dz),
                      'raw_uphill_or_flat':str(dz>=0)})
    bad=sum(x['raw_uphill_or_flat']=='True' for x in edges)
    p4d={'status':'P4_D_ANCHOR_AND_RAW_DESCENT_NEGATIVE_CONTROL_NOT_RIVERS',
         'prior_P4C2_source_file_hashes_verified':True,'physical_basin_identity_or_river_verified':False,
         'macro_A8_upstream_area_injected_km2':0,'raw_uphill_or_flat_edges':bad,
         'complete_P4C2_partition':{'strict':len(edges)-bad,'fill_only':0,'raw_uphill_only':bad,'both':0}}
    return macro,child,cm,cover,p4d,edges

def test_exact_baseline_three_reproducible_anchor_variants():
    args=fixture();saved=copy.deepcopy(args)
    fields,audit=compare(*args)
    assert [x['relief_strength'] for x in audit['variant_scores']]==[.5,1.25,2.]
    assert not audit['accepted_Core_MFD_or_P4C1_route_recomputed']
    assert not audit['true_alternative_basin_or_dendricity_computed']
    assert audit['variant_cover_colors_reuse_baseline_P3_NOT_RECOMPUTED']
    for key,score in zip([.5,1.25,2.],audit['variant_scores']):
        assert score['maximum_parent_anchor_error_m']<=1e-6
        np.testing.assert_array_equal(fields[key]['parent_interpolated_m'],args[1]['parent_interpolated_m'])
        np.testing.assert_array_equal(fields[key]['land_mask'],args[1]['land_mask'])
    for k in args[1]:np.testing.assert_array_equal(fields[2.][k],args[1][k])
    assert audit['variant_scores'][0]['effective_fine_relief_std_m']<audit['variant_scores'][1]['effective_fine_relief_std_m']
    for a,b in zip(args,saved):
        if isinstance(a,dict):
            for k,v in a.items():
                if isinstance(v,np.ndarray):np.testing.assert_array_equal(v,b[k])
                else:assert v==b[k]
        else:assert a==b

@pytest.mark.parametrize('kind',[
    'missing_baseline','wrong_order','duplicates','out_of_range','negative','above_max',
    'wrong_baseline','invalid_class','canon_p4d','tampered_edge_height','truncated_ledger',
    'disconnected','tampered_original','bad_parent','injected_water'])
def test_fail_closed(kind):
    a=list(fixture());kw={}
    if kind=='missing_baseline':kw['strengths']=(.25,.5,1.0)
    elif kind=='wrong_order':kw['strengths']=(1.25,.5,2.)
    elif kind=='duplicates':kw['strengths']=(.5,.5,2.)
    elif kind=='out_of_range':kw['strengths']=(.5,2.,3.)
    elif kind=='negative':kw['strengths']=(-1.,.5,2.)
    elif kind=='above_max':kw['strengths']=(.5,1.25,2.6)
    elif kind=='wrong_baseline':a[2]['relief_strength']=1.0
    elif kind=='invalid_class':a[3]['cover_class_candidate'][0,0]=9
    elif kind=='canon_p4d':a[4]['status']='GIVEN_RIVERS'
    elif kind=='tampered_edge_height':a[5][1]['raw_delta_m']='1200'
    elif kind=='truncated_ledger':a[5].pop()
    elif kind=='disconnected':a[5][2]['source_col']='0'
    elif kind=='tampered_original':a[1]['child_elevation_m'][0,0]+=1.
    elif kind=='bad_parent':a[1]['parent_interpolated_m'][0,0]+=1.
    elif kind=='injected_water':a[4]['macro_A8_upstream_area_injected_km2']=300.
    with pytest.raises(ReliefComparisonError):compare(*a,**kw)

def test_deterministic_map_render(tmp_path):
    args=fixture();variant,audit=compare(*args)
    for name in ('a','b'):
        folder=tmp_path/name;folder.mkdir();render_contact_sheet(variant,args[1],args[3],audit,folder,pixels_per_cell=5)
    for name in ('region-relief-comparison-sheet.png','region-relief-strength-0p5.png',
                 'region-relief-strength-1p25.png','region-relief-strength-2p0.png'):
        assert (tmp_path/'a'/name).read_bytes()==(tmp_path/'b'/name).read_bytes()
    with Image.open(tmp_path/'a'/'region-relief-comparison-sheet.png') as im:
        assert im.size==(3*7*5+2*50+2*24, 2*7*5+83+80+155)

def test_cli_sha_replay_and_refuse_overwrite(tmp_path):
    macro,child,cm,cover,p4d,edges=fixture();p=tmp_path/'in';p.mkdir()
    for name,arrays in [('macro.npz',macro),('child.npz',child),('cover.npz',cover)]:
        np.savez_compressed(p/name,**arrays)
    (p/'cm.json').write_text(json.dumps(cm))
    with (p/'edges.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=edges[0].keys());writer.writeheader();writer.writerows(edges)
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    p4d['input_sha256']={'macro_npz':sha(p/'macro.npz'),'child_npz':sha(p/'child.npz'),
                         'child_manifest':sha(p/'cm.json')}
    (p/'p4d.json').write_text(json.dumps(p4d))
    p4a={'status':'P4A_NONCANONICAL_CARTOGRAPHIC_BASE','is_author_canon':False,
         'is_measured_landcover':False,
         'input_sha256':{'child_npz':sha(p/'child.npz'),'cover_npz':sha(p/'cover.npz')}}
    (p/'p4a.json').write_text(json.dumps(p4a))
    args=[sys.executable,'-m','scripts.compare_region_relief_strength_v02']
    for key,name in [('macro-npz','macro.npz'),('child-npz','child.npz'),('child-manifest','cm.json'),
                     ('cover-npz','cover.npz'),('p4a-audit-json','p4a.json'),
                     ('p4d-audit-json','p4d.json'),('p4d-edges-csv','edges.csv')]:
        args+=['--'+key,str(p/name)]
    root=Path(__file__).resolve().parents[1]
    def run(t):return subprocess.run(args+['--output',str(tmp_path/t)],cwd=root,text=True,capture_output=True)
    a,b=run('first'),run('second');assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
    for f in (tmp_path/'first').iterdir():assert sha(f)==sha(tmp_path/'second'/f.name)
    assert run('first').returncode!=0
    with np.load(p/'child.npz') as z:changed={k:z[k].copy() for k in z.files}
    changed['child_elevation_m'][0,0]+=10.;np.savez_compressed(p/'child.npz',**changed)
    fail=run('invalid');assert fail.returncode!=0 and 'SHA lineage mismatch' in fail.stderr
