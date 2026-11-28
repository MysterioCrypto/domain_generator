"""P4-M: nested sampling of the same inland analytic terrain; NOT rivers."""
import argparse, hashlib, json
from pathlib import Path
from dataclasses import replace
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.colors import LightSource, LinearSegmentedColormap
from scripts.condition_planetary_child_terrain_v02 import ChildTerrainSettings, generate_child
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection
from scripts.diagnose_region_directional_bias_v02 import _edge_angles, straight_chain_runs


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    with np.load(p,allow_pickle=False) as a:return {k:a[k].copy() for k in a.files}


def nested_terrain(macro,child,meta):
    x,y=child['east_km'],child['north_km_north_first']
    if len(x)<3 or len(y)<3 or not np.all(np.diff(x)==1) or not np.all(np.diff(y)==-1) or x[0]!=-x[-1] or y[0]!=-y[-1]:raise ValueError('expected symmetric 1 km source axes')
    s=ChildTerrainSettings(center_lat_deg=meta['center_lat_lon_deg'][0],center_lon_deg=meta['center_lat_lon_deg'][1],half_width_km=float(x[-1]),half_height_km=float(y[0]),spacing_km=1.,planet_radius_km=meta['planet_radius_km'],planetary_year_earth_days=meta['planet_year_earth_days'],seed=meta['seed'],relief_strength=meta['relief_strength'],detail_coordinate_system=meta['detail_coordinate_system'])
    base,m0=generate_child(macro,s)
    if set(base)!=set(child) or any(not np.array_equal(base[k],child[k]) for k in base):raise ValueError('baseline terrain replay mismatch')
    fine,m1=generate_child(macro,replace(s,spacing_km=.5))
    for k,v in base.items():
        if not np.array_equal(v,fine[k][::2] if v.ndim==1 else fine[k][::2,::2]):raise ValueError('nested sample mismatch: '+k)
    if m0['source_elevation_anchors_in_child']!=m1['source_elevation_anchors_in_child'] or m0['source_elevation_anchors_in_child']!=meta['source_elevation_anchors_in_child'] or max(m0['max_parent_anchor_error_m'],m1['max_parent_anchor_error_m'])>1e-6:raise ValueError('anchor mismatch')
    if not np.all(base['land_mask']) or not np.all(fine['land_mask']):raise ValueError('inland-only experiment')
    return fine,m1,{'nested_all_six_arrays_exact':True,'anchor_count':m1['source_elevation_anchors_in_child'],'anchor_error_m':[m0['max_parent_anchor_error_m'],m1['max_parent_anchor_error_m']],'node_extent_km':[float(x[-1]-x[0]),float(y[0]-y[-1])]}


