from __future__ import annotations

import numpy as np
import pytest

from domain_generator.compiler import semantic_plan_fingerprint
from domain_generator.contracts.geometry import AreaGeometry, BandGeometry, WidthSample, WorldPoint
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
    ResolvedFeature,
)
from domain_generator.pipeline.rng import RngFactory
from domain_generator.terrain import TerrainCapabilityError, generate_terrain
from domain_generator.terrain.ridge import (
    nearest_centerline_distance_and_t,
    prepare_band,
    ridge_contribution_at,
    width_at,
)


def fp(value: float) -> FixedParameter:
    return FixedParameter(type=ParameterType.FLOAT, value=value)


def ip(value: int) -> FixedParameter:
    return FixedParameter(type=ParameterType.INTEGER, value=value)


def ridge_feature(
    feature_id: str,
    *,
    height_m: float = 100.0,
    profile_power: float = 1.0,
    roughness: float = 0.0,
    roughness_scale_km: float = 2.0,
    parameters_override=None,
) -> ResolvedFeature:
    parameters = {
        "height_m": fp(height_m),
        "profile_power": fp(profile_power),
        "roughness": fp(roughness),
        "roughness_scale_km": fp(roughness_scale_km),
    }
    if parameters_override is not None:
        parameters = parameters_override
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-ridge"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.BAND,
            parameters={
                "control_point_count": ip(0),
                "curvature": fp(0.0),
                "width_km": fp(2.0),
                "width_sample_count": ip(2),
            },
        ),
        effect=EffectRecipe(
            stage=EffectStage.TERRAIN,
            operator="ridge",
            parameters=parameters,
        ),
    )


def raise_feature(feature_id: str, height_m: float = 20.0) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset="test-raise"),
        family=FeatureFamily.TERRAIN,
        layout=GeometryLayoutRecipe(
            shape=GeometryShape.AREA,
            parameters={
                "vertex_count": ip(4),
                "radial_extent": fp(0.5),
                "radial_irregularity": fp(0.0),
            },
        ),
        effect=EffectRecipe(
            stage=EffectStage.TERRAIN,
            operator="raise",
            parameters={"height_m": fp(height_m)},
        ),
    )


def make_plan(features: tuple[ResolvedFeature, ...], *, seed: int = 123456) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="ridge-test",
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


def band(
    *,
    width_start: float = 2.0,
    width_end: float = 2.0,
) -> BandGeometry:
    return BandGeometry(
        centerline=(
            WorldPoint(x_km=0.0, y_km=2.0),
            WorldPoint(x_km=4.0, y_km=2.0),
        ),
        width_profile=(
            WidthSample(t=0.0, width_km=width_start),
            WidthSample(t=1.0, width_km=width_end),
        ),
    )


def whole_domain_area() -> AreaGeometry:
    return AreaGeometry(
        boundary=(
            WorldPoint(x_km=0.0, y_km=0.0),
            WorldPoint(x_km=4.0, y_km=0.0),
            WorldPoint(x_km=4.0, y_km=4.0),
            WorldPoint(x_km=0.0, y_km=4.0),
        )
    )


def make_layout(plan: GenerationPlan, geometries: dict, *, attempt_index: int = 0) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations=geometries,
        placement_reservations={},
    )


def test_nearest_projection_uses_total_arc_length_t_and_width_interpolation() -> None:
    geometry = BandGeometry(
        centerline=(
            WorldPoint(x_km=0.0, y_km=0.0),
            WorldPoint(x_km=3.0, y_km=0.0),
            WorldPoint(x_km=3.0, y_km=4.0),
        ),
        width_profile=(
            WidthSample(t=0.0, width_km=2.0),
            WidthSample(t=1.0, width_km=9.0),
        ),
    )
    prepared = prepare_band(geometry)

    distance, t = nearest_centerline_distance_and_t(prepared, x_km=4.0, y_km=2.0)

    assert distance == pytest.approx(1.0)
    assert t == pytest.approx(5.0 / 7.0)
    assert width_at(geometry, t) == pytest.approx(7.0)


