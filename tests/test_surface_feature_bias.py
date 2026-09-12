from __future__ import annotations

import numpy as np
import pytest

from domain_generator.compiler import semantic_plan_fingerprint
from domain_generator.contracts.data import RiverNetwork
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
    PlanHydrology,
    PlanSource,
    PlanSurface,
    RangeParameter,
    ResolvedFeature,
    UniformSampler,
)
from domain_generator.hydrology.state import HydrologyState
from domain_generator.pipeline.attempts import AttemptContext, CandidateState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.surface import SurfaceCapabilityError, generate_surface, surface_stage, validate_surface
from domain_generator.terrain.state import TerrainState


def fp(value: float) -> FixedParameter:
    return FixedParameter(type=ParameterType.FLOAT, value=value)


def ip(value: int) -> FixedParameter:
    return FixedParameter(type=ParameterType.INTEGER, value=value)


def surface_feature(
    feature_id: str,
    *,
    operator: str,
    parameter_name: str,
    recipe,
) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-surface-bias"),
        family=FeatureFamily.SURFACE,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.AREA,
            parameters={
                "vertex_count": ip(4),
                "radial_extent": fp(0.5),
                "radial_irregularity": fp(0.0),
            },
        ),
        effect=EffectRecipe(
            stage=EffectStage.SURFACE,
            operator=operator,
            parameters={parameter_name: recipe},
        ),
    )


def make_plan(
    features: tuple[ResolvedFeature, ...] = (),
    *,
    moisture_base: float = 0.5,
    seed: int = 123456,
) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="surface-bias-test",
            spec_schema_version="0.1",
            spec_fingerprint="sha256:test",
            generator_version="0.1.0.dev0",
        ),
        seed=seed,
        domain=PlanDomain(width_km=4.0, height_km=4.0),
        grid=PlanGrid(cell_size_km=1.0, rows=4, columns=4),
        hydrology=PlanHydrology(
            stream_threshold_km2=1.0,
            lake_min_area_km2=1.0,
            lake_min_depth_m=1.0,
            river_depth_at_threshold_m=0.5,
            river_depth_exponent=0.3,
        ),
        surface=PlanSurface(
            moisture_base=moisture_base,
            water_moisture_boost=0.0,
            water_moisture_decay_km=1.0,
            moisture_noise_amplitude=0.0,
            moisture_noise_scale_km=2.0,
            vegetation_slope_zero_deg=45.0,
        ),
        features=features,
        constraints=(),
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


