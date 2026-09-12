from __future__ import annotations

from domain_generator.compiler.compile import semantic_plan_fingerprint
from domain_generator.contracts.common import ConstraintStrength, FeaturePart
from domain_generator.contracts.geometry import AreaGeometry, PointGeometry, WorldPoint
from domain_generator.contracts.layout import LayoutCandidate, SourcePlanRef
from domain_generator.contracts.plan import (
    CompiledConstraint,
    CompiledEvaluator,
    CompiledFeatureRef,
    CompiledPoint,
    CompiledPredicate,
    EffectRecipe,
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
    ResolvedFeature,
)
from domain_generator.layout.area import area_self_intersects, area_signed_area
from domain_generator.layout.geometry import generate_geometry_layout, validate_geometry_layout
from domain_generator.pipeline.rng import RngFactory


def area_feature(
    feature_id: str,
    *,
    vertex_count: int = 7,
    radial_extent: float = 0.7,
    radial_irregularity: float = 0.4,
) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-area"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.AREA,
            parameters={
                "vertex_count": FixedParameter(
                    type=ParameterType.INTEGER,
                    value=vertex_count,
                ),
                "radial_extent": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=radial_extent,
                ),
                "radial_irregularity": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=radial_irregularity,
                ),
            },
        ),
        effect=EffectRecipe(stage="terrain", operator="test-effect"),
    )


def point_feature(feature_id: str) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-point"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(shape=GeometryShape.POINT, parameters={}),
        effect=EffectRecipe(stage="terrain", operator="test-effect"),
    )


def make_plan(
    *,
    features: tuple[ResolvedFeature, ...],
    constraints: tuple[CompiledConstraint, ...] = (),
    seed: int = 123456,
) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="area-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=seed,
        domain=PlanDomain(width_km=120.0, height_km=80.0),
        grid=PlanGrid(cell_size_km=1.0, rows=80, columns=120),
        hydrology=PlanHydrology(
            stream_threshold_km2=25.0,
            lake_min_area_km2=1.0,
            lake_min_depth_m=2.0,
            river_depth_at_threshold_m=0.5,
            river_depth_exponent=0.3,
        ),
        features=features,
        constraints=constraints,
    )


def manual_candidate(
    plan: GenerationPlan,
    *,
    geometries: dict[str, AreaGeometry | PointGeometry],
    attempt_index: int = 0,
) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations=geometries,
        placement_reservations={},
    )


def square_ccw() -> AreaGeometry:
    return AreaGeometry(
        boundary=(
            WorldPoint(x_km=1.0, y_km=1.0),
            WorldPoint(x_km=3.0, y_km=1.0),
            WorldPoint(x_km=3.0, y_km=3.0),
            WorldPoint(x_km=1.0, y_km=3.0),
        )
    )


def test_area_replay_is_exact_for_same_attempt() -> None:
    plan = make_plan(features=(area_feature("area-01"),))

    first = generate_geometry_layout(plan, attempt_index=4, rng_factory=RngFactory(plan.seed))
    second = generate_geometry_layout(plan, attempt_index=4, rng_factory=RngFactory(plan.seed))

    assert first == second


def test_different_attempt_changes_area_realization() -> None:
    plan = make_plan(features=(area_feature("area-01"),))

    first = generate_geometry_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    second = generate_geometry_layout(plan, attempt_index=1, rng_factory=RngFactory(plan.seed))

    assert first.geometry_realizations["area-01"] != second.geometry_realizations["area-01"]


def test_generated_area_is_ccw_simple_and_inside_domain() -> None:
    plan = make_plan(features=(area_feature("area-01", vertex_count=11, radial_extent=0.9, radial_irregularity=0.8),))

    for attempt_index in range(20):
        candidate = generate_geometry_layout(
            plan,
            attempt_index=attempt_index,
            rng_factory=RngFactory(plan.seed),
        )
        geometry = candidate.geometry_realizations["area-01"]
        assert isinstance(geometry, AreaGeometry)
        assert len(geometry.boundary) == 11
        assert area_signed_area(geometry) > 0.0
        assert area_self_intersects(geometry) is False
        assert all(0.0 <= point.x_km <= 120.0 for point in geometry.boundary)
        assert all(0.0 <= point.y_km <= 80.0 for point in geometry.boundary)

        validation = validate_geometry_layout(plan, candidate, attempt_index=attempt_index)
        assert validation.engine_invariants.passed is True


def test_feature_order_does_not_change_area_or_point_geometry() -> None:
    area = area_feature("area-01")
    point = point_feature("point-01")
    plan_ap = make_plan(features=(area, point))
    plan_pa = make_plan(features=(point, area))

    result_ap = generate_geometry_layout(plan_ap, attempt_index=6, rng_factory=RngFactory(plan_ap.seed))
    result_pa = generate_geometry_layout(plan_pa, attempt_index=6, rng_factory=RngFactory(plan_pa.seed))

    assert result_ap.geometry_realizations == result_pa.geometry_realizations


