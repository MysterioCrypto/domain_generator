from __future__ import annotations

import pytest

from domain_generator.contracts.common import ConstraintStrength, FeaturePart
from domain_generator.contracts.geometry import WorldPoint
from domain_generator.contracts.plan import (
    CompiledConstraint,
    CompiledEvaluator,
    CompiledFeatureRef,
    CompiledPoint,
    CompiledPredicate,
    CompiledRectangle,
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    FeatureMetadata,
    FixedParameter,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
    ParameterType,
    PlanDomain,
    PlanGrid,
    PlanHydrology,
    PlanSource,
    PlanSurface,
    ReservationLayoutRecipe,
    ResolvedFeature,
    SiteProfile,
)
from domain_generator.layout.reservations import ReservationCapabilityError, generate_layout, validate_layout
from domain_generator.pipeline.rng import RngFactory


def reservation_feature(feature_id: str = "poi-01") -> ResolvedFeature:
    return ResolvedFeature(id=feature_id, metadata=FeatureMetadata(source_preset="test-reservation"), family=FeatureFamily.POI, layout=ReservationLayoutRecipe(), effect=EffectRecipe(stage=EffectStage.DEPENDENT_PLACEMENT, operator="test-placement", site_profile=SiteProfile()))


def point_feature(feature_id: str = "point-01") -> ResolvedFeature:
    return ResolvedFeature(id=feature_id, metadata=FeatureMetadata(source_preset="test-point"), family=FeatureFamily.TERRAIN, layout=GeometryLayoutRecipe(shape=GeometryShape.POINT, parameters={}), effect=EffectRecipe(stage=EffectStage.TERRAIN, operator="test-effect"))


def band_feature(feature_id: str = "band-01") -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-band"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.BAND,
            parameters={
                "control_point_count": FixedParameter(type=ParameterType.INTEGER, value=2),
                "curvature": FixedParameter(type=ParameterType.FLOAT, value=0.4),
                "width_km": FixedParameter(type=ParameterType.FLOAT, value=10.0),
                "width_sample_count": FixedParameter(type=ParameterType.INTEGER, value=3),
            },
        ),
        effect=EffectRecipe(stage=EffectStage.TERRAIN, operator="test-effect"),
    )


def make_plan(*, features: tuple[ResolvedFeature, ...], constraints: tuple[CompiledConstraint, ...] = (), seed: int = 123456) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(spec_id="reservation-test", spec_schema_version="0.1", spec_fingerprint="sha256:test", generator_version="0.1.0.dev0"),
        seed=seed,
        domain=PlanDomain(width_km=100.0, height_km=80.0),
        grid=PlanGrid(cell_size_km=1.0, rows=80, columns=100),
        hydrology=PlanHydrology(stream_threshold_km2=25.0, lake_min_area_km2=1.0, lake_min_depth_m=2.0, river_depth_at_threshold_m=0.5, river_depth_exponent=0.3),
        surface=PlanSurface(moisture_base=0.35, water_moisture_boost=0.55, water_moisture_decay_km=8.0, moisture_noise_amplitude=0.1, moisture_noise_scale_km=12.0, vegetation_slope_zero_deg=45.0),
        features=features,
        constraints=constraints,
    )


def hard_constraint(constraint_id: str, *, evaluator_type: str, target, predicate_type: str, value: float, unit: str | None = None, subject_feature_id: str = "poi-01") -> CompiledConstraint:
    return CompiledConstraint(id=constraint_id, strength=ConstraintStrength.HARD, evaluator=CompiledEvaluator(type=evaluator_type, subject=CompiledFeatureRef(feature_id=subject_feature_id, part=FeaturePart.WHOLE), target=target), predicate=CompiledPredicate(type=predicate_type, value=value), unit=unit)


