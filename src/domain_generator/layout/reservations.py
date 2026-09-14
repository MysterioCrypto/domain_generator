from __future__ import annotations

from math import hypot

from ..compiler.compile import semantic_plan_fingerprint
from ..contracts.common import ConstraintStrength, FeaturePart
from ..contracts.geometry import AreaGeometry, BandGeometry, CorridorGeometry, PointGeometry, WorldPoint
from ..contracts.layout import LayoutCandidate, PlacementReservation, SourcePlanRef
from ..contracts.plan import (
    CompiledConstraint,
    CompiledFeatureRef,
    CompiledPoint,
    CompiledRectangle,
    CompiledSpatialRef,
    GenerationPlan,
    GeometryLayoutRecipe,
    ReservationLayoutRecipe,
)
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from ..geometry import (
    BooleanGeometry,
    backend_area,
    backend_area_boundary,
    backend_corridor,
    backend_domain,
    backend_point,
    backend_rectangle,
    buffer_geometry,
    intersect_geometry,
    subtract_geometry,
    to_region_set,
)
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngFactory
from .area import area_centroid
from .geometry import generate_geometry_layout, validate_geometry_layout


class ReservationCapabilityError(RuntimeError):
    """A valid plan construct is outside placement-reservation v0.1 capability."""


def _reservation_feature_ids(plan: GenerationPlan) -> frozenset[str]:
    return frozenset(
        feature.id
        for feature in plan.features
        if isinstance(feature.layout, ReservationLayoutRecipe)
    )


def _ref_feature_id(ref: CompiledSpatialRef) -> str | None:
    return ref.feature_id if isinstance(ref, CompiledFeatureRef) else None


def _constraint_references_any(
    constraint: CompiledConstraint,
    feature_ids: frozenset[str],
) -> bool:
    return (
        _ref_feature_id(constraint.evaluator.subject) in feature_ids
        or _ref_feature_id(constraint.evaluator.target) in feature_ids
    )


def _concrete_geometry_plan(plan: GenerationPlan) -> GenerationPlan:
    """Internal plan view for concrete geometry generation and hard validation only."""
    reservation_ids = _reservation_feature_ids(plan)
    features = tuple(
        feature
        for feature in plan.features
        if isinstance(feature.layout, GeometryLayoutRecipe)
    )
    constraints = tuple(
        constraint
        for constraint in plan.constraints
        if constraint.strength is ConstraintStrength.HARD
        and not _constraint_references_any(constraint, reservation_ids)
    )
    return plan.model_copy(update={"features": features, "constraints": constraints})


def _polyline_arc_center(centerline: tuple[WorldPoint, ...], *, name: str) -> PointGeometry:
    lengths: list[tuple[WorldPoint, WorldPoint, float]] = []
    total = 0.0
    for left, right in zip(centerline, centerline[1:]):
        length = hypot(right.x_km - left.x_km, right.y_km - left.y_km)
        lengths.append((left, right, length))
        total += length
    if total <= 0.0:
        raise ReservationCapabilityError(f"cannot resolve center of degenerate {name}")

    target = total * 0.5
    traversed = 0.0
    for left, right, length in lengths:
        if length > 0.0 and traversed + length >= target:
            local = (target - traversed) / length
            return PointGeometry(
                x_km=left.x_km + (right.x_km - left.x_km) * local,
                y_km=left.y_km + (right.y_km - left.y_km) * local,
            )
        traversed += length

    last = centerline[-1]
    return PointGeometry(x_km=last.x_km, y_km=last.y_km)


def _feature_geometry(
    ref: CompiledFeatureRef,
    candidate: LayoutCandidate,
):
    try:
        geometry = candidate.geometry_realizations[ref.feature_id]
    except KeyError as exc:
        raise ReservationCapabilityError(
            f"reservation target feature {ref.feature_id!r} has no concrete layout geometry"
        ) from exc
    return geometry


def _point_like_feature_target(
    ref: CompiledFeatureRef,
    candidate: LayoutCandidate,
) -> PointGeometry | None:
    geometry = _feature_geometry(ref, candidate)

    if isinstance(geometry, PointGeometry):
        if ref.part in (FeaturePart.WHOLE, FeaturePart.CENTER):
            return geometry
        return None

    if isinstance(geometry, CorridorGeometry):
        if ref.part is FeaturePart.START:
            point = geometry.centerline[0]
            return PointGeometry(x_km=point.x_km, y_km=point.y_km)
        if ref.part is FeaturePart.END:
            point = geometry.centerline[-1]
            return PointGeometry(x_km=point.x_km, y_km=point.y_km)
        if ref.part is FeaturePart.CENTER:
            return _polyline_arc_center(geometry.centerline, name="corridor")
        return None

    if isinstance(geometry, BandGeometry):
        if ref.part is FeaturePart.START:
            point = geometry.centerline[0]
            return PointGeometry(x_km=point.x_km, y_km=point.y_km)
        if ref.part is FeaturePart.END:
            point = geometry.centerline[-1]
            return PointGeometry(x_km=point.x_km, y_km=point.y_km)
        if ref.part is FeaturePart.CENTER:
            return _polyline_arc_center(geometry.centerline, name="band")
        return None

    if isinstance(geometry, AreaGeometry) and ref.part is FeaturePart.CENTER:
        return area_centroid(geometry)

    return None


