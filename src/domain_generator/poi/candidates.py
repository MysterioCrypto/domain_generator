from __future__ import annotations

from dataclasses import dataclass
from math import ceil, cos, floor, isfinite, pi, sin

from ..contracts.geometry import PointGeometry
from ..contracts.layout import LayoutCandidate, PlacementReservation
from ..contracts.plan import (
    EffectStage,
    FeatureFamily,
    GenerationPlan,
    ParameterType,
    ReservationLayoutRecipe,
    ResolvedFeature,
    SiteProfile,
    SiteRequirement,
)
from ..geometry import region_set_covers_point
from ..pipeline.rng import RngFactory, RngKey, RngStage
from ..pipeline.sampling import SamplingCapabilityError, sample_resolved_parameter
from .site_metrics import SITE_METRIC_IDS, SiteMetricContext, evaluate_site_metrics


class PlacementCandidateCapabilityError(RuntimeError):
    """Candidate filtering cannot evaluate the supplied placement recipe/runtime state."""


@dataclass(frozen=True, slots=True)
class EvaluatedSite:
    """One runtime candidate point with its complete Core 0.1 metric registry."""

    point: PointGeometry
    metrics: dict[str, float]


def _feature_by_id(plan: GenerationPlan, feature_id: str) -> ResolvedFeature:
    for feature in plan.features:
        if feature.id == feature_id:
            return feature
    raise PlacementCandidateCapabilityError(f"unknown placement feature {feature_id!r}")


def _placement_feature(plan: GenerationPlan, feature_id: str) -> ResolvedFeature:
    feature = _feature_by_id(plan, feature_id)
    if feature.family is not FeatureFamily.POI:
        raise PlacementCandidateCapabilityError(
            f"placement feature {feature_id!r} must use poi family"
        )
    if not isinstance(feature.layout, ReservationLayoutRecipe):
        raise PlacementCandidateCapabilityError(
            f"placement feature {feature_id!r} must use reservation layout"
        )
    if feature.effect.stage is not EffectStage.DEPENDENT_PLACEMENT:
        raise PlacementCandidateCapabilityError(
            f"placement feature {feature_id!r} must use dependent_placement effect stage"
        )
    if feature.effect.operator != "suitability_placement":
        raise PlacementCandidateCapabilityError(
            f"placement operator {feature.effect.operator!r} is unsupported"
        )
    if feature.effect.site_profile is None:
        raise PlacementCandidateCapabilityError(
            f"placement feature {feature_id!r} requires site_profile"
        )
    return feature


def _reservation(layout: LayoutCandidate, feature_id: str) -> PlacementReservation:
    try:
        return layout.placement_reservations[feature_id]
    except KeyError as exc:
        raise PlacementCandidateCapabilityError(
            f"placement feature {feature_id!r} has no materialized reservation"
        ) from exc


def _parameter_key(
    *,
    attempt_index: int,
    feature_id: str,
    parameter_name: str,
) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.PLACEMENT,
        scope=("feature", feature_id, "parameter", parameter_name),
        purpose="sample",
    )


def _sample_candidate_spacing_km(
    feature: ResolvedFeature,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> float:
    parameter_name = "candidate_spacing_km"
    try:
        recipe = feature.effect.parameters[parameter_name]
    except KeyError as exc:
        raise PlacementCandidateCapabilityError(
            f"placement feature {feature.id!r} requires effect parameter {parameter_name!r}"
        ) from exc

    if recipe.type is not ParameterType.FLOAT:
        raise PlacementCandidateCapabilityError(
            f"placement parameter {parameter_name!r} must be a float resolved parameter"
        )

    stream = rng_factory.stream(
        _parameter_key(
            attempt_index=attempt_index,
            feature_id=feature.id,
            parameter_name=parameter_name,
        )
    )
    try:
        sampled = sample_resolved_parameter(recipe, stream)
    except SamplingCapabilityError as exc:
        raise PlacementCandidateCapabilityError(
            f"placement parameter {parameter_name!r} recipe is unsupported for feature "
            f"{feature.id!r}"
        ) from exc

    if isinstance(sampled, bool) or not isinstance(sampled, (int, float)):
        raise PlacementCandidateCapabilityError(
            f"placement parameter {parameter_name!r} must resolve to a numeric value"
        )
    spacing = float(sampled)
    if not isfinite(spacing) or spacing <= 0.0:
        raise PlacementCandidateCapabilityError(
            f"placement parameter {parameter_name!r} must resolve to a finite value > 0"
        )
    return spacing


def _site_candidate_key(
    *,
    attempt_index: int,
    feature_id: str,
    purpose: str,
) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.PLACEMENT,
        scope=("feature", feature_id, "site-candidates"),
        purpose=purpose,
    )


