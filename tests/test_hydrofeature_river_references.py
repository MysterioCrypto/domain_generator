from __future__ import annotations

import pytest

from domain_generator.contracts.data import RiverNetwork, RiverNode, RiverNodeKind
from domain_generator.contracts.geometry import WorldPoint
from domain_generator.contracts.plan import GenerationPlan, PlanDomain, PlanGrid, PlanHydrology, PlanSource, PlanSurface
from domain_generator.hydrology import HydrologyCapabilityError, LakeCandidate, materialize_lake_features, validate_river_lake_references


def plan() -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(spec_id="lake-ref-test", spec_schema_version="0.1", spec_fingerprint="sha256:test", generator_version="0.1.0.dev0"),
        seed=7,
        domain=PlanDomain(width_km=2.0, height_km=2.0),
        grid=PlanGrid(cell_size_km=1.0, rows=2, columns=2),
        hydrology=PlanHydrology(stream_threshold_km2=1.0, lake_min_area_km2=1.0, lake_min_depth_m=1.0, river_depth_at_threshold_m=0.5, river_depth_exponent=0.3),
        surface=PlanSurface(moisture_base=0.3, water_moisture_boost=0.5, water_moisture_decay_km=5.0, moisture_noise_amplitude=0.0, moisture_noise_scale_km=5.0, vegetation_slope_zero_deg=45.0),
        features=(), constraints=(),
    )


def test_river_lake_reference_must_resolve_materialized_feature() -> None:
    candidate = LakeCandidate(cells=((0, 0),), area_km2=1.0, max_depth_m=2.0, surface_elevation_m=10.0)
    features = materialize_lake_features(plan(), (candidate,))
    valid = RiverNetwork(nodes={"n": RiverNode(kind=RiverNodeKind.LAKE_INFLOW, position=WorldPoint(x_km=0.5, y_km=1.5), feature_id="lake-0001")})
    validate_river_lake_references(valid, features)

    invalid = RiverNetwork(nodes={"n": RiverNode(kind=RiverNodeKind.LAKE_INFLOW, position=WorldPoint(x_km=0.5, y_km=1.5), feature_id="lake-9999")})
    with pytest.raises(HydrologyCapabilityError, match="unknown materialized lake"):
        validate_river_lake_references(invalid, features)
