from __future__ import annotations

from collections.abc import Callable

import pytest

from domain_generator.contracts.config import GenerationConfig
from domain_generator.contracts.plan import GenerationPlan
from domain_generator.contracts.validation import ValidationResult, ValidationStage
from domain_generator.pipeline.attempts import (
    STAGE_ORDER,
    DomainCandidate,
    GenerationFailure,
    PipelineInvariantError,
    RejectedAttempt,
    StageStep,
    run_attempt,
    run_generation,
)


def minimal_plan() -> GenerationPlan:
    return GenerationPlan.model_validate(
        {
            "plan_version": "0.1",
            "source": {
                "spec_id": "pipeline-test",
                "spec_schema_version": "0.1",
                "spec_fingerprint": "sha256:spec",
                "generator_version": "0.1.0.dev0",
            },
            "seed": 123456,
            "domain": {"width_km": 10.0, "height_km": 10.0},
            "grid": {"cell_size_km": 1.0, "rows": 10, "columns": 10},
            "hydrology": {
                "stream_threshold_km2": 25.0,
                "lake_min_area_km2": 1.0,
                "lake_min_depth_m": 2.0,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
            },
            "surface": {
                "moisture_base": 0.35,
                "water_moisture_boost": 0.55,
                "water_moisture_decay_km": 8.0,
                "moisture_noise_amplitude": 0.1,
                "moisture_noise_scale_km": 12.0,
                "vegetation_slope_zero_deg": 45.0,
            },
            "features": [],
            "constraints": [],
        }
    )


def config(*, max_attempts: int, target_valid_candidates: int, debug: bool = False) -> GenerationConfig:
    return GenerationConfig.model_validate(
        {
            "generation_config_version": "0.1",
            "semantic": {
                "max_attempts": max_attempts,
                "target_valid_candidates": target_valid_candidates,
            },
            "observability": {"debug": debug},
        }
    )


def validation(
    *,
    attempt_index: int,
    stage: ValidationStage,
    passed: bool = True,
    worst: float = 0.0,
    mean: float = 1.0,
) -> ValidationResult:
    engine = (
        {"passed": True, "results": []}
        if passed
        else {
            "passed": False,
            "results": [
                {
                    "id": "test-failure",
                    "passed": False,
                    "message": "synthetic stage rejection",
                }
            ],
        }
    )
    ranking = (
        {
            "worst_effective_violation": worst,
            "weighted_mean_score": mean,
        }
        if passed and stage is ValidationStage.FINAL
        else None
    )
    return ValidationResult.model_validate(
        {
            "validation_version": "0.1",
            "attempt_index": attempt_index,
            "stage": stage,
            "engine_invariants": engine,
            "hard_constraints": {"passed": True, "results": []},
            "soft_constraints": {"results": []},
            "ranking": ranking,
        }
    )


def make_steps(
    *,
    calls: list[tuple[int, ValidationStage]],
    fail_stage_by_attempt: dict[int, ValidationStage] | None = None,
    ranking_by_attempt: dict[int, tuple[float, float]] | None = None,
) -> tuple[StageStep, ...]:
    fail_stage_by_attempt = fail_stage_by_attempt or {}
    ranking_by_attempt = ranking_by_attempt or {}
    steps: list[StageStep] = []

    for stage in STAGE_ORDER:
        def handler(context, state, *, current_stage=stage):
            assert state.attempt_index == context.attempt_index
            assert context.rng_factory.root_seed == context.plan.seed
            calls.append((context.attempt_index, current_stage))

            if fail_stage_by_attempt.get(context.attempt_index) is current_stage:
                return validation(
                    attempt_index=context.attempt_index,
                    stage=current_stage,
                    passed=False,
                )

            worst, mean = ranking_by_attempt.get(context.attempt_index, (0.0, 1.0))
            return validation(
                attempt_index=context.attempt_index,
                stage=current_stage,
                passed=True,
                worst=worst,
                mean=mean,
            )

        steps.append(StageStep(stage=stage, handler=handler))

    return tuple(steps)


def test_attempt_stops_at_first_failed_stage_without_retry() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    steps = make_steps(calls=calls, fail_stage_by_attempt={0: ValidationStage.HYDROLOGY})
    outcome = run_attempt(plan=minimal_plan(), attempt_index=0, steps=steps)
    assert isinstance(outcome, RejectedAttempt)
    assert outcome.failed_validation.stage is ValidationStage.HYDROLOGY
    assert calls == [(0, ValidationStage.LAYOUT), (0, ValidationStage.TERRAIN), (0, ValidationStage.HYDROLOGY)]