def _distance_target_backend(
    ref: CompiledSpatialRef,
    candidate: LayoutCandidate,
) -> BooleanGeometry:
    if isinstance(ref, CompiledPoint):
        return backend_point(PointGeometry(x_km=ref.x_km, y_km=ref.y_km))
    if isinstance(ref, CompiledRectangle):
        return backend_rectangle(ref)
    if not isinstance(ref, CompiledFeatureRef):
        raise ReservationCapabilityError(f"unsupported reservation target: {ref!r}")

    point = _point_like_feature_target(ref, candidate)
    if point is not None:
        return backend_point(point)

    geometry = _feature_geometry(ref, candidate)
    if isinstance(geometry, CorridorGeometry) and ref.part is FeaturePart.WHOLE:
        return backend_corridor(geometry)
    if isinstance(geometry, AreaGeometry):
        if ref.part is FeaturePart.WHOLE:
            return backend_area(geometry)
        if ref.part is FeaturePart.BOUNDARY:
            return backend_area_boundary(geometry)
    if isinstance(geometry, BandGeometry) and ref.part in (FeaturePart.WHOLE, FeaturePart.BOUNDARY):
        raise ReservationCapabilityError(
            f"band part {ref.part.value!r} requires footprint materialization"
        )

    raise ReservationCapabilityError(
        f"feature {ref.feature_id!r} part {ref.part.value!r} is unsupported as distance target"
    )


def _region_target_backend(
    ref: CompiledSpatialRef,
    candidate: LayoutCandidate,
) -> BooleanGeometry:
    if isinstance(ref, CompiledRectangle):
        return backend_rectangle(ref)
    if isinstance(ref, CompiledFeatureRef):
        geometry = _feature_geometry(ref, candidate)
        if isinstance(geometry, AreaGeometry) and ref.part is FeaturePart.WHOLE:
            return backend_area(geometry)
    raise ReservationCapabilityError(
        "inside/outside reservation target must be a literal rectangle or AreaGeometry.whole"
    )


def _reservation_operation(
    constraint: CompiledConstraint,
    candidate: LayoutCandidate,
    allowed: BooleanGeometry,
) -> BooleanGeometry:
    if constraint.strength is not ConstraintStrength.HARD or constraint.predicate is None:
        raise ReservationCapabilityError(
            f"reservation materialization requires hard predicate constraint: {constraint.id!r}"
        )

    evaluator = constraint.evaluator
    predicate = constraint.predicate
    threshold = float(predicate.value)

    if (
        evaluator.type == "contained_fraction"
        and predicate.type == "greater_or_equal"
        and threshold == 1.0
    ):
        return intersect_geometry(allowed, _region_target_backend(evaluator.target, candidate))

    if (
        evaluator.type == "overlap_fraction"
        and predicate.type == "less_or_equal"
        and threshold == 0.0
    ):
        return subtract_geometry(allowed, _region_target_backend(evaluator.target, candidate))

    if evaluator.type == "distance" and predicate.type in ("less_or_equal", "greater_or_equal"):
        if constraint.unit != "km":
            raise ReservationCapabilityError(
                f"distance reservation constraint {constraint.id!r} must use km"
            )
        if threshold < 0.0:
            raise ReservationCapabilityError("distance reservation threshold must be >= 0")
        target = _distance_target_backend(evaluator.target, candidate)
        buffered = buffer_geometry(target, threshold)
        if predicate.type == "less_or_equal":
            return intersect_geometry(allowed, buffered)
        return subtract_geometry(allowed, buffered)

    raise ReservationCapabilityError(
        f"constraint {constraint.id!r} evaluator/predicate combination is unsupported "
        "for point reservation materialization"
    )


def _constraints_for_reservation(
    plan: GenerationPlan,
    feature_id: str,
) -> tuple[CompiledConstraint, ...]:
    result: list[CompiledConstraint] = []
    for constraint in sorted(plan.constraints, key=lambda item: item.id):
        if constraint.strength is ConstraintStrength.SOFT:
            continue

        subject = constraint.evaluator.subject
        target = constraint.evaluator.target
        subject_id = _ref_feature_id(subject)
        target_id = _ref_feature_id(target)

        if target_id == feature_id and subject_id != feature_id:
            raise ReservationCapabilityError(
                f"constraint {constraint.id!r} references deferred feature {feature_id!r} "
                "as target; Core 0.1 reservation materialization requires it as subject"
            )
        if subject_id != feature_id:
            continue
        if not isinstance(subject, CompiledFeatureRef) or subject.part not in (
            FeaturePart.WHOLE,
            FeaturePart.CENTER,
        ):
            raise ReservationCapabilityError(
                f"reservation subject {feature_id!r} must use whole/center point selector"
            )
        result.append(constraint)
    return tuple(result)


