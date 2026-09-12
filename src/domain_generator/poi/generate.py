from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from ..contracts.layout import LayoutCandidate
from ..contracts.plan import GenerationPlan, ReservationLayoutRecipe, ResolvedFeature
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from ..geometry import region_set_covers_point
from ..hydrology.state import HydrologyState
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngFactory
from ..surface.state import SurfaceState
from ..terrain.state import TerrainState
from .candidates import (
    PlacementCandidateCapabilityError,
    generate_valid_sites_for_feature,
    requirement_passes,
)
from .selection import PlacementSelectionCapabilityError, select_final_site
from .site_metrics import SiteMetricCapabilityError, SiteMetricContext, evaluate_site_metrics
from .state import PlacementState


@dataclass(frozen=True, slots=True)
class _PlacementBuildResult:
    state: PlacementState
    no_valid_feature_ids: tuple[str, ...]


def _placement_features(plan: GenerationPlan) -> tuple[ResolvedFeature, ...]:
    return tuple(
        sorted(
            (
                feature
                for feature in plan.features
                if isinstance(feature.layout, ReservationLayoutRecipe)
            ),
            key=lambda feature: feature.id,
        )
    )


def _build_placement(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    terrain: TerrainState,
    hydrology: HydrologyState,
    surface: SurfaceState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> _PlacementBuildResult:
    if layout.attempt_index != attempt_index:
        raise PlacementCandidateCapabilityError(
            "placement layout attempt index must match current attempt"
        )

    metric_context = SiteMetricContext.from_states(plan, terrain, hydrology, surface)
    final_points = {}
    no_valid: list[str] = []

    for feature in _placement_features(plan):
        valid_sites = generate_valid_sites_for_feature(
            plan,
            layout,
            metric_context,
            feature.id,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )
        selected = select_final_site(
            feature,
            valid_sites,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )
        if selected is None:
            no_valid.append(feature.id)
            continue
        final_points[feature.id] = selected.site.point

    return _PlacementBuildResult(
        state=PlacementState(final_points=final_points),
        no_valid_feature_ids=tuple(no_valid),
    )


def generate_placement(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    terrain: TerrainState,
    hydrology: HydrologyState,
    surface: SurfaceState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> PlacementState:
    """Generate final points for all deferred Core 0.1 placement features."""
    return _build_placement(
        plan,
        layout,
        terrain,
        hydrology,
        surface,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    ).state


def _selected_points_finite_in_domain(
    plan: GenerationPlan,
    placement: PlacementState,
) -> bool:
    return all(
        isfinite(point.x_km)
        and isfinite(point.y_km)
        and 0.0 <= point.x_km <= plan.domain.width_km
        and 0.0 <= point.y_km <= plan.domain.height_km
        for point in placement.final_points.values()
    )


def _selected_points_in_reservations(
    layout: LayoutCandidate,
    placement: PlacementState,
) -> bool:
    for feature_id, point in placement.final_points.items():
        reservation = layout.placement_reservations.get(feature_id)
        if reservation is None:
            return False
        if not region_set_covers_point(reservation.allowed_region, point):
            return False
    return True


def _selected_requirements_pass(
    plan: GenerationPlan,
    terrain: TerrainState,
    hydrology: HydrologyState,
    surface: SurfaceState,
    placement: PlacementState,
) -> bool:
    context = SiteMetricContext.from_states(plan, terrain, hydrology, surface)
    features = {feature.id: feature for feature in _placement_features(plan)}
    for feature_id, point in placement.final_points.items():
        feature = features.get(feature_id)
        if feature is None or feature.effect.site_profile is None:
            return False
        profile = feature.effect.site_profile
        metrics = evaluate_site_metrics(context, point, profile.footprint_radius_km)
        if not all(requirement_passes(metrics, requirement) for requirement in profile.requirements):
            return False
    return True


def validate_placement(
    plan: GenerationPlan,
    layout: LayoutCandidate | None,
    terrain: TerrainState | None,
    hydrology: HydrologyState | None,
    surface: SurfaceState | None,
    placement: PlacementState | None,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> ValidationResult:
    expected_ids = tuple(feature.id for feature in _placement_features(plan))
    expected_set = set(expected_ids)

    layout_exists = layout is not None
    layout_attempt_matches = layout_exists and layout.attempt_index == attempt_index
    terrain_exists = terrain is not None
    hydrology_exists = hydrology is not None
    surface_exists = surface is not None
    placement_exists = placement is not None

    actual_set = set(placement.final_points) if placement_exists else set()
    ids_known = placement_exists and actual_set <= expected_set
    ids_complete = placement_exists and actual_set == expected_set
    points_finite_in_domain = False
    points_in_reservations = False
    requirements_pass = False
    no_valid_feature_ids: tuple[str, ...] = ()
    deterministic_recompute = False

    upstream_ready = (
        layout_exists
        and layout_attempt_matches
        and terrain_exists
        and hydrology_exists
        and surface_exists
    )

    if placement_exists:
        points_finite_in_domain = _selected_points_finite_in_domain(plan, placement)
        if layout_exists:
            points_in_reservations = _selected_points_in_reservations(layout, placement)
        if terrain_exists and hydrology_exists and surface_exists:
            try:
                requirements_pass = _selected_requirements_pass(
                    plan,
                    terrain,
                    hydrology,
                    surface,
                    placement,
                )
            except (SiteMetricCapabilityError, PlacementCandidateCapabilityError):
                requirements_pass = False

    if upstream_ready:
        assert layout is not None and terrain is not None and hydrology is not None and surface is not None
        try:
            expected_build = _build_placement(
                plan,
                layout,
                terrain,
                hydrology,
                surface,
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
            no_valid_feature_ids = expected_build.no_valid_feature_ids
            if placement_exists:
                deterministic_recompute = placement == expected_build.state
        except (
            SiteMetricCapabilityError,
            PlacementCandidateCapabilityError,
            PlacementSelectionCapabilityError,
        ):
            deterministic_recompute = False

    all_features_have_valid_site = upstream_ready and not no_valid_feature_ids

    results = (
        EngineInvariantResult(id="placement-upstream-layout-exists", passed=layout_exists),
        EngineInvariantResult(
            id="placement-layout-attempt-index-matches",
            passed=layout_attempt_matches,
        ),
        EngineInvariantResult(id="placement-upstream-terrain-exists", passed=terrain_exists),
        EngineInvariantResult(id="placement-upstream-hydrology-exists", passed=hydrology_exists),
        EngineInvariantResult(id="placement-upstream-surface-exists", passed=surface_exists),
        EngineInvariantResult(id="placement-state-exists", passed=placement_exists),
        EngineInvariantResult(
            id="placement-feature-ids-known",
            passed=ids_known,
            measured={
                "expected_feature_count": len(expected_set),
                "actual_feature_count": len(actual_set),
            },
        ),
        EngineInvariantResult(
            id="placement-all-features-have-valid-site",
            passed=all_features_have_valid_site,
            measured={"no_valid_feature_count": len(no_valid_feature_ids)},
        ),
        EngineInvariantResult(
            id="placement-required-features-complete",
            passed=ids_complete,
            measured={
                "expected_feature_count": len(expected_set),
                "actual_feature_count": len(actual_set),
            },
        ),
        EngineInvariantResult(
            id="placement-points-finite-in-domain",
            passed=points_finite_in_domain,
        ),
        EngineInvariantResult(
            id="placement-points-inside-reservation",
            passed=points_in_reservations,
        ),
        EngineInvariantResult(
            id="placement-site-requirements-pass",
            passed=requirements_pass,
        ),
        EngineInvariantResult(
            id="placement-deterministic-recompute",
            passed=deterministic_recompute,
        ),
    )
    passed = all(result.passed for result in results)
    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.PLACEMENT,
        engine_invariants=EngineInvariantGroup(passed=passed, results=results),
        hard_constraints=HardConstraintGroup(passed=True, results=()),
        soft_constraints=SoftConstraintGroup(results=()),
        ranking=None,
    )


def placement_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    if (
        state.layout is None
        or state.terrain is None
        or state.hydrology is None
        or state.surface is None
    ):
        return validate_placement(
            context.plan,
            state.layout,
            state.terrain,
            state.hydrology,
            state.surface,
            None,
            attempt_index=context.attempt_index,
            rng_factory=context.rng_factory,
        )

    build = _build_placement(
        context.plan,
        state.layout,
        state.terrain,
        state.hydrology,
        state.surface,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
    state.placement = build.state
    return validate_placement(
        context.plan,
        state.layout,
        state.terrain,
        state.hydrology,
        state.surface,
        state.placement,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