def test_area_center_selector_uses_polygon_centroid() -> None:
    constraint = CompiledConstraint(
        id="center-at-two-two",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="area-01", part=FeaturePart.CENTER),
            target=CompiledPoint(x_km=2.0, y_km=2.0),
        ),
        predicate=CompiledPredicate(type="less_or_equal", value=0.0),
        unit="km",
    )
    plan = make_plan(features=(area_feature("area-01"),), constraints=(constraint,))
    candidate = manual_candidate(plan, geometries={"area-01": square_ccw()})

    validation = validate_geometry_layout(plan, candidate, attempt_index=0)

    assert validation.engine_invariants.passed is True
    assert validation.hard_constraints.passed is True
    assert validation.hard_constraints.results[0].measurement.value == 0.0


def test_point_inside_area_contained_fraction_is_one() -> None:
    constraint = CompiledConstraint(
        id="point-inside-area",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="contained_fraction",
            subject=CompiledFeatureRef(feature_id="point-01", part=FeaturePart.WHOLE),
            target=CompiledFeatureRef(feature_id="area-01", part=FeaturePart.WHOLE),
        ),
        predicate=CompiledPredicate(type="greater_or_equal", value=1.0),
    )
    plan = make_plan(
        features=(area_feature("area-01"), point_feature("point-01")),
        constraints=(constraint,),
    )
    candidate = manual_candidate(
        plan,
        geometries={
            "area-01": square_ccw(),
            "point-01": PointGeometry(x_km=2.0, y_km=2.0),
        },
    )

    validation = validate_geometry_layout(plan, candidate, attempt_index=0)

    assert validation.hard_constraints.passed is True
    assert validation.hard_constraints.results[0].measurement.value == 1.0


def test_point_inside_area_has_zero_whole_distance_but_positive_boundary_distance() -> None:
    whole_constraint = CompiledConstraint(
        id="whole-distance",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="point-01", part=FeaturePart.WHOLE),
            target=CompiledFeatureRef(feature_id="area-01", part=FeaturePart.WHOLE),
        ),
        predicate=CompiledPredicate(type="less_or_equal", value=0.0),
        unit="km",
    )
    boundary_constraint = CompiledConstraint(
        id="boundary-distance",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="point-01", part=FeaturePart.WHOLE),
            target=CompiledFeatureRef(feature_id="area-01", part=FeaturePart.BOUNDARY),
        ),
        predicate=CompiledPredicate(type="greater_or_equal", value=1.0),
        unit="km",
    )
    plan = make_plan(
        features=(area_feature("area-01"), point_feature("point-01")),
        constraints=(whole_constraint, boundary_constraint),
    )
    candidate = manual_candidate(
        plan,
        geometries={
            "area-01": square_ccw(),
            "point-01": PointGeometry(x_km=2.0, y_km=2.0),
        },
    )

    validation = validate_geometry_layout(plan, candidate, attempt_index=0)

    assert validation.hard_constraints.passed is True
    values = {result.constraint_id: result.measurement.value for result in validation.hard_constraints.results}
    assert values["whole-distance"] == 0.0
    assert values["boundary-distance"] == 1.0


def test_self_intersecting_area_is_rejected_by_engine_invariant() -> None:
    plan = make_plan(features=(area_feature("area-01"),))
    bow_tie = AreaGeometry(
        boundary=(
            WorldPoint(x_km=1.0, y_km=1.0),
            WorldPoint(x_km=3.0, y_km=3.0),
            WorldPoint(x_km=1.0, y_km=3.0),
            WorldPoint(x_km=3.0, y_km=1.0),
        )
    )
    candidate = manual_candidate(plan, geometries={"area-01": bow_tie})

    validation = validate_geometry_layout(plan, candidate, attempt_index=0)

    assert validation.engine_invariants.passed is False
    results = {item.id: item.passed for item in validation.engine_invariants.results}
    assert results["layout-area-simple"] is False


def test_clockwise_area_is_rejected_by_engine_invariant() -> None:
    plan = make_plan(features=(area_feature("area-01"),))
    clockwise = AreaGeometry(boundary=tuple(reversed(square_ccw().boundary)))
    candidate = manual_candidate(plan, geometries={"area-01": clockwise})

    validation = validate_geometry_layout(plan, candidate, attempt_index=0)

    assert validation.engine_invariants.passed is False
    results = {item.id: item.passed for item in validation.engine_invariants.results}
    assert results["layout-area-ccw-nondegenerate"] is False
