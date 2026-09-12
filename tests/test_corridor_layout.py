from __future__ import annotations

from math import isclose

import pytest

from domain_generator.contracts.common import ConstraintStrength, FeaturePart
from domain_generator.contracts.geometry import CorridorGeometry, PointGeometry
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
    PlanSource,
    ResolvedFeature,
    TriangularSampler,
    RangeParameter,
)
from domain_generator.layout.geometry import (
    LayoutCapabilityError,
    generate_geometry_layout,
    validate_geometry_layout,
)
from domain_generator.pipeline.rng import RngFactory, RngKey, RngStage
from domain_generator.pipeline.sampling import sample_resolved_parameter


def corridor_feature(
    feature_id: str,
    *,
    control_point_count: int = 3,
    curvature: float = 0.5,
) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-corridor"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.CORRIDOR,
            parameters={
                "control_point_count": FixedParameter(
                    type=ParameterType.INTEGER,
                    value=control_point_count,
                ),
                "curvature": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=curvature,
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
            spec_id="corridor-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=seed,
        domain=PlanDomain(width_km=120.0, height_km=80.0),
        grid=PlanGrid(cell_size_km=1.0, rows=80, columns=120),
        features=features,
        constraints=constraints,
    )


def test_triangular_sampler_rng_v1_golden_vector() -> None:
    recipe = RangeParameter(
        type=ParameterType.FLOAT,
        min=0.1,
        max=0.9,
        sampler=TriangularSampler(mode=0.35),
    )
    factory = RngFactory(123456)
    stream = factory.stream(
        RngKey(
            attempt_index=2,
            stage=RngStage.LAYOUT,
            scope=("feature", "corridor-01", "parameter", "curvature"),
            purpose="sample",
        )
    )

    sampled = sample_resolved_parameter(recipe, stream)

    assert sampled == pytest.approx(0.33653964725482616, rel=0.0, abs=1e-15)


def test_corridor_replay_is_exact_for_same_attempt() -> None:
    plan = make_plan(features=(corridor_feature("corridor-01"),))
    factory = RngFactory(plan.seed)

    first = generate_geometry_layout(plan, attempt_index=4, rng_factory=factory)
    second = generate_geometry_layout(plan, attempt_index=4, rng_factory=RngFactory(plan.seed))

    assert first == second


def test_different_attempt_changes_corridor_realization() -> None:
    plan = make_plan(features=(corridor_feature("corridor-01"),))

    first = generate_geometry_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
    second = generate_geometry_layout(plan, attempt_index=1, rng_factory=RngFactory(plan.seed))

    assert first.geometry_realizations["corridor-01"] != second.geometry_realizations["corridor-01"]


def test_control_point_count_does_not_change_corridor_endpoints() -> None:
    short_plan = make_plan(features=(corridor_feature("corridor-01", control_point_count=1),))
    long_plan = make_plan(features=(corridor_feature("corridor-01", control_point_count=7),))

    short = generate_geometry_layout(short_plan, attempt_index=3, rng_factory=RngFactory(short_plan.seed))
    long = generate_geometry_layout(long_plan, attempt_index=3, rng_factory=RngFactory(long_plan.seed))

    short_geometry = short.geometry_realizations["corridor-01"]
    long_geometry = long.geometry_realizations["corridor-01"]
    assert isinstance(short_geometry, CorridorGeometry)
    assert isinstance(long_geometry, CorridorGeometry)
    assert short_geometry.centerline[0] == long_geometry.centerline[0]
    assert short_geometry.centerline[-1] == long_geometry.centerline[-1]
    assert len(short_geometry.centerline) == 3
    assert len(long_geometry.centerline) == 9


