from __future__ import annotations

import numpy as np

from domain_generator.contracts.plan import GenerationPlan, PlanDomain, PlanGrid, PlanHydrology, PlanSource
from domain_generator.hydrology import (
    LakeCandidate,
    classify_stream_mask,
    extract_lake_candidates,
    generate_hydrology,
    priority_flood_surfaces,
    validate_hydrology,
)
from domain_generator.terrain.state import TerrainState


def make_plan(
    *,
    rows: int,
    columns: int,
    cell_size_km: float = 1.0,
    stream_threshold_km2: float = 3.0,
    lake_min_area_km2: float = 1.0,
    lake_min_depth_m: float = 1.0,
    river_depth_at_threshold_m: float = 0.5,
    river_depth_exponent: float = 0.3,
) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="hydrology-classification-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=123456,
        domain=PlanDomain(
            width_km=columns * cell_size_km,
            height_km=rows * cell_size_km,
        ),
        grid=PlanGrid(
            cell_size_km=cell_size_km,
            rows=rows,
            columns=columns,
        ),
        hydrology=PlanHydrology(
            stream_threshold_km2=stream_threshold_km2,
            lake_min_area_km2=lake_min_area_km2,
            lake_min_depth_m=lake_min_depth_m,
            river_depth_at_threshold_m=river_depth_at_threshold_m,
            river_depth_exponent=river_depth_exponent,
        ),
        features=(),
        constraints=(),
    )


def test_priority_flood_separates_physical_fill_from_routing_gradient() -> None:
    elevation = np.array(
        [
            [10.0, 10.0, 10.0],
            [10.0, 2.0, 10.0],
            [10.0, 10.0, 10.0],
        ],
        dtype=np.float32,
    )

    surfaces = priority_flood_surfaces(elevation)

    assert surfaces.fill_elevation_m[1, 1] == 10.0
    assert surfaces.routing_elevation_m[1, 1] > surfaces.fill_elevation_m[1, 1]
    assert surfaces.routing_elevation_m[1, 1] == np.nextafter(
        np.float64(10.0), np.float64(np.inf)
    )


def test_stream_mask_uses_physical_catchment_threshold() -> None:
    accumulation = np.array(
        [
            [0.25, 1.0, 2.99],
            [3.0, 4.0, 10.0],
        ],
        dtype=np.float64,
    )

    mask = classify_stream_mask(accumulation, stream_threshold_km2=3.0)

    expected = np.array(
        [
            [False, False, False],
            [True, True, True],
        ],
        dtype=np.bool_,
    )
    assert np.array_equal(mask, expected)


def test_lake_candidate_uses_fill_depth_and_physical_area() -> None:
    terrain = np.array(
        [
            [10, 10, 10, 10, 10],
            [10, 8, 8, 8, 10],
            [10, 8, 2, 8, 10],
            [10, 8, 8, 8, 10],
            [10, 10, 10, 10, 10],
        ],
        dtype=np.float32,
    )
    fill = priority_flood_surfaces(terrain).fill_elevation_m

    candidates = extract_lake_candidates(
        terrain,
        fill,
        cell_size_km=0.5,
        lake_min_area_km2=2.0,
        lake_min_depth_m=5.0,
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.cells[0] == (1, 1)
    assert len(candidate.cells) == 9
    assert candidate.area_km2 == 2.25
    assert candidate.max_depth_m == 8.0
    assert candidate.surface_elevation_m == 10.0


def test_lake_thresholds_filter_small_or_shallow_depressions() -> None:
    terrain = np.array(
        [
            [10, 10, 10, 10, 10],
            [10, 8, 8, 8, 10],
            [10, 8, 2, 8, 10],
            [10, 8, 8, 8, 10],
            [10, 10, 10, 10, 10],
        ],
        dtype=np.float32,
    )
    fill = priority_flood_surfaces(terrain).fill_elevation_m

    too_large = extract_lake_candidates(
        terrain,
        fill,
        cell_size_km=0.5,
        lake_min_area_km2=2.5,
        lake_min_depth_m=1.0,
    )
    too_deep = extract_lake_candidates(
        terrain,
        fill,
        cell_size_km=0.5,
        lake_min_area_km2=1.0,
        lake_min_depth_m=9.0,
    )

    assert too_large == ()
    assert too_deep == ()


def test_lake_candidates_have_canonical_component_and_candidate_order() -> None:
    terrain = np.array(
        [
            [10, 10, 10, 10, 10, 10, 10],
            [10, 1, 10, 10, 10, 2, 10],
            [10, 10, 10, 10, 10, 10, 10],
            [10, 10, 10, 10, 10, 10, 10],
            [10, 10, 10, 10, 10, 10, 10],
        ],
        dtype=np.float32,
    )
    fill = priority_flood_surfaces(terrain).fill_elevation_m

    candidates = extract_lake_candidates(
        terrain,
        fill,
        cell_size_km=1.0,
        lake_min_area_km2=1.0,
        lake_min_depth_m=1.0,
    )

    assert tuple(candidate.cells[0] for candidate in candidates) == ((1, 1), (1, 5))
    assert candidates[0].cells == ((1, 1),)
    assert candidates[1].cells == ((1, 5),)


def test_generate_hydrology_materializes_stream_and_lake_classification() -> None:
    plan = make_plan(
        rows=5,
        columns=5,
        cell_size_km=1.0,
        stream_threshold_km2=2.0,
        lake_min_area_km2=1.0,
        lake_min_depth_m=1.0,
    )
    terrain = TerrainState(
        elevation_m=np.array(
            [
                [10, 10, 10, 10, 10],
                [10, 8, 8, 8, 10],
                [10, 8, 2, 8, 10],
                [10, 8, 8, 8, 10],
                [10, 10, 10, 10, 10],
            ],
            dtype=np.float32,
        )
    )

    state = generate_hydrology(plan, terrain)
    validation = validate_hydrology(plan, terrain, state, attempt_index=0)

    assert state.fill_elevation_m.dtype == np.float64
    assert state.stream_mask.dtype == np.bool_
    assert state.water_depth_m.dtype == np.float32
    assert state.lake_candidates == (
        LakeCandidate(
            cells=(
                (1, 1), (1, 2), (1, 3),
                (2, 1), (2, 2), (2, 3),
                (3, 1), (3, 2), (3, 3),
            ),
            area_km2=9.0,
            max_depth_m=8.0,
            surface_elevation_m=10.0,
        ),
    )
    assert validation.engine_invariants.passed is True


def test_validation_rejects_tampered_stream_mask() -> None:
    plan = make_plan(rows=3, columns=3, stream_threshold_km2=1.0)
    terrain = TerrainState(
        elevation_m=np.array(
            [
                [3.0, 3.0, 3.0],
                [3.0, 1.0, 3.0],
                [3.0, 3.0, 3.0],
            ],
            dtype=np.float32,
        )
    )
    state = generate_hydrology(plan, terrain)
    tampered = state.stream_mask.copy()
    tampered[0, 0] = not bool(tampered[0, 0])
    mutated = type(state)(
        routing_elevation_m=state.routing_elevation_m,
        fill_elevation_m=state.fill_elevation_m,
        flow_direction=state.flow_direction,
        flow_accumulation_km2=state.flow_accumulation_km2,
        stream_mask=tampered,
        lake_candidates=state.lake_candidates,
        river_network=state.river_network,
        water_depth_m=state.water_depth_m,
    )

    validation = validate_hydrology(plan, terrain, mutated, attempt_index=0)
    invariant = next(
        result
        for result in validation.engine_invariants.results
        if result.id == "hydrology-stream-threshold-classification"
    )
    assert invariant.passed is False
