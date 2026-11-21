"""P4-C2 toy-only tests: avoid claiming hydrology or importing macro A8 area."""

import copy
import json

import numpy as np
from PIL import Image
import pytest

from scripts.audit_region_corridor_sensitivity_v02 import (
    CorridorSensitivityError, audit_route_sensitivity, render_map,
)


def toy():
    z=np.full((3,7),50.,dtype=np.float64)
    z[1]=[10,9,8,9,11,12,11]
    fill=np.zeros_like(z)
    fill[1,2:4]=3.
    n=z.shape[1]
    route=[(n+i,n+i+1,"safe" if i in (0,5) else "withheld") for i in range(6)]
    strict={(a,b) for a,b,t in route if t=="safe"}
    hidden={(a,b) for a,b,t in route if t=="withheld"}
    return z,fill,route,strict,hidden,set()


def test_at_baseline_partition_scenario_and_no_model_mutation():
    z,fill,route,strict,hidden,proxy=toy()
    z0=z.copy();f0=fill.copy();old_route=copy.deepcopy(route)
    report,edges=audit_route_sensitivity(z,fill,route,strict,hidden,proxy,
        thresholds=(0,2,5,10))
    assert report["edge_count"]==6
    counts=report["baseline_fill_reasons"]["reason_counts"]
    assert counts=={"strict":2,"fill_only":1,"uphill_or_flat_only":1,"both":2,"proxy":0}
    scenarios=report["scenario_thresholds"]
    assert [item["eligible_original_dem_downhill_edges"] for item in scenarios]==[2,2,3,3]
    assert all(not item["reason_counts"]["proxy"] for item in scenarios)
    assert report["raw_uphill_or_flat_irreducible_edges"]==3
    assert not report["strict_continuous_raw_dem_route_proved"]
    assert np.array_equal(z,z0) and np.array_equal(fill,f0) and route==old_route
    assert [item["reason_baseline"] for item in edges]==[
       "strict","virtual_fill_over_baseline",
       "raw_uphill_or_flat+virtual_fill_over_baseline",
       "raw_uphill_or_flat+virtual_fill_over_baseline",
       "raw_uphill_or_flat","strict"]


def test_fill_threshold_does_not_promote_any_raw_uphill():
    args=toy()
    r,_=audit_route_sensitivity(*args,thresholds=(0,2,5,20,100))
    assert r["scenario_thresholds"][-1]["eligible_original_dem_downhill_edges"]==3
    assert r["scenario_thresholds"][-1]["withheld_edges"]==3
    assert r["scenario_thresholds"][-1]["reason_counts"]["uphill_or_flat_only"]==3
    assert r["baseline_fill_reasons"]["eligible_original_dem_downhill_edges"]==2


@pytest.mark.parametrize("bad",[
    "missing_baseline", "negative", "duplicate", "unsorted", "inf",
    "wrong_baseline_tag", "replaced_edge", "disconnected", "nan_z", "bad_fill",
    "zero_spacing", "bad_proxy",
])
def test_fail_closed_when_route_or_threshold_is_unverifiable(bad):
    z,fill,route,strict,hidden,proxy=toy()
    kw={"thresholds":(0,2,10)}
    if bad=="missing_baseline":kw["thresholds"]=(0,1,5)
    elif bad=="negative":kw["thresholds"]=(-1,2)
    elif bad=="duplicate":kw["thresholds"]=(2,2)
    elif bad=="unsorted":kw["thresholds"]=(2,1)
    elif bad=="inf":kw["thresholds"]=(2,float('inf'))
    elif bad=="wrong_baseline_tag":route[0]=(route[0][0],route[0][1],"withheld")
    elif bad=="replaced_edge":strict.clear()
    elif bad=="disconnected":route[3]=(route[3][0]+1,route[3][1],route[3][2])
    elif bad=="nan_z":z[0,0]=float('nan')
    elif bad=="bad_fill":fill[1,0]=-10
    elif bad=="zero_spacing":kw["spacing_km"]=0
    elif bad=="bad_proxy":route[0]=(route[0][0],route[0][1],"proxy")
    with pytest.raises(CorridorSensitivityError):
        audit_route_sensitivity(z,fill,route,strict,hidden,proxy,**kw)


def test_proxy_never_becomes_water_or_downhill_proof():
    z=np.array([[10,9,8,7],[10,9,8,7],[10,9,8,7]],float)
    fill=np.zeros_like(z)
    route=[(4,5,"safe"),(5,6,"proxy"),(6,7,"safe")]
    r,rows=audit_route_sensitivity(z,fill,route,{(4,5),(6,7)},set(),{(5,6)},
                                    thresholds=(0,2,10))
    assert r["routing_proxy_edges_NOT_WATER"]==1
    assert r["scenario_thresholds"][-1]["withheld_edges"]==1
    assert not r["strict_continuous_raw_dem_route_proved"]


def test_empty_route_remains_explicitly_unresolved():
    z=np.ones((3,3),float);fill=np.zeros_like(z)
    report,_=audit_route_sensitivity(z,fill,[],set(),set(),set())
    assert report["edge_count"]==0
    assert report["scenario_thresholds"][-1]["eligible_original_dem_downhill_edges"]==0
    assert not report["strict_continuous_raw_dem_route_proved"]


def test_map_uses_distinct_failure_colors_and_zero_water_claim(tmp_path):
    z,fill,route,strict,hidden,proxy=toy()
    result,edges=audit_route_sensitivity(z,fill,route,strict,hidden,proxy)
    child={"child_elevation_m":z}
    raw=Image.new("RGB",(7*20,3*20),(81,110,83))
    render_map(raw,child,edges,{"per_route":[result]},tmp_path/"preview")
    assert (tmp_path/"preview/corridor-sensitivity-sheet.png").exists()
    with Image.open(tmp_path/"preview/corridor-sensitivity-base.png") as im:
        assert im.size==raw.size
        assert np.any(np.asarray(im)!=np.asarray(raw))
    with pytest.raises(FileExistsError):
        render_map(raw,child,edges,{"per_route":[result]},tmp_path/"preview")
