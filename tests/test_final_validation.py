from __future__ import annotations

import pytest

from domain_generator.compiler.compile import semantic_plan_fingerprint
from domain_generator.contracts.common import ConstraintStrength
from domain_generator.contracts.geometry import PointGeometry
from domain_generator.contracts.layout import LayoutCandidate, SourcePlanRef
from domain_generator.contracts.plan import (
    CompiledConstraint,
    CompiledEvaluator,
    CompiledFeatureRef,
    CompiledPredicate,
    CompiledScoring,
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    FeatureMetadata,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
    PlanDomain,
    PlanGrid,
    PlanHydrology,
    PlanSource,
    PlanSurface,
    ReservationLayoutRecipe,
    ResolvedFeature,
    SiteProfile,
)
from domain_generator.contracts.validation import ValidationStage
from domain_generator.pipeline.attempts import CandidateState
from domain_generator.pipeline.final import FinalValidationCapabilityError, validate_final
from domain_generator.poi.state import PlacementState


def _anchor_feature() -> ResolvedFeature:
    return ResolvedFeature(
        id="anchor",
        metadata=FeatureMetadata(source_preset="anchor"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(shape=GeometryShape.POINT),
        effect=EffectRecipe(stage=EffectStage.TERRAIN, operator="noop"),
    )


def _deferred_feature() -> ResolvedFeature:
    return ResolvedFeature(
        id="poi",
        metadata=FeatureMetadata(source_preset="poi"),
        family=FeatureFamily.POI,
        layout=ReservationLayoutRecipe(),
        effect=EffectRecipe(
            stage=EffectStage.DEPENDENT_PLACEMENT,
            operator="suitability_placement",
            site_profile=SiteProfile(),
        ),
    )


def _hard_constraint(*, constraint_id: str = "poi-near-anchor", evaluator_type: str = "distance") -> CompiledConstraint:
    return CompiledConstraint(
        id=constraint_id,
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type=evaluator_type,
            subject=CompiledFeatureRef(feature_id="poi"),
            target=CompiledFeatureRef(feature_id="anchor"),
        ),
        predicate=CompiledPredicate(
            type="less_or_equal" if evaluator_type == "distance" else "greater_than",
            value=2.0 if evaluator_type == "distance" else 0.0,
        ),
        unit="km",
    )


def _soft_constraint(
    *,
    constraint_id: str = "soft-near",
    ideal: float = 0.0,
    worst: float = 4.0,
    weight: float = 1.0,
    scoring_type: str = "linear_decreasing",
    evaluator_type: str = "distance",
) -> CompiledConstraint:
    return CompiledConstraint(
        id=constraint_id,
        strength=ConstraintStrength.SOFT,
        evaluator=CompiledEvaluator(
            type=evaluator_type,
            subject=CompiledFeatureRef(feature_id="poi"),
            target=CompiledFeatureRef(feature_id="anchor"),
        ),
        scoring=CompiledScoring(
            type=scoring_type,
            ideal=None if scoring_type == "positive" else ideal,
            worst=None if scoring_type == "positive" else worst,
        ),
        weight=weight,
        unit="km",
    )


def _plan(*, constraints: tuple[CompiledConstraint, ...] | None = None) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="final-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:spec",
            generator_version="0.1.0.dev0",
        ),
        seed=7,
        domain=PlanDomain(width_km=10.0, height_km=10.0),
        grid=PlanGrid(cell_size_km=1.0, rows=10, columns=10),
        hydrology=PlanHydrology(
            stream_threshold_km2=2.0,
            lake_min_area_km2=1.0,
            lake_min_depth_m=1.0,
            river_depth_at_threshold_m=0.5,
            river_depth_exponent=0.3,
        ),
        surface=PlanSurface(
            moisture_base=0.3,
            water_moisture_boost=0.5,
            water_moisture_decay_km=5.0,
            moisture_noise_amplitude=0.0,
            moisture_noise_scale_km=5.0,
            vegetation_slope_zero_deg=45.0,
        ),
        features=(_anchor_feature(), _deferred_feature()),
        constraints=constraints if constraints is not None else (_hard_constraint(),),
    )


def _complete_state(plan: GenerationPlan, *, poi_x: float) -> CandidateState:
    layout = LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=0,
        geometry_realizations={"anchor": PointGeometry(x_km=1.0, y_km=1.0)},
        placement_reservations={},
    )
    return CandidateState(
        attempt_index=0,
        layout=layout,
        terrain=object(),
        hydrology=object(),
        surface=object(),
        placement=PlacementState(final_points={"poi": PointGeometry(x_km=poi_x, y_km=1.0)}),
    )