def make_layout(
    plan: GenerationPlan,
    geometries: dict,
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


def make_hydrology(water_depth_m: np.ndarray | None = None) -> HydrologyState:
    if water_depth_m is None:
        water_depth_m = np.zeros((4, 4), dtype=np.float32)
    return HydrologyState(
        routing_elevation_m=np.zeros((4, 4), dtype=np.float64),
        fill_elevation_m=np.zeros((4, 4), dtype=np.float64),
        flow_direction=np.full((4, 4), -1, dtype=np.int8),
        flow_accumulation_km2=np.ones((4, 4), dtype=np.float64),
        stream_mask=np.zeros((4, 4), dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=water_depth_m.astype(np.float32, copy=False),
    )


def flat_terrain() -> TerrainState:
    return TerrainState(elevation_m=np.zeros((4, 4), dtype=np.float32))


def test_moisture_bias_uses_area_cell_center_rasterization_and_changes_vegetation() -> None:
    feature = surface_feature(
        "wet-01",
        operator="moisture_bias",
        parameter_name="delta_moisture",
        recipe=fp(0.2),
    )
    plan = make_plan((feature,))
    layout = make_layout(plan, {"wet-01": area(1.0, 1.0, 3.0, 3.0)})

    state = generate_surface(
        plan,
        layout,
        flat_terrain(),
        make_hydrology(),
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    expected = np.array(
        [
            [0.5, 0.5, 0.5, 0.5],
            [0.5, 0.7, 0.7, 0.5],
            [0.5, 0.7, 0.7, 0.5],
            [0.5, 0.5, 0.5, 0.5],
        ],
        dtype=np.float32,
    )
    assert np.array_equal(state.moisture, expected)
    assert np.array_equal(state.vegetation_density, expected)


def test_vegetation_bias_changes_only_vegetation() -> None:
    feature = surface_feature(
        "green-01",
        operator="vegetation_bias",
        parameter_name="delta_vegetation",
        recipe=fp(0.3),
    )
    plan = make_plan((feature,))
    layout = make_layout(plan, {"green-01": area(1.0, 1.0, 3.0, 3.0)})

    state = generate_surface(
        plan,
        layout,
        flat_terrain(),
        make_hydrology(),
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    assert np.array_equal(state.moisture, np.full((4, 4), 0.5, dtype=np.float32))
    assert state.vegetation_density[1, 1] == np.float32(0.8)
    assert state.vegetation_density[0, 0] == np.float32(0.5)


def test_overlapping_biases_sum_before_single_clamp_and_ignore_plan_feature_order() -> None:
    positive = surface_feature(
        "a-positive",
        operator="moisture_bias",
        parameter_name="delta_moisture",
        recipe=fp(0.5),
    )
    negative = surface_feature(
        "b-negative",
        operator="moisture_bias",
        parameter_name="delta_moisture",
        recipe=fp(-0.5),
    )
    geometries = {
        "a-positive": area(0.0, 0.0, 4.0, 4.0),
        "b-negative": area(0.0, 0.0, 4.0, 4.0),
    }
    plan_ab = make_plan((positive, negative), moisture_base=0.9)
    plan_ba = make_plan((negative, positive), moisture_base=0.9)

    first = generate_surface(
        plan_ab,
        make_layout(plan_ab, geometries),
        flat_terrain(),
        make_hydrology(),
        attempt_index=0,
        rng_factory=RngFactory(plan_ab.seed),
    )
    second = generate_surface(
        plan_ba,
        make_layout(plan_ba, geometries),
        flat_terrain(),
        make_hydrology(),
        attempt_index=0,
        rng_factory=RngFactory(plan_ba.seed),
    )

    assert np.array_equal(first.moisture, np.full((4, 4), 0.9, dtype=np.float32))
    assert np.array_equal(first.moisture, second.moisture)
    assert np.array_equal(first.vegetation_density, second.vegetation_density)


def test_canonical_water_overrides_surface_biases() -> None:
    moisture = surface_feature(
        "dry-01",
        operator="moisture_bias",
        parameter_name="delta_moisture",
        recipe=fp(-1.0),
    )
    vegetation = surface_feature(
        "green-01",
        operator="vegetation_bias",
        parameter_name="delta_vegetation",
        recipe=fp(1.0),
    )
    plan = make_plan((moisture, vegetation))
    whole = area(0.0, 0.0, 4.0, 4.0)
    layout = make_layout(plan, {"dry-01": whole, "green-01": whole})
    water = np.zeros((4, 4), dtype=np.float32)
    water[1, 1] = 2.0

    state = generate_surface(
        plan,
        layout,
        flat_terrain(),
        make_hydrology(water),
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    assert state.moisture[1, 1] == np.float32(1.0)
    assert state.vegetation_density[1, 1] == np.float32(0.0)


def test_surface_feature_parameter_sampling_replays_and_varies_by_attempt() -> None:
    feature = surface_feature(
        "random-wet",
        operator="moisture_bias",
        parameter_name="delta_moisture",
        recipe=RangeParameter(
            type=ParameterType.FLOAT,
            min=-0.4,
            max=0.4,
            sampler=UniformSampler(),
        ),
    )
    plan = make_plan((feature,))
    geometry = {"random-wet": area(0.0, 0.0, 4.0, 4.0)}

    first = generate_surface(
        plan,
        make_layout(plan, geometry, attempt_index=2),
        flat_terrain(),
        make_hydrology(),
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    replay = generate_surface(
        plan,
        make_layout(plan, geometry, attempt_index=2),
        flat_terrain(),
        make_hydrology(),
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    other = generate_surface(
        plan,
        make_layout(plan, geometry, attempt_index=3),
        flat_terrain(),
        make_hydrology(),
        attempt_index=3,
        rng_factory=RngFactory(plan.seed),
    )

    assert np.array_equal(first.moisture, replay.moisture)
    assert not np.array_equal(first.moisture, other.moisture)


def test_non_area_surface_geometry_is_explicit_capability_error() -> None:
    feature = surface_feature(
        "bad-geometry",
        operator="moisture_bias",
        parameter_name="delta_moisture",
        recipe=fp(0.2),
    )
    plan = make_plan((feature,))
    layout = make_layout(plan, {"bad-geometry": PointGeometry(x_km=2.0, y_km=2.0)})

    with pytest.raises(SurfaceCapabilityError, match="AreaGeometry"):
        generate_surface(
            plan,
            layout,
            flat_terrain(),
            make_hydrology(),
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )


def test_missing_surface_geometry_is_explicit_capability_error() -> None:
    feature = surface_feature(
        "missing",
        operator="vegetation_bias",
        parameter_name="delta_vegetation",
        recipe=fp(0.2),
    )
    plan = make_plan((feature,))

    with pytest.raises(SurfaceCapabilityError, match="no materialized layout geometry"):
        generate_surface(
            plan,
            make_layout(plan, {}),
            flat_terrain(),
            make_hydrology(),
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )


def test_delta_outside_normalized_range_is_explicit_capability_error() -> None:
    feature = surface_feature(
        "too-wet",
        operator="moisture_bias",
        parameter_name="delta_moisture",
        recipe=fp(1.1),
    )
    plan = make_plan((feature,))

    with pytest.raises(SurfaceCapabilityError, match=r"\[-1, 1\]"):
        generate_surface(
            plan,
            make_layout(plan, {"too-wet": area(0.0, 0.0, 4.0, 4.0)}),
            flat_terrain(),
            make_hydrology(),
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )


def test_surface_stage_records_complete_feature_application() -> None:
    feature = surface_feature(
        "green-01",
        operator="vegetation_bias",
        parameter_name="delta_vegetation",
        recipe=fp(0.2),
    )
    plan = make_plan((feature,))
    layout = make_layout(plan, {"green-01": area(1.0, 1.0, 3.0, 3.0)})
    candidate = CandidateState(
        attempt_index=0,
        layout=layout,
        terrain=flat_terrain(),
        hydrology=make_hydrology(),
    )
    context = AttemptContext(plan=plan, attempt_index=0, rng_factory=RngFactory(plan.seed))

    validation = surface_stage(context, candidate)

    invariant = next(
        item
        for item in validation.engine_invariants.results
        if item.id == "surface-feature-effects-applied-exactly"
    )
    assert invariant.passed is True
    assert candidate.surface is not None


def test_validation_rejects_incomplete_surface_feature_application() -> None:
    feature = surface_feature(
        "green-01",
        operator="vegetation_bias",
        parameter_name="delta_vegetation",
        recipe=fp(0.2),
    )
    plan = make_plan((feature,))
    layout = make_layout(plan, {"green-01": area(1.0, 1.0, 3.0, 3.0)})
    state = generate_surface(
        plan,
        layout,
        flat_terrain(),
        make_hydrology(),
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    validation = validate_surface(
        plan,
        layout,
        flat_terrain(),
        make_hydrology(),
        state,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
        applied_feature_ids=(),
    )

    invariant = next(
        item
        for item in validation.engine_invariants.results
        if item.id == "surface-feature-effects-applied-exactly"
    )
    assert invariant.passed is False
