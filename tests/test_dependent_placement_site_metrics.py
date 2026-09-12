from __future__ import annotations

import numpy as np
import pytest

from domain_generator.contracts.data import RiverNetwork
from domain_generator.contracts.geometry import PointGeometry
from domain_generator.contracts.plan import (
    GenerationPlan,
    PlanDomain,
    PlanGrid,
    PlanHydrology,
    PlanSource,
    PlanSurface,
)
from domain_generator.grid import GridAdapter
from domain_generator.hydrology.state import HydrologyState
from domain_generator.poi import (
    SITE_METRIC_IDS,
    SiteMetricCapabilityError,
    SiteMetricContext,
    evaluate_site_metrics,
    footprint_cells,
)
from domain_generator.surface.state import SurfaceState
from domain_generator.terrain.state import TerrainState


def make_plan(*, rows: int = 3, columns: int = 3, cell_size_km: float = 1.0) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="site-metric-test",
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
            river_depth_exponent=0.3,
        ),
        surface=PlanSurface(
            moisture_base=0.35,
            water_moisture_boost=0.55,
            water_moisture_decay_km=8.0,
            moisture_noise_amplitude=0.1,
            moisture_noise_scale_km=12.0,
            vegetation_slope_zero_deg=45.0,
        ),
        features=(),
        constraints=(),
    )


