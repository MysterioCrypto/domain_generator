"""P4-N: diagnostic comparison of unmodified Core traces and frozen ordinary reaches."""
import argparse, hashlib, json
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import LineString
from domain_generator.grid import GridAdapter
from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.continuous import continuous_routing_field, _trace_continuous
from domain_generator.hydrology.routing import priority_flood_surfaces, HydrologyCapabilityError
from domain_generator.hydrology.ids import lake_feature_id
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection
from scripts.generalize_semantic_channel_reaches_v02 import split_reaches


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    with np.load(p,allow_pickle=False) as a:return {k:a[k].copy() for k in a.files}


def classify(t,target,a,edge):
    if t.kind=='confluence':actual=t.anchor_cell
    elif t.kind=='domain_outlet':actual=a.containing_cell(t.position.x_km,t.position.y_km)
    else:return 'other_terminal',None
    if t.kind!=('domain_outlet' if edge else 'confluence'):return 'wrong_terminal_kind',actual
    return ('matched_target_cell' if actual==target else 'wrong_target_cell'),actual


def audit(c,macro,meta,f):
    z=c['child_elevation_m'];nr,nc=z.shape
    if not np.all(c['land_mask']) or not np.all(np.diff(c['east_km'])==.5) or not np.all(np.diff(c['north_km_north_first'])==-.5):raise ValueError('inland 500m only')
    replay,_=connected_mfd_channel_projection(c,macro,meta,stream_threshold_km2=30.)
    if set(f)!=set(replay) or any(not np.array_equal(f[k],replay[k]) for k in f):raise ValueError('frozen projection replay mismatch')
    a=GridAdapter(nc*.5,nr*.5,.5,nr,nc);surface=priority_flood_surfaces(z.astype(float));field=continuous_routing_field(surface.routing_elevation_m,cell_size_km=.5)
    lakes=extract_lake_candidates(z.astype(float),surface.fill_elevation_m,cell_size_km=.5,lake_min_area_km2=16.,lake_min_depth_m=10.)
    lake_cells={cell:lake_feature_id(i) for i,lake in enumerate(lakes) for cell in lake.cells}
    if any(divmod(int(i),nc) not in lake_cells for i in np.flatnonzero(f['lake_proxy_mask'])):raise ValueError('lake support mismatch')
    e=f['channel_edge_flat_from_to'];paths,_=split_reaches(e,z.shape);proxy=set(np.unique(f['lake_proxy_jumps_flat_from_to']).tolist());inc=np.bincount(e[:,1],minlength=nr*nc)
    confluences={divmod(int(i),nc) for i in np.flatnonzero(inc>1)}
    rows=[];raw=[];curves=[]
    for p in paths:
        xy=np.column_stack(((p%nc+.5)*.5,a.height_km-(p//nc+.5)*.5));raw.append(xy);curve=np.empty((0,2));start,end=divmod(int(p[0]),nc),divmod(int(p[-1]),nc);edge=end[0] in (0,nr-1) or end[1] in (0,nc-1)
        row={'start':int(p[0]),'expected_end':int(p[-1]),'expected_kind':'domain_outlet' if edge else 'confluence','ordinary_edges':len(p)-1}
        if proxy.intersection(p.tolist()):row['status']='excluded_proxy_contact'
        elif not edge and end not in confluences:raise ValueError('unexpected nonproxy terminal')
        else:
            try:
                t=_trace_continuous(adapter=a,field=field,accumulation=f['MFD_contributing_area_km2_NOT_Q'],start_position=a.cell_center(*start),start_cell=start,confluence_cells=confluences-{start},lake_by_cell=lake_cells)
                curve=np.array([(v.x_km,v.y_km) for v in t.points]);status,actual=classify(t.terminal,end,a,edge)
                row.update(status=status,actual_end=list(actual) if actual is not None else None,terminal_kind=t.terminal.kind,hausdorff_km=float(LineString(xy).hausdorff_distance(LineString(curve))),end_offset_km=float(np.linalg.norm(curve[-1]-xy[-1])),is_simple=bool(LineString(curve).is_simple))
            except HydrologyCapabilityError as exc:row.update(status='trace_error',error=str(exc))
        rows.append(row);curves.append(curve)
    counts=Counter(r['status'] for r in rows);tested=len(rows)-counts['excluded_proxy_contact'];matched=[r for r in rows if r['status']=='matched_target_cell'];con=[r for r in rows if r['expected_kind']=='confluence' and r['status']!='excluded_proxy_contact'];out=[r for r in rows if r['expected_kind']=='domain_outlet' and r['status']!='excluded_proxy_contact']
    report={'status':'P4_N_CORE_TRACE_TARGET_COMPATIBILITY_DIAGNOSTIC_NOT_RIVERS','source_projection_exact_replay':True,'source_edges':len(e),'ordinary_reaches':len(paths),'proxy_links_not_drawn':len(f['lake_proxy_jumps_flat_from_to']),'full_candidate_lake_cells':len(lake_cells),'counts':dict(sorted(counts.items())),'tested_reaches':tested,'matched_fraction':len(matched)/tested,'confluence_targets':len(con),'confluence_matches':sum(r['status']=='matched_target_cell' for r in con),'boundary_targets':len(out),'boundary_matches':sum(r['status']=='matched_target_cell' for r in out),'matched_max_hausdorff_km':max((r['hausdorff_km'] for r in matched),default=None),'matched_median_hausdorff_km':float(np.median([r['hausdorff_km'] for r in matched])) if matched else None,'matched_non_simple':sum(not r['is_simple'] for r in matched),'matched_end_coordinate_exact':sum(r['end_offset_km']<=1e-9 for r in matched),'errors':dict(Counter(r.get('error','') for r in rows if r['status']=='trace_error')),'all_tested_target_cells_preserved':counts['matched_target_cell']==tested,'approved_geography':False,'accepted_core_changed':False,'limitations':['independent reach traces, not an assembled network','boundary cell match is not exact node position: outer cell face versus archived center','no snapping or false-confluence normalization','lake-contact reaches excluded; candidate lake cell support used for termination; no proxy links drawn']}
    return report,rows,paths,raw,curves


def render(raw,curves,rows,shape,out):
    nr,nc=shape;w=1150;h=round(w*nr/nc);pad=24;gap=20;top=92;board=Image.new('RGB',(2*w+2*pad+gap,h+top+92),'#f4f1e8');d=ImageDraw.Draw(board)
    def font(n):
        try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
        except OSError:return ImageFont.load_default()
    d.text((pad,12),'OSVERA / P4-N — CORE STREAMLINE TARGET AUDIT',font=font(25),fill='#25332c')
    d.text((pad,53),'Frozen ordinary graph (500 m)',font=font(19),fill='#25332c');d.text((pad+w+gap,53),'Unmodified Core trace: match / mismatch',font=font(19),fill='#25332c')
    for j in range(2):
        im=Image.new('RGB',(w,h),'#e8e8d9');draw=ImageDraw.Draw(im)
        for i,row in enumerate(rows):
            p=raw[i] if j==0 else curves[i]
            if len(p)<2:continue
            color='#386d91' if j==0 or row['status']=='matched_target_cell' else '#c56b32'
            draw.line([(x/(nc*.5)*(w-1),(1-y/(nr*.5))*(h-1)) for x,y in p],fill=color,width=1)
        board.paste(im,(pad+j*(w+gap),top))
    d.text((pad,top+h+12),'Blue: same target cell. Orange: different terminal. Missing: failed / proxy-contact excluded.',font=font(18),fill='#25332c');d.text((pad,top+h+45),'Diagnostic traces only; not an assembled network, no lake proxy connections drawn.',font=font(18),fill='#25332c');board.save(out/'p4n-trace-target-audit.png')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('macro','child','manifest','projection','prior','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();prior=json.loads(a.prior.read_text());names={'child':'p4m-fine-terrain.npz','manifest':'p4m-fine-manifest.json','projection':'p4m-fine-projection.npz'}
    if prior.get('status')!='P4_M_NESTED_SAME_ANALYTIC_TERRAIN_RESOLUTION_NOT_RIVERS' or prior.get('approved_geography') is not False or sha(a.macro)!=prior['source_sha256']['macro'] or any(sha(getattr(a,k))!=prior['derived_sha256'][v] for k,v in names.items()):raise ValueError('P4-M SHA mismatch')
    if a.output.exists():raise ValueError('output exists')
    c=load(a.child);f=load(a.projection);r,rows,paths,raw,curves=audit(c,load(a.macro),json.loads(a.manifest.read_text()),f);a.output.mkdir(parents=True);render(raw,curves,rows,c['child_elevation_m'].shape,a.output)
    np.savez_compressed(a.output/'p4n-trace-candidates.npz',source_node_ids=np.concatenate(paths),source_offsets=np.r_[0,np.cumsum([len(p) for p in paths])],trace_xy_sw_km=np.concatenate(curves),trace_offsets=np.r_[0,np.cumsum([len(p) for p in curves])],origin_east_north_km=np.array([c['east_km'][0]-.25,c['north_km_north_first'][-1]-.25]));(a.output/'p4n-reaches.json').write_text(json.dumps(rows,indent=2)+'\n');r['source_sha256']={k:sha(getattr(a,k)) for k in ('macro','child','manifest','projection','prior')};r['derived_sha256']={v.name:sha(v) for v in sorted(a.output.iterdir())};(a.output/'p4n-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
