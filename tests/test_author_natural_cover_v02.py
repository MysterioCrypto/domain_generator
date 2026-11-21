"""P3-MVP natural-cover candidates are explicit editable hypotheses, never canon."""

import copy
import numpy as np
import pytest

from scripts.derive_author_natural_cover_v02 import (
    CoverEvidenceError, _defaults, classify_cover, render_preview,
)


def _fixture(*,north_first=False,wet=True):
    lat=np.linspace(-49,-45,13)
    lon=np.linspace(-99.1,-97.5,15)
    y,x=np.indices((13,15))
    scenario=np.where(x<=5,7,np.where(x>=11,6,8)).astype("uint8")
    moderate=scenario.copy()
    moderate[:,6:7]=7
    change=scenario.copy()
    change[:,5:7]=8
    source={
        "lat": lat, "lon": lon,
        "land":np.ones((13,15),dtype="uint8"),
        "biome_base":scenario,
        "biome_moderate":moderate,
        "biome_precip_minus20":change,
        "biome_precip_plus20":scenario.copy(),
        "stable4":(scenario==moderate).astype("uint8"),
        "wetland_candidate":np.where(y>=6,1 if wet else 0,0).astype("uint8"),
    }
    if north_first:
        source["lat"]=lat[::-1]
        for k,v in list(source.items()):
            if np.asarray(v).shape==(13,15):
                source[k]=v[::-1].copy()
    east=np.arange(-40.,41.)
    north=east[::-1]
    X,Y=np.meshgrid(east,north)
    # Low rolling relief but a steep scarp near the east edge.
    h=400+1.2*Y+2*np.sin(X/9)
    # A true LOCAL terrain bowl inside the coarse wetland-potential band.
    h-=26*np.exp(-((X+8)**2+(Y-18)**2)/65)
    h[:,60:]+=np.linspace(0,600,21)[None,:]
    child={
        "east_km":east,
        "north_km_north_first":north,
        "child_elevation_m":h.astype("float32"),
        "land_mask":np.ones(h.shape,dtype="uint8"),
    }
    manifest={
        "status":"NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData":False,
        "planet_radius_km":7008.1,
        "center_lat_lon_deg":[-47.25,-98.25],
    }
    return child,source,manifest


def test_visible_mosaic_with_open_woodland_and_sparse_classes():
    child,source,m=_fixture()
    out,report=classify_cover(child,source,m)
    cover=out["cover_class_candidate"]
    classes=set(np.unique(cover))
    assert {1,2,5}.issubset(classes)
    assert report["status"]=="P3_MVP_NONCANONICAL_SOURCE_CONDITIONED_COVER"
    assert not report["cover_is_author_canon"]
    assert not report["cover_is_measured_vegetation"]
    assert not report["wetland_is_confirmed_water"]
    assert report["no_terrain_changed"]
    assert report["not_koppen_to_biome"]
    assert sum(report["land_cover_area_fractions"].values()) == pytest.approx(1,abs=5e-5)


def test_geo_axes_south_and_north_first_produce_exact_same_cover():
    child,source,m=_fixture()
    child2,source2,m2=_fixture(north_first=True)
    a,r=classify_cover(child,source,m)
    b,q=classify_cover(child2,source2,m2)
    for name in a:
        np.testing.assert_array_equal(a[name],b[name])
    assert not r["source_lat_was_north_first"]
    assert q["source_lat_was_north_first"]


def test_field_missing_or_mismatched_shapes_rejects_not_fake_biomes():
    child,source,m=_fixture()
    del source["biome_base"]
    with pytest.raises(CoverEvidenceError,match="missing"):
        classify_cover(child,source,m)
    child,source,m=_fixture()
    source["stable4"]=np.ones((3,3))
    with pytest.raises(CoverEvidenceError,match="shape"):
        classify_cover(child,source,m)


def test_terrain_and_source_unchanged_deterministic():
    child,source,m=_fixture()
    old=copy.deepcopy(child)
    oldsource=copy.deepcopy(source)
    a,note=classify_cover(child,source,m)
    b,note2=classify_cover(child,source,m)
    assert note==note2
    for k in a:
        np.testing.assert_array_equal(a[k],b[k])
    for k in child:
        np.testing.assert_array_equal(child[k],old[k])
    for k in source:
        np.testing.assert_array_equal(source[k],oldsource[k])


def test_profile_explicit_overlap_or_bad_weights_fail_closed():
    child,source,m=_fixture()
    p=_defaults()
    p["source_biome_codes"]["open"].append(7)
    with pytest.raises(CoverEvidenceError,match="overlap"):
        classify_cover(child,source,m,p)
    p=_defaults()
    p["scenario_weights"]["biome_base"]=0.8
    with pytest.raises(CoverEvidenceError,match="normalized"):
        classify_cover(child,source,m,p)
    p=_defaults()
    p["status"]="AUTHOR_CANON"
    with pytest.raises(CoverEvidenceError,match="editable"):
        classify_cover(child,source,m,p)


def test_child_outside_reference_or_false_core_canon_rejects():
    child,source,m=_fixture()
    m["center_lat_lon_deg"]=[-47.25, 160]
    with pytest.raises(CoverEvidenceError,match="outside source"):
        classify_cover(child,source,m)
    m["center_lat_lon_deg"]=[-47.25,-98.25]
    m["is_accepted_Core_DomainData"]=True
    with pytest.raises(CoverEvidenceError,match="unaccepted"):
        classify_cover(child,source,m)


def test_wetland_hypothesis_requires_source_and_flat_relief():
    child,source,m=_fixture(wet=True)
    out,_=classify_cover(child,source,m)
    # Source reference for northern/southern halves differs. Even if wet, steep
    # land must not be auto converted into an actual swamp/water.
    possible=out["cover_class_candidate"]==4
    assert np.any(possible)
    assert np.all(out["child_slope_m_per_km"][possible] <= 16.01)
    child,source,m=_fixture(wet=False)
    dry,_=classify_cover(child,source,m)
    assert not np.any(dry["cover_class_candidate"]==4)


def test_rocky_slope_hypothesis_is_not_forest_and_remains_noncanonical():
    child,source,m=_fixture()
    p=_defaults()
    p["rock_slope_start_m_per_km"]=7
    p["rock_slope_full_m_per_km"]=20
    x,report=classify_cover(child,source,m,p)
    assert np.any(x["cover_class_candidate"]==3)
    assert report["cover_is_author_canon"] is False


def test_render_image(tmp_path):
    child,source,m=_fixture()
    arrays,report=classify_cover(child,source,m)
    path=tmp_path/"cover-before-after.png"
    render_preview(child,arrays,report,path)
    assert path.is_file() and path.stat().st_size > 20_000
    from PIL import Image
    with Image.open(path) as im:
        assert im.width > 1000 and im.height > 500


def test_no_earth_calendar_or_automatic_route_in_output():
    child,source,m=_fixture()
    _,report=classify_cover(child,source,m)
    payload=str(report).lower()
    assert "travel_time" not in payload
    assert "365" not in payload
    assert not report["no_species_or_groundwater_inferred"] is False
