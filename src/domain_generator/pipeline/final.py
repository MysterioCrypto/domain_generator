from __future__ import annotations

from ..compiler.compile import semantic_plan_fingerprint
from ..constraints import (
    SpatialConstraintCapabilityError,
    evaluate_hard_constraint,
    evaluate_soft_constraint,
)
from ..contracts.common import ConstraintStrength
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import GenerationPlan, GeometryLayoutRecipe, ReservationLayoutRecipe
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    RankingResult,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from .attempts import AttemptContext, CandidateState


class FinalValidationCapabilityError(RuntimeError):
    """The current Final Validation implementation cannot execute a valid Plan construct yet."""


def _feature_partitions(plan: GenerationPlan) -> tuple[set[str], set[str]]:
    structural = {
        feature.id
        for feature in plan.features
        if isinstance(feature.layout, GeometryLayoutRecipe)
    }
    deferred = {
        feature.id
        for feature in plan.features
        if isinstance(feature.layout, ReservationLayoutRecipe)
    }
    return structural, deferred


def _final_geometry_view(
    layout: LayoutCandidate,
    placement,
) -> LayoutCandidate:
    geometries = dict(layout.geometry_realizations)
    overlap = set(geometries) & set(placement.final_points)
    if overlap:
        raise FinalValidationCapabilityError(
            f"final geometry sources overlap for feature ids: {sorted(overlap)}"
        )
    geometries.update(placement.final_points)
    return LayoutCandidate(
        layout_version=layout.layout_version,
        source_plan=layout.source_plan,
        attempt_index=layout.attempt_index,
        geometry_realizations=geometries,
        placement_reservations={},
    )


def _ranking_from_soft_results(soft_results) -> RankingResult:
    if not soft_results:
        return RankingResult(
            worst_effective_violation=0.0,
            weighted_mean_score=1.0,
        )

    total_weight = sum(result.weight for result in soft_results)
    weighted_mean_score = (
        sum(result.score * result.weight for result in soft_results) / total_weight
    )
    return RankingResult(
        worst_effective_violation=max(
            result.effective_violation for result in soft_results
        ),
        weighted_mean_score=weighted_mean_score,
    )


def validate_final(
    plan: GenerationPlan,
    state: CandidateState,
    *,
    attempt_index: int,
) -> ValidationResult:
    """Observe one complete attempt and produce canonical final ranking."""
    expected_structural, expected_deferred = _feature_partitions(plan)
    expected_all = expected_structural | expected_deferred

    state_attempt_matches = state.attempt_index == attempt_index
    layout_exists = state.layout is not None
    terrain_exists = state.terrain is not None
    hydrology_exists = state.hydrology is not None
    surface_exists = state.surface is not None
    placement_exists = state.placement is not None

    layout_attempt_matches = layout_exists and state.layout.attempt_index == attempt_index
    layout_plan_matches = (
        layout_exists
        and state.layout.source_plan.fingerprint == semantic_plan_fingerprint(plan)
    )

    structural_actual = set(state.layout.geometry_realizations) if layout_exists else set()
    deferred_actual = set(state.placement.final_points) if placement_exists else set()
    structural_complete = layout_exists and structural_actual == expected_structural
    deferred_complete = placement_exists and deferred_actual == expected_deferred
    sources_disjoint = not bool(structural_actual & deferred_actual)
    final_actual = structural_actual | deferred_actual
    final_complete = (
        structural_complete
        and deferred_complete
        and sources_disjoint
        and final_actual == expected_all
    )

    invariant_results = (
        EngineInvariantResult(
            id="final-state-attempt-index-matches",
            passed=state_attempt_matches,
        ),
        EngineInvariantResult(id="final-upstream-layout-exists", passed=layout_exists),
        EngineInvariantResult(id="final-upstream-terrain-exists", passed=terrain_exists),
        EngineInvariantResult(id="final-upstream-hydrology-exists", passed=hydrology_exists),
        EngineInvariantResult(id="final-upstream-surface-exists", passed=surface_exists),
        EngineInvariantResult(id="final-upstream-placement-exists", passed=placement_exists),
        EngineInvariantResult(
            id="final-layout-attempt-index-matches",
            passed=layout_attempt_matches,
        ),
        EngineInvariantResult(
            id="final-layout-plan-fingerprint-matches",
            passed=layout_plan_matches,
        ),
        EngineInvariantResult(
            id="final-structural-feature-set-complete",
            passed=structural_complete,
            measured={
                "expected_count": len(expected_structural),
                "actual_count": len(structural_actual),
            },
        ),
        EngineInvariantResult(
            id="final-deferred-feature-set-complete",
            passed=deferred_complete,
            measured={
                "expected_count": len(expected_deferred),
                "actual_count": len(deferred_actual),
            },
        ),
        EngineInvariantResult(
            id="final-geometry-sources-disjoint",
            passed=sources_disjoint,
        ),
        EngineInvariantResult(
            id="final-feature-geometry-set-complete",
            passed=final_complete,
            measured={
                "expected_count": len(expected_all),
                "actual_count": len(final_actual),
            },
        ),
    )
    engine_passed = all(item.passed for item in invariant_results)

    hard_results = ()
    soft_results = ()
    if engine_passed:
        assert state.layout is not None and state.placement is not None
        geometry_view = _final_geometry_view(state.layout, state.placement)
        hard_constraints = sorted(
            (
                constraint
                for constraint in plan.constraints
                if constraint.strength is ConstraintStrength.HARD
            ),
            key=lambda item: item.id,
        )
        soft_constraints = sorted(
            (
                constraint
                for constraint in plan.constraints
                if constraint.strength is ConstraintStrength.SOFT
            ),
            key=lambda item: item.id,
        )
        try:
            hard_results = tuple(
                evaluate_hard_constraint(constraint, geometry_view)
                for constraint in hard_constraints
            )
            if all(item.satisfied for item in hard_results):
                soft_results = tuple(
                    evaluate_soft_constraint(constraint, geometry_view)
                    for constraint in soft_constraints
                )
        except SpatialConstraintCapabilityError as exc:
            raise FinalValidationCapabilityError(str(exc)) from exc

    hard_passed = all(item.satisfied for item in hard_results)
    valid = engine_passed and hard_passed
    ranking = _ranking_from_soft_results(soft_results) if valid else None

    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.FINAL,
        engine_invariants=EngineInvariantGroup(
            passed=engine_passed,
            results=invariant_results,
        ),
        hard_constraints=HardConstraintGroup(
            passed=hard_passed,
            results=hard_results,
        ),
        soft_constraints=SoftConstraintGroup(results=soft_results),
        ranking=ranking,
    )


def final_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    """Final StageHandler for Core 0.1 hard/soft plans."""
    return validate_final(
        context.plan,
        state,
        attempt_index=context.attempt_index,
    )
