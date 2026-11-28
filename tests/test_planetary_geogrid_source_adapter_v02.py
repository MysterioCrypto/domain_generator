"""External planetary-source alignment: tiny synthetic archive tests, no private data."""

from io import BytesIO
from zipfile import ZipFile

import numpy as np
import pytest

from scripts.export_planetary_macro_region_v02 import (
    WorldSourceMismatch,
    load_archives,
    region_crop,
)


def _fixtures(tmp_path):
    lat12 = np.array([-0.9, -0.6, -0.3, 0, 0.3, 0.6, 0.9],
                     dtype=np.float32)
    lon = np.array([-1.05, -0.75, -0.45, -0.15,
                    0.15, 0.45, 0.75, 1.05], dtype=np.float32)
    nrows, ncols = len(lat12), len(lon)
    a8_height = (np.arange(nrows * ncols, dtype=np.float32)
                 .reshape(nrows, ncols) * 7)
    land = np.ones((nrows, ncols), dtype=np.uint8)
    land[0, 0] = 0
    downstream = np.full((nrows, ncols), -1, dtype=np.int32)
    # Every nonterminal row goes one step SOUTH in A8's north-first raster.
    for row in range(nrows - 1):
        downstream[row] = np.arange((row + 1) * ncols, (row + 2) * ncols)
    a8 = {
        "lat": lat12[::-1].copy(),
        "lon": lon,
        "land": land,
        "elevation_m": a8_height,
        "downstream_index": downstream,
        "catchment_area_km2": np.ones_like(a8_height) * 25,
        "river_mask": np.ones_like(land),
    }
    a12 = {
        "lat": lat12, "lon": lon, "land": land[::-1].copy(),
        "elevation_m": a8_height[::-1].copy(),
        "temperature_annual_C": np.full((nrows, ncols), 16, dtype=np.float32),
        "precip_planet_year_mm": np.full((nrows, ncols), 899, dtype=np.float32),
        "biome_base": np.ones((nrows, ncols), dtype=np.uint8) * 7,
    }
    a10 = {
        "lat": lat12, "lon": lon, "land": a12["land"],
        "annual_Q_m3s": np.ones((nrows, ncols), dtype=np.float32) * 30,
    }
    zip_paths = {}
    for name, arrayset, member in (
        ("A8", a8, "planet_A8/A8_hydrology.npz"),
        ("A10", a10, "planet_A10/A10_water_balance.npz"),
        ("A12", a12, "planet_A12/A12_biome_fields.npz"),
    ):
        path = tmp_path / f"{name}.zip"
        buffer = BytesIO()
        np.savez_compressed(buffer, **arrayset)
        with ZipFile(path, "w") as z:
            z.writestr(member, buffer.getvalue())
        zip_paths[name] = path
    return zip_paths, a8, a12


def test_load_private_style_archives_requires_exact_latitude_flip_and_land(tmp_path):
    paths, a8, a12 = _fixtures(tmp_path)
    fields = load_archives(paths["A8"], paths["A12"], paths["A10"])
    np.testing.assert_array_equal(fields["a8_elevation_m"], a8["elevation_m"])
    np.testing.assert_array_equal(fields["a12_elevation_m"], a12["elevation_m"])
    assert np.array_equal(fields["a8_lat"][::-1], fields["a12_lat"])
    assert fields["a10_Q_m3s"].shape == (7, 8)


def test_three_by_three_crop_remaps_both_endpoints_and_retains_global_receivers(tmp_path):
    paths, a8, _ = _fixtures(tmp_path)
    data = load_archives(paths["A8"], paths["A12"])
    region, note = region_crop(
        data, center_lat_deg=0.0, center_lon_deg=0.0,
        half_width_km=60, half_height_km=60, planet_radius_km=7008.1,
        planetary_year_earth_days=202.755,
    )
    assert note["region_shape"] == [3, 4]  # grid is centered BETWEEN 0.15-degree lon cells
    np.testing.assert_allclose(region["latitude_deg_north_first"],
                               [0.3, 0, -0.3], rtol=0, atol=1e-6)
    # East-west source window includes four columns, no fabricated 1-km samples.
    rs, re = (note["source_crop_bounds"][k] for k in ("a8_row_start", "a8_row_stop"))
    cs, ce = (note["source_crop_bounds"][k] for k in ("column_start", "column_stop"))
    np.testing.assert_array_equal(region["elevation_m"], a8["elevation_m"][rs:re, cs:ce])
    expected = np.arange(4, 8, dtype=np.int64)
    np.testing.assert_array_equal(region["local_downstream_index"][0], expected)
    np.testing.assert_array_equal(region["local_downstream_index"][1], expected + 4)
    np.testing.assert_array_equal(region["local_downstream_index"][2], [-1] * 4)
    assert note["local_D8_exits_region_count"] == 4
    assert int(region["source_downstream_exits_region"].sum()) == 4
    assert np.all(region["source_global_downstream_index"][2] >= 0)
    assert note["is_DomainData"] is False
    assert note["planetary_year_earth_days"] == 202.755
    assert note["source_precip_unit"] == "mm per planetary year"


def test_incompatible_dem_is_rejected_not_resampled(tmp_path):
    paths, _, a12 = _fixtures(tmp_path)
    a12["elevation_m"][1, 1] += 1
    buffer = BytesIO()
    np.savez_compressed(buffer, **a12)
    with ZipFile(paths["A12"], "w") as z:
        z.writestr("planet_A12/A12_biome_fields.npz", buffer.getvalue())
    with pytest.raises(WorldSourceMismatch, match="elevation"):
        load_archives(paths["A8"], paths["A12"])


def test_geographic_approximation_rejects_pole_and_tiny_crop(tmp_path):
    paths, _, _ = _fixtures(tmp_path)
    data = load_archives(paths["A8"], paths["A12"])
    base = dict(center_lat_deg=0.0, center_lon_deg=0.0,
                half_width_km=60, half_height_km=60,
                planet_radius_km=7008.1, planetary_year_earth_days=202.755)
    with pytest.raises(ValueError, match="poles"):
        region_crop(data, **(base | {"center_lat_deg": 89.0}))
    with pytest.raises(WorldSourceMismatch, match="fewer"):
        region_crop(data, **(base | {"half_height_km": 1.0}))
    with pytest.raises(ValueError, match="positive"):
        region_crop(data, **(base | {"planetary_year_earth_days": 0}))
