from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from domain_generator.application import generate_domain, load_preset_catalog, registry_for_request
from domain_generator.bundle_export import export_domain_bundle
from domain_generator.compiler import compile_domain_spec, domain_spec_fingerprint, semantic_plan_fingerprint
from domain_generator.contracts import GenerationRequest
from domain_generator.contracts.data import DomainData, FieldRole
from domain_generator.contracts.spec import DomainSpec
from domain_generator.hydrology.continuous import distributed_flow_accumulation_km2
from domain_generator.hydrology.gross_input import accumulate_gross_precipitation_input
from domain_generator.hydrology.ids import lake_feature_id, marine_feature_id
from domain_generator.hydrology.marine import classify_marine_components
from domain_generator.hydrology.state import ContinuousRoutingField, LakeCandidate, LakeOutlet, MarineCandidate


ROOT = Path(__file__).resolve().parents[1]
A08 = ROOT / "tests" / "acceptance" / "cases" / "a08-core-v02-integrated"
FIELD = "gross_upstream_precipitation_m3_per_year"


def _request(*, enabled: bool = True, sea_level: float | None = None, precipitation: float | None = None) -> GenerationRequest:
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    if enabled:
        payload["domain_spec"]["hydrology"]["climatic_input"] = {"scheme": "gross_mfd_precipitation_v1"}
    if sea_level is not None:
        payload["domain_spec"]["hydrology"]["marine"] = {"sea_level_m": sea_level}
    if precipitation is not None:
        payload["domain_spec"]["surface"]["climate"]["mean_annual_precipitation_mm"] = precipitation
    return GenerationRequest.model_validate(payload)


def _generate(request: GenerationRequest):
    catalog = load_preset_catalog(A08 / "presets.json")
    return generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry_for_request(request, catalog),
    )


def _field(rows: int = 3, cols: int = 4) -> ContinuousRoutingField:
    fractions = np.zeros((rows, cols, 8), dtype=np.float64)
    # Interior node -> partly east, partly south, then east from receiver.
    fractions[1, 1, 0] = 0.55
    fractions[1, 1, 6] = 0.45
    if cols > 3:
        fractions[1, 2, 0] = 1.0
    return ContinuousRoutingField(
        flow_angle_rad=np.full((rows, cols), np.nan, dtype=np.float64),
        fractions=fractions,
    )


def _one_cell():
    return ContinuousRoutingField(
        flow_angle_rad=np.full((1, 1), np.nan, dtype=np.float64),
        fractions=np.zeros((1, 1, 8), dtype=np.float64),
    )


def _ledger_ok(a):
    assert abs(a.balance_error_m3_per_year) <= max(1e-4, 1e-9 * a.source_total_m3_per_year)
    assert np.isfinite(a.gross_upstream_precipitation_m3_per_year).all()
    assert np.all(a.gross_upstream_precipitation_m3_per_year >= 0.0)


def test_g01_opt_in_preserves_frozen_spec_and_plan_fingerprints():
    request = _request(enabled=False)
    catalog = load_preset_catalog(A08 / "presets.json")
    plan = compile_domain_spec(request.domain_spec, registry=registry_for_request(request, catalog), generator_version="0.2.0.dev0")
    assert plan.hydrology.climatic_input is None
    assert domain_spec_fingerprint(request.domain_spec) == "sha256:ae27f9151850fe61e789a182aeaa055cb2c511c2f352bd093c21283901e67bb9"
    assert semantic_plan_fingerprint(plan) == "sha256:15970c8b771e049ec958f2182419ee1f8316dd73e4e81e9b1014435ed3d6f1d8"
    assembly = _generate(request)
    assert FIELD not in assembly.data.fields
    assert FIELD not in assembly.field_payloads


def test_g02_scheme_version_and_core_01_boundary():
    payload = _request().domain_spec.model_dump(mode="python")
    payload["hydrology"]["climatic_input"]["scheme"] = "some_future_scheme"
    with pytest.raises(ValidationError):
        DomainSpec.model_validate(payload)
    payload = _request().domain_spec.model_dump(mode="python")
    payload["schema_version"] = "0.1"
    payload["terrain"] = None
    payload["surface"]["climate"] = None
    with pytest.raises(ValidationError, match="hydrology.climatic_input"):
        DomainSpec.model_validate(payload)


