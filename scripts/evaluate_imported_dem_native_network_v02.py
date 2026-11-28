"""P4-O: complete Core hydrology on an imported inland DEM, explicit experimental normalization."""
import argparse, hashlib, json
from collections import Counter
from dataclasses import replace
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.colors import LightSource, LinearSegmentedColormap
from shapely.geometry import LineString
import domain_generator
from domain_generator.contracts.spec import DomainSpec
from domain_generator.presets.registry import PresetRegistry
from domain_generator.compiler import compile_domain_spec
from domain_generator.terrain.state import TerrainState
from domain_generator.hydrology.continuous import (generate_hydrology_v02, validate_hydrology_v02, build_continuous_river_network)
from domain_generator.hydrology.water import build_water_depth_m


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def make_plan(shape,spacing=.5):
    # The terrain/surface recipe is mandatory compiler metadata only; neither stage is executed.
    nr,nc=shape
    spec=DomainSpec.model_validate(dict(schema_version='0.2',id='imported-dem-native-network-test',seed=1406,domain={'size':{'width_km':nc*spacing,'height_km':nr*spacing}},simulation={'cell_size_km':spacing},terrain={'base_elevation_m':0.,'noise_layers':[{'id':'unused','scale_km':1.,'amplitude_m':1.}]},hydrology={'stream_threshold_km2':30.,'lake_min_area_km2':16.,'lake_min_depth_m':10.,'river_depth_at_threshold_m':.5,'river_depth_exponent':.3},surface={'moisture_base':.35,'water_moisture_boost':.55,'water_moisture_decay_km':2.,'moisture_noise_amplitude':.1,'moisture_noise_scale_km':20.,'vegetation_slope_zero_deg':45.,'climate':{'mean_temperature_c':8.,'north_minus_south_temperature_c':-4.,'temperature_noise_amplitude_c':1.5,'mean_annual_precipitation_mm':900.,'moisture_transport_bearing_deg':90.,'orographic_scale_km':45.,'orographic_strength':2.,'precipitation_noise_log_amplitude':.22,'climate_noise_scale_km':60.}}))
    return compile_domain_spec(spec,registry=PresetRegistry([],operator_ids=[]),generator_version=domain_generator.__version__)


def stats(net):
    seg=list(net.segments.values());lines=[LineString([(p.x_km,p.y_km) for p in s.centerline]) for s in seg];inc=Counter(s.to_node for s in seg);kinds=Counter(n.kind.value for n in net.nodes.values());bad=0
    # Full spatial overlap/crossing audit is a separate product gate.
    bad=None
    return {'nodes':len(net.nodes),'segments':len(seg),'node_kinds':dict(kinds),'false_confluences':sum(n.kind.value=='confluence' and inc[k]<2 for k,n in net.nodes.items()),'length_km':sum(l.length for l in lines),'non_simple_segments':sum(not l.is_simple for l in lines),'pairs_intersecting_beyond_shared_nodes':bad,'boundary_outlets_sw_km':sorted([[n.position.x_km,n.position.y_km] for n in net.nodes.values() if n.kind.value=='domain_outlet'])}


def run(z,spacing=.5):
    if z.ndim!=2 or not np.isfinite(z).all():raise ValueError('finite 2D elevation required')
    plan=make_plan(z.shape,spacing);t=TerrainState(elevation_m=z.copy());h=generate_hydrology_v02(plan,t);v=validate_hydrology_v02(plan,t,h,attempt_index=0);print("native validation complete",flush=True)
    net,mask=build_continuous_river_network(plan,h.continuous_routing,h.flow_accumulation_km2,h.channel_support_mask,h.lake_candidates,h.lake_outlets,normalize_false_confluences=True,lake_features=h.lake_features)
    water=build_water_depth_m(t.elevation_m,h.fill_elevation_m,h.flow_accumulation_km2,mask,h.lake_candidates,stream_threshold_km2=30.,river_depth_at_threshold_m=.5,river_depth_exponent=.3)
    candidate=replace(h,river_network=net,stream_mask=mask,water_depth_m=water);w=validate_hydrology_v02(plan,t,candidate,attempt_index=0);print("normalized validation complete",flush=True)
    if not np.array_equal(z,t.elevation_m):raise ValueError('input mutated')
    def val(v):return {'passed':v.engine_invariants.passed,'failed':[i.id for i in v.engine_invariants.results if not i.passed],'checks':len(v.engine_invariants.results)}
    r={'status':'P4_O_IMPORTED_DEM_NATIVE_NETWORK_EXPERIMENT_NOT_CANON','native_validation':val(v),'normalized_validation':val(w),'native_regional':stats(h.river_network),'normalized_regional':stats(net),'potential':stats(h.potential_river_network),'lakes':[{'area_km2':l.area_km2,'max_depth_m':l.max_depth_m,'surface_elevation_m':l.surface_elevation_m} for l in h.lake_candidates],'terrain_unchanged':True,'core_code_changed':False,'approved_geography':False,'chapter1_compatibility_verified':False,'limitations':['imported TerrainState hydrology stage only, not a full DomainData generation pipeline','mandatory unused terrain and climate plan values are not author settings','normalization enabled only via existing builder in experimental adapter','independent geometric overlap/crossing audit not executed; Core graph validation is not spatial validation','catchment area and modeled lake geometry, not actual discharge or permanence']}
    return plan,h,candidate,r


