from __future__ import annotations

from ..contracts.common import ConstraintStrength
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import CompiledConstraint, CompiledScoring
from ..contracts.validation import (
    HardConstraintResult,
    Measurement,
    PredicateSnapshot,
    SoftConstraintResult,
)
from ..layout.geometry import LayoutCapabilityError, _measure, _predicate_satisfied


class SpatialConstraintCapabilityError(RuntimeError):
    """A structurally valid compiled spatial constraint is unsupported by Core v0.1."""


def measure_constraint(
    constraint: CompiledConstraint,
    geometry_view: LayoutCandidate,
) -> tuple[float, str | None]:
    """Measure one compiled spatial constraint using the canonical geometry evaluator."""
    try:
        return _measure(constraint, geometry_view)
    except LayoutCapabilityError as exc:
        raise SpatialConstraintCapabilityError(str(exc)) from exc


def predicate_satisfied(predicate_type: str, measured: float, threshold: float) -> bool:
    """Evaluate a compiled hard predicate with the canonical predicate semantics."""
    try:
        return _predicate_satisfied(predicate_type, measured, threshold)
    except LayoutCapabilityError as exc:
        raise SpatialConstraintCapabilityError(str(exc)) from exc


def score_measurement(scoring: CompiledScoring, measured: float) -> float:
    """Map one canonical measurement to a normalized soft score."""
    if scoring.type == "positive":
        if scoring.ideal is not None or scoring.worst is not None:
            raise SpatialConstraintCapabilityError(
                "positive scoring must not define ideal/worst"
            )
        return 1.0 if measured > 0.0 else 0.0

    if scoring.ideal is None or scoring.worst is None:
        raise SpatialConstraintCapabilityError(
            f"scoring {scoring.type!r} requires ideal/worst"
        )

    ideal = float(scoring.ideal)
    worst = float(scoring.worst)

    if scoring.type == "linear_increasing":
        if ideal < worst:
            raise SpatialConstraintCapabilityError(
                "linear_increasing scoring requires ideal >= worst"
            )
        if ideal == worst:
            return 1.0 if measured >= ideal else 0.0
        score = (measured - worst) / (ideal - worst)
        return min(1.0, max(0.0, score))

    if scoring.type == "linear_decreasing":
        if ideal > worst:
            raise SpatialConstraintCapabilityError(
                "linear_decreasing scoring requires ideal <= worst"
            )
        if ideal == worst:
            return 1.0 if measured <= ideal else 0.0
        score = (worst - measured) / (worst - ideal)
        return min(1.0, max(0.0, score))

    raise SpatialConstraintCapabilityError(
        f"scoring {scoring.type!r} is not implemented"
    )


def evaluate_hard_constraint(
    constraint: CompiledConstraint,
    geometry_view: LayoutCandidate,
) -> HardConstraintResult:
    """Evaluate one hard compiled constraint against concrete feature geometry."""
    if constraint.strength is not ConstraintStrength.HARD or constraint.predicate is None:
        raise SpatialConstraintCapabilityError(
            f"constraint {constraint.id!r} is not a hard predicate constraint"
        )

    value, measured_unit = measure_constraint(constraint, geometry_view)
    threshold = float(constraint.predicate.value)
    satisfied = predicate_satisfied(constraint.predicate.type, value, threshold)
    return HardConstraintResult(
        constraint_id=constraint.id,
        satisfied=satisfied,
        measurement=Measurement(
            type=constraint.evaluator.type,
            value=value,
            unit=constraint.unit or measured_unit,
        ),
        predicate=PredicateSnapshot(
            type=constraint.predicate.type,
            threshold=constraint.predicate.value,
        ),
    )


def evaluate_soft_constraint(
    constraint: CompiledConstraint,
    geometry_view: LayoutCandidate,
) -> SoftConstraintResult:
    """Evaluate one soft compiled constraint against concrete final geometry."""
    if (
        constraint.strength is not ConstraintStrength.SOFT
        or constraint.scoring is None
        or constraint.weight is None
    ):
        raise SpatialConstraintCapabilityError(
            f"constraint {constraint.id!r} is not a soft scoring constraint"
        )

    value, measured_unit = measure_constraint(constraint, geometry_view)
    score = score_measurement(constraint.scoring, value)
    weight = float(constraint.weight)
    effective_violation = (1.0 - score) * weight
    return SoftConstraintResult(
        constraint_id=constraint.id,
        score=score,
        weight=weight,
        effective_violation=effective_violation,
        measurement=Measurement(
            type=constraint.evaluator.type,
            value=value,
            unit=constraint.unit or measured_unit,
        ),
    )
