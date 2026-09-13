from __future__ import annotations

import pytest

from domain_generator.contracts.plan import GenerationPlan, PlanDomain, PlanGrid, PlanHydrology, PlanSource, PlanSurface
from domain_generator.geometry import is_canonical_region_set
from domain_generator.hydrology import HydrologyCapabilityError, LakeCandidate, lake_feature_id, materialize_lake_features


def make_plan(*, rows: int = 4, columns: int = 4) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(spec_id="lake-test", spec_schema_version="0.1", spec_fingerprint="sha256:test", generator_version="0.1.0.dev0"),
        seed=7,
        domain=PlanDomain(width_km=float(columns), height_km=float(rows)),
        grid=PlanGrid(cell_size_km=1.0, rows=rows, columns=columns),
        hydrology=PlanHydrology(stream_threshold_km2=1.0, lake_min_area_km2=1.0, lake_min_depth_m=1.0, river_depth_at_threshold_m=0.5, river_depth_exponent=0.3),
        surface=PlanSurface(moisture_base=0.3, water_moisture_boost=0.5, water_moisture_decay_km=5.0, moisture_noise_amplitude=0.0, moisture_noise_scale_km=5.0, vegetation_slope_zero_deg=45.0),
        features=(), constraints=(),
    )


def lake(cells, area: float, depth: float = 3.0, surface: float = 10.0) -> LakeCandidate:
    return LakeCandidate(cells=tuple(cells), area_km2=area, max_depth_m=depth, surface_elevation_m=surface)


def test_single_cell_materializes_exact_region_and_properties() -> None:
    feature = materialize_lake_features(make_plan(), (lake(((1, 2),), 1.0, 4.5, 12.0),))["lake-0001"]
    assert is_canonical_region_set(feature.geometry)
    assert len(feature.geometry.polygons) == 1
    assert feature.geometry.polygons[0].holes == ()
    assert {(p.x_km, p.y_km) for p in feature.geometry.polygons[0].outer} == {(2.0, 2.0), (3.0, 2.0), (3.0, 3.0), (2.0, 3.0)}
    assert feature.properties.area_km2 == 1.0
    assert feature.properties.max_depth_m == 4.5
    assert feature.properties.surface_elevation_m == 12.0
    assert feature.source.system == "hydrology"


def test_ring_cells_preserve_hole() -> None:
    cells = tuple((r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1))
    geometry = materialize_lake_features(make_plan(rows=3, columns=3), (lake(cells, 8.0),))["lake-0001"].geometry
    assert len(geometry.polygons) == 1
    assert len(geometry.polygons[0].holes) == 1


def test_diagonal_d8_cells_preserve_multipart_geometry() -> None:
    geometry = materialize_lake_features(make_plan(rows=2, columns=2), (lake(((0, 0), (1, 1)), 2.0),))["lake-0001"].geometry
    assert len(geometry.polygons) == 2


def test_ids_follow_candidate_order() -> None:
    features = materialize_lake_features(make_plan(), (lake(((0, 0),), 1.0), lake(((3, 3),), 1.0)))
    assert tuple(features) == ("lake-0001", "lake-0002")
    assert lake_feature_id(0) == "lake-0001"
    with pytest.raises(ValueError):
        lake_feature_id(-1)


def test_materialization_rejects_area_mismatch_overlap_and_empty() -> None:
    plan = make_plan()
    with pytest.raises(HydrologyCapabilityError, match="area"):
        materialize_lake_features(plan, (lake(((0, 0),), 2.0),))
    with pytest.raises(HydrologyCapabilityError, match="overlap"):
        materialize_lake_features(plan, (lake(((0, 0),), 1.0), lake(((0, 0),), 1.0)))
    with pytest.raises(HydrologyCapabilityError, match="at least one cell"):
        materialize_lake_features(plan, (lake((), 0.0),))
