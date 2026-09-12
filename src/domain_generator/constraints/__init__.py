"""Generic compiled-constraint evaluation boundaries."""

from .spatial import (
    SpatialConstraintCapabilityError,
    evaluate_hard_constraint,
    evaluate_soft_constraint,
    measure_constraint,
    predicate_satisfied,
    score_measurement,
)

__all__ = [
    "SpatialConstraintCapabilityError",
    "evaluate_hard_constraint",
    "evaluate_soft_constraint",
    "measure_constraint",
    "predicate_satisfied",
    "score_measurement",
]
