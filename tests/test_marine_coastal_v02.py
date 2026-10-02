from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from shapely.geometry import box

from domain_generator.application import (
    generate_domain,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.compiler import (
    compile_domain_spec,
    domain_spec_fingerprint,
    semantic_plan_fingerprint,
)
from domain_generator.contracts import GenerationRequest
from domain_generator.contracts.data import (
    FieldRole,
    MarineFeature,
    RiverNodeKind,
)
from domain_generator.contracts.plan import GenerationPlan
from domain_generator.contracts.spec import DomainSpec
from domain_generator.geometry import backend_region_set, region_set_boundary_distance_km
from domain_generator.hydrology import (
    build_water_depth_m,
    classify_marine_components,
    generate_hydrology_v02,
    materialize_marine_features,
    marine_feature_id,
)
from domain_generator.hydrology.classification import extract_lake_candidates
from domain_generator.hydrology.routing import priority_flood_surfaces
from domain_generator.terrain.state import TerrainState


ROOT = Path(__file__).resolve().parents[1]
A08 = ROOT / "tests" / "acceptance" / "cases" / "a08-core-v02-integrated"


def _plan(
    rows: int,
    columns: int,
    *,
    threshold: float = 6.0,
    sea_level_m: float | None = 0.0,
) -> GenerationPlan:
    hydrology: dict[str, object] = {
        "stream_threshold_km2": threshold,
        "lake_min_area_km2": 1.0,
        "lake_min_depth_m": 0.5,
        "river_depth_at_threshold_m": 0.5,
        "river_depth_exponent": 0.3,
    }
    if sea_level_m is not None:
        hydrology["marine"] = {"sea_level_m": sea_level_m}

    return GenerationPlan.model_validate(
        {
            "plan_version": "0.2",
            "source": {
                "spec_id": "h12-marine-test",
                "spec_schema_version": "0.2",
                "spec_fingerprint": "sha256:h12-test",
                "generator_version": "0.2-test",
            },
            "seed": 12012,
            "domain": {
                "width_km": float(columns),
                "height_km": float(rows),
            },
            "grid": {
                "cell_size_km": 1.0,
                "rows": rows,
                "columns": columns,
            },
            "terrain": {
                "base_elevation_m": 100.0,
                "noise_layers": [
                    {"id": "test", "scale_km": 10.0, "amplitude_m": 1.0}
                ],
            },
            "hydrology": hydrology,
            "surface": {
                "moisture_base": 0.35,
                "water_moisture_boost": 0.55,
                "water_moisture_decay_km": 2.0,
                "moisture_noise_amplitude": 0.1,
                "moisture_noise_scale_km": 8.0,
                "vegetation_slope_zero_deg": 45.0,
                "climate": {
                    "mean_temperature_c": 10.0,
                    "north_minus_south_temperature_c": 0.0,
                    "temperature_noise_amplitude_c": 0.0,
                    "mean_annual_precipitation_mm": 800.0,
                    "moisture_transport_bearing_deg": 90.0,
                    "orographic_scale_km": 20.0,
                    "orographic_strength": 1.0,
                    "precipitation_noise_log_amplitude": 0.0,
                    "climate_noise_scale_km": 30.0,
                },
            },
            "features": [],
            "constraints": [],
        }
    )


def _coastal_terrain(rows: int = 15, columns: int = 24) -> np.ndarray:
    result = np.empty((rows, columns), dtype=np.float32)
    center = rows / 2.0
    for row in range(rows):
        y = rows - row - 0.5
        for column in range(columns):
            x = column + 0.5
            # Eastward-sloping land with a broad convergent valley. The eastern
            # part lies below explicit sea level and is connected to the boundary.
            result[row, column] = (
                108.0
                - 7.5 * x
                + 0.30 * (y - center) ** 2
            )
    return result


def _marine_a08_request(*, sea_level_m: float = 0.0) -> GenerationRequest:
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    payload["domain_spec"]["hydrology"]["marine"] = {
        "sea_level_m": sea_level_m,
    }
    return GenerationRequest.model_validate(payload)


def _generate_a08(request: GenerationRequest):
    catalog = load_preset_catalog(A08 / "presets.json")
    return generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry_for_request(request, catalog),
    )