def generate_candidate_points(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    feature_id: str,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> tuple[PointGeometry, ...]:
    """Generate canonical world-space lattice points inside/on one reservation."""
    if layout.attempt_index != attempt_index:
        raise PlacementCandidateCapabilityError(
            "placement layout attempt index must match current attempt"
        )

    feature = _placement_feature(plan, feature_id)
    reservation = _reservation(layout, feature_id)
    spacing = _sample_candidate_spacing_km(
        feature,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )

    if not reservation.allowed_region.polygons:
        return ()

    rotation_stream = rng_factory.stream(
        _site_candidate_key(
            attempt_index=attempt_index,
            feature_id=feature_id,
            purpose="rotation",
        )
    )
    phase_stream = rng_factory.stream(
        _site_candidate_key(
            attempt_index=attempt_index,
            feature_id=feature_id,
            purpose="phase",
        )
    )

    theta = rotation_stream.uniform01() * (pi / 2.0)
    phase_u = phase_stream.uniform01() * spacing
    phase_v = phase_stream.uniform01() * spacing
    cosine = cos(theta)
    sine = sin(theta)

    corners = (
        (0.0, 0.0),
        (plan.domain.width_km, 0.0),
        (0.0, plan.domain.height_km),
        (plan.domain.width_km, plan.domain.height_km),
    )
    rotated_corners = tuple(
        (
            cosine * x + sine * y,
            -sine * x + cosine * y,
        )
        for x, y in corners
    )
    min_u = min(value[0] for value in rotated_corners)
    max_u = max(value[0] for value in rotated_corners)
    min_v = min(value[1] for value in rotated_corners)
    max_v = max(value[1] for value in rotated_corners)

    min_i = ceil((min_u - phase_u) / spacing)
    max_i = floor((max_u - phase_u) / spacing)
    min_j = ceil((min_v - phase_v) / spacing)
    max_j = floor((max_v - phase_v) / spacing)

    coordinates: set[tuple[float, float]] = set()
    for i in range(min_i, max_i + 1):
        u = phase_u + i * spacing
        for j in range(min_j, max_j + 1):
            v = phase_v + j * spacing
            x = cosine * u - sine * v
            y = sine * u + cosine * v
            if not (
                0.0 <= x <= plan.domain.width_km
                and 0.0 <= y <= plan.domain.height_km
            ):
                continue
            point = PointGeometry(x_km=float(x), y_km=float(y))
            if region_set_covers_point(reservation.allowed_region, point):
                coordinates.add((float(x), float(y)))

    return tuple(
        PointGeometry(x_km=x, y_km=y)
        for x, y in sorted(coordinates)
    )


def evaluate_candidate_sites(
    context: SiteMetricContext,
    candidate_points: tuple[PointGeometry, ...],
    site_profile: SiteProfile,
) -> tuple[EvaluatedSite, ...]:
    """Evaluate metrics for canonical candidate points without filtering preferences."""
    return tuple(
        EvaluatedSite(
            point=point,
            metrics=evaluate_site_metrics(
                context,
                point,
                site_profile.footprint_radius_km,
            ),
        )
        for point in candidate_points
    )


def requirement_passes(
    metrics: dict[str, float],
    requirement: SiteRequirement,
) -> bool:
    if requirement.metric not in SITE_METRIC_IDS:
        raise PlacementCandidateCapabilityError(
            f"unknown site metric {requirement.metric!r}"
        )
    try:
        measured = metrics[requirement.metric]
    except KeyError as exc:
        raise PlacementCandidateCapabilityError(
            f"candidate metrics are missing {requirement.metric!r}"
        ) from exc

    threshold = float(requirement.value)
    if requirement.evaluator == "less_or_equal":
        return measured <= threshold
    if requirement.evaluator == "greater_or_equal":
        return measured >= threshold
    raise PlacementCandidateCapabilityError(
        f"unsupported site requirement evaluator {requirement.evaluator!r}"
    )


def filter_valid_sites(
    evaluated_sites: tuple[EvaluatedSite, ...],
    requirements: tuple[SiteRequirement, ...],
) -> tuple[EvaluatedSite, ...]:
    """Keep only sites satisfying every hard SiteProfile requirement."""
    for requirement in requirements:
        if requirement.metric not in SITE_METRIC_IDS:
            raise PlacementCandidateCapabilityError(
                f"unknown site metric {requirement.metric!r}"
            )
        if requirement.evaluator not in ("less_or_equal", "greater_or_equal"):
            raise PlacementCandidateCapabilityError(
                f"unsupported site requirement evaluator {requirement.evaluator!r}"
            )

    return tuple(
        site
        for site in evaluated_sites
        if all(requirement_passes(site.metrics, requirement) for requirement in requirements)
    )


def generate_valid_sites_for_feature(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    context: SiteMetricContext,
    feature_id: str,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> tuple[EvaluatedSite, ...]:
    """Generate, evaluate and hard-filter sites for one deferred point feature."""
    feature = _placement_feature(plan, feature_id)
    profile = feature.effect.site_profile
    assert profile is not None

    points = generate_candidate_points(
        plan,
        layout,
        feature_id,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    evaluated = evaluate_candidate_sites(context, points, profile)
    return filter_valid_sites(evaluated, profile.requirements)