def test_zero_curvature_control_points_are_collinear() -> None:
    plan = make_plan(features=(corridor_feature("corridor-01", control_point_count=4, curvature=0.0),))
    candidate = generate_geometry_layout(plan, attempt_index=5, rng_factory=RngFactory(plan.seed))
    geometry = candidate.geometry_realizations["corridor-01"]
    assert isinstance(geometry, CorridorGeometry)

    start = geometry.centerline[0]
    end = geometry.centerline[-1]
    vx = end.x_km - start.x_km
    vy = end.y_km - start.y_km
    for point in geometry.centerline[1:-1]:
        cross = vx * (point.y_km - start.y_km) - vy * (point.x_km - start.x_km)
        assert isclose(cross, 0.0, rel_tol=0.0, abs_tol=1e-10)


def test_corridor_vertices_stay_inside_domain() -> None:
    plan = make_plan(features=(corridor_feature("corridor-01", control_point_count=12, curvature=1.0),))

    for attempt_index in range(20):
        candidate = generate_geometry_layout(
            plan,
            attempt_index=attempt_index,
            rng_factory=RngFactory(plan.seed),
        )
        geometry = candidate.geometry_realizations["corridor-01"]
        assert isinstance(geometry, CorridorGeometry)
        assert all(0.0 <= point.x_km <= 120.0 for point in geometry.centerline)
        assert all(0.0 <= point.y_km <= 80.0 for point in geometry.centerline)


def test_feature_order_does_not_change_point_or_corridor_geometry() -> None:
    a = corridor_feature("corridor-01", control_point_count=3, curvature=0.7)
    b = point_feature("point-01")
    plan_ab = make_plan(features=(a, b))
    plan_ba = make_plan(features=(b, a))

    result_ab = generate_geometry_layout(plan_ab, attempt_index=6, rng_factory=RngFactory(plan_ab.seed))
    result_ba = generate_geometry_layout(plan_ba, attempt_index=6, rng_factory=RngFactory(plan_ba.seed))

    assert result_ab.geometry_realizations == result_ba.geometry_realizations


def test_point_to_corridor_distance_constraint_is_evaluated() -> None:
    constraint = CompiledConstraint(
        id="point-near-corridor",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="point-01", part=FeaturePart.WHOLE),
            target=CompiledFeatureRef(feature_id="corridor-01", part=FeaturePart.WHOLE),
        ),
        predicate=CompiledPredicate(type="less_or_equal", value=1000.0),
        unit="km",
    )
    plan = make_plan(
        features=(point_feature("point-01"), corridor_feature("corridor-01")),
        constraints=(constraint,),
    )
    candidate = generate_geometry_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))

    validation = validate_geometry_layout(plan, candidate, attempt_index=0)

    assert validation.engine_invariants.passed is True
    assert validation.hard_constraints.passed is True
    assert validation.hard_constraints.results[0].measurement.type == "distance"


def test_corridor_start_part_can_be_used_as_point_distance_subject() -> None:
    constraint = CompiledConstraint(
        id="start-near-origin",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="corridor-01", part=FeaturePart.START),
            target=CompiledPoint(x_km=0.0, y_km=0.0),
        ),
        predicate=CompiledPredicate(type="less_or_equal", value=1000.0),
        unit="km",
    )
    plan = make_plan(features=(corridor_feature("corridor-01"),), constraints=(constraint,))
    candidate = generate_geometry_layout(plan, attempt_index=1, rng_factory=RngFactory(plan.seed))

    validation = validate_geometry_layout(plan, candidate, attempt_index=1)

    assert validation.hard_constraints.passed is True


def test_unsupported_area_shape_fails_as_capability_error() -> None:
    feature = ResolvedFeature(
        id="area-01",
        metadata=FeatureMetadata(source_preset="test-area"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(shape=GeometryShape.AREA, parameters={}),
        effect=EffectRecipe(stage="terrain", operator="test-effect"),
    )
    plan = make_plan(features=(feature,))

    with pytest.raises(LayoutCapabilityError, match="not implemented"):
        generate_geometry_layout(plan, attempt_index=0, rng_factory=RngFactory(plan.seed))
