from __future__ import annotations

from math import atan2, cos, pi, sin

import numpy as np

from domain_generator.contracts.plan import GenerationPlan
from domain_generator.hydrology import ContinuousRoutingField, build_continuous_river_network
from domain_generator.hydrology.continuous import (
    _activate_channel_skeleton,
    _strahler_order_field,
    _terrain_aware_initiation,
    choose_lake_outlets,
    continuous_routing_field,
    distributed_flow_accumulation_km2,
    generate_hydrology_v02,
)
from domain_generator.hydrology.classification import classify_stream_mask, extract_lake_candidates
from domain_generator.hydrology.depression_hierarchy import build_nested_depression_hierarchy
from domain_generator.hydrology.ids import lake_feature_id
from domain_generator.geometry import region_set_boundary_distance_km
from domain_generator.hydrology.materialize import materialize_lake_features, refined_lake_region_set
from domain_generator.hydrology.routing import priority_flood_surfaces
from domain_generator.hydrology.state import LakeCandidate, LakeOutlet
from domain_generator.terrain.state import TerrainState


def _plan(rows: int, columns: int, *, threshold: float = 8.0) -> GenerationPlan:
    return GenerationPlan.model_validate(
        {
            "plan_version": "0.2",
            "source": {
                "spec_id": "hydrology-v02-test",
                "spec_schema_version": "0.2",
                "spec_fingerprint": "sha256:test",
                "generator_version": "0.1.0.dev0",
            },
            "seed": 7,
            "domain": {"width_km": float(columns), "height_km": float(rows)},
            "grid": {"cell_size_km": 1.0, "rows": rows, "columns": columns},
            "terrain": {
                "base_elevation_m": 100.0,
                "noise_layers": [{"id": "test", "scale_km": 10.0, "amplitude_m": 1.0}],
            },
            "hydrology": {
                "stream_threshold_km2": threshold,
                "lake_min_area_km2": 1.0,
                "lake_min_depth_m": 0.5,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
            },
            "surface": {
                "moisture_base": 0.3,
                "water_moisture_boost": 0.4,
                "water_moisture_decay_km": 5.0,
                "moisture_noise_amplitude": 0.1,
                "moisture_noise_scale_km": 5.0,
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


def _plane(rows: int, columns: int, angle_rad: float, slope: float = 2.0) -> np.ndarray:
    result = np.empty((rows, columns), dtype=np.float64)
    for row in range(rows):
        y = rows - row - 0.5
        for column in range(columns):
            x = column + 0.5
            result[row, column] = 1000.0 - slope * (
                x * cos(angle_rad) + y * sin(angle_rad)
            )
    return result


def _angle_error(actual: np.ndarray, expected: float) -> np.ndarray:
    return np.abs((actual - expected + pi) % (2.0 * pi) - pi)


def test_h05_oblique_planar_slope_is_not_quantized_to_d8() -> None:
    target = np.deg2rad(23.0)
    routing = _plane(31, 31, target)

    field = continuous_routing_field(routing, cell_size_km=1.0)

    interior = field.flow_angle_rad[4:-4, 4:-4]
    assert float(np.max(_angle_error(interior, target))) < np.deg2rad(0.05)
    grid_distance = np.abs(interior / (pi / 4.0) - np.rint(interior / (pi / 4.0)))
    assert float(np.min(grid_distance)) > 0.20
    fractions = np.sum(field.fractions[4:-4, 4:-4, :], axis=2)
    np.testing.assert_allclose(fractions, 1.0, rtol=0.0, atol=1e-12)
    positive_receivers = np.count_nonzero(field.fractions[15, 15, :] > 0.0)
    assert positive_receivers >= 3


def _sloping_valley(rows: int, columns: int, angle_rad: float) -> np.ndarray:
    cx = columns / 2.0
    cy = rows / 2.0
    result = np.empty((rows, columns), dtype=np.float64)
    ux, uy = cos(angle_rad), sin(angle_rad)
    vx, vy = -uy, ux
    for row in range(rows):
        y = rows - row - 0.5 - cy
        for column in range(columns):
            x = column + 0.5 - cx
            downstream = x * ux + y * uy
            cross = x * vx + y * vy
            result[row, column] = 800.0 - 1.4 * downstream + 0.08 * cross * cross
    return result


def test_h06_rotated_valley_preserves_continuous_flow_orientation() -> None:
    rotation = np.deg2rad(27.0)
    base = continuous_routing_field(_sloping_valley(61, 61, 0.0), cell_size_km=1.0)
    rotated = continuous_routing_field(_sloping_valley(61, 61, rotation), cell_size_km=1.0)

    # Triangular-facet discretization may introduce a small sub-degree error, but a
    # D8 backend would snap this 27-degree valley by many degrees to 0/45 degrees.
    # Slope-weighted MFD uses all downslope neighbours, so the resultant vector
    # is a low-bias approximation rather than the exact facet gradient.
    tolerance = np.deg2rad(1.5)
    center_base = float(base.flow_angle_rad[30, 30])
    center_rotated = float(rotated.flow_angle_rad[30, 30])
    assert float(_angle_error(np.array([center_base]), 0.0)[0]) < tolerance
    assert float(_angle_error(np.array([center_rotated]), rotation)[0]) < tolerance
    observed_rotation = (center_rotated - center_base) % (2.0 * pi)
    assert abs(observed_rotation - rotation) < tolerance


def test_h07_lake_supernode_has_one_outlet_and_aggregates_catchment() -> None:
    rows = columns = 21
    terrain = np.empty((rows, columns), dtype=np.float64)
    for row in range(rows):
        y = rows - row - 0.5
        for column in range(columns):
            x = column + 0.5
            terrain[row, column] = 200.0 - 0.8 * x + 0.03 * (y - 10.5) ** 2
    terrain[8:13, 8:13] -= 18.0

    surfaces = priority_flood_surfaces(terrain)
    lakes = extract_lake_candidates(
        terrain,
        surfaces.fill_elevation_m,
        cell_size_km=1.0,
        lake_min_area_km2=2.0,
        lake_min_depth_m=1.0,
    )
    assert len(lakes) == 1
    field = continuous_routing_field(surfaces.routing_elevation_m, cell_size_km=1.0)
    outlets = choose_lake_outlets(
        terrain,
        surfaces.routing_elevation_m,
        field,
        lakes,
    )
    assert len(outlets) == 1

    accumulation = distributed_flow_accumulation_km2(
        field,
        cell_size_km=1.0,
        lake_candidates=lakes,
        lake_outlets=outlets,
    )
    lake_total = float(accumulation[lakes[0].cells[0]])
    assert lake_total >= lakes[0].area_km2
    np.testing.assert_allclose(
        [accumulation[cell] for cell in lakes[0].cells],
        lake_total,
        rtol=0.0,
        atol=1e-10,
    )
    assert float(accumulation[outlets[0].receiver_cell]) >= lake_total


def _merging_valleys(rows: int, columns: int) -> np.ndarray:
    result = np.empty((rows, columns), dtype=np.float64)
    center = rows / 2.0
    for row in range(rows):
        y = rows - row - 0.5
        for column in range(columns):
            x = column + 0.5
            convergence = max(0.0, 1.0 - x / (columns * 0.68))
            separation = 7.0 * convergence
            valley_a = (y - (center - separation)) ** 2
            valley_b = (y - (center + separation)) ** 2
            cross = min(valley_a, valley_b)
            # Preserve the branching geometry while scaling relief into the
            # terrain-aware initiation regime (~5% longitudinal grade).
            result[row, column] = 900.0 - 50.0 * x + 2.25 * cross
    return result


def test_h08_branching_catchment_forms_confluence_without_downstream_split() -> None:
    rows, columns = 45, 70
    plan = _plan(rows, columns, threshold=7.0)
    routing = _merging_valleys(rows, columns)
    field = continuous_routing_field(routing, cell_size_km=1.0)
    accumulation = distributed_flow_accumulation_km2(
        field,
        cell_size_km=1.0,
        lake_candidates=(),
        lake_outlets=(),
    )
    support = classify_stream_mask(accumulation, stream_threshold_km2=7.0)

    network, stream_mask = build_continuous_river_network(
        plan,
        field,
        accumulation,
        support,
        (),
        (),
    )

    assert np.count_nonzero(stream_mask) > 0
    confluences = {
        node_id
        for node_id, node in network.nodes.items()
        if node.kind.value == "confluence"
    }
    assert confluences
    outdegree = {node_id: 0 for node_id in network.nodes}
    indegree = {node_id: 0 for node_id in network.nodes}
    all_bearings: list[float] = []
    for segment in network.segments.values():
        outdegree[segment.from_node] += 1
        indegree[segment.to_node] += 1
        points = segment.centerline
        assert len(points) >= 2
        for first, second in zip(points, points[1:]):
            dx = second.x_km - first.x_km
            dy = second.y_km - first.y_km
            if abs(dx) + abs(dy) > 1e-9:
                all_bearings.append(atan2(dy, dx) % (2.0 * pi))

    # Individual rivers are allowed to be genuinely cardinal. The network as a whole,
    # however, must contain substantial non-D8 geometry on this oblique/merging fixture.
    assert all_bearings
    non_grid = [
        angle
        for angle in all_bearings
        if abs(angle / (pi / 4.0) - round(angle / (pi / 4.0))) > 0.03
    ]
    assert len(non_grid) / len(all_bearings) >= 0.20
    assert all(outdegree[node_id] <= 1 for node_id in network.nodes)
    assert all(indegree[node_id] >= 2 for node_id in confluences)



def test_i01_area_slope_and_convergence_control_source_eligibility() -> None:
    shape = (5, 5)
    fractions = np.zeros((5, 5, 8), dtype=np.float64)

    # Convergent centre: two upstream neighbours each send 0.7 into (2,2).
    fractions[2, 1, 0] = 0.7  # east
    fractions[1, 2, 6] = 0.7  # south

    slope = np.full(shape, 0.02, dtype=np.float64)
    slope[2, 2] = 0.10
    field = ContinuousRoutingField(
        flow_angle_rad=np.zeros(shape, dtype=np.float64),
        fractions=fractions,
        local_slope=slope,
    )
    channel_area = np.full(shape, 100.0, dtype=np.float64)

    convergence, score, eligible = _terrain_aware_initiation(
        field,
        channel_area,
        stream_threshold_km2=150.0,
    )

    assert convergence[2, 2] > 1.0
    assert score[2, 2] > 150.0
    assert bool(eligible[2, 2])
    assert not bool(eligible[3, 3])


def test_i02_fixed_area_baseline_is_preserved_on_planar_terrain() -> None:
    shape = (5, 5)
    fractions = np.zeros((5, 5, 8), dtype=np.float64)
    for row in range(1, 4):
        for column in range(0, 4):
            fractions[row, column, 0] = 1.0  # uniform east flow

    field = ContinuousRoutingField(
        flow_angle_rad=np.zeros(shape, dtype=np.float64),
        fractions=fractions,
        local_slope=np.full(shape, 0.005, dtype=np.float64),
    )
    channel_area = np.full(shape, 200.0, dtype=np.float64)

    convergence, score, eligible = _terrain_aware_initiation(
        field,
        channel_area,
        stream_threshold_km2=150.0,
    )

    assert abs(float(convergence[2, 2]) - 1.0) < 1e-12
    assert score[2, 2] < 150.0
    assert bool(eligible[2, 2])


def test_i02b_subthreshold_planar_cell_is_not_promoted_by_slope_alone() -> None:
    shape = (5, 5)
    fractions = np.zeros((5, 5, 8), dtype=np.float64)
    for row in range(1, 4):
        for column in range(0, 4):
            fractions[row, column, 0] = 1.0

    field = ContinuousRoutingField(
        flow_angle_rad=np.zeros(shape, dtype=np.float64),
        fractions=fractions,
        local_slope=np.full(shape, 0.20, dtype=np.float64),
    )
    channel_area = np.full(shape, 100.0, dtype=np.float64)

    convergence, score, eligible = _terrain_aware_initiation(
        field,
        channel_area,
        stream_threshold_km2=150.0,
    )

    assert score[2, 2] > 150.0
    assert abs(float(convergence[2, 2]) - 1.0) < 1e-12
    assert not bool(eligible[2, 2])


def test_i03_active_channel_does_not_restart_downstream() -> None:
    shape = (3, 6)
    receiver = np.full(shape, -1, dtype=np.int32)
    columns = shape[1]
    for column in range(1, 5):
        receiver[1, column] = np.int32(1 * columns + column + 1)

    eligible = np.zeros(shape, dtype=np.bool_)
    eligible[1, 1] = True
    eligible[1, 3] = True

    skeleton, sources, confluences = _activate_channel_skeleton(
        receiver,
        eligible,
        lake_candidates=(),
        lake_outlets=(),
    )

    assert sources == {(1, 1)}
    assert not confluences
    assert all(bool(skeleton[1, column]) for column in range(1, 6))



def test_m02_strahler_equal_order_merge_increments() -> None:
    shape = (5, 5)
    receiver = np.full(shape, -1, dtype=np.int32)
    columns = shape[1]
    receiver[1, 1] = np.int32(2 * columns + 2)
    receiver[1, 3] = np.int32(2 * columns + 2)
    receiver[2, 2] = np.int32(3 * columns + 2)
    receiver[3, 2] = np.int32(4 * columns + 2)

    skeleton = np.zeros(shape, dtype=np.bool_)
    for cell in ((1, 1), (1, 3), (2, 2), (3, 2), (4, 2)):
        skeleton[cell] = True

    hierarchy = _strahler_order_field(
        receiver,
        skeleton,
        lake_candidates=(),
        lake_outlets=(),
    )

    assert hierarchy.cell_order[1, 1] == 1
    assert hierarchy.cell_order[1, 3] == 1
    assert hierarchy.cell_order[2, 2] == 2
    assert hierarchy.cell_order[4, 2] == 2


def test_m03_strahler_unequal_merge_keeps_higher_order() -> None:
    shape = (7, 7)
    receiver = np.full(shape, -1, dtype=np.int32)
    columns = shape[1]

    # Two order-1 branches form order 2 at (2,3).
    receiver[1, 2] = np.int32(2 * columns + 3)
    receiver[1, 4] = np.int32(2 * columns + 3)
    receiver[2, 3] = np.int32(3 * columns + 3)

    # A separate order-1 tributary joins the order-2 trunk at (4,3).
    receiver[3, 1] = np.int32(4 * columns + 3)
    receiver[3, 3] = np.int32(4 * columns + 3)
    receiver[4, 3] = np.int32(5 * columns + 3)
    receiver[5, 3] = np.int32(6 * columns + 3)

    skeleton = np.zeros(shape, dtype=np.bool_)
    for cell in ((1, 2), (1, 4), (2, 3), (3, 3), (3, 1), (4, 3), (5, 3), (6, 3)):
        skeleton[cell] = True

    hierarchy = _strahler_order_field(
        receiver,
        skeleton,
        lake_candidates=(),
        lake_outlets=(),
    )

    assert hierarchy.cell_order[2, 3] == 2
    assert hierarchy.cell_order[3, 1] == 1
    assert hierarchy.cell_order[4, 3] == 2
    assert hierarchy.cell_order[6, 3] == 2


def test_m05_strahler_order_passes_through_lake_supernode() -> None:
    shape = (6, 5)
    columns = shape[1]
    receiver = np.full(shape, -1, dtype=np.int32)
    lake_cell = (2, 2)
    outlet_receiver = (3, 2)

    receiver[1, 1] = np.int32(lake_cell[0] * columns + lake_cell[1])
    receiver[1, 3] = np.int32(lake_cell[0] * columns + lake_cell[1])
    receiver[3, 2] = np.int32(4 * columns + 2)
    receiver[4, 2] = np.int32(5 * columns + 2)

    skeleton = np.zeros(shape, dtype=np.bool_)
    for cell in ((1, 1), (1, 3), (3, 2), (4, 2), (5, 2)):
        skeleton[cell] = True

    lake = LakeCandidate(
        cells=(lake_cell,),
        area_km2=1.0,
        max_depth_m=2.0,
        surface_elevation_m=100.0,
    )
    outlet = LakeOutlet(
        lake_id=lake_feature_id(0),
        lake_cell=lake_cell,
        receiver_cell=outlet_receiver,
        saddle_elevation_m=100.0,
    )

    hierarchy = _strahler_order_field(
        receiver,
        skeleton,
        lake_candidates=(lake,),
        lake_outlets=(outlet,),
    )

    assert hierarchy.lake_order[lake_feature_id(0)] == 2
    assert hierarchy.cell_order[outlet_receiver] == 2
    assert hierarchy.cell_order[5, 2] == 2



def test_l01_l03_refined_lake_shoreline_is_deterministic_and_contained() -> None:
    plan = _plan(7, 7)
    terrain = np.full((7, 7), 120.0, dtype=np.float64)
    cells = tuple(
        (row, column)
        for row in range(2, 5)
        for column in range(2, 5)
    )
    for cell in cells:
        terrain[cell] = 90.0
    candidate = LakeCandidate(
        cells=cells,
        area_km2=9.0,
        max_depth_m=10.0,
        surface_elevation_m=100.0,
    )

    first = refined_lake_region_set(plan, candidate, terrain, subdivision=4)
    second = refined_lake_region_set(plan, candidate, terrain, subdivision=4)
    assert first == second

    features = materialize_lake_features(
        plan,
        (candidate,),
        terrain_elevation_m=terrain,
        shoreline_subdivision=4,
    )
    feature = features[lake_feature_id(0)]
    assert feature.geometry == first
    assert 0.0 < float(feature.properties.area_km2) <= 9.0
    assert float(feature.properties.area_km2) < 9.0


def test_l05_l08_generated_lake_nodes_lie_on_refined_shoreline() -> None:
    rows = columns = 21
    plan = _plan(rows, columns, threshold=7.0)
    terrain = np.empty((rows, columns), dtype=np.float64)
    for row in range(rows):
        y = rows - row - 0.5
        for column in range(columns):
            x = column + 0.5
            terrain[row, column] = 200.0 - 0.8 * x + 0.03 * (y - 10.5) ** 2
    terrain[8:13, 8:13] -= 18.0

    hydrology = generate_hydrology_v02(
        plan,
        TerrainState(elevation_m=terrain),
    )
    assert len(hydrology.lake_candidates) == 1
    lake_id = lake_feature_id(0)
    feature = hydrology.lake_features[lake_id]
    assert 0.0 < float(feature.properties.area_km2) <= hydrology.lake_candidates[0].area_km2

    networks = [hydrology.river_network]
    assert hydrology.potential_river_network is not None
    networks.append(hydrology.potential_river_network)
    seen_lake_node = False
    for network in networks:
        for node in network.nodes.values():
            if node.feature_id != lake_id:
                continue
            seen_lake_node = True
            assert region_set_boundary_distance_km(feature.geometry, node.position) <= 1e-8

    assert seen_lake_node
    for cell in hydrology.lake_candidates[0].cells:
        assert float(hydrology.water_depth_m[cell]) > 0.0


def test_n01_n04_nested_depression_two_leaf_merge_is_deterministic() -> None:
    terrain = np.full((5, 7), 50.0, dtype=np.float64)
    cells = tuple((2, column) for column in range(1, 6))
    terrain[2, 1] = 0.0
    terrain[2, 2] = 2.0
    terrain[2, 3] = 5.0
    terrain[2, 4] = 2.0
    terrain[2, 5] = 0.0
    candidate = LakeCandidate(
        cells=cells,
        area_km2=5.0,
        max_depth_m=10.0,
        surface_elevation_m=10.0,
    )

    first = build_nested_depression_hierarchy(
        terrain,
        candidate,
        cell_size_km=1.0,
        lake_min_area_km2=1.0,
        lake_min_depth_m=1.0,
    )
    second = build_nested_depression_hierarchy(
        terrain,
        candidate,
        cell_size_km=1.0,
        lake_min_area_km2=1.0,
        lake_min_depth_m=1.0,
    )

    assert first == second
    nodes = first.node_map()
    root = nodes[first.root_id]
    assert len(root.child_ids) == 2
    assert root.spill_elevation_m == 10.0
    assert root.area_at_spill_km2 == 5.0
    leaves = first.leaf_nodes()
    assert len(leaves) == 2
    assert all(node.spill_elevation_m == 5.0 for node in leaves)
    assert all(node.threshold_significant for node in leaves)
    assert all(nodes[child_id].parent_id == root.id for child_id in root.child_ids)


def test_n01_equal_elevation_plateau_merge_is_batch_stable() -> None:
    terrain = np.full((5, 8), 50.0, dtype=np.float64)
    cells = tuple((2, column) for column in range(1, 7))
    values = (0.0, 2.0, 5.0, 5.0, 2.0, 0.0)
    for column, value in zip(range(1, 7), values):
        terrain[2, column] = value
    candidate = LakeCandidate(
        cells=cells,
        area_km2=6.0,
        max_depth_m=10.0,
        surface_elevation_m=10.0,
    )

    hierarchy = build_nested_depression_hierarchy(
        terrain,
        candidate,
        cell_size_km=1.0,
        lake_min_area_km2=1.0,
        lake_min_depth_m=1.0,
    )
    root = hierarchy.node_map()[hierarchy.root_id]
    assert len(root.child_ids) == 2
    assert len(hierarchy.leaf_nodes()) == 2
    assert {node.spill_elevation_m for node in hierarchy.leaf_nodes()} == {5.0}


def test_n02_single_bowl_has_one_root_leaf() -> None:
    terrain = np.full((5, 7), 50.0, dtype=np.float64)
    cells = tuple((2, column) for column in range(1, 6))
    for column, value in zip(range(1, 6), (0.0, 1.0, 2.0, 3.0, 4.0)):
        terrain[2, column] = value
    candidate = LakeCandidate(
        cells=cells,
        area_km2=5.0,
        max_depth_m=10.0,
        surface_elevation_m=10.0,
    )
    hierarchy = build_nested_depression_hierarchy(
        terrain,
        candidate,
        cell_size_km=1.0,
        lake_min_area_km2=1.0,
        lake_min_depth_m=1.0,
    )
    assert len(hierarchy.nodes) == 1
    root = hierarchy.nodes[0]
    assert root.id == hierarchy.root_id
    assert root.child_ids == ()
    assert root.cells_at_spill == cells
    assert root.area_at_spill_km2 == 5.0
