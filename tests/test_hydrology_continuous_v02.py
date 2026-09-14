from __future__ import annotations

from math import atan2, cos, pi, sin

import numpy as np

from domain_generator.contracts.plan import GenerationPlan
from domain_generator.hydrology import build_continuous_river_network
from domain_generator.hydrology.continuous import (
    choose_lake_outlets,
    continuous_routing_field,
    distributed_flow_accumulation_km2,
)
from domain_generator.hydrology.classification import classify_stream_mask, extract_lake_candidates
from domain_generator.hydrology.routing import priority_flood_surfaces


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
    fractions = field.fraction_a[4:-4, 4:-4] + field.fraction_b[4:-4, 4:-4]
    np.testing.assert_allclose(fractions, 1.0, rtol=0.0, atol=1e-12)
    assert np.count_nonzero(field.fraction_b[4:-4, 4:-4] > 0.0) > 0


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
    tolerance = np.deg2rad(0.5)
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
            result[row, column] = 900.0 - 2.0 * x + 0.09 * cross
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