def test_ridge_without_roughness_has_exact_cross_band_profile() -> None:
    feature = ridge_feature("ridge-01")
    plan = make_plan((feature,))
    layout = make_layout(plan, {"ridge-01": band()})

    state = generate_terrain(
        plan,
        layout,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )

    expected = np.array(
        [
            [0.0, 0.0, 0.0, 0.0],
            [50.0, 50.0, 50.0, 50.0],
            [50.0, 50.0, 50.0, 50.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )
    assert np.array_equal(state.elevation_m, expected)


def test_ridge_centerline_peak_remains_height_with_roughness() -> None:
    geometry = band(width_start=4.0, width_end=4.0)
    prepared = prepare_band(geometry)

    value = ridge_contribution_at(
        prepared,
        x_km=2.0,
        y_km=2.0,
        height_m=120.0,
        profile_power=2.0,
        roughness=1.0,
        roughness_scale_km=1.5,
        feature_id="ridge-01",
        attempt_index=4,
        rng_factory=RngFactory(123456),
    )

    assert value == pytest.approx(120.0)


def test_rough_ridge_replays_within_attempt_and_varies_across_attempts() -> None:
    feature = ridge_feature("ridge-01", roughness=1.0, roughness_scale_km=1.25)
    plan = make_plan((feature,))
    geometry = band(width_start=4.0, width_end=4.0)

    first = generate_terrain(
        plan,
        make_layout(plan, {"ridge-01": geometry}, attempt_index=2),
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    replay = generate_terrain(
        plan,
        make_layout(plan, {"ridge-01": geometry}, attempt_index=2),
        attempt_index=2,
        rng_factory=RngFactory(plan.seed),
    )
    other = generate_terrain(
        plan,
        make_layout(plan, {"ridge-01": geometry}, attempt_index=3),
        attempt_index=3,
        rng_factory=RngFactory(plan.seed),
    )

    assert np.array_equal(first.elevation_m, replay.elevation_m)
    assert not np.array_equal(first.elevation_m, other.elevation_m)


def test_raise_and_ridge_are_additive_and_feature_order_independent() -> None:
    area_feature = raise_feature("a-base", 20.0)
    band_feature = ridge_feature("b-ridge", height_m=100.0)
    plan_ab = make_plan((area_feature, band_feature))
    plan_ba = make_plan((band_feature, area_feature))
    geometries = {
        "a-base": whole_domain_area(),
        "b-ridge": band(),
    }

    first = generate_terrain(
        plan_ab,
        make_layout(plan_ab, geometries),
        attempt_index=0,
        rng_factory=RngFactory(plan_ab.seed),
    )
    second = generate_terrain(
        plan_ba,
        make_layout(plan_ba, geometries),
        attempt_index=0,
        rng_factory=RngFactory(plan_ba.seed),
    )

    assert np.array_equal(first.elevation_m, second.elevation_m)
    assert first.elevation_m[0, 0] == np.float32(20.0)
    assert first.elevation_m[1, 0] == np.float32(70.0)


def test_ridge_requires_exact_parameter_set() -> None:
    feature = ridge_feature(
        "ridge-01",
        parameters_override={"height_m": fp(100.0)},
    )
    plan = make_plan((feature,))

    with pytest.raises(TerrainCapabilityError, match="requires exactly effect parameters"):
        generate_terrain(
            plan,
            make_layout(plan, {"ridge-01": band()}),
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )


def test_ridge_rejects_invalid_roughness() -> None:
    feature = ridge_feature("ridge-01", roughness=1.1)
    plan = make_plan((feature,))

    with pytest.raises(TerrainCapabilityError, match="roughness must be in"):
        generate_terrain(
            plan,
            make_layout(plan, {"ridge-01": band()}),
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )
