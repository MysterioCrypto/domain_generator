from __future__ import annotations

import numpy as np
import pytest

from domain_generator.compiler import semantic_plan_fingerprint
from domain_generator.contracts.geometry import AreaGeometry, PointGeometry, WorldPoint
from domain_generator.contracts.layout import LayoutCandidate, SourcePlanRef
from domain_generator.contracts.plan import (
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    FeatureMetadata,
    FixedParameter,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
    ParameterType,
    PlanDomain,
    PlanGrid,
    PlanSource,
    RangeParameter,
    ResolvedFeature,
    UniformSampler,
)
from domain_generator.pipeline.attempts import AttemptContext, CandidateState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.terrain import (
    TerrainCapabilityError,
    TerrainState,
    generate_terrain,
    terrain_stage,
    validate_terrain,
)


def area(min_x: float, min_y: float, max_x: float, max_y: float) -> AreaGeometry:
    return AreaGeometry(
        boundary=(
            WorldPoint(x_km=min_x, y_km=min_y),
            WorldPoint(x_km=max_x, y_km=min_y),
            WorldPoint(x_km=max_x, y_km=max_y),
            WorldPoint(x_km=min_x, y_km=max_y),
        )
    )


def terrain_feature(
    feature_id: str,
    *,
    height_recipe=None,
    operator: str = "raise",
) -> ResolvedFeature:
    if height_recipe is None:
        height_recipe = FixedParameter(type=ParameterType.FLOAT, value=300.0)
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-area-raise"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.AREA,
            parameters={
                "vertex_count": FixedParameter(type=ParameterType.INTEGER, value=4),
                "radial_extent": FixedParameter(type=ParameterType.FLOAT, value=0.5),
                "radial_irregularity": FixedParameter(type=ParameterType.FLOAT, value=0.0),
            },
        ),
        effect=EffectRecipe(
            stage=EffectStage.TERRAIN,
            operator=operator,
            parameters={"height_m": height_recipe},
        ),
    )


def make_plan(features: tuple[ResolvedFeature, ...], *, seed: int = 123456) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="terrain-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=seed,
        domain=PlanDomain(width_km=4.0, height_km=4.0),
        grid=PlanGrid(cell_size_km=1.0, rows=4, columns=4),
        features=features,
        constraints=(),
    )


def make_layout(
    plan: GenerationPlan,
    geometries: dict[str, AreaGeometry | PointGeometry],
    *,
    attempt_index: int = 0,
) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations=geometries,
        placement_reservations={},
    )