def test_o01_absent_marine_preserves_frozen_a08_fingerprints_and_contract() -> None:
    request = GenerationRequest.model_validate(
        json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    )
    assert request.domain_spec.hydrology.marine is None
    assert domain_spec_fingerprint(request.domain_spec) == (
        "sha256:ae27f9151850fe61e789a182aeaa055cb2c511c2f352bd093c21283901e67bb9"
    )

    catalog = load_preset_catalog(A08 / "presets.json")
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version="0.2.0.dev0",
    )
    assert plan.hydrology.marine is None
    assert semantic_plan_fingerprint(plan) == (
        "sha256:15970c8b771e049ec958f2182419ee1f8316dd73e4e81e9b1014435ed3d6f1d8"
    )

    terrain = TerrainState(elevation_m=_coastal_terrain())
    state = generate_hydrology_v02(
        _plan(*terrain.elevation_m.shape, sea_level_m=None),
        terrain,
    )
    assert state.marine_mask is None
    assert state.marine_candidates == ()
    assert state.marine_features == {}
    assert all(
        node.kind is not RiverNodeKind.MARINE_OUTLET
        for network in (state.river_network, state.potential_river_network)
        if network is not None
        for node in network.nodes.values()
    )


def test_o02_explicit_sea_level_changes_fingerprint_and_negative_land_is_not_implicit_sea() -> None:
    request = _marine_a08_request(sea_level_m=0.0)
    changed = _marine_a08_request(sea_level_m=10.0)
    assert domain_spec_fingerprint(request.domain_spec) != domain_spec_fingerprint(
        changed.domain_spec
    )

    catalog = load_preset_catalog(A08 / "presets.json")
    first_plan = compile_domain_spec(
        request.domain_spec,
        registry=registry_for_request(request, catalog),
        generator_version="0.2-test",
    )
    changed_plan = compile_domain_spec(
        changed.domain_spec,
        registry=registry_for_request(changed, catalog),
        generator_version="0.2-test",
    )
    assert semantic_plan_fingerprint(first_plan) != semantic_plan_fingerprint(
        changed_plan
    )

    negative = np.full((5, 5), 10.0, dtype=np.float32)
    negative[0, 0] = -20.0
    no_marine = generate_hydrology_v02(
        _plan(5, 5, threshold=2.0, sea_level_m=None),
        TerrainState(elevation_m=negative),
    )
    assert no_marine.marine_mask is None


def test_o03_boundary_connected_four_neighbour_marine_classification() -> None:
    terrain = np.full((7, 7), 10.0, dtype=np.float32)

    # Boundary-connected component.
    terrain[0, 1] = -2.0
    terrain[1, 1] = -3.0
    terrain[2, 1] = -4.0

    # Enclosed component.
    terrain[4, 4] = -5.0

    # Diagonal-only contact with boundary water: must remain enclosed under 4-neighbour.
    terrain[1, 3] = -2.0
    terrain[0, 2] = -2.0

    mask, candidates = classify_marine_components(
        terrain,
        sea_level_m=0.0,
        cell_size_km=1.0,
    )

    assert mask[0, 1]
    assert mask[1, 1]
    assert mask[2, 1]
    assert not mask[4, 4]

    # (1,3) is diagonal to boundary cell (0,2), but it may connect through
    # no edge-sharing below-sea path.
    assert not mask[1, 3]
    assert mask[0, 2]
    assert len(candidates) == 1


def test_o04_marine_component_identity_and_geometry_are_deterministic() -> None:
    terrain = _coastal_terrain()
    first_mask, first = classify_marine_components(
        terrain,
        sea_level_m=0.0,
        cell_size_km=1.0,
    )
    second_mask, second = classify_marine_components(
        terrain,
        sea_level_m=0.0,
        cell_size_km=1.0,
    )
    np.testing.assert_array_equal(first_mask, second_mask)
    assert first == second

    plan = _plan(*terrain.shape)
    first_features = materialize_marine_features(plan, first, terrain)
    second_features = materialize_marine_features(plan, second, terrain)
    assert first_features == second_features
    assert tuple(first_features) == tuple(
        marine_feature_id(index) for index in range(len(first))
    )


