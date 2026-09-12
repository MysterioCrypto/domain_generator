from __future__ import annotations

import numpy as np
import pytest

from domain_generator.contracts.data import RiverNetwork
from domain_generator.contracts.geometry import PointGeometry, RegionPolygon, RegionSet, WorldPoint
from domain_generator.contracts.layout import LayoutCandidate, PlacementReservation, SourcePlanRef
from domain_generator.contracts.plan import (
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    FeatureMetadata,
    FixedParameter,
    GenerationPlan,
    ParameterType,
    PlanDomain,
    PlanGrid,
    PlanHydrology,
    PlanSource,
    PlanSurface,
    ReservationLayoutRecipe,
    ResolvedFeature,
    SiteProfile,
    SiteRequirement,
)
from domain_generator.hydrology.state import HydrologyState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.poi import (
    EvaluatedSite,
    PlacementCandidateCapabilityError,
    SiteMetricContext,
    filter_valid_sites,
    generate_candidate_points,
    generate_valid_sites_for_feature,
    requirement_passes,
)
from domain_generator.surface.state import SurfaceState
from domain_generator.terrain.state import TerrainState


def rectangle_region(min_x: float, min_y: float, max_x: float, max_y: float) -> RegionSet:
    return RegionSet(
        polygons=(
            RegionPolygon(
                outer=(
                    WorldPoint(x_km=min_x, y_km=min_y),
                    WorldPoint(x_km=max_x, y_km=min_y),
                    WorldPoint(x_km=max_x, y_km=max_y),
                    WorldPoint(x_km=min_x, y_km=max_y),
                )
            ),
        )
    )


def placement_feature(
    feature_id: str,
    *,
    spacing_km: float = 1.0,
    requirements: tuple[SiteRequirement, ...] = (),
) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-placement"),
        family=FeatureFamily.POI,
        layout=ReservationLayoutRecipe(),
        effect=EffectRecipe(
            stage=EffectStage.DEPENDENT_PLACEMENT,
            operator="suitability_placement",
            parameters={
                "candidate_spacing_km": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=spacing_km,
                )
            },
            site_profile=SiteProfile(
                footprint_radius_km=0.0,
                requirements=requirements,
                preferences=(),
            ),
        ),
    )


def make_plan(
    *features: ResolvedFeature,
    width_km: float = 4.0,
    height_km: float = 4.0,
    cell_size_km: float = 1.0,
) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="candidate-filter-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=123456,
        domain=PlanDomain(width_km=width_km, height_km=height_km),
        grid=PlanGrid(
            cell_size_km=cell_size_km,
            rows=int(height_km / cell_size_km),
            columns=int(width_km / cell_size_km),
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
        features=features,
        constraints=(),
    )


def make_layout(
    plan: GenerationPlan,
    reservations: dict[str, RegionSet],
    *,
    attempt_index: int,
) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint="sha256:test-plan"),
        attempt_index=attempt_index,
        geometry_realizations={},
        placement_reservations={
            feature_id: PlacementReservation(allowed_region=region)
            for feature_id, region in reservations.items()
        },
    )


