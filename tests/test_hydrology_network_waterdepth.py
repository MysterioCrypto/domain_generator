from __future__ import annotations

import numpy as np
import pytest

from domain_generator.contracts.data import BoundarySide, RiverNodeKind
from domain_generator.contracts.plan import GenerationPlan, PlanDomain, PlanGrid, PlanHydrology, PlanSource
from domain_generator.hydrology import (
    LakeCandidate,
    build_river_network,
    build_water_depth_m,
    river_depth_proxy_m,
)


def make_plan(*, rows: int, columns: int, cell_size_km: float = 1.0) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="hydrology-network-test",
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
            stream_threshold_km2=1.0,
            lake_min_area_km2=1.0,
            lake_min_depth_m=1.0,
            river_depth_at_threshold_m=0.5,
            river_depth_exponent=0.5,
        ),
        features=(),
        constraints=(),
    )


def blank_direction(rows: int, columns: int) -> np.ndarray:
    return np.full((rows, columns), -1, dtype=np.int8)


def test_simple_stream_chain_compresses_to_source_and_domain_outlet() -> None:
    plan = make_plan(rows=3, columns=5)
    direction = blank_direction(3, 5)
    direction[1, 1] = 2  # E
    direction[1, 2] = 2
    direction[1, 3] = 2
    accumulation = np.ones((3, 5), dtype=np.float64)
    accumulation[1, 1:5] = [1.0, 2.0, 3.0, 4.0]
    stream = np.zeros((3, 5), dtype=np.bool_)
    stream[1, 1:5] = True

    network = build_river_network(plan, direction, accumulation, stream, ())

    assert len(network.nodes) == 2
    assert len(network.segments) == 1
    kinds = {node.kind for node in network.nodes.values()}
    assert kinds == {RiverNodeKind.SOURCE, RiverNodeKind.DOMAIN_OUTLET}
    outlet = next(node for node in network.nodes.values() if node.kind is RiverNodeKind.DOMAIN_OUTLET)
    assert outlet.boundary_side is BoundarySide.EAST
    assert outlet.position.x_km == pytest.approx(5.0)
    segment = next(iter(network.segments.values()))
    assert len(segment.centerline) == 5
    assert segment.properties.catchment_area_km2 == pytest.approx(4.0)


def test_two_tributaries_create_confluence() -> None:
    plan = make_plan(rows=5, columns=5)
    direction = blank_direction(5, 5)
    direction[1, 1] = 3  # SE -> (2,2)
    direction[1, 3] = 5  # SW -> (2,2)
    direction[2, 2] = 4  # S
    direction[3, 2] = 4  # S -> edge outlet
    accumulation = np.ones((5, 5), dtype=np.float64)
    accumulation[1, 1] = 1.0
    accumulation[1, 3] = 1.0
    accumulation[2, 2] = 3.0
    accumulation[3, 2] = 4.0
    accumulation[4, 2] = 5.0
    stream = np.zeros((5, 5), dtype=np.bool_)
    for cell in ((1, 1), (1, 3), (2, 2), (3, 2), (4, 2)):
        stream[cell] = True

    network = build_river_network(plan, direction, accumulation, stream, ())

    kinds = [node.kind for node in network.nodes.values()]
    assert kinds.count(RiverNodeKind.SOURCE) == 2
    assert kinds.count(RiverNodeKind.CONFLUENCE) == 1
    assert kinds.count(RiverNodeKind.DOMAIN_OUTLET) == 1
    assert len(network.segments) == 3


def test_lake_splits_visible_river_into_inflow_and_outlet_segments() -> None:
    plan = make_plan(rows=5, columns=5)
    direction = blank_direction(5, 5)
    direction[1, 2] = 4  # stream -> lake
    direction[2, 2] = 4  # lake -> outside stream
    direction[3, 2] = 4  # outside stream -> edge
    accumulation = np.ones((5, 5), dtype=np.float64)
    accumulation[1, 2] = 1.0
    accumulation[2, 2] = 2.0
    accumulation[3, 2] = 3.0
    accumulation[4, 2] = 4.0
    stream = np.zeros((5, 5), dtype=np.bool_)
    stream[1:5, 2] = True
    lake = LakeCandidate(
        cells=((2, 2),),
        area_km2=1.0,
        max_depth_m=5.0,
        surface_elevation_m=10.0,
    )

    network = build_river_network(plan, direction, accumulation, stream, (lake,))

    kinds = {node.kind for node in network.nodes.values()}
    assert RiverNodeKind.LAKE_INFLOW in kinds
    assert RiverNodeKind.LAKE_OUTLET in kinds
    assert len(network.segments) == 2
    assert all(
        not (
            segment.centerline[0].x_km == pytest.approx(2.5)
            and segment.centerline[-1].x_km == pytest.approx(2.5)
            and segment.centerline[0].y_km > 2.5 > segment.centerline[-1].y_km
        )
        for segment in network.segments.values()
    )
    lake_nodes = [
        node
        for node in network.nodes.values()
        if node.kind in {RiverNodeKind.LAKE_INFLOW, RiverNodeKind.LAKE_OUTLET}
    ]
    assert {node.feature_id for node in lake_nodes} == {"lake-0001"}


def test_lake_outlet_plus_ordinary_tributary_creates_effective_confluence() -> None:
    plan = make_plan(rows=4, columns=5)
    direction = blank_direction(4, 5)
    direction[1, 1] = 3  # lake -> (2,2)
    direction[1, 3] = 5  # ordinary tributary -> (2,2)
    direction[2, 2] = 4  # -> edge
    accumulation = np.ones((4, 5), dtype=np.float64)
    accumulation[1, 1] = 1.0
    accumulation[1, 3] = 1.0
    accumulation[2, 2] = 3.0
    accumulation[3, 2] = 4.0
    stream = np.zeros((4, 5), dtype=np.bool_)
    for cell in ((1, 1), (1, 3), (2, 2), (3, 2)):
        stream[cell] = True
    lake = LakeCandidate(
        cells=((1, 1),),
        area_km2=1.0,
        max_depth_m=2.0,
        surface_elevation_m=10.0,
    )

    network = build_river_network(plan, direction, accumulation, stream, (lake,))

    confluences = [node for node in network.nodes.values() if node.kind is RiverNodeKind.CONFLUENCE]
    assert len(confluences) == 1
    assert confluences[0].position.x_km == pytest.approx(2.5)
    assert confluences[0].position.y_km == pytest.approx(1.5)

    lake_outlet_id = next(
        node_id
        for node_id, node in network.nodes.items()
        if node.kind is RiverNodeKind.LAKE_OUTLET
    )
    confluence_id = next(
        node_id
        for node_id, node in network.nodes.items()
        if node.kind is RiverNodeKind.CONFLUENCE
    )
    lake_branch = next(
        segment
        for segment in network.segments.values()
        if segment.from_node == lake_outlet_id and segment.to_node == confluence_id
    )
    assert lake_branch.properties.catchment_area_km2 == pytest.approx(1.0)


def test_corner_domain_outlet_uses_north_east_south_west_precedence() -> None:
    plan = make_plan(rows=3, columns=3)
    direction = blank_direction(3, 3)
    accumulation = np.ones((3, 3), dtype=np.float64)
    stream = np.zeros((3, 3), dtype=np.bool_)
    stream[0, 2] = True

    network = build_river_network(plan, direction, accumulation, stream, ())

    outlet = next(node for node in network.nodes.values() if node.kind is RiverNodeKind.DOMAIN_OUTLET)
    assert outlet.boundary_side is BoundarySide.NORTH
    assert outlet.position.y_km == pytest.approx(3.0)


def test_river_depth_proxy_scales_from_threshold() -> None:
    assert river_depth_proxy_m(
        4.0,
        stream_threshold_km2=4.0,
        river_depth_at_threshold_m=0.5,
        river_depth_exponent=0.5,
    ) == pytest.approx(0.5)
    assert river_depth_proxy_m(
        16.0,
        stream_threshold_km2=4.0,
        river_depth_at_threshold_m=0.5,
        river_depth_exponent=0.5,
    ) == pytest.approx(1.0)


def test_water_depth_gives_accepted_lake_precedence_over_stream_proxy() -> None:
    terrain = np.full((3, 3), 10.0, dtype=np.float32)
    terrain[1, 1] = 2.0
    fill = np.full((3, 3), 10.0, dtype=np.float64)
    accumulation = np.ones((3, 3), dtype=np.float64)
    accumulation[1, 0] = 1.0
    accumulation[1, 1] = 4.0
    accumulation[1, 2] = 9.0
    stream = np.zeros((3, 3), dtype=np.bool_)
    stream[1, :] = True
    lake = LakeCandidate(
        cells=((1, 1),),
        area_km2=1.0,
        max_depth_m=8.0,
        surface_elevation_m=10.0,
    )

    depth = build_water_depth_m(
        terrain,
        fill,
        accumulation,
        stream,
        (lake,),
        stream_threshold_km2=1.0,
        river_depth_at_threshold_m=0.5,
        river_depth_exponent=0.5,
    )

    assert depth.dtype == np.float32
    assert depth[1, 0] == pytest.approx(0.5)
    assert depth[1, 1] == pytest.approx(8.0)
    assert depth[1, 2] == pytest.approx(1.5)
    assert depth[0, 0] == 0.0
