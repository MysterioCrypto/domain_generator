from __future__ import annotations

"""P4-J: bounded G1-continuous display curves on a FROZEN 1-receiver channel graph.

No accepted terrain, MFD fractions, area, water, outlets or channel graph altered.
Source grid-node positions are passed through EXACTLY; lines are an optional
cartographic representation of the original model (NOT approved rivers).
"""

import argparse
from hashlib import file_digest
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree


class GeometryDisplayError(ValueError):
    pass

SAMPLES_PER_EDGE = 9
MAX_OFFSET_KM = 0.20
TANGENT_FACTOR = 0.95


def _sha(path: Path) -> str:
    with path.open('rb') as f:
        return file_digest(f,'sha256').hexdigest()


def _read(path:Path) ->dict:
    with np.load(path,allow_pickle=False) as src:
        return {key:src[key].copy() for key in src.files}


def _font(n):
    for fn in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
               '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(fn).is_file():return ImageFont.truetype(fn,n)
    return ImageFont.load_default()


def _unit(v):
    length=float(np.hypot(v[0],v[1]))
    if length<1e-14:raise GeometryDisplayError('zero vector tangent')
    return np.asarray(v,dtype=np.float64)/length


def _check_graph(fields:dict,axis_x:np.ndarray,axis_y:np.ndarray):
    if not {'channel_mask','channel_edge_flat_from_to','lake_proxy_jumps_flat_from_to','Core_dominant_receiver_index'}<=set(fields):
        raise GeometryDisplayError('noncanonical graph fields missing')
    mask=np.asarray(fields['channel_mask']);edges=np.asarray(fields['channel_edge_flat_from_to'])
    proxy=np.asarray(fields['lake_proxy_jumps_flat_from_to']);rec=np.asarray(fields['Core_dominant_receiver_index'])
    if (mask.ndim!=2 or min(mask.shape)<3 or edges.ndim!=2 or edges.shape[1]!=2 or
        not np.issubdtype(edges.dtype,np.integer) or not len(edges) or
        proxy.shape!=(0,2) or rec.shape!=mask.shape):
        raise GeometryDisplayError('invalid ordinary graph or unsupported lake proxy hops')
    nr,nc=mask.shape;N=nr*nc
    src,dst=edges[:,0],edges[:,1]
    if (np.any(edges<0) or np.any(edges>=N) or len(np.unique(src))!=len(src) or
        not np.all(mask.ravel()[src]) or not np.all(mask.ravel()[dst])):
        raise GeometryDisplayError('invalid edge IDs, masks or duplicate outgoing edge')
    dr=dst//nc-src//nc;dc=dst%nc-src%nc
    if np.any(np.maximum(np.abs(dr),np.abs(dc))!=1):
        raise GeometryDisplayError('non-adjacent edge in model channel')
    if not np.all(rec.ravel()[src]==dst):
        raise GeometryDisplayError('graph differs from accepted dominant receiver field')
    ax=np.asarray(axis_x,float);ay=np.asarray(axis_y,float)
    if (ax.shape!=(nc,) or ay.shape!=(nr,) or not np.isfinite(ax).all() or not np.isfinite(ay).all()
        or np.any(np.diff(ax)<=0) or np.any(np.diff(ay)>=0)
        or not np.allclose(np.diff(ax),np.diff(ax)[0],rtol=0,atol=1e-9)
        or not np.allclose(np.diff(ay),np.diff(ay)[0],rtol=0,atol=1e-9)
        or not np.isclose(np.diff(ax)[0],-np.diff(ay)[0],rtol=0,atol=1e-9)):
        raise GeometryDisplayError('bad square metric child grid')
    # Full cycle rejection including heading-changing cycles (topological validity).
    next_at=np.full(N,-1,dtype=np.int32);next_at[src]=np.arange(len(src),dtype=np.int32)
    state=np.zeros(len(src),dtype=np.uint8)
    for first in range(len(src)):
        if state[first]:continue
        walk=[];cursor=first
        while cursor>=0 and state[cursor]==0:
            state[cursor]=1;walk.append(cursor);cursor=int(next_at[dst[cursor]])
        if cursor>=0 and state[cursor]==1:raise GeometryDisplayError('directed cycle in graph')
        state[walk]=2
    return mask,edges,next_at,float(np.diff(ax)[0])


