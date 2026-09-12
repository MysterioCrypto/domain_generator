"""Deterministic generation-pipeline infrastructure."""

from .attempts import (
    STAGE_ORDER,
    AttemptContext,
    CandidateState,
    DomainCandidate,
    GenerationFailure,
    GenerationRunResult,
    PipelineInvariantError,
    RejectedAttempt,
    StageStep,
    candidate_rank_key,
    run_attempt,
    run_generation,
    validation_passed,
)
from .final import FinalValidationCapabilityError, final_stage, validate_final
from .rng import RngFactory, RngKey, RngStage, Xoshiro256StarStar

__all__ = [
    "STAGE_ORDER",
    "AttemptContext",
    "CandidateState",
    "DomainCandidate",
    "FinalValidationCapabilityError",
    "GenerationFailure",
    "GenerationRunResult",
    "PipelineInvariantError",
    "RejectedAttempt",
    "RngFactory",
    "RngKey",
    "RngStage",
    "StageStep",
    "Xoshiro256StarStar",
    "candidate_rank_key",
    "final_stage",
    "run_attempt",
    "run_generation",
    "validate_final",
    "validation_passed",
]
