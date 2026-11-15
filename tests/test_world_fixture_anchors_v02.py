"""External world-source fixture guardrails (not a Core runtime dependency)."""

import json
from pathlib import Path


FILE = (
    Path(__file__).resolve().parents[1]
    / "examples/world-fixtures/dakhar-first-arc-anchors.json"
)


def _load():
    return json.loads(FILE.read_text(encoding="utf-8"))


def test_fixture_is_explicitly_noncanonical_and_not_a_domainspec():
    x = _load()
    assert x["fixture_schema"] == "world-source-anchors-v0.1"
    assert x["is_domain_spec"] is False
    assert x["status"] == "SOURCE_ANCHORED_NON_CANONICAL"
    assert x["source_availability"]["original_a8_a10_a12_rasters"] == "SOURCE_ZIPS_LOCATED_NOT_EXTRACTED"
    assert x["source_availability"]["source_archives_found_in_drive"] is True
    assert x["source_availability"]["archive_contents_verified"] is False
    assert set(x["source_availability"]["archives"]) == {"A8", "A10", "A11", "A12", "atlas_png"}
    assert not x["source_availability"]["georeferenced_original_imported"]
    assert not x["source_availability"]["source_data_imported"]


def test_calendar_and_non_earth_precipitation_units_are_explicit():
    x = _load()
    assert x["planet_model"]["planetary_year_earth_days_approx"] == 202.755
    assert x["unit_boundary"]["source_precipitation_unit"] == "mm per planetary year"
    assert x["unit_boundary"]["direct_equivalence_asserted"] is False
    assert x["unit_boundary"]["external_planetary_calendar_adapter_implemented"] is False
    for candidate in x["region_candidates"]:
        assert "precipitation_mm_per_planetary_year_approx" in candidate
        assert "precipitation_mm_per_earth_year" not in candidate


def test_all_proposed_locations_remain_model_only_and_anchors_unpinned():
    x = _load()
    assert {c["id"] for c in x["region_candidates"]} == {"A", "B", "C"}
    for c in x["region_candidates"]:
        assert c["status"] == "MODEL_CANDIDATE_NOT_CANON"
        assert c["author_approved"] is False
        assert -90 <= c["lat_deg"] <= 90
        assert -180 <= c["lon_deg"] <= 180
    assert len(x["narrative_anchors"]) == 5
    assert all(not item["exact_coordinates_known"] for item in x["narrative_anchors"])
