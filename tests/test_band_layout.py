from __future__ import annotations

import pytest

from domain_generator.contracts.common import ConstraintStrength, FeaturePart
from domain_generator.contracts.geometry import BandGeometry, CorridorGeometry
from domain_generator.contracts.plan import (
    CompiledConstraint,
    CompiledEvaluator,
    CompiledFeatureRef,
    CompiledPoint,
    CompiledPredicate,
    EffectRecipe,
    FeatureFamily,
    FeatureMetadata,
    FixedParameter,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
    ParameterType,
    PlanDomain,
    PlanGrid,
    PlanHydrology,
    PlanSource,
    RangeParameter,
    ResolvedFeature,
    UniformSampler,
)
from domain_generator.layout.geometry import (
    LayoutCapabilityError,
    generate_geometry_layout,
    validate_geometry_layout,
)
from domain_generator.pipeline.rng import RngFactory


def band_feature(
    feature_id: str,
    *,
    control_point_count: int = 3,
    curvature: float = 0.5,
    width_sample_count: int = 5,
    width_recipe=None,
) -> ResolvedFeature:
    if width_recipe is None:
        width_recipe = FixedParameter(type=ParameterType.FLOAT, value=12.0)
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-band"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.BAND,
            parameters={
                "control_point_count": FixedParameter(
                    type=ParameterType.INTEGER,
                    value=control_point_count,
                ),
                "curvature": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=curvature,
                ),
                "width_km": width_recipe,
                "width_sample_count": FixedParameter(
                    type=ParameterType.INTEGER,
                    value=width_sample_count,
                ),
            },
        ),
        effect=EffectRecipe(stage="terrain", operator="test-effect"),
    )


def corridor_feature(feature_id: str) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-corridor"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.CORRIDOR,
            parameters={
                "control_point_count": FixedParameter(
                    type=ParameterType.INTEGER,
                    value=3,
                ),
                "curvature": FixedParameter(
                    type=ParameterType.FLOAT,
                    value=0.5,
                ),
            },
        ),
        effect=EffectRecipe(stage="terrain", operator="test-effect"),
    )


def make_plan(
    *,
    features: tuple[ResolvedFeature, ...],
    constraints: tuple[CompiledConstraint, ...] = (),
    seed: int = 123456,
) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="band-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=seed,
        domain=PlanDomain(width_km=120.0, height_km=80.0),
        grid=PlanGrid(cell_size_km=1.0, rows=80, columns=120),
        hydrology=PlanHydrology(
            stream_threshold_km2=25.0,
            lake_min_area_km2=1.0,
            lake_min_depth_m=2.0,
        ),
        features=features,
        constraints=constraints,
    )


def test_band_replay_is_exact_for_same_attempt() -> None:
    plan = make_plan(features=(band_feature("band-01"),))

    first = generate_geometry_layout(
        plan,
        attempt_index=4,
        rng_factory=RngFactory(plan.seed),
    )
    second = generate_geometry_layout(
        plan,
        attempt_index=4,
        rng_factory=RngFactory(plan.seed),
    )

    assert first == second