def test_stage_sequence_must_be_exact_core_order() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    steps = make_steps(calls=calls)[:-1]
    with pytest.raises(ValueError, match="stage steps must exactly follow"):
        run_attempt(plan=minimal_plan(), attempt_index=0, steps=steps)


def test_stage_validation_must_match_attempt_and_stage() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    good_steps = list(make_steps(calls=calls))

    def wrong_layout(context, state):
        return validation(attempt_index=context.attempt_index, stage=ValidationStage.TERRAIN, passed=True)

    good_steps[0] = StageStep(stage=ValidationStage.LAYOUT, handler=wrong_layout)
    with pytest.raises(PipelineInvariantError, match="returned validation"):
        run_attempt(plan=minimal_plan(), attempt_index=0, steps=good_steps)


def test_target_one_is_first_valid_behavior() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    steps = make_steps(calls=calls, fail_stage_by_attempt={0: ValidationStage.LAYOUT}, ranking_by_attempt={1: (0.7, 0.2)})
    result = run_generation(plan=minimal_plan(), config=config(max_attempts=5, target_valid_candidates=1), steps=steps)
    assert result.selected.attempt_index == 1
    assert result.attempts_executed == 2
    assert [candidate.attempt_index for candidate in result.valid_candidates] == [1]
    assert all(attempt_index < 2 for attempt_index, _ in calls)


def test_multiple_valid_candidates_use_minimax_then_mean_then_attempt_index() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    steps = make_steps(calls=calls, ranking_by_attempt={0: (0.20, 0.95), 1: (0.10, 0.70), 2: (0.10, 0.85)})
    result = run_generation(plan=minimal_plan(), config=config(max_attempts=10, target_valid_candidates=3), steps=steps)
    assert result.attempts_executed == 3
    assert result.selected.attempt_index == 2
    assert [candidate.attempt_index for candidate in result.valid_candidates] == [2, 1, 0]


def test_exact_ranking_tie_prefers_lower_attempt_index() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    steps = make_steps(calls=calls, ranking_by_attempt={0: (0.1, 0.8), 1: (0.1, 0.8)})
    result = run_generation(plan=minimal_plan(), config=config(max_attempts=2, target_valid_candidates=2), steps=steps)
    assert result.selected.attempt_index == 0


def test_budget_exhaustion_with_some_valid_candidates_selects_best_available() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    steps = make_steps(calls=calls, fail_stage_by_attempt={1: ValidationStage.SURFACE}, ranking_by_attempt={0: (0.3, 0.9), 2: (0.2, 0.6)})
    result = run_generation(plan=minimal_plan(), config=config(max_attempts=3, target_valid_candidates=3), steps=steps)
    assert result.attempts_executed == 3
    assert result.rejected_attempt_count == 1
    assert result.selected.attempt_index == 2


def test_no_valid_candidate_raises_generation_failure() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    steps = make_steps(calls=calls, fail_stage_by_attempt={0: ValidationStage.LAYOUT, 1: ValidationStage.TERRAIN, 2: ValidationStage.PLACEMENT})
    with pytest.raises(GenerationFailure) as exc_info:
        run_generation(plan=minimal_plan(), config=config(max_attempts=3, target_valid_candidates=2), steps=steps)
    assert exc_info.value.attempts_executed == 3


def test_observability_flags_do_not_change_semantic_result() -> None:
    plan = minimal_plan()
    calls_a: list[tuple[int, ValidationStage]] = []
    calls_b: list[tuple[int, ValidationStage]] = []
    rankings = {0: (0.3, 0.9), 1: (0.1, 0.7)}
    result_a = run_generation(plan=plan, config=config(max_attempts=2, target_valid_candidates=2, debug=False), steps=make_steps(calls=calls_a, ranking_by_attempt=rankings))
    result_b = run_generation(plan=plan, config=config(max_attempts=2, target_valid_candidates=2, debug=True), steps=make_steps(calls=calls_b, ranking_by_attempt=rankings))
    assert result_a.selected.attempt_index == result_b.selected.attempt_index == 1
    assert calls_a == calls_b


def test_completed_attempt_returns_domain_candidate_with_all_stage_validations() -> None:
    calls: list[tuple[int, ValidationStage]] = []
    outcome = run_attempt(plan=minimal_plan(), attempt_index=4, steps=make_steps(calls=calls, ranking_by_attempt={4: (0.0, 1.0)}))
    assert isinstance(outcome, DomainCandidate)
    assert outcome.attempt_index == 4
    assert tuple(item.stage for item in outcome.validations) == STAGE_ORDER
    assert outcome.ranking.worst_effective_violation == 0.0