def test_g03_millimetre_km2_volume_conversion():
    a = accumulate_gross_precipitation_input(_one_cell(), np.array([[1000.0]], dtype=np.float32), cell_size_km=1.0)
    assert a.gross_upstream_precipitation_m3_per_year[0, 0] == 1_000_000.0
    assert a.land_edge_terminal_m3_per_year == 1_000_000.0
    _ledger_ok(a)


def test_g04_uniform_precipitation_matches_accepted_weighted_area_accumulation():
    field = _field()
    area = distributed_flow_accumulation_km2(field, cell_size_km=1.0)
    gross = accumulate_gross_precipitation_input(field, np.full((3, 4), 1100.0, dtype=np.float32), cell_size_km=1.0)
    np.testing.assert_allclose(gross.gross_upstream_precipitation_m3_per_year, area * 1_100_000.0, rtol=1e-12, atol=1e-6)
    _ledger_ok(gross)

    # The same oracle must hold when one accepted lake supernode carries
    # local lake-cell precipitation plus upstream weighted input exactly once.
    lake_field, lakes, outlets = _lake_field()
    lake_area = distributed_flow_accumulation_km2(
        lake_field, cell_size_km=1.0, lake_candidates=lakes, lake_outlets=outlets,
    )
    lake_gross = accumulate_gross_precipitation_input(
        lake_field, np.full((3, 3), 1100.0, dtype=np.float32),
        cell_size_km=1.0, lake_candidates=lakes, lake_outlets=outlets,
    )
    np.testing.assert_allclose(
        lake_gross.gross_upstream_precipitation_m3_per_year,
        lake_area * 1_100_000.0, rtol=1e-12, atol=1e-6,
    )
    _ledger_ok(lake_gross)


def test_g05_heterogeneous_rain_uses_cell_sources_not_catchment_area_only():
    rain = np.full((3, 4), 100.0, dtype=np.float32)
    rain[1, 1] = 1100.0
    a = accumulate_gross_precipitation_input(_field(), rain, cell_size_km=1.0)
    b = accumulate_gross_precipitation_input(_field(), np.full((3, 4), 100.0, dtype=np.float32), cell_size_km=1.0)
    assert a.gross_upstream_precipitation_m3_per_year[1, 2] - b.gross_upstream_precipitation_m3_per_year[1, 2] == pytest.approx(550_000.0)
    _ledger_ok(a)


def test_g06_mfd_split_counts_each_fraction_at_its_own_receiver():
    rain = np.zeros((3, 4), dtype=np.float32)
    rain[1, 1] = 1000.0
    a = accumulate_gross_precipitation_input(_field(), rain, cell_size_km=1.0)
    assert a.gross_upstream_precipitation_m3_per_year[1, 2] == pytest.approx(550_000)
    assert a.gross_upstream_precipitation_m3_per_year[2, 1] == pytest.approx(450_000)
    assert a.gross_upstream_precipitation_m3_per_year[1, 3] == pytest.approx(550_000)
    assert a.land_edge_terminal_m3_per_year == pytest.approx(1_000_000)
    _ledger_ok(a)


def _lake_field(*, coastal=False):
    rows, cols = (3, 4) if coastal else (3, 3)
    fractions = np.zeros((rows, cols, 8), dtype=np.float64)
    fractions[1, 0, 0] = 1.0  # upstream land -> lake
    if coastal:
        fractions[1, 2, 0] = 1.0  # lake outlet -> marine
    field = ContinuousRoutingField(flow_angle_rad=np.full((rows, cols), np.nan), fractions=fractions)
    lake = LakeCandidate(cells=((1, 1),), area_km2=1.0, max_depth_m=4.0, surface_elevation_m=0.0)
    outlet = LakeOutlet(lake_id=lake_feature_id(0), lake_cell=(1, 1), receiver_cell=(1, 2), saddle_elevation_m=1.0)
    return field, (lake,), (outlet,)


