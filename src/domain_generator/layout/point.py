from __future__ import annotations

from math import hypot

from ..compiler.compile import semantic_plan_fingerprint
from ..contracts.common import FeaturePart
from ..contracts.geometry import PointGeometry
from ..contracts.layout import LayoutCandidate, SourcePlanRef
from ..contracts.plan import (
    CompiledConstraint,
    CompiledFeatureRef,
    CompiledPoint,
    CompiledRectangle,
    CompiledSpatialRef,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
)
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    HardConstraintResult,
    Measurement,
    PredicateSnapshot,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngKey, RngStage


class LayoutCapabilityError(RuntimeError):
    """The current layout implementation cannot execute a valid plan construct yet."""


def _point_stream_key(attempt_index: int, feature_id: str) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.LAYOUT,
        scope=("feature", feature_id, "geometry", "point"),
        purpose="position",
    )


def generate_point_layout(plan: GenerationPlan, *, attempt_index: int, rng_factory) -> LayoutCandidate:
    """Realize every geometry/point feature once using its isolated semantic RNG stream."""
    geometries: dict[str, PointGeometry] = {}

    for feature in plan.features:
        layout = feature.layout
        if not isinstance(layout, GeometryLayoutRecipe):
            raise LayoutCapabilityError(
                f"placement reservation layout is not implemented yet: {feature.id!r}"
            )
        if layout.shape is not GeometryShape.POINT:
            raise LayoutCapabilityError(
                f"geometry shape {layout.shape.value!r} is not implemented yet: {feature.id!r}"
            )
        if layout.parameters:
            raise LayoutCapabilityError(
                f"point layout v0.1 does not define layout parameters: {feature.id!r}"
            )

        stream = rng_factory.stream(_point_stream_key(attempt_index, feature.id))
        geometries[feature.id] = PointGeometry(
            x_km=plan.domain.width_km * stream.uniform01(),
            y_km=plan.domain.height_km * stream.uniform01(),
        )

    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations=geometries,
        placement_reservations={},
    )


def _resolve_point(ref: CompiledSpatialRef, candidate: LayoutCandidate) -> PointGeometry:
    if isinstance(ref, CompiledPoint):
        return PointGeometry(x_km=ref.x_km, y_km=ref.y_km)
    if isinstance(ref, CompiledFeatureRef):
        if ref.part not in (FeaturePart.WHOLE, FeaturePart.CENTER):
            raise LayoutCapabilityError(f"point feature does not support part {ref.part.value!r}")
        geometry = candidate.geometry_realizations.get(ref.feature_id)
        if not isinstance(geometry, PointGeometry):
            raise LayoutCapabilityError(
                f"feature reference {ref.feature_id!r} does not resolve to point geometry"
            )
        return geometry
    raise LayoutCapabilityError(f"expected point reference, got {ref.type!r}")


def _point_in_rectangle(point: PointGeometry, rectangle: CompiledRectangle) -> bool:
    return (
        rectangle.min_x_km <= point.x_km <= rectangle.max_x_km
        and rectangle.min_y_km <= point.y_km <= rectangle.max_y_km
    )


def _distance_point_rectangle(point: PointGeometry, rectangle: CompiledRectangle) -> float:
    dx = max(rectangle.min_x_km - point.x_km, 0.0, point.x_km - rectangle.max_x_km)
    dy = max(rectangle.min_y_km - point.y_km, 0.0, point.y_km - rectangle.max_y_km)
    return hypot(dx, dy)


def _measure(constraint: CompiledConstraint, candidate: LayoutCandidate) -> tuple[float, str | None]:
    evaluator = constraint.evaluator
    subject = _resolve_point(evaluator.subject, candidate)
    target = evaluator.target

    if evaluator.type == "distance":
        if isinstance(target, CompiledRectangle):
            return _distance_point_rectangle(subject, target), "km"
        target_point = _resolve_point(target, candidate)
        return hypot(subject.x_km - target_point.x_km, subject.y_km - target_point.y_km), "km"

    if evaluator.type in ("contained_fraction", "overlap_fraction"):
        if not isinstance(target, CompiledRectangle):
            raise LayoutCapabilityError(
                f"{evaluator.type} point layout evaluator currently requires rectangle target"
            )
        return (1.0 if _point_in_rectangle(subject, target) else 0.0), None

    raise LayoutCapabilityError(f"layout evaluator {evaluator.type!r} is not implemented in point slice")


def _predicate_satisfied(predicate_type: str, measured: float, threshold: float) -> bool:
    if predicate_type == "less_or_equal":
        return measured <= threshold
    if predicate_type == "greater_or_equal":
        return measured >= threshold
    if predicate_type == "greater_than":
        return measured > threshold
    raise LayoutCapabilityError(f"predicate {predicate_type!r} is not implemented in point slice")


def validate_point_layout(
    plan: GenerationPlan,
    candidate: LayoutCandidate,
    *,
    attempt_index: int,
) -> ValidationResult:
    """Observe one point-only LayoutCandidate without mutating or repairing it."""
    expected_ids = {
        feature.id
        for feature in plan.features
        if isinstance(feature.layout, GeometryLayoutRecipe) and feature.layout.shape is GeometryShape.POINT
    }
    actual_ids = set(candidate.geometry_realizations)
    expected_fingerprint = semantic_plan_fingerprint(plan)

    invariant_results = (
        EngineInvariantResult(
            id="layout-plan-fingerprint-matches",
            passed=candidate.source_plan.fingerprint == expected_fingerprint,
        ),
        EngineInvariantResult(
            id="layout-attempt-index-matches",
            passed=candidate.attempt_index == attempt_index,
        ),
        EngineInvariantResult(
            id="layout-point-feature-set-complete",
            passed=actual_ids == expected_ids,
            measured={
                "expected_count": len(expected_ids),
                "actual_count": len(actual_ids),
            },
        ),
        EngineInvariantResult(
            id="layout-points-inside-domain",
            passed=all(
                isinstance(geometry, PointGeometry)
                and 0.0 <= geometry.x_km <= plan.domain.width_km
                and 0.0 <= geometry.y_km <= plan.domain.height_km
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
    )
    engine_passed = all(item.passed for item in invariant_results)

    hard_results: list[HardConstraintResult] = []
    if engine_passed:
        for constraint in plan.constraints:
            if constraint.predicate is None:
                raise LayoutCapabilityError(
                    f"point layout slice cannot evaluate soft constraint {constraint.id!r}"
                )
            value, measured_unit = _measure(constraint, candidate)
            threshold = float(constraint.predicate.value)
            satisfied = _predicate_satisfied(constraint.predicate.type, value, threshold)
            hard_results.append(
                HardConstraintResult(
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
            )

    hard_passed = all(item.satisfied for item in hard_results)
    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.LAYOUT,
        engine_invariants=EngineInvariantGroup(
            passed=engine_passed,
            results=invariant_results,
        ),
        hard_constraints=HardConstraintGroup(
            passed=hard_passed,
            results=tuple(hard_results),
        ),
        soft_constraints=SoftConstraintGroup(results=()),
        ranking=None,
    )


def point_layout_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    """StageHandler adapter for the existing attempt orchestrator."""
    candidate = generate_point_layout(
        context.plan,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
    state.layout = candidate
    return validate_point_layout(
        context.plan,
        candidate,
        attempt_index=context.attempt_index,
    )