def make_context(
    elevation: np.ndarray,
    water_depth: np.ndarray,
    moisture: np.ndarray,
    vegetation: np.ndarray,
    *,
    cell_size_km: float = 1.0,
) -> SiteMetricContext:
    rows, columns = elevation.shape
    plan = make_plan(rows=rows, columns=columns, cell_size_km=cell_size_km)
    terrain = TerrainState(elevation_m=elevation.astype(np.float32, copy=False))
    hydrology = HydrologyState(
        routing_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        fill_elevation_m=np.zeros((rows, columns), dtype=np.float64),
        flow_direction=np.full((rows, columns), -1, dtype=np.int8),
        flow_accumulation_km2=np.ones((rows, columns), dtype=np.float64),
        stream_mask=np.zeros((rows, columns), dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=water_depth.astype(np.float32, copy=False),
    )
    surface = SurfaceState(
        moisture=moisture.astype(np.float32, copy=False),
        vegetation_density=vegetation.astype(np.float32, copy=False),
    )
    return SiteMetricContext.from_states(plan, terrain, hydrology, surface)


def test_grid_containing_cell_uses_east_and_north_internal_boundary_ties() -> None:
    adapter = GridAdapter.from_plan(make_plan(rows=2, columns=2, cell_size_km=1.0))

    assert adapter.containing_cell(1.0, 1.0) == (0, 1)
    assert adapter.containing_cell(2.0, 2.0) == (0, 1)
    assert adapter.containing_cell(0.0, 0.0) == (1, 0)


def test_zero_or_tiny_footprint_falls_back_to_containing_cell() -> None:
    adapter = GridAdapter.from_plan(make_plan(rows=2, columns=2, cell_size_km=1.0))
    candidate = PointGeometry(x_km=1.0, y_km=1.0)

    assert footprint_cells(adapter, candidate, 0.0) == ((0, 1),)
    assert footprint_cells(adapter, candidate, 0.1) == ((0, 1),)


def test_footprint_uses_exact_center_distance_and_clips_to_domain() -> None:
    adapter = GridAdapter.from_plan(make_plan(rows=2, columns=2, cell_size_km=1.0))
    candidate = PointGeometry(x_km=0.0, y_km=0.0)

    cells = footprint_cells(adapter, candidate, 1.6)

    assert cells == ((0, 0), (1, 0), (1, 1))


def test_complete_metric_registry_has_expected_physical_semantics() -> None:
    elevation = np.array(
        [
            [0.0, 10.0, 0.0],
            [10.0, 20.0, 10.0],
            [0.0, 10.0, 0.0],
        ],
        dtype=np.float32,
    )
    water = np.zeros((3, 3), dtype=np.float32)
    water[1, 2] = 2.0
    moisture = np.array(
        [
            [0.0, 0.2, 0.0],
            [0.4, 0.6, 0.8],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )
    vegetation = np.array(
        [
            [0.0, 0.1, 0.0],
            [0.2, 0.3, 0.4],
            [0.0, 0.5, 0.0],
        ],
        dtype=np.float32,
    )
    context = make_context(elevation, water, moisture, vegetation)
    candidate = PointGeometry(x_km=1.5, y_km=1.5)

    metrics = evaluate_site_metrics(context, candidate, 1.01)

    assert tuple(metrics) == SITE_METRIC_IDS
    assert metrics["elevation_mean"] == pytest.approx(12.0)
    assert metrics["local_relief"] == pytest.approx(10.0)
    assert metrics["relative_elevation"] == pytest.approx(8.0)
    assert metrics["water_fraction"] == pytest.approx(0.2)
    assert metrics["moisture_mean"] == pytest.approx(0.6)
    assert metrics["vegetation_density_mean"] == pytest.approx(0.3)
    assert metrics["distance_to_water"] == pytest.approx(0.0)

    expected_slope_mean = float(
        np.mean(
            np.asarray(
                [
                    context.slope_deg[0, 1],
                    context.slope_deg[1, 0],
                    context.slope_deg[1, 1],
                    context.slope_deg[1, 2],
                    context.slope_deg[2, 1],
                ],
                dtype=np.float64,
            )
        )
    )
    assert metrics["slope_mean"] == pytest.approx(expected_slope_mean)


def test_relative_elevation_uses_candidate_containing_cell_not_nearest_mean_cell() -> None:
    elevation = np.array(
        [
            [5.0, 50.0],
            [10.0, 20.0],
        ],
        dtype=np.float32,
    )
    zeros = np.zeros((2, 2), dtype=np.float32)
    context = make_context(elevation, zeros, zeros, zeros)

    candidate = PointGeometry(x_km=1.0, y_km=1.0)
    metrics = evaluate_site_metrics(context, candidate, 2.0)

    assert context.adapter.containing_cell(candidate.x_km, candidate.y_km) == (0, 1)
    assert metrics["elevation_mean"] == pytest.approx(21.25)
    assert metrics["relative_elevation"] == pytest.approx(28.75)


def test_distance_to_water_is_infinite_when_domain_has_no_canonical_water() -> None:
    elevation = np.zeros((3, 3), dtype=np.float32)
    zeros = np.zeros((3, 3), dtype=np.float32)
    context = make_context(elevation, zeros, zeros, zeros)

    metrics = evaluate_site_metrics(
        context,
        PointGeometry(x_km=1.5, y_km=1.5),
        1.0,
    )

    assert metrics["distance_to_water"] == float("inf")


def test_context_rejects_invalid_normalized_surface_field() -> None:
    elevation = np.zeros((2, 2), dtype=np.float32)
    water = np.zeros((2, 2), dtype=np.float32)
    moisture = np.zeros((2, 2), dtype=np.float32)
    moisture[0, 0] = 1.1
    vegetation = np.zeros((2, 2), dtype=np.float32)

    with pytest.raises(SiteMetricCapabilityError, match="moisture"):
        make_context(elevation, water, moisture, vegetation)


def test_out_of_domain_candidate_and_negative_radius_are_capability_errors() -> None:
    elevation = np.zeros((2, 2), dtype=np.float32)
    zeros = np.zeros((2, 2), dtype=np.float32)
    context = make_context(elevation, zeros, zeros, zeros)

    with pytest.raises(SiteMetricCapabilityError, match="candidate point"):
        evaluate_site_metrics(
            context,
            PointGeometry(x_km=2.1, y_km=1.0),
            0.0,
        )

    with pytest.raises(SiteMetricCapabilityError, match="footprint_radius_km"):
        evaluate_site_metrics(
            context,
            PointGeometry(x_km=1.0, y_km=1.0),
            -0.1,
        )