def physical_runs(edges,shape,spacing):
    if not np.isfinite(spacing) or spacing<=0:raise ValueError('invalid spacing')
    straight_chain_runs(edges,shape)
    _,heading=_edge_angles(edges,shape);lookup=np.full(np.prod(shape),-1,dtype=np.int32);lookup[edges[:,0]]=np.arange(len(edges))
    nxt=lookup[edges[:,1]];valid=nxt>=0;valid[valid]&=heading[nxt[valid]]==heading[valid]
    prev=np.zeros(len(edges),bool);prev[nxt[valid]]=True
    lengths=[];counts=[]
    for i in np.flatnonzero(~prev):
        k=int(i);n=1
        while valid[k]:k=int(nxt[k]);n+=1
        h=int(heading[i]);lengths.append(n*spacing*(np.sqrt(2) if h//3!=1 and h%3!=1 else 1));counts.append(n)
    if sum(counts)!=len(edges):raise ValueError('incomplete physical runs')
    a=np.array(lengths);total=float(a.sum())
    return {'edges':len(edges),'runs':len(a),'total_length_km':total,'max_run_km':float(a.max()),'length_fraction_ge8km':float(a[a>=8-1e-10].sum()/total),'length_fraction_ge16km':float(a[a>=16-1e-10].sum()/total),'runs_ge8km':int((a>=8-1e-10).sum()),'runs_ge16km':int((a>=16-1e-10).sum())}


def outlet_distances(a,b):
    x=np.array(a,float).reshape(-1,2);y=np.array(b,float).reshape(-1,2)
    if not len(x) or not len(y):raise ValueError('no boundary outlets')
    d=np.linalg.norm(x[:,None]-y[None,:],axis=2)
    def stats(v):return {'median_km':float(np.median(v)),'max_km':float(v.max()),'within_1km':int((v<=1+1e-10).sum()),'within_5km':int((v<=5+1e-10).sum())}
    return {'baseline_to_fine':stats(d.min(axis=1)),'fine_to_baseline':stats(d.min(axis=0)),'exact_common_locations':len(set(map(tuple,x))&set(map(tuple,y)))}


def summarize(c,f,l):
    spacing=float(np.diff(c['east_km'])[0]);area=l['internal_mfd_mass_ledger']
    if not l['no_external_A8_source_area_auto_injected'] or area['explicit_external_area_km2']!=0 or abs(area['balance_error_km2'])>1e-6 or area['local_source_area_km2']!=c['land_mask'].size*spacing**2:raise ValueError('area ledger failed')
    if l['lake_topology_status'].startswith('UNRESOLVED'):raise ValueError('unresolved lake topology')
    return {**physical_runs(f['channel_edge_flat_from_to'],c['land_mask'].shape,spacing),'spacing_km':spacing,'shape':list(c['land_mask'].shape),'channel_cells':int(f['channel_mask'].sum()),'lake_proxy_cells':int(f['lake_proxy_mask'].sum()),'outlets':sorted(r['crossing_east_north_km'] for r in l['connected_boundary_endpoints']),'mass_balance':area}


def run(macro,child,meta,archive):
    fine,m1,terrain=nested_terrain(macro,child,meta)
    f,l=connected_mfd_channel_projection(child,macro,meta,stream_threshold_km2=30.)
    if set(f)!=set(archive) or any(not np.array_equal(f[k],archive[k]) for k in f):raise ValueError('baseline projection replay mismatch')
    g,m=connected_mfd_channel_projection(fine,macro,m1,stream_threshold_km2=30.)
    a,b=summarize(child,f,l),summarize(fine,g,m)
    report={'status':'P4_M_NESTED_SAME_ANALYTIC_TERRAIN_RESOLUTION_NOT_RIVERS','terrain':terrain,'baseline':a,'fine':b,'outlet_spatial_comparison':outlet_distances(a['outlets'],b['outlets']),'original_projection_exact_replay':True,'accepted_core_changed':False,'approved_geography':False,'stream_threshold_km2':30.,'local_area_difference_fraction':b['mass_balance']['local_source_area_km2']/a['mass_balance']['local_source_area_km2']-1,'limitations':['fixed node extent, not identical cell footprint: existing Core counts full boundary cells','same analytic surface, independently sampled and routed; conditioning and extraction are resolution-sensitive','nearest outlet proximity is not basin identity','inland only; one region and two resolutions do not establish convergence or real rivers']}
    return fine,m1,g,report


def render(child,fine,f,g,out):
    W=1150;H=round(W*(child['north_km_north_first'][0]-child['north_km_north_first'][-1])/(child['east_km'][-1]-child['east_km'][0]));pad=22;gap=24;top=80
    board=Image.new('RGB',(2*W+2*pad+gap,2*H+top+105),'#f1eee5');d=ImageDraw.Draw(board)
    def font(n):
        try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
        except OSError:return ImageFont.load_default()
    d.text((pad,13),'OSVERA / P4-M — SAME ANALYTIC TERRAIN, TWO GRID RESOLUTIONS',font=font(24),fill='#2b352e')
    lo=min(float(child['child_elevation_m'].min()),float(fine['child_elevation_m'].min()));hi=max(float(child['child_elevation_m'].max()),float(fine['child_elevation_m'].max()))
    cmap=LinearSegmentedColormap.from_list('land',['#718c63','#a6b17c','#c2b68d','#ddd0ae','#f1e8d7'])
    for j,(c,p) in enumerate(((child,f),(fine,g))):
        z=c['child_elevation_m'];s=float(np.diff(c['east_km'])[0]);nr,nc=z.shape
        rgb=LightSource(azdeg=315,altdeg=40).shade(z,cmap=cmap,vmin=lo,vmax=max(hi,lo+1e-6),vert_exag=12,dx=s*1000,dy=s*1000,blend_mode='soft')
        im=Image.fromarray((rgb[:,:,:3]*255).astype('uint8')).resize((W,H),Image.Resampling.BICUBIC)
        xx=pad+j*(W+gap);d.text((xx,48),f'{s:g} km / {nr} x {nc} nodes',font=font(19),fill='#2b352e');board.paste(im,(xx,top))
        over=im.copy();dr=ImageDraw.Draw(over);area=p['Core_dominant_channel_area_km2_NOT_Q'].ravel()
        for a,b in p['channel_edge_flat_from_to']:
            r0,c0=divmod(int(a),nc);r1,c1=divmod(int(b),nc)
            dr.line((c0*(W-1)/(nc-1),r0*(H-1)/(nr-1),c1*(W-1)/(nc-1),r1*(H-1)/(nr-1)),fill='#245982',width=3 if area[a]>=200 else 1)
        d.text((xx,top+H+8),'Independent Core MFD channel projection',font=font(18),fill='#2b352e');board.paste(over,(xx,top+H+37))
    d.text((pad,top+2*H+60),'Same 30 km² area threshold; model channels, NOT confirmed rivers or discharge.',font=font(18),fill='#2b352e');board.save(out/'p4m-resolution-comparison.png')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('macro','child','manifest','projection','prior','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();prior=json.loads(a.prior.read_text());sources={k:getattr(a,k) for k in ('macro','child','manifest','projection')}
    if prior.get('status')!='P4_L_ANISOTROPIC_DETAIL_COUNTERFACTUAL_NOT_RIVERS' or not prior.get('original_projection_exact_replay') or prior.get('approved_geography') is not False or any(sha(v)!=prior['source_sha256'].get(k) for k,v in sources.items()):raise ValueError('P4-L provenance / SHA mismatch')
    if a.output.exists():raise ValueError('output already exists')
    c=load(a.child);f=load(a.projection);fine,m,g,r=run(load(a.macro),c,json.loads(a.manifest.read_text()),f);a.output.mkdir(parents=True);render(c,fine,f,g,a.output)
    np.savez_compressed(a.output/'p4m-fine-terrain.npz',**fine);np.savez_compressed(a.output/'p4m-fine-projection.npz',**g);(a.output/'p4m-fine-manifest.json').write_text(json.dumps(m,indent=2)+'\n');r['source_sha256']={k:sha(v) for k,v in {**sources,'prior':a.prior}.items()};r['derived_sha256']={v.name:sha(v) for v in sorted(a.output.iterdir())};(a.output/'p4m-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