def test_band_width_profile_has_deterministic_even_t_samples() -> None:
    plan = make_plan(features=(band_feature("band-01", width_sample_count=5),))
    candidate = generate_geometry_layout(
        plan,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    geometry = candidate.geometry_realizations["band-01"]

    assert isinstance(geometry, BandGeometry)
    assert tuple(sample.t for sample in geometry.width_profile) == (
        0.0,
        0.25,
        0.5,
        0.75,
        1.0,
    )


def test_fixed_band_width_is_constant_across_profile() -> None:
    plan = make_plan(
        features=(
            band_feature(
                "band-01",
                width_sample_count=7,
                width_recipe=FixedParameter(type=ParameterType.FLOAT, value=18.0),
            ),
        )
    )
    candidate = generate_geometry_layout(
        plan,
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    geometry = candidate.geometry_realizations["band-01"]

    assert isinstance(geometry, BandGeometry)
    assert tuple(sample.width_km for sample in geometry.width_profile) == (18.0,) * 7


def test_width_sample_count_does_not_change_endpoint_widths() -> None:
    width_recipe = RangeParameter(
        type=ParameterType.FLOAT,
        min=5.0,
        max=20.0,
        sampler=UniformSampler(),
    )
    short_plan = make_plan(
        features=(
            band_feature(
                "band-01",
                width_sample_count=3,
                width_recipe=width_recipe,
            ),
        )
    )
    long_plan = make_plan(
        features=(
            band_feature(
                "band-01",
                width_sample_count=9,
                width_recipe=width_recipe,
            ),
        )
    )

    short = generate_geometry_layout(
        short_plan,
        attempt_index=3,
        rng_factory=RngFactory(short_plan.seed),
    )
    long = generate_geometry_layout(
        long_plan,
        attempt_index=3,
        rng_factory=RngFactory(long_plan.seed),
    )
    short_geometry = short.geometry_realizations["band-01"]
    long_geometry = long.geometry_realizations["band-01"]

    assert isinstance(short_geometry, BandGeometry)
    assert isinstance(long_geometry, BandGeometry)
    assert short_geometry.width_profile[0].width_km == long_geometry.width_profile[0].width_km
    assert short_geometry.width_profile[-1].width_km == long_geometry.width_profile[-1].width_km
    assert len(short_geometry.width_profile) == 3
    assert len(long_geometry.width_profile) == 9


def test_band_and_corridor_use_distinct_geometry_namespaces() -> None:
    band_plan = make_plan(features=(band_feature("linear-01"),))
    corridor_plan = make_plan(features=(corridor_feature("linear-01"),))

    band_candidate = generate_geometry_layout(
        band_plan,
        attempt_index=5,
        rng_factory=RngFactory(band_plan.seed),
    )
    corridor_candidate = generate_geometry_layout(
        corridor_plan,
        attempt_index=5,
        rng_factory=RngFactory(corridor_plan.seed),
    )
    band = band_candidate.geometry_realizations["linear-01"]
    corridor = corridor_candidate.geometry_realizations["linear-01"]

    assert isinstance(band, BandGeometry)
    assert isinstance(corridor, CorridorGeometry)
    assert band.centerline != corridor.centerline


def test_band_centerline_vertices_stay_inside_domain() -> None:
    plan = make_plan(
        features=(band_feature("band-01", control_point_count=12, curvature=1.0),)
    )

    for attempt_index in range(20):
        candidate = generate_geometry_layout(
            plan,
            attempt_index=attempt_index,
            rng_factory=RngFactory(plan.seed),
        )
        geometry = candidate.geometry_realizations["band-01"]
        assert isinstance(geometry, BandGeometry)
        assert all(0.0 <= point.x_km <= 120.0 for point in geometry.centerline)
        assert all(0.0 <= point.y_km <= 80.0 for point in geometry.centerline)


def test_band_start_part_can_be_used_as_point_distance_subject() -> None:
    constraint = CompiledConstraint(
        id="band-start-near-origin",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="band-01", part=FeaturePart.START),
            target=CompiledPoint(x_km=0.0, y_km=0.0),
        ),
        predicate=CompiledPredicate(type="less_or_equal", value=1000.0),
        unit="km",
    )
    plan = make_plan(features=(band_feature("band-01"),), constraints=(constraint,))
    candidate = generate_geometry_layout(
        plan,
        attempt_index=1,
        rng_factory=RngFactory(plan.seed),
    )

    validation = validate_geometry_layout(plan, candidate, attempt_index=1)

    assert validation.engine_invariants.passed is True
    assert validation.hard_constraints.passed is True


def test_band_center_part_is_resolved_at_half_arc_length() -> None:
    constraint = CompiledConstraint(
        id="band-center-near-origin",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="band-01", part=FeaturePart.CENTER),
            target=CompiledPoint(x_km=0.0, y_km=0.0),
        ),
        predicate=CompiledPredicate(type="less_or_equal", value=1000.0),
        unit="km",
    )
    plan = make_plan(features=(band_feature("band-01"),), constraints=(constraint,))
    candidate = generate_geometry_layout(
        plan,
        attempt_index=7,
        rng_factory=RngFactory(plan.seed),
    )

    validation = validate_geometry_layout(plan, candidate, attempt_index=7)

    assert validation.hard_constraints.passed is True


def test_band_whole_is_not_silently_treated_as_centerline() -> None:
    constraint = CompiledConstraint(
        id="band-whole-near-origin",
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type="distance",
            subject=CompiledFeatureRef(feature_id="band-01", part=FeaturePart.WHOLE),
            target=CompiledPoint(x_km=0.0, y_km=0.0),
        ),
        predicate=CompiledPredicate(type="less_or_equal", value=1000.0),
        unit="km",
    )
    plan = make_plan(features=(band_feature("band-01"),), constraints=(constraint,))
    candidate = generate_geometry_layout(
        plan,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    with pytest.raises(LayoutCapabilityError, match="footprint materialization"):
        validate_geometry_layout(plan, candidate, attempt_index=0)


def test_band_width_profile_invariants_pass_for_generated_geometry() -> None:
    width_recipe = RangeParameter(
        type=ParameterType.FLOAT,
        min=8.0,
        max=24.0,
        sampler=UniformSampler(),
    )
    plan = make_plan(
        features=(
            band_feature(
                "band-01",
                width_sample_count=6,
                width_recipe=width_recipe,
            ),
        )
    )
    candidate = generate_geometry_layout(
        plan,
        attempt_index=9,
        rng_factory=RngFactory(plan.seed),
    )

    validation = validate_geometry_layout(plan, candidate, attempt_index=9)
    results = {result.id: result.passed for result in validation.engine_invariants.results}

    assert results["layout-band-nondegenerate"] is True
    assert results["layout-band-width-profile-valid"] is True
