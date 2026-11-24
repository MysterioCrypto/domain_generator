"""P4-K: noncanonical semantic reach display only; source graph never rewritten."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely import line_locate_point, line_interpolate_point, points, get_coordinates
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

LIMIT_KM = .75
SIMPLIFY_KM = .35
HEIGHT_LIMIT_M = 15.
SAMPLE_KM = .125


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_npz(p):
    with np.load(p, allow_pickle=False) as z:
        return {k:z[k].copy() for k in z.files}


def split_reaches(edges, shape):
    """Maximal directed paths between sources, confluences, terminals and boundary nodes."""
    e=np.asarray(edges); nr,nc=shape; n=nr*nc
    if e.ndim!=2 or e.shape[1]!=2 or not len(e) or e.dtype.kind not in 'iu' or np.any(e<0) or np.any(e>=n):
        raise ValueError('invalid edges')
    a,b=e.T
    if len(np.unique(a))!=len(a) or np.any(np.maximum(abs(a//nc-b//nc),abs(a%nc-b%nc))!=1):
        raise ValueError('not an ordinary single-receiver adjacency graph')
    incoming=np.bincount(b,minlength=n); outgoing=np.full(n,-1,int); outgoing[a]=b
    nodes=np.unique(e); boundary=(nodes//nc==0)|(nodes//nc==nr-1)|(nodes%nc==0)|(nodes%nc==nc-1)
    fixed=nodes[(incoming[nodes]!=1)|(outgoing[nodes]<0)|boundary]; fs=set(fixed.tolist())
    seen=set(); paths=[]
    for start in fixed:
        if outgoing[start]<0: continue
        p=[int(start)]; cursor=int(start)
        while outgoing[cursor]>=0:
            if cursor in seen: raise ValueError('cycle or duplicate reach')
            seen.add(cursor);cursor=int(outgoing[cursor]);p.append(cursor)
            if cursor in fs:break
        if p[-1] not in fs or p[0]==p[-1]:raise ValueError('invalid reach endpoint')
        paths.append(np.array(p,int))
    if seen!=set(a.tolist()):raise ValueError('unrepresented cycle or edge')
    # A cycle passing through multiple fixed nodes must also be rejected.
    state={}
    for start in nodes:
        trail=[];cur=int(start)
        while cur>=0 and state.get(cur,0)==0:
            state[cur]=1;trail.append(cur);cur=int(outgoing[cur])
        if cur>=0 and state.get(cur)==1:raise ValueError('cycle')
        for q in trail:state[q]=2
    return paths,fixed


def chaikin(p):
    a,b=p[:-1],p[1:]; mid=np.empty((2*len(a),2))
    mid[::2]=.75*a+.25*b;mid[1::2]=.25*a+.75*b
    return np.vstack([p[0],mid,p[-1]])


def bad_pairs(lines,paths):
    tree=STRtree(lines);ii,jj=tree.query(lines,predicate='intersects');bad=set()
    for i,j in zip(ii.tolist(),jj.tolist()):
        if j<=i:continue
        shared=set((paths[i][0],paths[i][-1]))&set((paths[j][0],paths[j][-1]))
        x=lines[i].intersection(lines[j])
        if x.is_empty:continue
        permitted=[Point(lines[i].coords[0 if p==paths[i][0] else -1]) for p in shared]
        if x.geom_type=='Point': valid=any(x.equals(q) for q in permitted)
        elif x.geom_type=='MultiPoint':valid=all(any(t.equals(q) for q in permitted) for t in x.geoms)
        else:valid=False
        if not valid:bad.add((i,j))
    return bad


def turn_sum(p):
    d=np.diff(p,axis=0);d=d[np.linalg.norm(d,axis=1)>1e-9];a=np.arctan2(d[:,1],d[:,0]);return float(np.degrees(np.abs(np.arctan2(np.sin(np.diff(a)),np.cos(np.diff(a)))).sum()))


def process(fields, child):
    e=fields['channel_edge_flat_from_to']; mask=np.asarray(fields['channel_mask']); nr,nc=mask.shape
    x=np.asarray(child['east_km'],float); y=np.asarray(child['north_km_north_first'],float)
    if len(x)!=nc or len(y)!=nr or not np.isfinite(x).all() or not np.isfinite(y).all() or not np.allclose(np.diff(x),1,rtol=0,atol=1e-9) or not np.allclose(np.diff(y),-1,rtol=0,atol=1e-9):raise ValueError('requires 1 km metric grid')
    if fields['lake_proxy_jumps_flat_from_to'].shape!=(0,2) or np.any(fields['lake_proxy_mask']):raise ValueError('lake proxies unsupported')
    paths,fixed=split_reaches(e,mask.shape)
    if set(np.flatnonzero(mask))!=set(np.unique(e)) or not np.array_equal(fields['Core_dominant_receiver_index'].ravel()[e[:,0]],e[:,1]):raise ValueError('source graph mismatch')
    z=np.asarray(child['child_elevation_m'],float); parent=np.asarray(child['parent_interpolated_m'],float);land=np.asarray(child['land_mask'],bool)
    if any(v.shape!=mask.shape for v in (z,parent,land)) or not np.isfinite(z).all() or not np.isfinite(parent).all() or not np.all(land.ravel()[e]):raise ValueError('bad terrain or channel crosses sea')
    domain=box(x[0],y[-1],x[-1],y[0]);land_poly=domain if land.all() else unary_union([box(x[c]-.5,y[r]-.5,x[c]+.5,y[r]+.5) for r,c in np.argwhere(land)]).intersection(domain)
    raw=[np.column_stack((x[p%nc],y[p//nc])) for p in paths]; original=[LineString(p) for p in raw]
    if any(not v.is_simple or not land_poly.covers(v) for v in original) or bad_pairs(original,paths):raise ValueError('invalid original geometry')
    def height(p):
        # Bilinear sampling on the validated 1-km grid; no extra dependency.
        r=np.clip(y[0]-p[:,1],0,nr-1);c=np.clip(p[:,0]-x[0],0,nc-1)
        r0=np.floor(r).astype(int);c0=np.floor(c).astype(int)
        r1=np.minimum(r0+1,nr-1);c1=np.minimum(c0+1,nc-1)
        u=r-r0;v=c-c0
        return (1-u)*((1-v)*z[r0,c0]+v*z[r0,c1])+u*((1-v)*z[r1,c0]+v*z[r1,c1])
    def elevation_delta(a,b):
        sample=get_coordinates(line_interpolate_point(b,np.linspace(0,b.length,max(2,int(np.ceil(b.length/SAMPLE_KM))+1))))
        nearest=get_coordinates(line_interpolate_point(a,line_locate_point(a,points(sample))))
        return float(np.max(np.abs(height(sample)-height(nearest))))
    result=[]; rejected={'corridor_or_land':0,'terrain_height':0,'intersection':0}; dz=[]
    for a,p in zip(original,raw):
        c=np.asarray(a.simplify(SIMPLIFY_KM,preserve_topology=True).coords)
        # Fixed endpoints; no invented meanders on straight reaches.
        if len(c)>2:c=chaikin(chaikin(c))
        b=LineString(c)
        if not b.is_simple or not land_poly.covers(b) or not a.buffer(LIMIT_KM,quad_segs=32).covers(b) or not b.buffer(LIMIT_KM,quad_segs=32).covers(a):
            rejected['corridor_or_land']+=1;b=a;d=0.
        else:
            d=elevation_delta(a,b)
            if d>HEIGHT_LIMIT_M:rejected['terrain_height']+=1;b=a;d=0.
        result.append(b);dz.append(d)
    # Revert any participating changed reach; repeat because fallback may introduce a new collision.
    while True:
        conflicts=bad_pairs(result,paths)
        if not conflicts:break
        affected={i for pair in conflicts for i in pair if not result[i].equals(original[i])}
        if not affected:raise ValueError('unresolvable crossing')
        for i in sorted(affected):result[i]=original[i];dz[i]=0.;rejected['intersection']+=1
    out=[np.asarray(v.coords) for v in result]
    if any(not np.array_equal(p[[0,-1]],q[[0,-1]]) for p,q in zip(raw,out)):raise ValueError('semantic node moved')
    offsets=np.array([a.hausdorff_distance(b) for a,b in zip(original,result)])
    # Independent source macro orientation diagnostic on exact same-heading runs >=8 steps.
    dy,dx=np.gradient(parent);long_n=0;aligned=0;angles=[];other_angles=[]
    for path,p in zip(paths,raw):
        steps=np.diff(p,axis=0); starts=np.r_[0,np.flatnonzero(np.any(steps[1:]!=steps[:-1],axis=1))+1,len(steps)]
        for lo,hi in zip(starts[:-1],starts[1:]):
            ids=path[lo:hi];v=steps[lo];g=np.column_stack((-dx.ravel()[ids],dy.ravel()[ids]));norm=np.linalg.norm(g,axis=1);valid=norm>1e-10
            gap=np.degrees(np.arccos(np.clip(g[valid]@v/(norm[valid]*np.linalg.norm(v)),-1,1)))
            if hi-lo>=8:
                long_n+=int(hi-lo);aligned+=int(np.count_nonzero(gap<=22.5));angles.extend(gap.tolist())
            else:other_angles.extend(gap.tolist())
    report={'status':'P4_K_SEMANTIC_REACH_DISPLAY_ONLY_NOT_RIVERS','source_edges':len(e),'source_nodes':int(len(np.unique(e))), 'fixed_nodes':len(fixed),'reaches':len(paths),'intermediate_nodes_not_fixed_in_display':int(len(np.unique(e))-len(fixed)), 'unchanged_source_graph':True,'new_crossings':0,'corridor_limit_km':LIMIT_KM,'simplify_tolerance_km':SIMPLIFY_KM,'height_sample_limit_m':HEIGHT_LIMIT_M,'height_sample_interval_km':SAMPLE_KM,'maximum_sampled_height_difference_m':max(dz),'max_hausdorff_km':float(offsets.max()),'changed_reaches_gt_20m':int(np.count_nonzero(offsets>.02)),'fallback_counts':rejected,'turn_sum_original_deg':sum(turn_sum(p) for p in raw),'turn_sum_display_deg':sum(turn_sum(p) for p in out),'vertices_original':sum(map(len,raw)),'vertices_display':sum(map(len,out)), 'original_reach_length_km':sum(v.length for v in original),'display_reach_length_km':sum(v.length for v in result),'straight_run_edges_ge8_within_semantic_reaches':long_n,'macro_gradient_valid_edges_on_those_runs':len(angles),'macro_gradient_aligned_within_22p5_deg':aligned,'macro_gradient_mean_angle_deg':float(np.mean(angles)) if angles else None,'other_edges_macro_gradient_valid':len(other_angles),'other_edges_macro_gradient_aligned_within_22p5_deg':int(np.count_nonzero(np.asarray(other_angles)<=22.5)),'other_edges_macro_gradient_mean_angle_deg':float(np.mean(other_angles)) if other_angles else None,'is_approved_river_geometry':False,'limitations':['height difference sampled against nearest original line, not continuous flow or valley proof','final crossing check, not continuous deformation proof','no invented meanders, straight runs may remain','comparison width determined by upstream area at reach start, not discharge','graph semantics and terrain unchanged']}
    return paths,fixed,raw,out,report


def render(fields,child,raw,out,paths,background,dest):
    nr,nc=fields['channel_mask'].shape; x=child['east_km'];y=child['north_km_north_first'];area=fields['Core_dominant_channel_area_km2_NOT_Q'].ravel()
    with Image.open(background) as im:bg=im.convert('RGB')
    if bg.size!=(nc*5,nr*5):raise ValueError('background size mismatch')
    def font(n):
        try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
        except OSError:return ImageFont.load_default()
    for label,r,c,h,w,scale in [('region',0,0,nr,nc,5),('zoom',min(123,max(0,nr-65)),min(102,max(0,nc-65)),min(65,nr),min(65,nc),12)]:
        panel=bg.crop((c*5,r*5,(c+w)*5,(r+h)*5)).resize((w*scale,h*scale),Image.Resampling.BICUBIC)
        panels=[]
        for lines in (raw,out):
            overlay=Image.new('RGBA',panel.size);d=ImageDraw.Draw(overlay)
            for p,ids in zip(lines,paths):
                a=float(area[ids[0]]);wid=3 if a>=200 else 2 if a>=60 else 1
                d.line([((xx-x[0]-c+.5)*scale,(y[0]-yy-r+.5)*scale) for xx,yy in p],fill=(25,78,137,220 if wid==3 else 170),width=wid,joint='curve')
            panels.append(Image.alpha_composite(panel.convert('RGBA'),overlay).convert('RGB'))
        pw,ph=panel.size;board=Image.new('RGB',(2*pw+90,ph+125),(240,237,227));d=ImageDraw.Draw(board)
        d.text((25,12),'ОСВЕРА / P4-K — ГЕНЕРАЛИЗАЦИЯ УЧАСТКОВ СЕТИ',font=font(22),fill=(40,48,47))
        d.text((25,47),'Оригинал',font=font(17),fill=(40,48,47));d.text((pw+50,47),'Семантические участки, коридор 750 м',font=font(17),fill=(40,48,47))
        board.paste(panels[0],(25,75));board.paste(panels[1],(pw+50,75));d.text((25,ph+88),'Модельные каналы, не подтверждённые реки. Одинаковая подложка и стиль.',font=font(15),fill=(74,64,60))
        board.save(dest/f'p4k-{label}.png')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('projection','child','background','prior','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prior=json.loads(a.prior.read_text())
    if prior.get('status')!='P4_J_TOPOLOGY_PRESERVING_DISPLAY_GEOMETRY_ONLY_NOT_RIVERS' or prior.get('channel_graph_topology_mutated') is not False or prior.get('is_approved_river_geometry') is not False:raise ValueError('bad prior provenance')
    sources={'baseline_projection_npz':a.projection,'baseline_child_npz':a.child,'terrain_p4e_png':a.background}
    if any(sha(v)!=prior['source_sha256'].get(k) for k,v in sources.items()):raise ValueError('source SHA mismatch')
    f=load_npz(a.projection);c=load_npz(a.child);paths,fixed,raw,out,r=process(f,c)
    a.output.mkdir(parents=True,exist_ok=False);render(f,c,raw,out,paths,a.background,a.output)
    np.savez_compressed(a.output/'p4k-display-reaches.npz',source_nodes=np.concatenate(paths),source_offsets=np.r_[0,np.cumsum([len(p) for p in paths])],display_xy_km=np.concatenate(out),display_offsets=np.r_[0,np.cumsum([len(p) for p in out])],fixed_nodes=fixed)
    r['source_sha256']={k:sha(v) for k,v in sources.items()};r['source_sha256']['p4j_audit']=sha(a.prior);r['derived_sha256']={v.name:sha(v) for v in sorted(a.output.iterdir())}
    (a.output/'p4k-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

if __name__=='__main__':main()
