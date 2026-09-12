from __future__ import annotations

import numpy as np
import pytest

from domain_generator.contracts.geometry import PointGeometry, RegionPolygon, RegionSet, WorldPoint
from domain_generator.contracts.layout import LayoutCandidate, PlacementReservation, SourcePlanRef
from domain_generator.contracts.plan import (
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    FeatureMetadata,
    FixedParameter,
    GenerationPlan,
    ParameterType,
    PlanDomain,
    PlanGrid,
    PlanHydrology,
    PlanSource,
    PlanSurface,
    ReservationLayoutRecipe,
    ResolvedFeature,
    SitePreference,
    SiteProfile,
    SiteRequirement,
)
from domain_generator.contracts.validation import (
    EngineInvariantGroup,
    HardConstraintGroup,
    RankingResult,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from domain_generator.hydrology.generate import hydrology_stage
from domain_generator.layout import layout_stage
from domain_generator.pipeline.attempts import RejectedAttempt, StageStep, run_attempt
from domain_generator.pipeline.rng import RngFactory
from domain_generator.poi import (
    EvaluatedSite,
    PlacementSelectionCapabilityError,
    PlacementState,
    ScoredSite,
    choose_weighted_site,
    generate_placement,
    near_best_sites,
    placement_stage,
    preference_scores,
    sample_near_best_delta,
    score_valid_sites,
    validate_placement,
)
from domain_generator.surface.generate import surface_stage
from domain_generator.surface.state import SurfaceState
from domain_generator.terrain.generate import terrain_stage
from domain_generator.terrain.state import TerrainState
from domain_generator.hydrology.state import HydrologyState
from domain_generator.contracts.data import RiverNetwork


def rectangle_region(min_x: float, min_y: float, max_x: float, max_y: float) -> RegionSet:
    return RegionSet(
        polygons=(
            RegionPolygon(
                outer=(
                    WorldPoint(x_km=min_x, y_km=min_y),
                    WorldPoint(x_km=max_x, y_km=min_y),
                    WorldPoint(x_km=max_x, y_km=max_y),
                    WorldPoint(x_km=min_x, y_km=max_y),
                )
            ),
        )
    )


def placement_feature(
    feature_id: str = "poi-01",
    *,
    spacing_km: float = 1.0,
    near_best_delta: float = 0.2,
    requirements: tuple[SiteRequirement, ...] = (),
    preferences: tuple[SitePreference, ...] = (),
) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-placement"),
        family=FeatureFamily.POI,
        layout=ReservationLayoutRecipe(),
        effect=EffectRecipe(
            stage=EffectStage.DEPENDENT_PLACEMENT,
            operator="suitability_placement",
            parameters={
                "candidate_spacing_km": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=spacing_km,
                ),
                "near_best_delta": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=near_best_delta,
                ),
            },
            site_profile=SiteProfile(
                footprint_radius_km=0.0,
                requirements=requirements,
                preferences=preferences,
            ),
        ),
    )


def make_plan(*features: ResolvedFeature) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="placement-selection-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=123456,
        domain=PlanDomain(width_km=4.0, height_km=4.0),
        grid=PlanGrid(cell_size_km=1.0, rows=4, columns=4),
        hydrology=PlanHydrology(
            stream_threshold_km2=1000.0,
            lake_min_area_km2=1000.0,
            lake_min_depth_m=1000.0,
            river_depth_at_threshold_m=0.5,
            river_depth_exponent=0.3,
        ),
        surface=PlanSurface(
            moisture_base=0.5,
            water_moisture_boost=0.0,
            water_moisture_decay_km=8.0,
            moisture_noise_amplitude=0.0,
            moisture_noise_scale_km=12.0,
            vegetation_slope_zero_deg=45.0,
        ),
        features=features,
        constraints=(),
    )


