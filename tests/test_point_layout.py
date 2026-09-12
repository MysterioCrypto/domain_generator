from __future__ import annotations

from domain_generator.compiler.compile import semantic_plan_fingerprint
from domain_generator.contracts.common import ConstraintStrength, FeaturePart
from domain_generator.contracts.plan import (
    CompiledConstraint,
    CompiledEvaluator,
    CompiledFeatureRef,
    CompiledPredicate,
    CompiledRectangle,
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    FeatureMetadata,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
    PlanDomain,
    PlanGrid,
    PlanSource,
    ResolvedFeature,
)
from domain_generator.pipeline.attempts import AttemptContext, CandidateState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.layout import (
    LayoutCapabilityError,
    generate_point_layout,
    point_layout_stage,
    validate_point_layout,
)


def point_feature(feature_id: str, *, label: str | None = None) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(label=label, source_preset="test_point_feature"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(mode="geometry", shape=GeometryShape.POINT, parameters={}),
        effect=EffectRecipe(stage=EffectStage.TERRAIN, operator="test_noop", parameters={}),
    )


def plan(*features: ResolvedFeature, constraints=()) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="test-domain",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0-test",
        ),
        seed=123456,
        domain=PlanDomain(width_km=120.0, height_km=100.0),
        grid=PlanGrid(cell_size_km=0.25, rows=400, columns=480),
        features=features,
        constraints=constraints,
    )


def test_point_layout_replays_exactly_for_same_attempt() -> None:
    generation_plan = plan(point_feature("alpha"), point_feature("beta"))
    factory = RngFactory(generation_plan.seed)

    first = generate_point_layout(generation_plan, attempt_index=3, rng_factory=factory)
    second = generate_point_layout(generation_plan, attempt_index=3, rng_factory=factory)

    assert first == second
    assert first.source_plan.fingerprint == semantic_plan_fingerprint(generation_plan)


def test_point_layout_changes_stream_between_attempts() -> None:
    generation_plan = plan(point_feature("alpha"))
    factory = RngFactory(generation_plan.seed)

    first = generate_point_layout(generation_plan, attempt_index=0, rng_factory=factory)
    second = generate_point_layout(generation_plan, attempt_index=1, rng_factory=factory)

    assert first.geometry_realizations["alpha"] != second.geometry_realizations["alpha"]


def test_feature_order_does_not_change_each_feature_geometry() -> None:
    alpha = point_feature("alpha")
    beta = point_feature("beta")
    first_plan = plan(alpha, beta)
    second_plan = plan(beta, alpha)

    first = generate_point_layout(first_plan, attempt_index=7, rng_factory=RngFactory(first_plan.seed))
    second = generate_point_layout(second_plan, attempt_index=7, rng_factory=RngFactory(second_plan.seed))

    assert first.geometry_realizations["alpha"] == second.geometry_realizations["alpha"]
    assert first.geometry_realizations["beta"] == second.geometry_realizations["beta"]
    assert first.source_plan.fingerprint == second.source_plan.fingerprint


def test_label_change_does_not_change_geometry_or_semantic_fingerprint() -> None:
    first_plan = plan(point_feature("alpha", label="First label"))
    second_plan = plan(point_feature("alpha", label="Renamed"))

    first = generate_point_layout(first_plan, attempt_index=2, rng_factory=RngFactory(first_plan.seed))
    second = generate_point_layout(second_plan, attempt_index=2, rng_factory=RngFactory(second_plan.seed))

    assert first.geometry_realizations == second.geometry_realizations
    assert first.source_plan.fingerprint == second.source_plan.fingerprint


def test_generated_points_are_inside_domain() -> None:
    generation_plan = plan(*(point_feature(f"p-{index}") for index in range(20)))
    candidate = generate_point_layout(
        generation_plan,
        attempt_index=11,
        rng_factory=RngFactory(generation_plan.seed),
    )

    for geometry in candidate.geometry_realizations.values():
        assert 0.0 <= geometry.x_km < generation_plan.domain.width_km
        assert 0.0 <= geometry.y_km < generation_plan.domain.height_km


def test_point_inside_rectangle_constraint_can_reject_without_regeneration() -> None:
    constraint = CompiledConstraint(
        id="alpha-inside-impossible-corner",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="contained_fraction",
            subject=CompiledFeatureRef(feature_id="alpha", part=FeaturePart.WHOLE),
            target=CompiledRectangle(
                min_x_km=120.0,
                max_x_km=120.0,
                min_y_km=100.0,
                max_y_km=100.0,
            ),
        ),
        predicate=CompiledPredicate(type="greater_or_equal", value=1.0),
    )
    generation_plan = plan(point_feature("alpha"), constraints=(constraint,))
    candidate = generate_point_layout(
        generation_plan,
        attempt_index=0,
        rng_factory=RngFactory(generation_plan.seed),
    )
    before = candidate.geometry_realizations["alpha"]

    result = validate_point_layout(generation_plan, candidate, attempt_index=0)

    assert result.engine_invariants.passed is True
    assert result.hard_constraints.passed is False
    assert result.hard_constraints.results[0].measurement.value == 0.0
    assert candidate.geometry_realizations["alpha"] == before


def test_point_distance_constraint_is_measured_in_km() -> None:
    constraint = CompiledConstraint(
        id="alpha-near-beta",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="alpha"),
            target=CompiledFeatureRef(feature_id="beta"),
        ),
        predicate=CompiledPredicate(type="less_or_equal", value=1000.0),
        unit="km",
    )
    generation_plan = plan(point_feature("alpha"), point_feature("beta"), constraints=(constraint,))
    candidate = generate_point_layout(
        generation_plan,
        attempt_index=0,
        rng_factory=RngFactory(generation_plan.seed),
    )

    result = validate_point_layout(generation_plan, candidate, attempt_index=0)

    assert result.hard_constraints.passed is True
    assert result.hard_constraints.results[0].measurement.type == "distance"
    assert result.hard_constraints.results[0].measurement.unit == "km"


def test_stage_handler_sets_candidate_state_layout() -> None:
    generation_plan = plan(point_feature("alpha"))
    context = AttemptContext(
        plan=generation_plan,
        attempt_index=4,
        rng_factory=RngFactory(generation_plan.seed),
    )
    state = CandidateState(attempt_index=4)

    result = point_layout_stage(context, state)

    assert result.stage.value == "layout"
    assert result.engine_invariants.passed is True
    assert state.layout is not None
    assert state.layout.attempt_index == 4


def test_non_point_geometry_is_explicitly_unsupported() -> None:
    feature = point_feature("alpha").model_copy(
        update={"layout": GeometryLayoutRecipe(mode="geometry", shape=GeometryShape.AREA, parameters={})}
    )
    generation_plan = plan(feature)

    try:
        generate_point_layout(generation_plan, attempt_index=0, rng_factory=RngFactory(generation_plan.seed))
    except LayoutCapabilityError as exc:
        assert "not implemented" in str(exc)
    else:
        raise AssertionError("area geometry must not be silently handled by point layout")