def ring_bounds(points: tuple[WorldPoint, ...]) -> tuple[float, float, float, float]:
    xs = [point.x_km for point in points]
    ys = [point.y_km for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def test_unconstrained_reservation_starts_as_entire_domain() -> None:
    plan = make_plan(features=(reservation_feature(),))
    candidate = generate_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    reservation = candidate.placement_reservations["poi-01"]
    assert reservation.source_constraints == ()
    assert len(reservation.allowed_region.polygons) == 1
    assert ring_bounds(reservation.allowed_region.polygons[0].outer) == (0.0, 0.0, 100.0, 80.0)
    assert candidate.geometry_realizations == {}


def test_inside_rectangle_intersects_allowed_region() -> None:
    constraint = hard_constraint("inside-west", evaluator_type="contained_fraction", target=CompiledRectangle(min_x_km=10.0, max_x_km=40.0, min_y_km=5.0, max_y_km=30.0), predicate_type="greater_or_equal", value=1.0)
    plan = make_plan(features=(reservation_feature(),), constraints=(constraint,))
    candidate = generate_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    reservation = candidate.placement_reservations["poi-01"]
    assert reservation.source_constraints == ("inside-west",)
    assert ring_bounds(reservation.allowed_region.polygons[0].outer) == (10.0, 5.0, 40.0, 30.0)


def test_outside_rectangle_creates_hole() -> None:
    constraint = hard_constraint("outside-center", evaluator_type="overlap_fraction", target=CompiledRectangle(min_x_km=40.0, max_x_km=60.0, min_y_km=30.0, max_y_km=50.0), predicate_type="less_or_equal", value=0.0)
    plan = make_plan(features=(reservation_feature(),), constraints=(constraint,))
    candidate = generate_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    polygon = candidate.placement_reservations["poi-01"].allowed_region.polygons[0]
    assert len(polygon.holes) == 1
    assert ring_bounds(polygon.holes[0]) == (40.0, 30.0, 60.0, 50.0)


def test_near_literal_point_builds_buffer_region() -> None:
    constraint = hard_constraint("near-point", evaluator_type="distance", target=CompiledPoint(x_km=50.0, y_km=40.0), predicate_type="less_or_equal", value=5.0, unit="km")
    plan = make_plan(features=(reservation_feature(),), constraints=(constraint,))
    candidate = generate_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    polygon = candidate.placement_reservations["poi-01"].allowed_region.polygons[0]
    min_x, min_y, max_x, max_y = ring_bounds(polygon.outer)
    assert min_x == pytest.approx(45.0)
    assert min_y == pytest.approx(35.0)
    assert max_x == pytest.approx(55.0)
    assert max_y == pytest.approx(45.0)
    assert len(polygon.outer) == 32


def test_far_from_literal_point_subtracts_buffer_as_hole() -> None:
    constraint = hard_constraint("far-point", evaluator_type="distance", target=CompiledPoint(x_km=50.0, y_km=40.0), predicate_type="greater_or_equal", value=5.0, unit="km")
    plan = make_plan(features=(reservation_feature(),), constraints=(constraint,))
    candidate = generate_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    polygon = candidate.placement_reservations["poi-01"].allowed_region.polygons[0]
    assert len(polygon.holes) == 1
    assert len(polygon.holes[0]) == 32


def test_constraint_order_is_canonicalized_by_constraint_id() -> None:
    constraint_z = hard_constraint("z-wide", evaluator_type="contained_fraction", target=CompiledRectangle(min_x_km=10.0, max_x_km=90.0, min_y_km=10.0, max_y_km=70.0), predicate_type="greater_or_equal", value=1.0)
    constraint_a = hard_constraint("a-inner", evaluator_type="contained_fraction", target=CompiledRectangle(min_x_km=20.0, max_x_km=80.0, min_y_km=20.0, max_y_km=60.0), predicate_type="greater_or_equal", value=1.0)
    plan_za = make_plan(features=(reservation_feature(),), constraints=(constraint_z, constraint_a))
    plan_az = make_plan(features=(reservation_feature(),), constraints=(constraint_a, constraint_z))
    result_za = generate_layout(plan_za, attempt_index=2, rng_factory=RngFactory(plan_za.seed))
    result_az = generate_layout(plan_az, attempt_index=2, rng_factory=RngFactory(plan_az.seed))
    reservation = result_za.placement_reservations["poi-01"]
    assert reservation.source_constraints == ("a-inner", "z-wide")
    assert result_za == result_az


def test_empty_reservation_is_structural_but_rejects_layout_validation() -> None:
    left = hard_constraint("inside-left", evaluator_type="contained_fraction", target=CompiledRectangle(min_x_km=0.0, max_x_km=20.0, min_y_km=0.0, max_y_km=80.0), predicate_type="greater_or_equal", value=1.0)
    right = hard_constraint("inside-right", evaluator_type="contained_fraction", target=CompiledRectangle(min_x_km=80.0, max_x_km=100.0, min_y_km=0.0, max_y_km=80.0), predicate_type="greater_or_equal", value=1.0)
    plan = make_plan(features=(reservation_feature(),), constraints=(left, right))
    candidate = generate_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    assert candidate.placement_reservations["poi-01"].allowed_region.polygons == ()
    validation = validate_layout(plan, candidate, attempt_index=0)
    reservation_invariant = next(result for result in validation.engine_invariants.results if result.id == "layout-placement-reservations-nonempty")
    assert reservation_invariant.passed is False
    assert validation.engine_invariants.passed is False


def test_reservation_and_concrete_geometry_coexist_in_one_candidate() -> None:
    constraint = hard_constraint("near-concrete-point", evaluator_type="distance", target=CompiledFeatureRef(feature_id="point-01", part=FeaturePart.WHOLE), predicate_type="less_or_equal", value=8.0, unit="km")
    plan = make_plan(features=(reservation_feature(), point_feature()), constraints=(constraint,))
    candidate = generate_layout(plan, attempt_index=3, rng_factory=RngFactory(plan.seed))
    validation = validate_layout(plan, candidate, attempt_index=3)
    assert set(candidate.geometry_realizations) == {"point-01"}
    assert set(candidate.placement_reservations) == {"poi-01"}
    assert validation.engine_invariants.passed is True


def test_band_whole_target_is_explicit_capability_error() -> None:
    constraint = hard_constraint("near-band", evaluator_type="distance", target=CompiledFeatureRef(feature_id="band-01", part=FeaturePart.WHOLE), predicate_type="less_or_equal", value=5.0, unit="km")
    plan = make_plan(features=(reservation_feature(), band_feature()), constraints=(constraint,))
    with pytest.raises(ReservationCapabilityError, match="footprint materialization"):
        generate_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))


def test_deferred_feature_as_constraint_target_is_explicit_capability_error() -> None:
    constraint = CompiledConstraint(id="reverse-near", strength=ConstraintStrength.HARD, evaluator=CompiledEvaluator(type="distance", subject=CompiledPoint(x_km=10.0, y_km=10.0), target=CompiledFeatureRef(feature_id="poi-01", part=FeaturePart.WHOLE)), predicate=CompiledPredicate(type="less_or_equal", value=5.0), unit="km")
    plan = make_plan(features=(reservation_feature(),), constraints=(constraint,))
    with pytest.raises(ReservationCapabilityError, match="as target"):
        generate_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