def render(z,f,plan,h,c,out):
    nr,nc=z.shape;W=1080;H=round(W*nr/nc);width=plan.domain.width_km;height=plan.domain.height_km;pad=22;gap=18;top=80
    cmap=LinearSegmentedColormap.from_list('land',['#738c66','#a7b37e','#c7bc94','#e1d5bb','#f1e8d8']);rgb=LightSource(azdeg=315,altdeg=40).shade(z,cmap=cmap,vert_exag=12,dx=500,dy=500,blend_mode='soft');bg=Image.fromarray((rgb[:,:,:3]*255).astype('uint8')).resize((W,H),Image.Resampling.BICUBIC)
    def xy(x,y):return (x/width*(W-1),(1-y/height)*(H-1))
    board=Image.new('RGB',(2*W+2*pad+gap,H+top+88),'#f4f0e4');d=ImageDraw.Draw(board)
    def font(n):
        try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
        except OSError:return ImageFont.load_default()
    d.text((pad,12),'OSVERA / P4-O — NATIVE NETWORK ON IMPORTED TERRAIN',font=font(25),fill='#29362d')
    for j in range(2):
        im=bg.copy();draw=ImageDraw.Draw(im)
        if j==0:
            area=f['Core_dominant_channel_area_km2_NOT_Q'].ravel()
            for a,b in f['channel_edge_flat_from_to']:
                r0,c0=divmod(int(a),nc);r1,c1=divmod(int(b),nc);draw.line([xy((c0+.5)*.5,height-(r0+.5)*.5),xy((c1+.5)*.5,height-(r1+.5)*.5)],fill='#285d87',width=2 if area[a]>=200 else 1)
        else:
            for s in c.river_network.segments.values():draw.line([xy(p.x_km,p.y_km) for p in s.centerline],fill='#285d87',width=2 if s.properties.catchment_area_km2>=200 else 1,joint='curve')
        for lake in h.lake_features.values():
            for p in lake.geometry.polygons:
                draw.polygon([xy(v.x_km,v.y_km) for v in p.outer],fill='#719bb0',outline='#386681');
                for ring in p.holes:draw.polygon([xy(v.x_km,v.y_km) for v in ring],fill='#a6b27f')
        x=pad+j*(W+gap);board.paste(im,(x,top));d.text((x,47),['P4-M: ordinary raster edges','P4-O: normalized native regional network'][j],font=font(19),fill='#29362d')
    d.text((pad,top+H+12),'Same DEM, threshold 30 km², common geometric lake fill; no physical water or canon claim.',font=font(17),fill='#29362d');d.text((pad,top+H+41),'Candidate may change topology; separate graph and spatial validation required.',font=font(17),fill='#29362d');board.save(out/'p4o-comparison.png')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('child','projection','prior','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();prior=json.loads(a.prior.read_text());names={'child':'p4m-fine-terrain.npz','projection':'p4m-fine-projection.npz'}
    if prior.get('status')!='P4_M_NESTED_SAME_ANALYTIC_TERRAIN_RESOLUTION_NOT_RIVERS' or any(sha(getattr(a,k))!=prior['derived_sha256'][v] for k,v in names.items()):raise ValueError('P4-M SHA mismatch')
    with np.load(a.child,allow_pickle=False) as x:
        z=x['child_elevation_m'];assert np.all(x['land_mask']) and np.all(np.diff(x['east_km'])==.5) and np.all(np.diff(x['north_km_north_first'])==-.5)
        origin=[float(x['east_km'][0]-.25),float(x['north_km_north_first'][-1]-.25)]
    with np.load(a.projection,allow_pickle=False) as x:f={k:x[k] for k in x.files}
    plan,h,c,r=run(z);r['origin_east_north_km']=origin;r['baseline_ordinary_edges']=len(f['channel_edge_flat_from_to']);r['baseline_mfd_area_exact']=bool(np.array_equal(h.flow_accumulation_km2,f['MFD_contributing_area_km2_NOT_Q']));a.output.mkdir(parents=True,exist_ok=False)
    render(z,f,plan,h,c,a.output)
    for name,net in [('native-regional',h.river_network),('normalized-regional',c.river_network),('potential',h.potential_river_network)]: (a.output/(name+'.json')).write_text(net.model_dump_json(by_alias=True)+'\n')
    (a.output/'lakes.json').write_text(json.dumps({k:v.model_dump(mode='json') for k,v in h.lake_features.items()})+'\n');r['source_sha256']={k:sha(getattr(a,k)) for k in ('child','projection','prior')};r['derived_sha256']={v.name:sha(v) for v in sorted(a.output.iterdir())};(a.output/'p4o-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('native_regional','normalized_regional','potential')}));print({k:{x:y for x,y in r[k].items() if x!='boundary_outlets_sw_km'} for k in ('native_regional','normalized_regional','potential')})
if __name__=='__main__':main()