def _crossings(edges:np.ndarray, polylines:np.ndarray):
    # A pair of edges meeting at an existing common graph node is permitted only
    # to meet at exactly that known endpoint. Independent edges may not cross.
    geometry=[LineString(p) for p in polylines]
    tree=STRtree(geometry)
    ia,ib=tree.query(geometry,predicate='intersects')
    invalid=set()
    for i,j in zip(ia.tolist(),ib.tolist()):
        if j<=i:continue
        common=set(edges[i])&set(edges[j])
        if not common:
            invalid.add((i,j));continue
        intersection=geometry[i].intersection(geometry[j])
        if intersection.is_empty:continue
        shared=[]
        for node in common:
            if node==edges[i,0]:shared.append(polylines[i,0]);
            else:shared.append(polylines[i,-1])
        if intersection.geom_type=='Point':
            valid=any(intersection.distance(Point(p))<1e-8 for p in shared)
        elif intersection.geom_type=='MultiPoint':
            valid=all(any(pt.distance(Point(p))<1e-8 for p in shared) for pt in intersection.geoms)
        else:valid=False
        if not valid:invalid.add((i,j))
    return invalid


def generalize_model_edges(fields:dict,axis_x:np.ndarray,axis_y:np.ndarray,
                           *, max_offset_km=MAX_OFFSET_KM, tangent_factor=TANGENT_FACTOR):
    if not (0<max_offset_km<=.25 and 0<tangent_factor<=1.0):
        raise GeometryDisplayError('bounded display-only parameters required')
    mask,edges,out_at,spacing=_check_graph(fields,axis_x,axis_y)
    nr,nc=mask.shape;N=nr*nc;src,dst=edges[:,0],edges[:,1]
    in_degree=np.bincount(dst,minlength=N)
    in_edge=np.full(N,-1,dtype=np.int32)
    for idx,target in enumerate(dst):
        if in_degree[target]==1:in_edge[target]=idx
    # Work in geographic XY km, NOT image raster Y-down.
    centers=np.empty((N,2),dtype=np.float64)
    rr,cc=np.indices(mask.shape)
    centers[:,0]=np.asarray(axis_x)[cc.ravel()]
    centers[:,1]=np.asarray(axis_y)[rr.ravel()]
    endpoints=np.stack([centers[src],centers[dst]],axis=1)
    params=np.linspace(0,1,SAMPLES_PER_EDGE)
    result=np.zeros((len(edges),SAMPLES_PER_EDGE,2),dtype=np.float64)
    source_line=np.stack([endpoints[:,0,:],endpoints[:,1,:]],axis=1)
    displaced=[];straightened=0
    for k,(a,b) in enumerate(edges):
        p0,p1=endpoints[k];step=p1-p0;length=float(np.linalg.norm(step));u=_unit(step)
        previous=int(in_edge[a]);follower=int(out_at[b])
        t0=(_unit(_unit(p0-centers[edges[previous,0]])+u)
            if in_degree[a]==1 and previous>=0 else u)
        t1=(_unit(u+_unit(centers[edges[follower,1]]-p1))
            if in_degree[b]==1 and follower>=0 else u)
        m0=tangent_factor*length*t0;m1=tangent_factor*length*t1
        tt=params[:,None]
        poly=((2*tt**3-3*tt**2+1)*p0+(tt**3-2*tt**2+tt)*m0+
              (-2*tt**3+3*tt**2)*p1+(tt**3-tt**2)*m1)
        poly[0]=p0;poly[-1]=p1
        result[k]=poly
        original=LineString([p0,p1]);curved=LineString(poly)
        offset=curved.hausdorff_distance(original)
        if offset>max_offset_km+1e-8:
            raise GeometryDisplayError('display curve exceeds maximum geometric deviation')
        displaced.append(float(offset))
        if offset<1e-8:straightened+=1
    if not np.array_equal(result[:,0],endpoints[:,0]) or not np.array_equal(result[:,-1],endpoints[:,1]):
        raise GeometryDisplayError('source graph node position moved')
    before=_crossings(edges,source_line)
    after=_crossings(edges,result)
    if before or after:
        raise GeometryDisplayError(f'graph crosses between unrelated segments: old={len(before)},new={len(after)}')
    if not np.isfinite(result).all():raise GeometryDisplayError('nonfinite display coordinate')
    offsets=np.asarray(displaced)
    summary={'status':'P4_J_TOPOLOGY_PRESERVING_DISPLAY_GEOMETRY_ONLY_NOT_RIVERS',
             'source_edge_count':len(edges),'source_node_count':int(len(np.unique(edges))),
             'source_model_channel_mask_cells':int(mask.sum()),
             'original_node_ids_and_edge_order_preserved':True,
             'all_original_node_positions_exact':True,
             'channel_graph_topology_mutated':False,'is_approved_river_geometry':False,
             'metric_grid_spacing_km':spacing,
             'curve_subdivision_points_per_source_edge':SAMPLES_PER_EDGE,
             'max_allowed_hausdorff_offset_km':max_offset_km,
             'maximum_hausdorff_offset_km':float(offsets.max()),
             'p95_hausdorff_offset_km':float(np.percentile(offsets,95)),
             'mean_hausdorff_offset_km':float(offsets.mean()),
             'edges_with_geometric_change_gt_0p02_km':int(np.count_nonzero(offsets>.02)),
             'straight_edge_count_eps_1e_minus8':straightened,
             'independent_original_crossing_count':len(before),
             'independent_display_crossing_count':len(after),
             'lake_proxy_jumps_drawn_as_rivers':False,
             'original_and_derived_endpoints_identical':True,
             'display_algorithm':'local Hermite cubic with G1 node tangents, constant per-edge factor, no topological rewrite',
             'limitation':'all 1-km raster nodes are fixed; this only softens joins and cannot fix long grid-aligned chains or physical water semantics'}
    return result,summary