def manual_runtime(plan: GenerationPlan, *, attempt_index: int = 0):
    shape = (4, 4)
    layout = LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint="sha256:test-plan"),
        attempt_index=attempt_index,
        geometry_realizations={},
        placement_reservations={
            feature.id: PlacementReservation(
                allowed_region=rectangle_region(0.0, 0.0, 4.0, 4.0)
            )
            for feature in plan.features
            if isinstance(feature.layout, ReservationLayoutRecipe)
        },
    )
    terrain = TerrainState(elevation_m=np.zeros(shape, dtype=np.float32))
    hydrology = HydrologyState(
        routing_elevation_m=np.zeros(shape, dtype=np.float64),
        fill_elevation_m=np.zeros(shape, dtype=np.float64),
        flow_direction=np.full(shape, -1, dtype=np.int8),
        flow_accumulation_km2=np.ones(shape, dtype=np.float64),
        stream_mask=np.zeros(shape, dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=np.zeros(shape, dtype=np.float32),
    )
    surface = SurfaceState(
        moisture=np.full(shape, 0.5, dtype=np.float32),
        vegetation_density=np.full(shape, 0.5, dtype=np.float32),
    )
    return layout, terrain, hydrology, surface


def evaluated(x: float, elevation: float, moisture: float = 0.5) -> EvaluatedSite:
    return EvaluatedSite(
        point=PointGeometry(x_km=x, y_km=1.0),
        metrics={
            "elevation_mean": elevation,
            "moisture_mean": moisture,
            "distance_to_water": 3.0,
        },
    )


def test_maximize_and_minimize_preferences_normalize_observed_range() -> None:
    sites = (evaluated(0.5, 0.0), evaluated(1.5, 5.0), evaluated(2.5, 10.0))
    maximize = SitePreference(metric="elevation_mean", evaluator="maximize")
    minimize = SitePreference(metric="elevation_mean", evaluator="minimize")

    assert preference_scores(sites, maximize) == pytest.approx((0.0, 0.5, 1.0))
    assert preference_scores(sites, minimize) == pytest.approx((1.0, 0.5, 0.0))


def test_equal_infinite_metric_does_not_create_artificial_preference() -> None:
    sites = (
        EvaluatedSite(PointGeometry(x_km=0.5, y_km=1.0), {"distance_to_water": float("inf")}),
        EvaluatedSite(PointGeometry(x_km=1.5, y_km=1.0), {"distance_to_water": float("inf")}),
    )
    preference = SitePreference(metric="distance_to_water", evaluator="minimize")
    assert preference_scores(sites, preference) == (1.0, 1.0)


def test_preferred_range_scores_inside_as_one_and_falls_off_by_observed_side() -> None:
    sites = (
        evaluated(0.5, 0.0),
        evaluated(1.5, 5.0),
        evaluated(2.5, 10.0),
        evaluated(3.5, 20.0),
    )
    preference = SitePreference(
        metric="elevation_mean",
        evaluator="preferred_range",
        min=5.0,
        max=10.0,
    )
    assert preference_scores(sites, preference) == pytest.approx((0.0, 1.0, 1.0, 0.0))


def test_composite_suitability_is_weighted_mean() -> None:
    sites = (
        evaluated(0.5, 0.0, moisture=0.2),
        evaluated(1.5, 10.0, moisture=0.8),
    )
    preferences = (
        SitePreference(metric="elevation_mean", evaluator="maximize", weight=0.25),
        SitePreference(metric="moisture_mean", evaluator="minimize", weight=0.75),
    )
    scored = score_valid_sites(sites, preferences)
    assert tuple(site.suitability for site in scored) == pytest.approx((0.75, 0.25))


def test_no_preferences_give_every_site_suitability_one() -> None:
    scored = score_valid_sites((evaluated(2.5, 10.0), evaluated(0.5, 0.0)), ())
    assert tuple(item.site.point.x_km for item in scored) == (0.5, 2.5)
    assert tuple(item.suitability for item in scored) == (1.0, 1.0)


def test_near_best_uses_inclusive_best_minus_delta_threshold() -> None:
    base_sites = (evaluated(0.5, 0.0), evaluated(1.5, 0.0), evaluated(2.5, 0.0))
    scored = tuple(
        ScoredSite(site=site, preference_scores=(), suitability=value)
        for site, value in zip(base_sites, (1.0, 0.8, 0.4))
    )
    result = near_best_sites(scored, 0.2)
    assert tuple(site.suitability for site in result) == (1.0, 0.8)


def test_weighted_choice_replays_and_is_independent_of_input_order() -> None:
    a = ScoredSite(evaluated(0.5, 0.0), (), 0.2)
    b = ScoredSite(evaluated(1.5, 0.0), (), 0.8)
    factory = RngFactory(123456)
    first = choose_weighted_site((a, b), feature_id="poi-01", attempt_index=4, rng_factory=factory)
    replay = choose_weighted_site((b, a), feature_id="poi-01", attempt_index=4, rng_factory=RngFactory(123456))
    assert first == replay


def test_zero_total_weight_falls_back_to_uniform_protocol_choice() -> None:
    a = ScoredSite(evaluated(0.5, 0.0), (), 0.0)
    b = ScoredSite(evaluated(1.5, 0.0), (), 0.0)
    first = choose_weighted_site((a, b), feature_id="poi-01", attempt_index=7, rng_factory=RngFactory(123456))
    replay = choose_weighted_site((a, b), feature_id="poi-01", attempt_index=7, rng_factory=RngFactory(123456))
    assert first == replay
    assert first in (a, b)


def test_missing_near_best_delta_is_capability_error_even_with_no_valid_sites() -> None:
    feature = placement_feature().model_copy(
        update={
            "effect": placement_feature().effect.model_copy(
                update={
                    "parameters": {
                        "candidate_spacing_km": FixedParameter(
                            type=ParameterType.FLOAT,
                            value=1.0,
                        )
                    }
                }
            )
        }
    )
    with pytest.raises(PlacementSelectionCapabilityError, match="exactly effect parameters"):
        sample_near_best_delta(feature, attempt_index=0, rng_factory=RngFactory(123456))


def test_generate_placement_replays_and_selects_inside_reservation() -> None:
    preference = SitePreference(metric="elevation_mean", evaluator="maximize")
    feature = placement_feature(preferences=(preference,))
    plan = make_plan(feature)
    layout, terrain, hydrology, surface = manual_runtime(plan, attempt_index=3)

    first = generate_placement(
        plan,
        layout,
        terrain,
        hydrology,
        surface,
        attempt_index=3,
        rng_factory=RngFactory(plan.seed),
    )
    replay = generate_placement(
        plan,
        layout,
        terrain,
        hydrology,
        surface,
        attempt_index=3,
        rng_factory=RngFactory(plan.seed),
    )

    assert first == replay
    point = first.final_points["poi-01"]
    assert 0.0 <= point.x_km <= 4.0
    assert 0.0 <= point.y_km <= 4.0


def test_validation_rejects_tampered_final_point() -> None:
    feature = placement_feature()
    plan = make_plan(feature)
    layout, terrain, hydrology, surface = manual_runtime(plan, attempt_index=0)
    placement = generate_placement(
        plan,
        layout,
        terrain,
        hydrology,
        surface,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    tampered = PlacementState(
        final_points={"poi-01": PointGeometry(x_km=4.0, y_km=4.0)}
    )
    assert tampered != placement

    validation = validate_placement(
        plan,
        layout,
        terrain,
        hydrology,
        surface,
        tampered,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    by_id = {item.id: item for item in validation.engine_invariants.results}
    assert by_id["placement-deterministic-recompute"].passed is False
    assert validation.engine_invariants.passed is False


def test_full_attempt_rejects_at_placement_when_no_site_meets_requirements() -> None:
    impossible = SiteRequirement(
        metric="moisture_mean",
        evaluator="less_or_equal",
        value=0.0,
    )
    feature = placement_feature(requirements=(impossible,))
    plan = make_plan(feature)
    final_called = False

    def final_stage(context, state):
        nonlocal final_called
        final_called = True
        return ValidationResult(
            validation_version="0.1",
            attempt_index=context.attempt_index,
            stage=ValidationStage.FINAL,
            engine_invariants=EngineInvariantGroup(passed=True, results=()),
            hard_constraints=HardConstraintGroup(passed=True, results=()),
            soft_constraints=SoftConstraintGroup(results=()),
            ranking=RankingResult(
                worst_effective_violation=0.0,
                weighted_mean_score=1.0,
            ),
        )

    outcome = run_attempt(
        plan=plan,
        attempt_index=0,
        steps=(
            StageStep(ValidationStage.LAYOUT, layout_stage),
            StageStep(ValidationStage.TERRAIN, terrain_stage),
            StageStep(ValidationStage.HYDROLOGY, hydrology_stage),
            StageStep(ValidationStage.SURFACE, surface_stage),
            StageStep(ValidationStage.PLACEMENT, placement_stage),
            StageStep(ValidationStage.FINAL, final_stage),
        ),
    )

    assert isinstance(outcome, RejectedAttempt)
    assert outcome.failed_validation.stage is ValidationStage.PLACEMENT
    assert final_called is False
    by_id = {item.id: item for item in outcome.failed_validation.engine_invariants.results}
    assert by_id["placement-all-features-have-valid-site"].passed is False
    assert by_id["placement-required-features-complete"].passed is False