def materialize_placement_reservations(
    plan: GenerationPlan,
    geometry_candidate: LayoutCandidate,
) -> LayoutCandidate:
    reservations: dict[str, PlacementReservation] = {}

    for feature in sorted(plan.features, key=lambda item: item.id):
        if not isinstance(feature.layout, ReservationLayoutRecipe):
            continue

        allowed = backend_domain(plan.domain.width_km, plan.domain.height_km)
        source_constraints: list[str] = []
        for constraint in _constraints_for_reservation(plan, feature.id):
            allowed = _reservation_operation(constraint, geometry_candidate, allowed)
            source_constraints.append(constraint.id)

        reservations[feature.id] = PlacementReservation(
            final_shape="point",
            source_constraints=tuple(source_constraints),
            allowed_region=to_region_set(allowed),
        )

    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=geometry_candidate.attempt_index,
        geometry_realizations=geometry_candidate.geometry_realizations,
        placement_reservations=reservations,
    )


def generate_layout(
    plan: GenerationPlan,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> LayoutCandidate:
    geometry_plan = _concrete_geometry_plan(plan)
    geometry_candidate = generate_geometry_layout(
        geometry_plan,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    return materialize_placement_reservations(plan, geometry_candidate)


def validate_layout(
    plan: GenerationPlan,
    candidate: LayoutCandidate,
    *,
    attempt_index: int,
) -> ValidationResult:
    geometry_plan = _concrete_geometry_plan(plan)
    projected_candidate = LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(geometry_plan)),
        attempt_index=candidate.attempt_index,
        geometry_realizations=candidate.geometry_realizations,
        placement_reservations={},
    )
    geometry_validation = validate_geometry_layout(
        geometry_plan,
        projected_candidate,
        attempt_index=attempt_index,
    )

    expected_geometry_ids = {
        feature.id
        for feature in plan.features
        if isinstance(feature.layout, GeometryLayoutRecipe)
    }
    expected_reservation_ids = {
        feature.id
        for feature in plan.features
        if isinstance(feature.layout, ReservationLayoutRecipe)
    }
    actual_geometry_ids = set(candidate.geometry_realizations)
    actual_reservation_ids = set(candidate.placement_reservations)

    inherited_geometry_invariants = tuple(
        result
        for result in geometry_validation.engine_invariants.results
        if result.id not in {
            "layout-plan-fingerprint-matches",
            "layout-attempt-index-matches",
            "layout-supported-feature-set-complete",
        }
    )
    reservation_nonempty = all(
        bool(reservation.allowed_region.polygons)
        for reservation in candidate.placement_reservations.values()
    )

    invariant_results = (
        EngineInvariantResult(
            id="layout-plan-fingerprint-matches",
            passed=candidate.source_plan.fingerprint == semantic_plan_fingerprint(plan),
        ),
        EngineInvariantResult(
            id="layout-attempt-index-matches",
            passed=candidate.attempt_index == attempt_index,
        ),
        EngineInvariantResult(
            id="layout-feature-partition-complete",
            passed=(
                actual_geometry_ids == expected_geometry_ids
                and actual_reservation_ids == expected_reservation_ids
            ),
            measured={
                "expected_geometry_count": len(expected_geometry_ids),
                "actual_geometry_count": len(actual_geometry_ids),
                "expected_reservation_count": len(expected_reservation_ids),
                "actual_reservation_count": len(actual_reservation_ids),
            },
        ),
        *inherited_geometry_invariants,
        EngineInvariantResult(
            id="layout-placement-reservations-nonempty",
            passed=reservation_nonempty,
            measured={"reservation_count": len(candidate.placement_reservations)},
        ),
    )
    engine_passed = all(result.passed for result in invariant_results)

    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.LAYOUT,
        engine_invariants=EngineInvariantGroup(
            passed=engine_passed,
            results=invariant_results,
        ),
        hard_constraints=HardConstraintGroup(
            passed=geometry_validation.hard_constraints.passed,
            results=geometry_validation.hard_constraints.results,
        ),
        soft_constraints=SoftConstraintGroup(results=()),
        ranking=None,
    )


def layout_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    candidate = generate_layout(
        context.plan,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
    state.layout = candidate
    return validate_layout(
        context.plan,
        candidate,
        attempt_index=context.attempt_index,
    )
