"""P4-L: one noncanonical slope-aligned detail hypothesis, independent Core reroute."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from math import pi, cos, radians
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.colors import LightSource, LinearSegmentedColormap
from scripts.condition_planetary_child_terrain_v02 import (ChildTerrainSettings, evaluate_terrain, generate_child, _source_fields, _bilinear)
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection
from scripts.diagnose_region_directional_bias_v02 import straight_chain_runs

OFFSETS_KM=(-4.,-2.,0.,2.,4.)
WEIGHTS=np.array([1.,4.,6.,4.,1.])/16
TAPER_KM=8.
MAX_CHANGE_M=60.

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    with np.load(p,allow_pickle=False) as a:return {k:a[k].copy() for k in a.files}
def rms(a):return float(np.sqrt(np.mean(np.square(a,dtype=np.float64))))

def candidate_surface(macro, child, meta):
    x=np.asarray(child['east_km'],float);y=np.asarray(child['north_km_north_first'],float)
    if not np.allclose(np.diff(x),1,rtol=0,atol=1e-9) or not np.allclose(np.diff(y),-1,rtol=0,atol=1e-9):raise ValueError('requires 1 km grid')
    s=ChildTerrainSettings(center_lat_deg=meta['center_lat_lon_deg'][0],center_lon_deg=meta['center_lat_lon_deg'][1],half_width_km=float(x[-1]),half_height_km=float(y[0]),planet_radius_km=meta['planet_radius_km'],planetary_year_earth_days=meta['planet_year_earth_days'],seed=meta['seed'],relief_strength=meta['relief_strength'],detail_coordinate_system=meta['detail_coordinate_system'])
    replay,rm=generate_child(macro,s)
    if set(replay)!=set(child) or any(not np.array_equal(replay[k],child[k]) for k in replay):raise ValueError('baseline terrain replay mismatch')
    lat,lon,z,_=_source_fields(macro);kpd=pi*s.planet_radius_km/180;px=(lon-s.center_lon_deg)*kpd*cos(radians(s.center_lat_deg));py=(lat-s.center_lat_deg)*kpd
    gy,gx=np.gradient(z,py,px)
    def direction(xx,yy):
        u=_bilinear(xx,yy,px,py,gx);v=_bilinear(xx,yy,px,py,gy);norm=np.hypot(u,v)
        # Flat parent has no preferred direction: use zero offset there.
        return np.divide(u,norm,out=np.zeros_like(u),where=norm>1e-10),np.divide(v,norm,out=np.zeros_like(v),where=norm>1e-10)
    def filt(xx,yy):
        u,v=direction(xx,yy);out=np.zeros_like(xx,dtype=float)
        for d,w in zip(OFFSETS_KM,WEIGHTS):
            _,_,detail=evaluate_terrain(macro,s,np.clip(xx+d*u,px[0],px[-1]),np.clip(yy+d*v,py[0],py[-1]));out+=w*detail
        return out
    nx,ny=np.meshgrid(px,py);coarse=filt(nx,ny)
    def components(xx,yy):
        h,p,d=evaluate_terrain(macro,s,xx,yy)
        detail=filt(xx,yy)-_bilinear(xx,yy,px,py,coarse)
        dist=np.minimum(np.minimum(xx-x[0],x[-1]-xx),np.minimum(yy-y[-1],y[0]-yy))
        t=np.clip(dist/TAPER_KM,0,1);w=t*t*(3-2*t)*np.clip(p/45,0,1)
        return p,(1-w)*d,w*detail
    xx,yy=np.meshgrid(x,y);p,a,b=components(xx,yy);land=child['land_mask'].astype(bool)
    # Preserve whole land-detail RMS by solving a single quadratic, not by tuning network outcomes.
    target=rms(child['new_local_relief_m'][land]);aa=np.mean(b[land]**2);ab=np.mean(a[land]*b[land]);cc=np.mean(a[land]**2)-target**2
    if aa<=1e-12 or ab**2-aa*cc<0:raise ValueError('RMS match not feasible')
    gain=float((-ab+np.sqrt(ab**2-aa*cc))/aa)
    if not 0<gain<=4:raise ValueError('RMS gain outside declared bound')
    detail=a+gain*b;h=np.where(p>=0,p+detail,p)
    if not np.isfinite(h).all() or not np.array_equal(h.astype(np.float32)>=0,land):raise ValueError('land sign changed')
    result={k:v.copy() for k,v in child.items()};result['child_elevation_m']=h.astype(np.float32);result['new_local_relief_m']=detail.astype(np.float32)
    edge=np.zeros(h.shape,bool);edge[[0,-1],:]=True;edge[:,[0,-1]]=True
    if not np.array_equal(result['child_elevation_m'][edge],child['child_elevation_m'][edge]) or not np.array_equal(result['new_local_relief_m'][edge],child['new_local_relief_m'][edge]):raise ValueError('boundary elevations changed')
    delta=h-child['child_elevation_m'];maxchange=float(np.max(abs(delta)))
    if maxchange>MAX_CHANGE_M:raise ValueError('terrain change bound exceeded')
    inside=(nx>=x[0])&(nx<=x[-1])&(ny>=y[-1])&(ny<=y[0]);ap,ad,bd=components(nx[inside],ny[inside]);err=float(np.max(abs(ap+ad+gain*bd-z[inside])))
    if err>1e-6 or int(inside.sum())!=rm['source_elevation_anchors_in_child']:raise ValueError('continuous anchor check failed')
    # directional roughness proxy at +/-2 km, using common local slope and interior sample
    u,v=direction(xx,yy);valid=land&(np.hypot(u,v)>.5)&(xx>x[0]+10)&(xx<x[-1]-10)&(yy>y[-1]+10)&(yy<y[0]-10)
    if not np.any(valid):raise ValueError('no interior directional sample')
    def rough(d):
        along=_bilinear(xx[valid]+2*u[valid],yy[valid]+2*v[valid],x,y[::-1],d[::-1]);cross=_bilinear(xx[valid]-2*v[valid],yy[valid]+2*u[valid],x,y[::-1],d[::-1]);return {'along_rms_m':rms(along-d[valid]),'across_rms_m':rms(cross-d[valid])}
    return result,{'anchor_count':int(inside.sum()),'continuous_anchor_max_error_m':err,'boundary_exact':True,'land_mask_exact':True,'original_terrain_exact_replay':True,'detail_rms_original_m':target,'detail_rms_candidate_m':rms(detail[land]),'rms_gain':gain,'max_height_change_m':maxchange,'rms_height_change_m':rms(delta),'directional_roughness_2km_original':rough(child['new_local_relief_m']),'directional_roughness_2km_candidate':rough(detail),'offsets_km':list(OFFSETS_KM),'weights':WEIGHTS.tolist(),'boundary_taper_km':TAPER_KM}

def metrics(child,f,ledger):
    z=child['child_elevation_m'];center=z[1:-1,1:-1];nr,nc=z.shape
    pit=np.ones_like(center,bool)
    for i in range(3):
        for j in range(3):
            if (i,j)!=(1,1):pit &= center<z[i:i+nr-2,j:j+nc-2]
    return {**straight_chain_runs(f['channel_edge_flat_from_to'],z.shape),'channel_cells':int(f['channel_mask'].sum()),'strict_interior_pits':int(pit.sum()),'raw_nondescending_ordinary_edges':int(np.count_nonzero(z.ravel()[f['channel_edge_flat_from_to'][:,1]]>=z.ravel()[f['channel_edge_flat_from_to'][:,0]])),'outlets':sorted([r['child_edge_cell_row_col'] for r in ledger['connected_boundary_endpoints']]),'lake_proxy_cells':int(f['lake_proxy_mask'].sum()),'mass_balance':ledger['internal_mfd_mass_ledger'],'no_external_A8_area':ledger['no_external_A8_source_area_auto_injected']}

def run(macro,child,meta,archived):
    alt,terrain=candidate_surface(macro,child,meta);f,l=connected_mfd_channel_projection(child,macro,meta,stream_threshold_km2=30);g,m=connected_mfd_channel_projection(alt,macro,meta,stream_threshold_km2=30)
    if set(f)!=set(archived) or any(not np.array_equal(f[k],archived[k]) for k in f):raise ValueError('baseline projection replay mismatch')
    a,b=metrics(child,f,l),metrics(alt,g,m)
    if any(not q['no_external_A8_area'] or q['mass_balance']['explicit_external_area_km2']!=0 or abs(q['mass_balance']['balance_error_km2'])>1e-6 for q in (a,b)):raise ValueError('mass ledger failed')
    ma=f['channel_mask'].astype(bool);mb=g['channel_mask'].astype(bool)
    report={'status':'P4_L_ANISOTROPIC_DETAIL_COUNTERFACTUAL_NOT_RIVERS','terrain':terrain,'baseline':a,'candidate':b,'original_projection_exact_replay':True,'channel_mask_iou':float((ma&mb).sum()/(ma|mb).sum()),'outlet_set_exact':a['outlets']==b['outlets'],'outlet_intersection':len(set(map(tuple,a['outlets']))&set(map(tuple,b['outlets']))),'accepted_core_changed':False,'approved_geography':False,'limitations':['directional smoothing proxy, not erosion simulation or measured valleys','local crop taper and RMS normalization are not globally seamless','raw pit count and straight chains are diagnostics, not river validity','analytic source anchors exact; child raster samples approximate continuous surface']}
    return alt,g,report

def render(child,alt,f,g,report,out):
    z0=child['child_elevation_m'];z1=alt['child_elevation_m'];nr,nc=z0.shape;scale=5;w=nc*scale;h=nr*scale
    board=Image.new('RGB',(2*w+70,2*h+185),'#f2efe5');d=ImageDraw.Draw(board)
    def font(n):
        try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
        except OSError:return ImageFont.load_default()
    d.text((20,10),'P4-L / OSVERA — SLOPE-ALIGNED DETAIL TEST (NOT RIVERS)',font=font(23),fill='#28352c')
    for j,(c,p) in enumerate(((child,f),(alt,g))):
        z=c['child_elevation_m'];rgb=LightSource(azdeg=315,altdeg=40).shade(z,cmap=LinearSegmentedColormap.from_list('land_relief',['#66815c','#9aab75','#b9b18a','#d6c7a4','#e8dfce']),vmin=float(min(z0.min(),z1.min())),vmax=float(max(z0.max(),z1.max())),vert_exag=12,dx=1000,dy=1000,blend_mode='soft');im=Image.fromarray((rgb[:,:,:3]*255).astype(np.uint8)).resize((w,h),Image.Resampling.BICUBIC)
        x=20+j*(w+25);d.text((x,45),'Original Hermite + local detail' if j==0 else 'Slope-aligned detail, RMS matched',font=font(17),fill='#28352c');board.paste(im,(x,75));overlay=im.copy();dr=ImageDraw.Draw(overlay);area=p['Core_dominant_channel_area_km2_NOT_Q'].ravel()
        for a,b in p['channel_edge_flat_from_to']:
            r,c0=divmod(int(a),nc);r2,c2=divmod(int(b),nc);dr.line(((c0+.5)*scale,(r+.5)*scale,(c2+.5)*scale,(r2+.5)*scale),fill='#245c8b',width=3 if area[a]>=200 else 1)
        board.paste(overlay,(x,h+110));d.text((x,h+82),'Independent Core MFD channel projection',font=font(17),fill='#28352c')
    d.text((20,2*h+140),'Same height color scale, light, channel threshold (30 km²). Independent routing; no physical water claim.',font=font(16),fill='#28352c');board.save(out/'p4l-terrain-and-network.png')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('macro','child','manifest','projection','prior','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();prior=json.loads(a.prior.read_text());sources={'baseline_child_npz':a.child,'baseline_projection_npz':a.projection}
    if prior.get('status')!='P4_K_SEMANTIC_REACH_DISPLAY_ONLY_NOT_RIVERS' or prior.get('unchanged_source_graph') is not True or any(sha(v)!=prior['source_sha256'].get(k) for k,v in sources.items()):raise ValueError('P4-K source SHA/provenance mismatch')
    child=load(a.child);archive=load(a.projection);alt,g,r=run(load(a.macro),child,json.loads(a.manifest.read_text()),archive);a.output.mkdir(parents=True,exist_ok=False);render(child,alt,archive,g,r,a.output)
    np.savez_compressed(a.output/'p4l-candidate-detail.npz',candidate_child_elevation_m=alt['child_elevation_m'],candidate_local_relief_m=alt['new_local_relief_m']);np.savez_compressed(a.output/'p4l-candidate-model-projection.npz',**g)
    r['source_sha256']={k:sha(getattr(a,k)) for k in ('macro','child','manifest','projection','prior')};r['derived_sha256']={f.name:sha(f) for f in sorted(a.output.iterdir())};(a.output/'p4l-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
