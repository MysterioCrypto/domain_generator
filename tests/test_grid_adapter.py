from __future__ import annotations

import pytest

from domain_generator.contracts.plan import GenerationPlan, PlanDomain, PlanGrid, PlanHydrology, PlanSource
from domain_generator.grid import GridAdapter


def make_plan() -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="grid-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=1,
        domain=PlanDomain(width_km=2.0, height_km=2.0),
        grid=PlanGrid(cell_size_km=1.0, rows=2, columns=2),
        hydrology=PlanHydrology(
            stream_threshold_km2=1.0,
            lake_min_area_km2=1.0,
            lake_min_depth_m=1.0,
        ),
        features=(),
        constraints=(),
    )


def test_cell_centers_use_southwest_world_origin_and_north_first_raster_rows() -> None:
    adapter = GridAdapter.from_plan(make_plan())

    northwest = adapter.cell_center(0, 0)
    southeast = adapter.cell_center(1, 1)

    assert (northwest.x_km, northwest.y_km) == (0.5, 1.5)
    assert (southeast.x_km, southeast.y_km) == (1.5, 0.5)


def test_grid_adapter_rejects_invalid_indices() -> None:
    adapter = GridAdapter.from_plan(make_plan())

    with pytest.raises(IndexError):
        adapter.cell_center(-1, 0)
    with pytest.raises(IndexError):
        adapter.cell_center(0, 2)
    with pytest.raises(TypeError):
        adapter.cell_center(True, 0)
