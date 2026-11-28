"""P4-O: imported DEM native assembly without private inputs."""
import numpy as np
import pytest
from scripts.evaluate_imported_dem_native_network_v02 import make_plan, run, stats


def test_compiled_import_grid():
    p=make_plan((41,51))
    assert (p.grid.rows,p.grid.columns,p.grid.cell_size_km)==(41,51,.5)
    assert p.domain.width_km==25.5 and p.domain.height_km==20.5
    assert p.hydrology.stream_threshold_km2==30.
    assert p.hydrology.marine is None


@pytest.mark.parametrize('z',[np.array([1.,2.]),np.array([[1.,np.nan]])])
def test_invalid_elevation(z):
    with pytest.raises(ValueError,match='finite 2D'):run(z)


def test_small_imported_surface_and_normalization():
    rr,cc=np.indices((51,51));z=(500.-2*cc+.10*(rr-25)**2).astype(np.float32);old=z.copy()
    p,h,c,r=run(z)
    np.testing.assert_array_equal(z,old)
    np.testing.assert_array_equal(h.flow_accumulation_km2,c.flow_accumulation_km2)
    assert r['normalized_validation']['passed']
    assert r['normalized_regional']['false_confluences']==0
    assert len(c.river_network.segments)>0
    assert not r['approved_geography']
    assert not r['chapter1_compatibility_verified']
