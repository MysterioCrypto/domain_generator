from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

from ..contracts.config import GenerationConfig
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import GenerationPlan
from ..contracts.validation import RankingResult, ValidationResult, ValidationStage
from .rng import RngFactory, UINT64_MAX

if TYPE_CHECKING:
    from ..hydrology.state import HydrologyState
    from ..surface.state import SurfaceState
    from ..terrain.state import TerrainState


STAGE_ORDER: tuple[ValidationStage, ...] = (
    ValidationStage.LAYOUT,
    ValidationStage.TERRAIN,
    ValidationStage.HYDROLOGY,
    ValidationStage.SURFACE,
    ValidationStage.PLACEMENT,
    ValidationStage.FINAL,
)


class PipelineInvariantError(RuntimeError):
    """A stage violated the internal orchestration contract."""


class GenerationFailure(RuntimeError):
    """Generation exhausted its attempt budget without one valid candidate."""

    def __init__(self, *, attempts_executed: int) -> None:
        self.attempts_executed = attempts_executed
        super().__init__(f"generation produced no valid candidate after {attempts_executed} attempts")


@dataclass(slots=True)
class CandidateState:
    """Mutable per-attempt runtime state, intentionally not a serialized contract."""

    attempt_index: int
    layout: LayoutCandidate | None = None
    terrain: TerrainState | None = None
    hydrology: HydrologyState | None = None
    surface: SurfaceState | None = None

    def __post_init__(self) -> None:
        if isinstance(self.attempt_index, bool) or not isinstance(self.attempt_index, int):
            raise TypeError("attempt_index must be an integer")
        if not 0 <= self.attempt_index <= UINT64_MAX:
            raise ValueError("attempt_index must be in [0, 2^64-1]")


@dataclass(frozen=True, slots=True)
class AttemptContext:
    """Read-only semantic context shared by all stages of one attempt."""

    plan: GenerationPlan
    attempt_index: int
    rng_factory: RngFactory


StageHandler: TypeAlias = Callable[[AttemptContext, CandidateState], ValidationResult]


@dataclass(frozen=True, slots=True)
class StageStep:
    stage: ValidationStage
    handler: StageHandler


@dataclass(frozen=True, slots=True)
class RejectedAttempt:
    attempt_index: int
    validations: tuple[ValidationResult, ...]

    @property
    def failed_validation(self) -> ValidationResult:
        return self.validations[-1]


@dataclass(frozen=True, slots=True)
class DomainCandidate:
    """One complete valid attempt before DomainData assembly."""

    attempt_index: int
    state: CandidateState
    validations: tuple[ValidationResult, ...]

    @property
    def final_validation(self) -> ValidationResult:
        return self.validations[-1]

    @property
    def ranking(self) -> RankingResult:
        ranking = self.final_validation.ranking
        if ranking is None:
            raise PipelineInvariantError("valid DomainCandidate must have final ranking")
        return ranking


AttemptOutcome: TypeAlias = RejectedAttempt | DomainCandidate


@dataclass(frozen=True, slots=True)
class GenerationRunResult:
    selected: DomainCandidate
    valid_candidates: tuple[DomainCandidate, ...]
    attempts_executed: int

    @property
    def rejected_attempt_count(self) -> int:
        return self.attempts_executed - len(self.valid_candidates)


def validation_passed(result: ValidationResult) -> bool:
    return result.engine_invariants.passed and result.hard_constraints.passed


def _validate_stage_steps(steps: Sequence[StageStep]) -> tuple[StageStep, ...]:
    normalized = tuple(steps)
    actual = tuple(step.stage for step in normalized)
    if actual != STAGE_ORDER:
        expected_text = ", ".join(stage.value for stage in STAGE_ORDER)
        actual_text = ", ".join(stage.value for stage in actual)
        raise ValueError(f"stage steps must exactly follow [{expected_text}], got [{actual_text}]")
    return normalized


def _validate_stage_result(
    *,
    validation: ValidationResult,
    expected_stage: ValidationStage,
    attempt_index: int,
) -> None:
    if validation.attempt_index != attempt_index:
        raise PipelineInvariantError(
            f"stage {expected_stage.value!r} returned validation for attempt "
            f"{validation.attempt_index}, expected {attempt_index}"
        )
    if validation.stage is not expected_stage:
        raise PipelineInvariantError(
            f"stage step {expected_stage.value!r} returned validation for {validation.stage.value!r}"
        )
    if expected_stage is not ValidationStage.FINAL and validation.ranking is not None:
        raise PipelineInvariantError("candidate ranking is only valid on final validation")


def run_attempt(
    *,
    plan: GenerationPlan,
    attempt_index: int,
    steps: Sequence[StageStep],
) -> AttemptOutcome:
    """Execute one independent attempt once through each stage until first hard rejection."""
    normalized_steps = _validate_stage_steps(steps)
    state = CandidateState(attempt_index=attempt_index)
    context = AttemptContext(
        plan=plan,
        attempt_index=attempt_index,
        rng_factory=RngFactory(plan.seed),
    )
    validations: list[ValidationResult] = []

    for step in normalized_steps:
        validation = step.handler(context, state)
        if not isinstance(validation, ValidationResult):
            raise PipelineInvariantError(f"stage {step.stage.value!r} did not return ValidationResult")
        _validate_stage_result(
            validation=validation,
            expected_stage=step.stage,
            attempt_index=attempt_index,
        )
        validations.append(validation)

        if not validation_passed(validation):
            return RejectedAttempt(
                attempt_index=attempt_index,
                validations=tuple(validations),
            )

    candidate = DomainCandidate(
        attempt_index=attempt_index,
        state=state,
        validations=tuple(validations),
    )
    _ = candidate.ranking
    return candidate


def candidate_rank_key(candidate: DomainCandidate) -> tuple[float, float, int]:
    ranking = candidate.ranking
    return (
        ranking.worst_effective_violation,
        -ranking.weighted_mean_score,
        candidate.attempt_index,
    )


def run_generation(
    *,
    plan: GenerationPlan,
    config: GenerationConfig,
    steps: Sequence[StageStep],
) -> GenerationRunResult:
    """Run independent attempts in ascending index order and deterministically select a valid candidate."""
    normalized_steps = _validate_stage_steps(steps)
    semantic = config.semantic
    valid_candidates: list[DomainCandidate] = []
    attempts_executed = 0

    for attempt_index in range(semantic.max_attempts):
        outcome = run_attempt(
            plan=plan,
            attempt_index=attempt_index,
            steps=normalized_steps,
        )
        attempts_executed += 1

        if isinstance(outcome, DomainCandidate):
            valid_candidates.append(outcome)
            if len(valid_candidates) >= semantic.target_valid_candidates:
                break

    if not valid_candidates:
        raise GenerationFailure(attempts_executed=attempts_executed)

    ranked = tuple(sorted(valid_candidates, key=candidate_rank_key))
    return GenerationRunResult(
        selected=ranked[0],
        valid_candidates=ranked,
        attempts_executed=attempts_executed,
    )