def test_g07_lake_supernode_local_rain_and_upstream_are_counted_once():
    field, lakes, outlets = _lake_field()
    rain = np.full((3, 3), 1000.0, dtype=np.float32)
    a = accumulate_gross_precipitation_input(field, rain, cell_size_km=1.0, lake_candidates=lakes, lake_outlets=outlets)
    assert a.gross_upstream_precipitation_m3_per_year[1, 1] == pytest.approx(2_000_000)
    assert a.gross_upstream_precipitation_m3_per_year[1, 2] == pytest.approx(3_000_000)
    _ledger_ok(a)


def test_g08_first_marine_entry_absorbs_supply_and_excludes_ocean_source():
    field = ContinuousRoutingField(flow_angle_rad=np.full((3, 3), np.nan), fractions=np.zeros((3, 3, 8)))
    field.fractions[1, 1, 0] = 0.5
    field.fractions[1, 1, 6] = 0.5
    # If the marine receiver were incorrectly processed as seabed transport,
    # it would route back onto [2,2]. First-entry absorption must stop it.
    field.fractions[1, 2, 6] = 1.0
    mask = np.zeros((3, 3), dtype=np.bool_)
    mask[1, 2] = True
    marine = (MarineCandidate(cells=((1, 2),), raster_area_km2=1.0, sea_level_m=0.0, max_depth_m=3.0),)
    a = accumulate_gross_precipitation_input(field, np.full((3, 3), 1000.0, dtype=np.float32),
        cell_size_km=1.0, marine_mask=mask, marine_candidates=marine)
    assert a.gross_upstream_precipitation_m3_per_year[1, 2] == 0.0
    assert a.gross_upstream_precipitation_m3_per_year[2, 2] == pytest.approx(1_000_000.0)
    assert a.marine_terminal_by_id_m3_per_year[marine_feature_id(0)] == pytest.approx(500_000)
    assert a.source_total_m3_per_year == pytest.approx(8_000_000)
    _ledger_ok(a)


def test_g09_enclosed_below_sea_depression_is_not_marine():
    terrain = np.ones((5, 5), dtype=np.float64) * 100.0
    terrain[0, 0] = -5.0       # boundary-connected marine
    terrain[2, 2] = -20.0     # enclosed below-sea inland depression
    mask, marine = classify_marine_components(terrain, sea_level_m=0.0, cell_size_km=1.0)
    assert mask[0, 0] and not mask[2, 2]
    assert len(marine) == 1

    fractions = np.zeros((5, 5, 8), dtype=np.float64)
    fractions[1:4, 1:4, 0] = 1.0  # interior routes to east edge
    field = ContinuousRoutingField(
        flow_angle_rad=np.full((5, 5), np.nan, dtype=np.float64),
        fractions=fractions,
    )
    inland_lake = LakeCandidate(
        cells=((2, 2),), area_km2=1.0, max_depth_m=120.0,
        surface_elevation_m=100.0,
    )
    outlet = LakeOutlet(
        lake_id=lake_feature_id(0), lake_cell=(2, 2),
        receiver_cell=(2, 3), saddle_elevation_m=100.0,
    )
    ledger = accumulate_gross_precipitation_input(
        field, np.full((5, 5), 1000.0, dtype=np.float32),
        cell_size_km=1.0, lake_candidates=(inland_lake,),
        lake_outlets=(outlet,), marine_mask=mask, marine_candidates=marine,
    )
    # Unlike the marine cell, the below-sea inland depression retains local
    # precipitation and an accepted lake supernode that receives upstream input.
    assert ledger.gross_upstream_precipitation_m3_per_year[0, 0] == 0.0
    assert ledger.gross_upstream_precipitation_m3_per_year[2, 2] == pytest.approx(2_000_000.0)
    assert ledger.gross_upstream_precipitation_m3_per_year[2, 3] == pytest.approx(3_000_000.0)
    assert ledger.source_total_m3_per_year == pytest.approx(24_000_000.0)
    assert ledger.marine_terminal_by_id_m3_per_year[marine_feature_id(0)] == 0.0
    _ledger_ok(ledger)