def make_metric_context(plan: GenerationPlan, *, moisture_value: float = 0.75) -> SiteMetricContext:
    shape = (plan.grid.rows, plan.grid.columns)
    terrain = TerrainState(elevation_m=np.zeros(shape, dtype=np.float32))
    hydrology = HydrologyState(
        routing_elevation_m=np.zeros(shape, dtype=np.float64),
        fill_elevation_m=np.zeros(shape, dtype=np.float64),
        flow_direction=np.full(shape, -1, dtype=np.int8),
        flow_accumulation_km2=np.ones(shape, dtype=np.float64),
        stream_mask=np.zeros(shape, dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=np.zeros(shape, dtype=np.float32),
    )
    surface = SurfaceState(
        moisture=np.full(shape, moisture_value, dtype=np.float32),
        vegetation_density=np.full(shape, 0.5, dtype=np.float32),
    )
    return SiteMetricContext.from_states(plan, terrain, hydrology, surface)


def test_candidate_lattice_replays_exactly_for_same_attempt() -> None:
    feature = placement_feature("poi-01", spacing_km=0.8)
    plan = make_plan(feature)
    layout = make_layout(
        plan,
        {"poi-01": rectangle_region(0.0, 0.0, 4.0, 4.0)},
        attempt_index=3,
    )

    first = generate_candidate_points(
        plan,
        layout,
        "poi-01",
        attempt_index=3,
        rng_factory=RngFactory(plan.seed),
    )
    replay = generate_candidate_points(
        plan,
        layout,
        "poi-01",
        attempt_index=3,
        rng_factory=RngFactory(plan.seed),
    )

    assert first == replay
    assert first


def test_candidate_lattice_changes_between_attempts() -> None:
    feature = placement_feature("poi-01", spacing_km=0.8)
    plan = make_plan(feature)
    first_layout = make_layout(
        plan,
        {"poi-01": rectangle_region(0.0, 0.0, 4.0, 4.0)},
        attempt_index=0,
    )
    second_layout = make_layout(
        plan,
        {"poi-01": rectangle_region(0.0, 0.0, 4.0, 4.0)},
        attempt_index=1,
    )

    first = generate_candidate_points(
        plan,
        first_layout,
        "poi-01",
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    second = generate_candidate_points(
        plan,
        second_layout,
        "poi-01",
        attempt_index=1,
        rng_factory=RngFactory(plan.seed),
    )

    assert first != second


def test_unrelated_feature_order_does_not_change_candidate_stream() -> None:
    alpha = placement_feature("alpha", spacing_km=0.9)
    beta = placement_feature("beta", spacing_km=1.2)
    plan_ab = make_plan(alpha, beta)
    plan_ba = make_plan(beta, alpha)
    reservations = {
        "alpha": rectangle_region(0.0, 0.0, 4.0, 4.0),
        "beta": rectangle_region(0.0, 0.0, 4.0, 4.0),
    }
    layout_ab = make_layout(plan_ab, reservations, attempt_index=4)
    layout_ba = make_layout(plan_ba, reservations, attempt_index=4)

    points_ab = generate_candidate_points(
        plan_ab,
        layout_ab,
        "alpha",
        attempt_index=4,
        rng_factory=RngFactory(plan_ab.seed),
    )
    points_ba = generate_candidate_points(
        plan_ba,
        layout_ba,
        "alpha",
        attempt_index=4,
        rng_factory=RngFactory(plan_ba.seed),
    )

    assert points_ab == points_ba


def test_candidates_are_reservation_filtered_and_canonically_sorted() -> None:
    feature = placement_feature("poi-01", spacing_km=0.4)
    plan = make_plan(feature)
    layout = make_layout(
        plan,
        {"poi-01": rectangle_region(1.0, 1.0, 3.0, 2.5)},
        attempt_index=2,
    )

    points = generate_candidate_points(
        plan,
        layout,
        "poi-01",
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    coordinates = tuple((point.x_km, point.y_km) for point in points)

    assert points
    assert coordinates == tuple(sorted(coordinates))
    assert len(coordinates) == len(set(coordinates))
    assert all(1.0 <= x <= 3.0 and 1.0 <= y <= 2.5 for x, y in coordinates)


def test_empty_reservation_has_no_candidate_fallback() -> None:
    feature = placement_feature("poi-01")
    plan = make_plan(feature)
    layout = make_layout(plan, {"poi-01": RegionSet()}, attempt_index=0)

    points = generate_candidate_points(
        plan,
        layout,
        "poi-01",
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    assert points == ()


def test_hard_requirements_filter_sites_without_relaxation() -> None:
    pass_requirement = SiteRequirement(
        metric="moisture_mean",
        evaluator="greater_or_equal",
        value=0.7,
    )
    fail_requirement = SiteRequirement(
        metric="moisture_mean",
        evaluator="less_or_equal",
        value=0.2,
    )

    pass_feature = placement_feature(
        "poi-pass",
        spacing_km=1.0,
        requirements=(pass_requirement,),
    )
    fail_feature = placement_feature(
        "poi-fail",
        spacing_km=1.0,
        requirements=(fail_requirement,),
    )
    plan = make_plan(pass_feature, fail_feature)
    region = rectangle_region(0.0, 0.0, 4.0, 4.0)
    layout = make_layout(
        plan,
        {"poi-pass": region, "poi-fail": region},
        attempt_index=5,
    )
    context = make_metric_context(plan, moisture_value=0.75)

    passed = generate_valid_sites_for_feature(
        plan,
        layout,
        context,
        "poi-pass",
        attempt_index=5,
        rng_factory=RngFactory(plan.seed),
    )
    failed = generate_valid_sites_for_feature(
        plan,
        layout,
        context,
        "poi-fail",
        attempt_index=5,
        rng_factory=RngFactory(plan.seed),
    )

    assert passed
    assert all(site.metrics["moisture_mean"] >= 0.7 for site in passed)
    assert failed == ()


def test_infinite_distance_to_water_uses_normal_comparison_semantics() -> None:
    metrics = {"distance_to_water": float("inf")}
    near = SiteRequirement(
        metric="distance_to_water",
        evaluator="less_or_equal",
        value=10.0,
    )
    far = SiteRequirement(
        metric="distance_to_water",
        evaluator="greater_or_equal",
        value=10.0,
    )

    assert requirement_passes(metrics, near) is False
    assert requirement_passes(metrics, far) is True


def test_unknown_metric_and_evaluator_are_explicit_capability_errors() -> None:
    site = EvaluatedSite(
        point=PointGeometry(x_km=1.0, y_km=1.0),
        metrics={"moisture_mean": 0.5},
    )
    unknown_metric = SiteRequirement(
        metric="unknown_metric",
        evaluator="less_or_equal",
        value=1.0,
    )
    unknown_evaluator = SiteRequirement(
        metric="moisture_mean",
        evaluator="approximately",
        value=0.5,
    )

    with pytest.raises(PlacementCandidateCapabilityError, match="unknown site metric"):
        filter_valid_sites((site,), (unknown_metric,))
    with pytest.raises(PlacementCandidateCapabilityError, match="unsupported site requirement evaluator"):
        filter_valid_sites((site,), (unknown_evaluator,))


def test_missing_spacing_parameter_is_explicit_capability_error() -> None:
    feature = placement_feature("poi-01").model_copy(
        update={
            "effect": placement_feature("poi-01").effect.model_copy(update={"parameters": {}})
        }
    )
    plan = make_plan(feature)
    layout = make_layout(
        plan,
        {"poi-01": rectangle_region(0.0, 0.0, 4.0, 4.0)},
        attempt_index=0,
    )

    with pytest.raises(PlacementCandidateCapabilityError, match="candidate_spacing_km"):
        generate_candidate_points(
            plan,
            layout,
            "poi-01",
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )
