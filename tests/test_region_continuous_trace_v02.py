"""Public tests: P4-N target semantics and actual accepted Core trace."""
from types import SimpleNamespace as NS
import numpy as np
import pytest
from domain_generator.grid import GridAdapter
from domain_generator.hydrology.continuous import continuous_routing_field,_trace_continuous
from scripts.audit_region_continuous_trace_v02 import classify,audit
from scripts.condition_planetary_child_terrain_v02 import ChildTerrainSettings,generate_child
from scripts.compare_planetary_child_mfd_outlets_v02 import connected_mfd_channel_projection


def test_actual_core_confluence_and_boundary():
    a=GridAdapter(5.,5.,.5,10,10);z=np.tile(np.arange(10,0,-1,dtype=float),(10,1));f=continuous_routing_field(z,cell_size_km=.5);start=(5,2)
    def trace(targets):return _trace_continuous(adapter=a,field=f,accumulation=np.ones(z.shape),start_position=a.cell_center(*start),start_cell=start,confluence_cells=targets,lake_by_cell={})
    c=trace({(5,6)});assert classify(c.terminal,(5,6),a,False)==('matched_target_cell',(5,6));assert (c.terminal.position.x_km,c.terminal.position.y_km)==(a.cell_center(5,6).x_km,a.cell_center(5,6).y_km)
    assert classify(c.terminal,(5,7),a,False)[0]=='wrong_target_cell'
    o=trace(set());assert classify(o.terminal,(5,9),a,True)==('matched_target_cell',(5,9));assert o.terminal.position.x_km==a.width_km
    assert (o.terminal.position.x_km,o.terminal.position.y_km)!=(a.cell_center(5,9).x_km,a.cell_center(5,9).y_km)
    assert classify(o.terminal,(5,6),a,False)[0]=='wrong_terminal_kind'


def test_lake_is_not_ordinary_terminal():
    assert classify(NS(kind='lake_inflow'),(1,1),None,False)==('other_terminal',None)


def test_synthetic_full_replay_and_immutability():
    lat=np.arange(36.,-37.,-12.);lon=np.arange(-36.,37.,12.);yy,xx=np.meshgrid(lat,lon,indexing='ij');z=(400+4*xx+2*yy+3*np.sin(yy/12)*np.cos(xx/12)).astype(np.float32)
    m={'latitude_deg_north_first':lat,'longitude_deg_west_to_east':lon,'elevation_m':z,'land_mask':np.ones(z.shape,np.uint8),'source_river_mask_D8':np.zeros(z.shape,np.uint8),'local_downstream_index':np.full(z.shape,-1,np.int32),'source_catchment_km2_D8':np.ones(z.shape,np.float32)}
    s=ChildTerrainSettings(center_lat_deg=0.,center_lon_deg=0.,half_width_km=24.,half_height_km=24.,spacing_km=.5,planet_radius_km=180/np.pi,planetary_year_earth_days=200.,seed=1406,relief_strength=2.,detail_coordinate_system='spherical_xyz_v1')
    c,meta=generate_child(m,s);f,_=connected_mfd_channel_projection(c,m,meta,stream_threshold_km2=30.);original={k:v.copy() for k,v in f.items()};r,rows,paths,raw,curves=audit(c,m,meta,f)
    assert r['source_projection_exact_replay'] and not r['approved_geography'];assert sum(r['counts'].values())==len(paths)==len(rows)==len(curves)
    assert sum(len(p)-1 for p in paths)==len(f['channel_edge_flat_from_to']);assert r['tested_reaches']>0
    for k in f:np.testing.assert_array_equal(f[k],original[k])
    f['channel_mask'].flat[0]^=1
    with pytest.raises(ValueError,match='replay mismatch'):audit(c,m,meta,f)
