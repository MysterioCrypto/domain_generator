"""P2-B2.3 global original D8 first-entry partition; re-entry MUST not duplicate."""

from io import BytesIO
from zipfile import ZipFile

import numpy as np
import pytest

from scripts.trace_a8_external_first_entry_v02 import (
    ExternalProvenanceError, audit_global_first_entry,
    first_entry_partition, read_global_a8,
)
from scripts.condition_planetary_child_boundary_mfd_v02 import source_inlet_candidates


def _graph():
    """Exit and RE-ENTER: upstream inside-area must never enter second ledger."""
    nr, nc = 4, 8
    d = np.full((nr, nc), -1, dtype=np.int32)
    # Outside west -> inside left.
    d[0, 1] = 1 * nc + 1
    d[1, 1] = 1 * nc + 2
    d[1, 2] = 1 * nc + 3
    # Inside -> exit east -> return inside from SE.
    d[1, 3] = 1 * nc + 4
    d[1, 4] = 1 * nc + 5
    d[1, 5] = 2 * nc + 5
    d[0, 5] = 1 * nc + 5
    d[2, 5] = 2 * nc + 4
    inside = np.zeros((nr, nc), dtype=bool)
    inside[1:3, 3:5] = True
    area = np.full(nr, 10., dtype=float)
    return d, inside, area


def test_global_partition_handles_reentry_without_doublecount_or_child_source():
    d, inside, area = _graph()
    result, labels, info = first_entry_partition(
        d, np.ones(d.shape, dtype=np.uint8), inside, area
    )
    west = 1 * 8 + 2
    east = 2 * 8 + 5
    assert result == {west: 30., east: 30.}
    assert info["all_directed_external_area_km2"] == 60.
    assert info["contributed_external_land_cells"] == 6
    assert info["entry_with_prior_inside_upstream_count"] == 1
    assert east in info["entry_with_prior_inside_upstream_global_source_ids"]
    assert labels[1, 3] == -1  # INTERNAL original source never counted as external.
    assert labels[1, 5] == east  # Outside soil after exit can feed second entry.
    assert labels[0, 1] == west
    assert labels[0, 0] == -1  # Unconnected outside source does not reach child.


def test_first_entry_replay_and_area_weighting_vary_by_latitude():
    d, inside, area = _graph()
    area = np.array([20., 10., 8., 4.])
    p, l, a = first_entry_partition(d, np.ones(d.shape), inside, area)
    assert p[1*8+2] == 20 + 10 + 10
    assert p[2*8+5] == 20 + 10 + 8
    p2,l2,a2 = first_entry_partition(d, np.ones(d.shape), inside, area)
    assert p == p2 and a == a2
    np.testing.assert_array_equal(l, l2)


def test_graph_cycles_and_bad_downstream_fail_closed():
    d, inside, area = _graph()
    d[0, 0], d[0, 1] = 1, 0
    with pytest.raises(ExternalProvenanceError, match="cycle"):
        first_entry_partition(d, np.ones(d.shape), inside, area)
    d, inside, area = _graph()
    d[0, 0] = 999
    with pytest.raises(ExternalProvenanceError, match="outside source grid"):
        first_entry_partition(d, np.ones(d.shape), inside, area)
    d[0, 0] = -2
    with pytest.raises(ExternalProvenanceError, match="outside source grid"):
        first_entry_partition(d, np.ones(d.shape), inside, area)


def test_outside_cell_without_boundary_entry_contributes_zero():
    d, inside, area = _graph()
    d[:] = -1
    out, labels, status = first_entry_partition(d, np.ones(d.shape),
                                                inside, area)
    assert out == {}
    assert status["all_directed_a8_entries"] == 0
    assert status["all_directed_external_area_km2"] == 0
    assert np.all(labels == -1)


def _realistic_synthetic_source():
    d, inside, area = _graph()
    lat = np.array([.45, .15, -.15, -.45], dtype=np.float32)
    lon = np.array([-1.05, -.75, -.45, -.15,
                    .15, .45, .75, 1.05], dtype=np.float32)
    river = np.zeros_like(d, dtype=np.uint8)
    river[1, 2] = 1
    river[2, 5] = 1
    global_source = {
        "lat": lat, "lon": lon,
        "land": np.ones_like(d, dtype=np.uint8),
        "downstream_index": d,
        "catchment_area_km2": np.full(d.shape, 999., dtype=np.float32),
        "river_mask": river,
    }
    # The clipped macro source has exactly the same stations, like the real
    # external source adapter. One old river source carries a deliberately
    # WRONG 999km² catchment so audit must NOT take it for external area.
    macro = {
        "latitude_deg_north_first": lat,
        "longitude_deg_west_to_east": lon,
        "local_downstream_index": d,
        "source_river_mask_D8": river,
        "source_catchment_km2_D8": global_source["catchment_area_km2"],
    }
    edge = np.arange(-35., 36., 1.)
    child = {
        "east_km": edge,
        "north_km_north_first": edge[::-1],
    }
    manifest = {
        "center_lat_lon_deg": [0., 0.],
        "planet_radius_km": 7008.1,
    }
    return global_source, macro, child, manifest


def test_matching_original_global_source_to_macro_inlets_and_reentry():
    global_a8, macro, child, manifest = _realistic_synthetic_source()
    entries = source_inlet_candidates(macro, child, manifest)
    assert len(entries) == 2
    report, labels = audit_global_first_entry(
        global_a8, macro, child, manifest, entries
    )
    assert report["old_A8_major_river_inlets_matched"] == 2
    assert report["entry_with_prior_inside_upstream_count"] == 1
    assert report["all_directed_a8_entries"] == 2
    assert report["old_A8_major_river_entry_area_km2"] == pytest.approx(
        report["all_directed_external_area_km2"]
    )
    assert report["other_unmapped_macro_entry_area_km2"] == pytest.approx(0)
    assert report["auto_injected_external_area_km2"] == 0
    assert report["original_A8_source_cells_partitioned_once"]
    assert not report["genuine_child_MFD_topology_validated"]
    for item in report["entries"]:
        assert item["old_A8_total_upstream_catchment_km2_UNSAFE_HINT"] == 999.
        assert item["A8_external_macro_land_source_area_km2_FIRST_ENTRY_ONLY"] != 999.
        assert not item["may_auto_inject_into_child"]


def test_edited_or_misaligned_macro_global_source_rejected():
    source,macro,child,manifest = _realistic_synthetic_source()
    proposals = source_inlet_candidates(macro,child,manifest)
    broken = dict(source)
    broken["downstream_index"] = source["downstream_index"].copy()
    broken["downstream_index"][1,2] = -1
    with pytest.raises(ExternalProvenanceError, match="graph link disagrees"):
        audit_global_first_entry(broken,macro,child,manifest,proposals)
    broken = dict(macro)
    broken["longitude_deg_west_to_east"] = macro["longitude_deg_west_to_east"]+.001
    with pytest.raises(ExternalProvenanceError, match="not exactly aligned"):
        audit_global_first_entry(source,broken,child,manifest,proposals)


def test_global_source_archive_loader_is_private_path_based(tmp_path):
    source, _, _, _ = _realistic_synthetic_source()
    data = BytesIO()
    np.savez_compressed(data, **source)
    file = tmp_path / "fake-A8.zip"
    with ZipFile(file, "w") as z:
        z.writestr("planet_A8/A8_hydrology.npz", data.getvalue())
    loaded = read_global_a8(file)
    for key in source:
        np.testing.assert_array_equal(source[key], loaded[key])
