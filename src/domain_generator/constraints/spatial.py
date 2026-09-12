from __future__ import annotations

from ..contracts.common import ConstraintStrength
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import CompiledConstraint
from ..contracts.validation import HardConstraintResult, Measurement, PredicateSnapshot
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