def _choose_review_crop(polylines:np.ndarray,edges:np.ndarray,shape:tuple[int,int],window=65):
    nr,nc=shape;window=min(window,nr,nc);h=np.zeros(shape,dtype=np.int32)
    mids=polylines[:,SAMPLES_PER_EDGE//2]
    p0=polylines[:,0];p1=polylines[:,-1];t=(p0+p1)/2
    dev=np.linalg.norm(mids-t,axis=1)
    h[np.clip(edges[:,0]//nc,0,nr-1),np.clip(edges[:,0]%nc,0,nc-1)]+=(dev>.01).astype(np.int32)
    cum=np.pad(h,((1,0),(1,0))).cumsum(axis=0).cumsum(axis=1)
    sums=cum[window:,window:]-cum[:-window,window:]-cum[window:,:-window]+cum[:-window,:-window]
    r,c=np.unravel_index(np.argmax(sums),sums.shape)
    return [int(r),int(c),int(window),int(window)]


def _render_map(background:Image.Image, fields:dict,xy:np.ndarray,origin:np.ndarray,
                *,region:tuple[int,int,int,int],ppu:int, curved:bool):
    r0,c0,hh,ww=region;rows,cols=fields['channel_mask'].shape
    crop=background.crop((c0*5,r0*5,(c0+ww)*5,(r0+hh)*5))
    image=crop.resize((ww*ppu,hh*ppu),Image.Resampling.BICUBIC).convert('RGBA')
    paint=Image.new('RGBA',image.size,(0,0,0,0));draw=ImageDraw.Draw(paint)
    areas=fields['Core_dominant_channel_area_km2_NOT_Q'].ravel();edges=fields['channel_edge_flat_from_to']
    # Physical XY N+ axes mapped back to raster by fixed origin.
    for i,(a,b) in enumerate(edges):
        a=int(a);p=xy[i] if curved else xy[i,::SAMPLES_PER_EDGE-1]
        points=[((x-origin[0]-c0+.5)*ppu,(origin[1]-y-r0+.5)*ppu) for x,y in p]
        area=float(areas[a]);width=3 if area>=200 else (2 if area>=60 else 1)
        opacity=228 if area>=200 else 168
        draw.line(points,fill=(31,80,140,opacity),width=width,joint='curve')
    return Image.alpha_composite(image,paint).convert('RGB')


def render_comparison(fields:dict,xy:np.ndarray,report:dict,background_path:Path,output:Path):
    if output.exists():raise GeometryDisplayError('output exists; refuse overwrite')
    mask=fields['channel_mask'];nr,nc=mask.shape
    with Image.open(background_path) as bg:
        backdrop=bg.convert('RGB')
    expected=(nc*5,nr*5)
    if backdrop.size!=expected:
        # A known legacy P4-E SYNTHETIC exporter encoded a rectangular
        # (nr, nc) DEM as a square (nc*5, nc*5) PNG. This is a display-only
        # correction; numeric coordinates/graph are never resized or cropped.
        if nr!=nc and backdrop.size==(nc*5,nc*5):
            backdrop=backdrop.resize(expected,Image.Resampling.BICUBIC)
        else:
            raise GeometryDisplayError('unverified P4-E source background dimensions')
    # region crop comes from shape-only displacement density; deterministic.
    edges=fields['channel_edge_flat_from_to'];box=_choose_review_crop(xy,edges,mask.shape)
    report['zoom_crop_top_left_row_col_height_width']=box
    origin=np.asarray(report['origin_xy_km'],float)
    for mode in ('overview','zoom'):
        review=mode=='zoom';region=tuple(box if review else (0,0,nr,nc));ppu=10 if review else 5
        panel1=_render_map(backdrop,fields,xy,origin,region=region,ppu=ppu,curved=False)
        panel2=_render_map(backdrop,fields,xy,origin,region=region,ppu=ppu,curved=True)
        pad=44;gap=22;header=110;footer=82;pw,ph=panel1.size
        image=Image.new('RGB',(2*pw+2*pad+gap,ph+header+footer),(235,232,223));d=ImageDraw.Draw(image)
        d.text((pad,13),'ОСВЕРА / P4-J — НЕИЗМЕННАЯ СЕТЬ, ДВА СПОСОБА ОТРИСОВКИ',font=_font(29),fill=(48,52,49))
        d.text((pad,52),f'{"Фрагмент " + str(box) if review else "Регион A"} • исходная 1-receiver модель 2.0 / порог 30 км²',font=_font(19),fill=(56,62,55))
        for idx,im in enumerate((panel1,panel2)):
            x=pad+idx*(pw+gap);image.paste(im,(x,header))
            d.rectangle((x,header,x+pw-1,header+ph-1),outline=(100,103,91),width=2)
            label='Оригинал: отрезки между узлами' if idx==0 else 'G1-кривые: те же узлы, рёбра и выходы'
            d.text((x,header+ph+15),label,font=_font(20),fill=(52,57,53))
        d.text((pad,header+ph+53),'Только отображение модельных каналов; не принятые природные реки. Фон P4-E без изменений.',font=_font(16),fill=(87,70,67))
        output.mkdir(parents=True,exist_ok=True)
        image.save(output/f'p4j-{mode}-original-vs-bounded-curves.png',compress_level=3)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline-projection-npz','baseline-child-npz','p4i-audit-json','terrain-png'):
        cli.add_argument('--'+name,required=True,type=Path)
    cli.add_argument('--output',required=True,type=Path)
    a=cli.parse_args()
    if a.output.exists():raise GeometryDisplayError('output already exists')
    previous=json.loads(a.p4i_audit_json.read_text('utf8'))
    if (previous.get('status')!='P4_I_HERMITE_VS_BILINEAR_PARENT_ANCHOR_CONTROL_NOT_RIVERS'
        or previous.get('not_author_accepted_geography_or_rivers') is not True
        or previous.get('P4F_archived_3_original_model_fields_exact_replay') is not True
        or previous.get('accepted_Core_changed') is not False):
        raise GeometryDisplayError('unverified P4-I source provenance')
    for k,p in [('baseline_projection_npz',a.baseline_projection_npz),('baseline_child_npz',a.baseline_child_npz)]:
        if _sha(p)!=previous.get('source_sha256',{}).get(k):
            raise GeometryDisplayError('P4-I SHA mismatch: '+k)
    fields=_read(a.baseline_projection_npz);child=_read(a.baseline_child_npz)
    xy,summary=generalize_model_edges(fields,child['east_km'],child['north_km_north_first'])
    summary['model_terrain_relief_strength']=2.0
    summary['source_stream_threshold_km2_NOT_Q']=30.0
    summary['original_P4B_projection_sha256_verified']=True
    summary['P4I_provenance_file_sha256']=_sha(a.p4i_audit_json)
    summary['origin_xy_km']=[float(child['east_km'][0]),float(child['north_km_north_first'][0])]
    summary['derived_geometry_units']='kilometers east/north, raster row 0 north'
    summary['P4I_original_and_private_geometry_remain_unchanged']=True
    render_comparison(fields,xy,summary,a.terrain_png,a.output)
    np.savez_compressed(a.output/'p4j-display-only-channel-curves.npz',
       source_target_flat=fields['channel_edge_flat_from_to'],polyline_xy_km=xy,
       original_raster_grid_shape=np.array(fields['channel_mask'].shape,dtype=np.int32))
    summary['source_sha256']={'baseline_projection_npz':_sha(a.baseline_projection_npz),
                              'baseline_child_npz':_sha(a.baseline_child_npz),
                              'p4i_audit_json':_sha(a.p4i_audit_json),'terrain_p4e_png':_sha(a.terrain_png)}
    summary['derived_sha256']={f.name:_sha(f) for f in sorted(a.output.iterdir())}
    (a.output/'p4j-display-geometry-audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
