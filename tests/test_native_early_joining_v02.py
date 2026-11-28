"""Public P4-S regressions for opt-in native assembly and grid reconstruction."""
import numpy as np
import pytest
from domain_generator.grid import GridAdapter
from domain_generator.terrain.state import TerrainState
from domain_generator.hydrology.continuous import generate_hydrology_v02, validate_hydrology_v02, HydrologyCapabilityError
from domain_generator.hydrology.early_joining import traversed_geometry_cells, audit_network, terminals
from scripts.evaluate_imported_dem_native_network_v02 import make_plan


def surface(seed, lake=False):
    rr,cc=np.indices((61,61));rng=np.random.default_rng(seed)
    z=400-cc*1.5+sum(rng.uniform(1,8)*np.sin(rr*rng.uniform(.07,.45)+cc*rng.uniform(.07,.45)+rng.uniform(0,6)) for _ in range(8))
    if lake:z-=60*np.exp(-((rr-30)**2+(cc-30)**2)/90)
    return z


def test_cell_coverage_corner_boundary_and_long_line():
    a=GridAdapter(4.,4.,1.,4,4)
    assert traversed_geometry_cells(a,[(.5,.5),(3.5,3.5)])==((3,0),(2,1),(1,2),(0,3))
    assert traversed_geometry_cells(a,[(1.,.5),(1.,3.5)])==((3,1),(2,1),(1,1),(0,1))
    assert traversed_geometry_cells(a,[(.5,1.),(3.5,1.)])==((2,0),(2,1),(2,2),(2,3))
    assert traversed_geometry_cells(a,[(.5,.5),(4.,.5)])==((3,0),(3,1),(3,2),(3,3))
    assert traversed_geometry_cells(a,[(.5,.5),(.5,.5),(3.5,3.5)])==((3,0),(2,1),(1,2),(0,3))


@pytest.mark.parametrize('seed,lake',[(6,False),(0,True)])
def test_native_joining_reconstructs_properties_and_masks(seed,lake):
    z=surface(seed,lake);p=make_plan(z.shape);t=TerrainState(elevation_m=z.copy());a=GridAdapter.from_plan(p)
    old=generate_hydrology_v02(p,t,experimental_network_assembly=True)
    new=generate_hydrology_v02(p,t,experimental_network_assembly=True,experimental_early_joining=True)
    assert validate_hydrology_v02(p,t,new,attempt_index=0).engine_invariants.passed
    assert old.lake_outlets==new.lake_outlets and old.lake_features==new.lake_features
    np.testing.assert_array_equal(t.elevation_m,z)
    for k in ('routing_elevation_m','fill_elevation_m','flow_accumulation_km2','channel_skeleton_mask','potential_channel_skeleton_mask','channel_strahler_order'):
        np.testing.assert_array_equal(getattr(old,k),getattr(new,k))
    excluded={c for l in new.lake_candidates for c in l.cells}
    for i,(n0,n1) in enumerate(((old.river_network,new.river_network),(old.potential_river_network,new.potential_river_network))):
        r0=n0.model_dump(mode='json',by_alias=True);r1=n1.model_dump(mode='json',by_alias=True)
        if not lake and i==1:assert audit_network(r0)['defective_pairs']==1
        audit=audit_network(r1)
        assert audit['defective_pairs']==0 and not audit['degenerate_segment_ids']
        assert terminals(r0)==terminals(r1)
        mask=np.zeros(z.shape,bool)
        for s in n1.segments.values():
            cells=[c for c in traversed_geometry_cells(a,[(q.x_km,q.y_km) for q in s.centerline]) if c not in excluded]
            assert s.properties.catchment_area_km2==max(float(new.flow_accumulation_km2[c]) for c in cells)
            for c in cells:mask[c]=True
        if i==0:np.testing.assert_array_equal(mask,new.stream_mask)
    assert set(new.potential_segment_strahler_order)==set(new.potential_river_network.segments)
    assert min(new.potential_segment_strahler_order.values())>=1
    if lake:assert len(new.lake_candidates)==1


def test_opt_in_required_and_cross_target_fails_closed():
    z=surface(3);p=make_plan(z.shape);t=TerrainState(elevation_m=z)
    with pytest.raises(HydrologyCapabilityError,match='requires experimental network assembly'):
        generate_hydrology_v02(p,t,experimental_early_joining=True)
    with pytest.raises(HydrologyCapabilityError,match='cross-target'):
        generate_hydrology_v02(p,t,experimental_network_assembly=True,experimental_early_joining=True)
    # Earlier experimental mode remains available; failure does not mutate input.
    old=generate_hydrology_v02(p,t,experimental_network_assembly=True)
    assert validate_hydrology_v02(p,t,old,attempt_index=0).engine_invariants.passed


def test_legacy_mode_unchanged_by_explicit_false():
    z=surface(0);p=make_plan(z.shape);t=TerrainState(elevation_m=z)
    old=generate_hydrology_v02(p,t)
    new=generate_hydrology_v02(p,t,experimental_early_joining=False)
    assert old.river_network==new.river_network and old.potential_river_network==new.potential_river_network
    np.testing.assert_array_equal(old.stream_mask,new.stream_mask)
    np.testing.assert_array_equal(old.water_depth_m,new.water_depth_m)