def test_o05_marine_and_lake_support_are_exclusive_and_enclosed_below_sea_basin_can_be_lake() -> None:
    terrain = np.full((7, 7), 12.0, dtype=np.float64)
    terrain[0, 1] = -3.0
    terrain[1, 1] = -2.0
    terrain[3, 3] = -5.0

    marine, _ = classify_marine_components(
        terrain,
        sea_level_m=0.0,
        cell_size_km=1.0,
    )
    assert marine[0, 1]
    assert marine[1, 1]
    assert not marine[3, 3]

    surfaces = priority_flood_surfaces(terrain)
    lakes = extract_lake_candidates(
        terrain,
        surfaces.fill_elevation_m,
        cell_size_km=1.0,
        lake_min_area_km2=1.0,
        lake_min_depth_m=0.5,
        excluded_mask=marine,
    )
    lake_cells = {cell for candidate in lakes for cell in candidate.cells}
    assert (3, 3) in lake_cells
    assert all(not bool(marine[cell]) for cell in lake_cells)


def test_o06_canonical_water_depth_uses_exact_marine_depth() -> None:
    terrain = np.array(
        [
            [-4.0, -2.0, 5.0],
            [3.0, 4.0, 5.0],
            [5.0, 5.0, 5.0],
        ],
        dtype=np.float64,
    )
    marine, _ = classify_marine_components(
        terrain,
        sea_level_m=0.0,
        cell_size_km=1.0,
    )
    fill = terrain.copy()
    accumulation = np.ones_like(terrain, dtype=np.float64)
    streams = np.zeros_like(terrain, dtype=np.bool_)
    water = build_water_depth_m(
        terrain,
        fill,
        accumulation,
        streams,
        (),
        stream_threshold_km2=1.0,
        river_depth_at_threshold_m=0.5,
        river_depth_exponent=0.3,
        marine_mask=marine,
        sea_level_m=0.0,
    )
    expected = np.zeros_like(terrain, dtype=np.float32)
    expected[marine] = (-terrain[marine]).astype(np.float32)
    np.testing.assert_array_equal(water, expected)


def test_o07_refined_marine_geometry_is_valid_bounded_and_boundary_connected() -> None:
    terrain = _coastal_terrain()
    mask, candidates = classify_marine_components(
        terrain,
        sea_level_m=0.0,
        cell_size_km=1.0,
    )
    assert np.any(mask)
    plan = _plan(*terrain.shape)
    features = materialize_marine_features(plan, candidates, terrain)
    domain_boundary = box(
        0.0,
        0.0,
        plan.domain.width_km,
        plan.domain.height_km,
    ).boundary

    assert features
    for index, candidate in enumerate(candidates):
        feature = features[marine_feature_id(index)]
        geometry = backend_region_set(feature.geometry)._value
        assert geometry.is_valid
        assert geometry.area > 0.0
        assert geometry.area <= candidate.raster_area_km2 + 1e-12
        for polygon in geometry.geoms if hasattr(geometry, "geoms") else (geometry,):
            assert polygon.intersects(domain_boundary)