def test_g10_nonmarine_domain_edge_is_valid_terminal():
    a = accumulate_gross_precipitation_input(_one_cell(), np.array([[500.0]], dtype=np.float32), cell_size_km=2.0)
    assert a.land_edge_terminal_m3_per_year == 2_000_000.0
    assert not a.marine_terminal_by_id_m3_per_year
    _ledger_ok(a)


def test_g11_global_ledger_mixes_inland_lake_marine_and_land_edges():
    field, lakes, outlets = _lake_field(coastal=True)
    mask = np.zeros((3, 4), dtype=np.bool_)
    mask[1, 3] = True
    marine = (MarineCandidate(cells=((1, 3),), raster_area_km2=1.0, sea_level_m=0.0, max_depth_m=1.0),)
    a = accumulate_gross_precipitation_input(field, np.full((3, 4), 1000.0, dtype=np.float32),
        cell_size_km=1.0, lake_candidates=lakes, lake_outlets=outlets, marine_mask=mask, marine_candidates=marine)
    assert a.source_total_m3_per_year == pytest.approx(11_000_000)
    assert a.marine_terminal_by_id_m3_per_year[marine_feature_id(0)] == pytest.approx(3_000_000)
    assert a.land_edge_terminal_m3_per_year == pytest.approx(8_000_000)
    _ledger_ok(a)


def test_g12_existing_world_fields_features_and_networks_are_exact_when_enabled():
    off = _generate(_request(enabled=False, sea_level=0.0))
    on = _generate(_request(enabled=True, sea_level=0.0))
    assert set(on.data.fields) == set(off.data.fields) | {FIELD}
    for name in off.field_payloads:
        np.testing.assert_array_equal(on.field_payloads[name], off.field_payloads[name])
    assert on.data.features == off.data.features
    assert on.data.networks == off.data.networks
    assert on.data.grid == off.data.grid


def test_g13_derived_float64_field_schema_and_bundle_round_trip(tmp_path: Path):
    assembly = _generate(_request())
    descriptor = assembly.data.fields[FIELD]
    data = assembly.field_payloads[FIELD]
    assert descriptor.role is FieldRole.DERIVED
    assert descriptor.dtype == "float64" and descriptor.unit == "m3/year"
    assert data.dtype == np.float64 and np.isfinite(data).all() and np.all(data >= 0)
    result = export_domain_bundle(assembly=assembly, output_dir=tmp_path / "bundle")
    round_trip = DomainData.model_validate_json((result.root / "domain.json").read_text(encoding="utf-8"))
    assert round_trip == assembly.data
    np.testing.assert_array_equal(np.load(result.root / descriptor.path, allow_pickle=False), data)
    assert any(x.field_id == FIELD for x in result.manifest.canonical_files)


def test_g14_opt_in_fingerprints_and_deterministic_replay():
    enabled = _request()
    disabled = _request(enabled=False)
    catalog = load_preset_catalog(A08 / "presets.json")
    plan_on = compile_domain_spec(enabled.domain_spec, registry=registry_for_request(enabled, catalog), generator_version="0.2.0.dev0")
    plan_off = compile_domain_spec(disabled.domain_spec, registry=registry_for_request(disabled, catalog), generator_version="0.2.0.dev0")
    assert domain_spec_fingerprint(enabled.domain_spec) != domain_spec_fingerprint(disabled.domain_spec)
    assert semantic_plan_fingerprint(plan_on) != semantic_plan_fingerprint(plan_off)
    first, second = _generate(enabled), _generate(enabled)
    assert first.data == second.data
    for name in first.field_payloads:
        np.testing.assert_array_equal(first.field_payloads[name], second.field_payloads[name])


def test_g15_dry_wet_and_coastal_domains_are_not_region_hardcoded():
    dry = _generate(_request(precipitation=100.0))
    wet = _generate(_request(precipitation=1800.0))
    coastal = _generate(_request(sea_level=0.0))
    a, b = dry.field_payloads[FIELD], wet.field_payloads[FIELD]
    assert float(np.median(b)) > float(np.median(a)) * 10.0
    assert np.any(coastal.field_payloads["marine_mask"] == 1)
    assert np.all(coastal.field_payloads[FIELD][coastal.field_payloads["marine_mask"].astype(bool)] == 0)
    assert np.isfinite(coastal.field_payloads[FIELD]).all()
