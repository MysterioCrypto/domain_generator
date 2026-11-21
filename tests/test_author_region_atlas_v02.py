"""Author-map product QA: no fictional canon, no fictional distances."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from scripts.render_author_region_atlas_v02 import (
    AuthorAtlasError, audit_atlas, notes, render_sheet,
)


def _data():
    n = 61
    y, x = np.indices((n, n))
    child = {
        "east_km": np.arange(n, dtype=float)-30,
        "north_km_north_first": 30-np.arange(n, dtype=float),
        "child_elevation_m": (320+1.8*x-.8*y+60*np.sin(x/12)*np.cos(y/13)).astype("float32"),
        "land_mask": np.ones((n, n), dtype="uint8"),
    }
    manifest = {
        "status": "NEW_PROCEDURAL_CHILD_TERRAIN_NOT_AUTHOR_CANON",
        "is_accepted_Core_DomainData": False,
        "center_lat_lon_deg": [-47.25, -98.25],
    }
    ledger = {
        "schema": "author-region-atlas-v0.1",
        "world": {"name": "Осве́ра", "name_status": "WORKING_NOT_CANON"},
        "story": {"protagonist": "Д’Акхар"},
        "region": {
            "id": "A", "center_lat_lon_deg": [-47.25, -98.25],
            "status": "MODEL_CANDIDATE_NOT_CANON",
        },
        "landmarks": [
            {"id": "mansion", "label": "Особняк мага", "evidence": "WRITTEN",
             "position_status": "UNPLACED", "position": None},
            {"id": "city", "label": "Город", "evidence": "AUTHOR_BRIEF",
             "position_status": "UNPLACED", "position": None},
        ],
        "routes": [
            {"id": "road", "label": "Курьерский путь", "from": "mansion", "to": "city",
             "polyline_east_north_km": None, "status": "UNKNOWN"},
        ],
    }
    return child, manifest, ledger


def test_user_facts_hero_is_not_region_name_and_unknowns_stay_unknown():
    child, manifest, ledger = _data()
    result = audit_atlas(ledger, child, manifest)
    assert result["planet"] == "Осве́ра"
    assert result["protagonist"] == "Д’Акхар"
    assert result["landmarks_unplaced"] == 2
    assert result["routes"][0]["distance_km"] is None
    assert result["routes"][0]["distance_kind"] == "UNPLACED_NO_DISTANCE"
    assert not result["any_locations_automatically_placed"]
    assert not result["landcover_inferred_from_elevation"]
    assert not result["map_is_author_canon"]
    assert "пока не размещено" in notes(ledger, result)


def test_model_proposed_location_only_gives_straight_lower_bound():
    child, manifest, ledger = _data()
    ledger["landmarks"][0].update(
        {"position": [-10, 10], "position_status": "MODEL_PROPOSAL"}
    )
    ledger["landmarks"][1].update(
        {"position": [20, -10], "position_status": "MODEL_PROPOSAL"}
    )
    result = audit_atlas(ledger, child, manifest)
    assert result["landmarks_unplaced"] == 0
    route = result["routes"][0]
    assert route["distance_kind"] == "STRAIGHT_LINE_LOWER_BOUND_NOT_TRAVEL_DISTANCE"
    assert route["distance_km"] == round(1300**.5, 3)
    assert not route["travel_time_inferred"]


def test_route_polyline_is_the_only_route_length_not_real_travel_time():
    child, manifest, ledger = _data()
    ledger["landmarks"][0].update(
        {"position": [-10, 10], "position_status": "MODEL_PROPOSAL"}
    )
    ledger["landmarks"][1].update(
        {"position": [20, -10], "position_status": "MODEL_PROPOSAL"}
    )
    ledger["routes"][0]["polyline_east_north_km"] = [
        [-10, 10], [0, 10], [0, -10], [20, -10],
    ]
    route = audit_atlas(ledger, child, manifest)["routes"][0]
    assert route["distance_km"] == 50.0
    assert route["distance_kind"] == "DRAWN_MODEL_POLYLINE_NOT_TRAVEL_TIME"
    assert not route["travel_time_inferred"]


def test_author_approved_needs_provenance_and_models_never_become_author_fixed():
    child, manifest, ledger = _data()
    ledger["landmarks"][0].update({
        "position": [0, 0], "position_status": "AUTHOR_FIXED"
    })
    with pytest.raises(AuthorAtlasError, match="provenance"):
        audit_atlas(ledger, child, manifest)
    ledger["landmarks"][0]["position_source"] = "Author note 2026-11-21"
    result = audit_atlas(ledger, child, manifest)
    assert result["landmarks_unplaced"] == 1
    assert not result["map_is_author_canon"]


def test_out_of_region_or_false_canon_or_invented_route_fails_closed():
    child, manifest, ledger = _data()
    ledger["landmarks"][0].update({
        "position": [60, 0], "position_status": "MODEL_PROPOSAL"
    })
    with pytest.raises(AuthorAtlasError, match="outside"):
        audit_atlas(ledger, child, manifest)
    ledger["landmarks"][0]["position"] = [0, 0]
    with pytest.raises(AuthorAtlasError, match="unplaced"):
        audit_atlas(ledger, child, manifest)
    ledger["landmarks"][1].update({
        "position": [10, 10], "position_status": "MODEL_PROPOSAL"
    })
    ledger["routes"][0]["polyline_east_north_km"] = [[0, 0], [9, 11]]
    with pytest.raises(AuthorAtlasError, match="does not connect"):
        audit_atlas(ledger, child, manifest)
    ledger["routes"][0]["polyline_east_north_km"] = [[0, 0], [10, 10]]
    manifest["is_accepted_Core_DomainData"] = True
    with pytest.raises(AuthorAtlasError, match="noncanonical"):
        audit_atlas(ledger, child, manifest)


def test_visual_sheet_and_notes_standalone(tmp_path: Path):
    child, manifest, ledger = _data()
    report = audit_atlas(ledger, child, manifest)
    original = child["child_elevation_m"].copy()
    path=tmp_path/"author-atlas-sheet.png"
    render_sheet(ledger, child, report, path)
    assert path.exists() and path.stat().st_size > 15_000
    np.testing.assert_array_equal(original, child["child_elevation_m"])
    assert "Расстояния" not in notes(ledger, report) or "Контроль маршрутов" in notes(ledger, report)
    from PIL import Image
    with Image.open(path) as im:
        assert im.width > 1700 and im.height > 900