def test_o08_o09_o10_generated_regional_and_potential_networks_terminate_at_marine_coast() -> None:
    terrain = _coastal_terrain()
    plan = _plan(*terrain.shape, threshold=5.0)
    state = generate_hydrology_v02(
        plan,
        TerrainState(elevation_m=terrain),
    )
    assert state.marine_mask is not None
    assert state.marine_features
    assert state.potential_river_network is not None

    networks = (state.river_network, state.potential_river_network)
    marine_outlets = []
    for network in networks:
        indegree = {node_id: 0 for node_id in network.nodes}
        outdegree = {node_id: 0 for node_id in network.nodes}
        for segment in network.segments.values():
            indegree[segment.to_node] += 1
            outdegree[segment.from_node] += 1

        for node_id, node in network.nodes.items():
            if node.kind is not RiverNodeKind.MARINE_OUTLET:
                continue
            marine_outlets.append(node)
            assert node.feature_id in state.marine_features
            assert node.boundary_side is None
            assert outdegree[node_id] == 0
            assert indegree[node_id] >= 1
            assert (
                region_set_boundary_distance_km(
                    state.marine_features[node.feature_id].geometry,
                    node.position,
                )
                <= 1e-8
            )

        for segment in network.segments.values():
            for point in segment.centerline[:-1]:
                x = min(plan.domain.width_km - 1e-9, max(0.0, point.x_km))
                y = min(plan.domain.height_km - 1e-9, max(0.0, point.y_km))
                row = min(
                    plan.grid.rows - 1,
                    max(0, int((plan.domain.height_km - y) // plan.grid.cell_size_km)),
                )
                column = min(
                    plan.grid.columns - 1,
                    max(0, int(x // plan.grid.cell_size_km)),
                )
                assert not bool(state.marine_mask[row, column])

    assert marine_outlets
    assert not np.any(state.channel_skeleton_mask & state.marine_mask)
    assert not np.any(state.potential_channel_skeleton_mask & state.marine_mask)


def test_o11_public_marine_contract_exports_mask_and_distinct_features() -> None:
    assembly = _generate_a08(_marine_a08_request(sea_level_m=0.0))
    descriptor = assembly.data.fields["marine_mask"]
    payload = assembly.field_payloads["marine_mask"]

    assert descriptor.role is FieldRole.DERIVED
    assert descriptor.dtype == "uint8"
    assert descriptor.unit == "binary"
    assert payload.dtype == np.dtype(np.uint8)
    assert set(np.unique(payload)).issubset({0, 1})

    marine_features = {
        feature_id: feature
        for feature_id, feature in assembly.data.features.items()
        if isinstance(feature, MarineFeature)
    }
    assert marine_features
    for network in assembly.data.networks.values():
        for node in network.nodes.values():
            if node.kind is RiverNodeKind.MARINE_OUTLET:
                assert node.feature_id in marine_features


def test_o12_marine_propagates_only_through_already_accepted_environmental_dependencies() -> None:
    base = GenerationRequest.model_validate(
        json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    )
    marine = _marine_a08_request(sea_level_m=0.0)
    inland_assembly = _generate_a08(base)
    marine_assembly = _generate_a08(marine)

    # Marine topology cannot alter atmospheric climate generation.
    for field_id in ("temperature", "annual_precipitation"):
        np.testing.assert_array_equal(
            marine_assembly.field_payloads[field_id],
            inland_assembly.field_payloads[field_id],
        )

    mask = marine_assembly.field_payloads["marine_mask"].astype(bool)
    assert np.any(mask)
    np.testing.assert_array_equal(
        marine_assembly.field_payloads["moisture"][mask],
        np.ones(int(np.count_nonzero(mask)), dtype=np.float32),
    )
    np.testing.assert_array_equal(
        marine_assembly.field_payloads["vegetation_density"][mask],
        np.zeros(int(np.count_nonzero(mask)), dtype=np.float32),
    )


def test_o13_marine_generation_replays_exactly() -> None:
    request = _marine_a08_request(sea_level_m=0.0)
    first = _generate_a08(request)
    replay = _generate_a08(request)

    assert first.data == replay.data
    assert set(first.field_payloads) == set(replay.field_payloads)
    for field_id in first.field_payloads:
        np.testing.assert_array_equal(
            first.field_payloads[field_id],
            replay.field_payloads[field_id],
        )


def test_core_v01_rejects_marine_spec() -> None:
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))[
        "domain_spec"
    ]
    payload["schema_version"] = "0.1"
    payload["terrain"] = None
    payload["surface"]["climate"] = None
    payload["hydrology"]["marine"] = {"sea_level_m": 0.0}
    with pytest.raises(ValidationError, match="hydrology.marine is only valid"):
        DomainSpec.model_validate(payload)