def test_final_merges_deferred_point_and_evaluates_hard_constraint() -> None:
    plan = _plan()
    result = validate_final(plan, _complete_state(plan, poi_x=2.5), attempt_index=0)

    assert result.stage is ValidationStage.FINAL
    assert result.engine_invariants.passed
    assert result.hard_constraints.passed
    assert len(result.hard_constraints.results) == 1
    hard = result.hard_constraints.results[0]
    assert hard.constraint_id == "poi-near-anchor"
    assert hard.measurement.type == "distance"
    assert hard.measurement.value == pytest.approx(1.5)
    assert result.ranking is not None
    assert result.ranking.worst_effective_violation == 0.0
    assert result.ranking.weighted_mean_score == 1.0
    assert result.soft_constraints.results == ()


def test_final_hard_violation_rejects_without_ranking() -> None:
    plan = _plan()
    result = validate_final(plan, _complete_state(plan, poi_x=5.0), attempt_index=0)

    assert result.engine_invariants.passed
    assert not result.hard_constraints.passed
    assert result.hard_constraints.results[0].satisfied is False
    assert result.ranking is None
    assert result.soft_constraints.results == ()


def test_final_missing_upstream_state_is_normal_rejection_without_constraint_evaluation() -> None:
    plan = _plan()
    state = _complete_state(plan, poi_x=2.0)
    state.placement = None

    result = validate_final(plan, state, attempt_index=0)

    assert not result.engine_invariants.passed
    assert result.hard_constraints.results == ()
    assert result.hard_constraints.passed
    assert result.soft_constraints.results == ()
    assert result.ranking is None


def test_final_constraint_results_are_canonically_sorted_by_id() -> None:
    plan = _plan(
        constraints=(
            _hard_constraint(constraint_id="z-last"),
            _hard_constraint(constraint_id="a-first"),
        )
    )
    result = validate_final(plan, _complete_state(plan, poi_x=2.0), attempt_index=0)

    assert [item.constraint_id for item in result.hard_constraints.results] == ["a-first", "z-last"]


def test_final_evaluates_soft_constraints_and_builds_weighted_ranking() -> None:
    plan = _plan(
        constraints=(
            _hard_constraint(),
            _soft_constraint(
                constraint_id="z-medium",
                worst=4.0,
                weight=0.5,
            ),
            _soft_constraint(
                constraint_id="a-strict",
                worst=2.0,
                weight=1.0,
            ),
        )
    )
    result = validate_final(plan, _complete_state(plan, poi_x=2.0), attempt_index=0)

    assert result.hard_constraints.passed
    assert [item.constraint_id for item in result.soft_constraints.results] == [
        "a-strict",
        "z-medium",
    ]
    first, second = result.soft_constraints.results
    assert first.measurement.value == pytest.approx(1.0)
    assert first.score == pytest.approx(0.5)
    assert first.effective_violation == pytest.approx(0.5)
    assert second.score == pytest.approx(0.75)
    assert second.effective_violation == pytest.approx(0.125)
    assert result.ranking is not None
    assert result.ranking.worst_effective_violation == pytest.approx(0.5)
    assert result.ranking.weighted_mean_score == pytest.approx((0.5 + 0.75 * 0.5) / 1.5)


def test_final_wraps_unsupported_soft_spatial_evaluator_as_capability_error() -> None:
    plan = _plan(
        constraints=(
            _soft_constraint(
                evaluator_type="crossing_length",
                scoring_type="positive",
            ),
        )
    )

    with pytest.raises(FinalValidationCapabilityError, match="crossing_length"):
        validate_final(plan, _complete_state(plan, poi_x=2.0), attempt_index=0)


def test_final_wraps_unknown_scoring_recipe_as_capability_error() -> None:
    plan = _plan(
        constraints=(
            _soft_constraint(scoring_type="unknown", ideal=0.0, worst=4.0),
        )
    )

    with pytest.raises(FinalValidationCapabilityError, match="scoring 'unknown'"):
        validate_final(plan, _complete_state(plan, poi_x=2.0), attempt_index=0)


def test_final_wraps_unsupported_spatial_evaluator_as_capability_error() -> None:
    plan = _plan(constraints=(_hard_constraint(evaluator_type="crossing_length"),))

    with pytest.raises(FinalValidationCapabilityError, match="crossing_length"):
        validate_final(plan, _complete_state(plan, poi_x=2.0), attempt_index=0)
