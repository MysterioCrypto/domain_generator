"""Generic compiled-constraint evaluation boundaries."""

from .spatial import (
    SpatialConstraintCapabilityError,
    evaluate_hard_constraint,
    measure_constraint,
    predicate_satisfied,
)

__all__ = [
    "SpatialConstraintCapabilityError",
    "evaluate_hard_constraint",
    "measure_constraint",
    "predicate_satisfied",
]