def test_no_terrain_features_produce_zero_float32_base_field() -> None:
    plan = make_plan(())
    layout = make_layout(plan, {})

    state = generate_terrain(
        plan,
        layout,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    assert state.elevation_m.dtype == np.dtype(np.float32)
    assert state.elevation_m.shape == (4, 4)
    assert np.array_equal(state.elevation_m, np.zeros((4, 4), dtype=np.float32))


def test_area_raise_uses_cell_center_rasterization() -> None:
    feature = terrain_feature("hill-01")
    plan = make_plan((feature,))
    layout = make_layout(plan, {"hill-01": area(1.0, 1.0, 3.0, 3.0)})

    state = generate_terrain(
        plan,
        layout,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    expected = np.array(
        [
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 300.0, 300.0, 0.0],
            [0.0, 300.0, 300.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )
    assert np.array_equal(state.elevation_m, expected)


def test_overlapping_raise_features_add_and_feature_order_does_not_matter() -> None:
    feature_a = terrain_feature(
        "a-hill",
        height_recipe=FixedParameter(type=ParameterType.FLOAT, value=100.0),
    )
    feature_b = terrain_feature(
        "b-hill",
        height_recipe=FixedParameter(type=ParameterType.FLOAT, value=200.0),
    )
    plan_ab = make_plan((feature_a, feature_b))
    plan_ba = make_plan((feature_b, feature_a))
    geometries = {
        "a-hill": area(0.0, 0.0, 3.0, 3.0),
        "b-hill": area(1.0, 1.0, 4.0, 4.0),
    }

    state_ab = generate_terrain(
        plan_ab,
        make_layout(plan_ab, geometries),
        attempt_index=0,
        rng_factory=RngFactory(plan_ab.seed),
    )
    state_ba = generate_terrain(
        plan_ba,
        make_layout(plan_ba, geometries),
        attempt_index=0,
        rng_factory=RngFactory(plan_ba.seed),
    )

    assert np.array_equal(state_ab.elevation_m, state_ba.elevation_m)
    assert state_ab.elevation_m[1, 1] == np.float32(300.0)
    assert state_ab.elevation_m[3, 0] == np.float32(100.0)
    assert state_ab.elevation_m[0, 3] == np.float32(200.0)


def test_height_sampling_replays_within_attempt_and_varies_across_attempts() -> None:
    feature = terrain_feature(
        "hill-01",
        height_recipe=RangeParameter(
            type=ParameterType.FLOAT,
            min=100.0,
            max=200.0,
            sampler=UniformSampler(),
        ),
    )
    plan = make_plan((feature,))
    geometry = {"hill-01": area(1.0, 1.0, 3.0, 3.0)}

    first = generate_terrain(
        plan,
        make_layout(plan, geometry, attempt_index=2),
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    replay = generate_terrain(
        plan,
        make_layout(plan, geometry, attempt_index=2),
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    other_attempt = generate_terrain(
        plan,
        make_layout(plan, geometry, attempt_index=3),
        attempt_index=3,
        rng_factory=RngFactory(plan.seed),
    )

    assert np.array_equal(first.elevation_m, replay.elevation_m)
    assert not np.array_equal(first.elevation_m, other_attempt.elevation_m)


def test_unsupported_terrain_operator_is_capability_error() -> None:
    feature = terrain_feature("ridge-01", operator="ridge")
    plan = make_plan((feature,))
    layout = make_layout(plan, {"ridge-01": area(1.0, 1.0, 3.0, 3.0)})

    with pytest.raises(TerrainCapabilityError, match="unsupported"):
        generate_terrain(
            plan,
            layout,
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )


def test_raise_rejects_non_area_geometry() -> None:
    feature = terrain_feature("hill-01")
    plan = make_plan((feature,))
    layout = make_layout(
        plan,
        {"hill-01": PointGeometry(x_km=2.0, y_km=2.0)},
    )

    with pytest.raises(TerrainCapabilityError, match="AreaGeometry"):
        generate_terrain(
            plan,
            layout,
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )


def test_terrain_stage_stores_state_and_returns_passing_validation() -> None:
    feature = terrain_feature("hill-01")
    plan = make_plan((feature,))
    layout = make_layout(plan, {"hill-01": area(1.0, 1.0, 3.0, 3.0)})
    state = CandidateState(attempt_index=0, layout=layout)
    context = AttemptContext(
        plan=plan,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    validation = terrain_stage(context, state)

    assert state.terrain is not None
    assert validation.engine_invariants.passed is True
    assert validation.hard_constraints.passed is True
    assert validation.ranking is None


def test_terrain_validation_rejects_wrong_dtype_and_nonfinite_values() -> None:
    plan = make_plan(())
    layout = make_layout(plan, {})
    malformed = TerrainState(
        elevation_m=np.array(
            [
                [np.nan, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
            ],
            dtype=np.float64,
        )
    )

    validation = validate_terrain(
        plan,
        layout,
        malformed,
        attempt_index=0,
        applied_feature_ids=(),
    )

    by_id = {result.id: result for result in validation.engine_invariants.results}
    assert by_id["terrain-elevation-dtype-float32"].passed is False
    assert by_id["terrain-elevation-finite"].passed is False
    assert validation.engine_invariants.passed is False
