from __future__ import annotations

import numpy as np
import pytest

from domain_generator.contracts.geometry import AreaGeometry, BandGeometry, PointGeometry
from domain_generator.geometry.queries import region_set_covers_point
from domain_generator.pipeline import candidate_rank_key
from domain_generator.terrain.generate import rasterize_area_cell_centers

from .support import (
    CASE_IDS,
    assert_or_report_baseline,
    load_case,
    run_detailed,
    verify_bundle,
)


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_acceptance_world_semantics_and_baseline(case_id: str) -> None:
    case = load_case(case_id)
    result = run_detailed(case)
    assembly = result.assembly
    data = assembly.data

    assert data.validation.engine_invariants_passed is True
    assert data.validation.hard_constraints_passed is True
    if data.provenance.spec_schema_version == "0.2":
        assert tuple(data.fields) == (
            "elevation",
            "water_depth",
            "moisture",
            "vegetation_density",
            "temperature",
            "annual_precipitation",
        )
    else:
        assert tuple(data.fields) == (
            "elevation",
            "water_depth",
            "moisture",
            "vegetation_density",
        )

    expected_shape = (data.grid.rows, data.grid.columns)
    for field_id, array in assembly.field_payloads.items():
        assert array.dtype == np.dtype(np.float32), field_id
        assert array.shape == expected_shape, field_id
        assert np.isfinite(array).all(), field_id

    assert np.all(assembly.field_payloads["water_depth"] >= 0.0)
    assert np.all((assembly.field_payloads["moisture"] >= 0.0) & (assembly.field_payloads["moisture"] <= 1.0))
    assert np.all(
        (assembly.field_payloads["vegetation_density"] >= 0.0)
        & (assembly.field_payloads["vegetation_density"] <= 1.0)
    )
    if data.provenance.spec_schema_version == "0.2":
        assert np.isfinite(assembly.field_payloads["temperature"]).all()
        assert np.all(assembly.field_payloads["annual_precipitation"] > 0.0)
        assert set(data.networks) == {"rivers", "potential_drainage"}

    if case_id == "a01-minimal":
        assert data.features == {}
        assert np.count_nonzero(assembly.field_payloads["elevation"]) == 0

    elif case_id == "a02-terrain-ridge":
        feature = data.features["ridge-01"]
        assert feature.family.value == "terrain"
        assert isinstance(feature.geometry, BandGeometry)
        elevation = assembly.field_payloads["elevation"]
        assert float(np.max(elevation)) > float(np.min(elevation))
        assert float(np.max(elevation)) > 100.0
        assert all(
            0.0 <= point.x_km <= data.domain.width_km
            and 0.0 <= point.y_km <= data.domain.height_km
            for point in feature.geometry.centerline
        )

    elif case_id == "a03-hydrology-lake-river":
        lake_ids = [
            feature_id
            for feature_id, feature in data.features.items()
            if feature.family.value == "hydro"
        ]
        assert lake_ids
        rivers = data.networks["rivers"]
        assert rivers.nodes
        assert rivers.segments
        for segment in rivers.segments.values():
            assert segment.from_node in rivers.nodes
            assert segment.to_node in rivers.nodes
        water = assembly.field_payloads["water_depth"]
        assert np.count_nonzero(water > 0.0) > 0

    elif case_id == "a04-surface":
        wetland = data.features["wetland-01"]
        assert wetland.family.value == "surface"
        assert isinstance(wetland.geometry, AreaGeometry)
        water_mask = assembly.field_payloads["water_depth"] > 0.0
        moisture = assembly.field_payloads["moisture"]
        vegetation = assembly.field_payloads["vegetation_density"]
        assert np.count_nonzero(water_mask) > 0
        assert np.all(moisture[water_mask] == np.float32(1.0))
        assert np.all(vegetation[water_mask] == np.float32(0.0))
        target_mask = rasterize_area_cell_centers(result.plan, wetland.geometry)
        nonwater_target = target_mask & ~water_mask
        nonwater_outside = ~target_mask & ~water_mask
        assert np.count_nonzero(nonwater_target) > 0
        assert np.count_nonzero(nonwater_outside) > 0
        assert float(np.mean(moisture[nonwater_target])) > float(np.mean(moisture[nonwater_outside]))

    elif case_id == "a05-dependent-poi":
        poi = data.features["poi-01"]
        assert poi.family.value == "poi"
        assert isinstance(poi.geometry, PointGeometry)
        selected_state = result.run.selected.state
        assert selected_state.layout is not None
        assert selected_state.placement is not None
        assert "poi-01" not in selected_state.layout.geometry_realizations
        reservation = selected_state.layout.placement_reservations["poi-01"]
        assert region_set_covers_point(reservation.allowed_region, poi.geometry)
        assert selected_state.placement.final_points["poi-01"] == poi.geometry

    elif case_id == "a06-constraints-ranking":
        assert result.run.attempts_executed > len(result.run.valid_candidates)
        assert len(result.run.valid_candidates) >= 2
        ranking_pairs = {
            (
                candidate.ranking.worst_effective_violation,
                candidate.ranking.weighted_mean_score,
            )
            for candidate in result.run.valid_candidates
        }
        assert len(ranking_pairs) > 1
        ranked = tuple(sorted(result.run.valid_candidates, key=candidate_rank_key))
        assert result.run.selected == ranked[0]
        assert result.run.selected.attempt_index != 0

    elif case_id == "a07-complex-mixed":
        assert {"ridge-01", "basin-01", "wetland-01", "settlement-01"}.issubset(data.features)
        assert isinstance(data.features["settlement-01"].geometry, PointGeometry)
        assert data.features["wetland-01"].family.value == "surface"
        assert any(feature.family.value == "hydro" for feature in data.features.values())
        assert data.networks["rivers"].segments
        assert result.run.valid_candidates
        assert data.validation.soft.weighted_mean_score <= 1.0

    elif case_id == "a08-core-v02-integrated":
        settlement = data.features["settlement-01"]
        assert settlement.family.value == "poi"
        assert isinstance(settlement.geometry, PointGeometry)
        selected_state = result.run.selected.state
        assert selected_state.layout is not None
        assert selected_state.placement is not None
        assert selected_state.hydrology is not None
        assert selected_state.surface is not None
        reservation = selected_state.layout.placement_reservations["settlement-01"]
        assert region_set_covers_point(reservation.allowed_region, settlement.geometry)
        assert selected_state.placement.final_points["settlement-01"] == settlement.geometry
        assert data.networks["rivers"].segments
        assert data.networks["potential_drainage"].segments
        assert selected_state.hydrology.potential_river_network is not None
        assert (
            data.networks["potential_drainage"]
            == selected_state.hydrology.potential_river_network
        )
        assert selected_state.surface.annual_mean_temperature_c is not None
        assert selected_state.surface.annual_precipitation_mm is not None
        placement_feature = next(
            feature for feature in result.plan.features if feature.id == "settlement-01"
        )
        assert placement_feature.effect.site_profile is not None
        used_metrics = {
            requirement.metric
            for requirement in placement_feature.effect.site_profile.requirements
        } | {
            preference.metric
            for preference in placement_feature.effect.site_profile.preferences
        }
        assert {
            "temperature_mean",
            "annual_precipitation_mean",
            "distance_to_potential_drainage",
        }.issubset(used_metrics)

    else:  # pragma: no cover - guarded by CASE_IDS
        raise AssertionError(case_id)

    assert_or_report_baseline(result)


def test_representative_cases_publish_canonical_bundles(tmp_path) -> None:
    for case_id, expected_file_count in (
        ("a01-minimal", 5),
        ("a07-complex-mixed", 5),
        ("a08-core-v02-integrated", 7),
    ):
        result = verify_bundle(load_case(case_id), tmp_path)
        assert result.technical_preview is None
        assert len(result.manifest.canonical_files) == expected_file_count
