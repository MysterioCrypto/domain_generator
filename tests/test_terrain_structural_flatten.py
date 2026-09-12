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
    ResolvedFeature,
)
from domain_generator.pipeline.attempts import AttemptContext, CandidateState
from domain_generator.pipeline.rng import RngFactory
from domain_generator.terrain import TerrainCapabilityError, generate_terrain, terrain_stage
from domain_generator.terrain.shaping import FlattenSpec, flatten_conflicts, flatten_weight_at


def fp(value: float) -> FixedParameter:
    return FixedParameter(type=ParameterType.FLOAT, value=value)


def ip(value: int) -> FixedParameter:
    return FixedParameter(type=ParameterType.INTEGER, value=value)


def area(min_x: float, min_y: float, max_x: float, max_y: float) -> AreaGeometry:
    return AreaGeometry(
        boundary=(
            WorldPoint(x_km=min_x, y_km=min_y),
            WorldPoint(x_km=max_x, y_km=min_y),
            WorldPoint(x_km=max_x, y_km=max_y),
            WorldPoint(x_km=min_x, y_km=max_y),
        )
    )


def area_layout() -> GeometryLayoutRecipe:
    return GeometryLayoutRecipe(
        shape=GeometryShape.AREA,
        parameters={
            "vertex_count": ip(4),
            "radial_extent": fp(0.5),
            "radial_irregularity": fp(0.0),
        },
    )


def terrain_feature(feature_id: str, operator: str, parameters: dict) -> ResolvedFeature:
    return ResolvedFeature(
        id=feature_id,
        metadata=FeatureMetadata(source_preset=f"test-{operator}"),
        family=FeatureFamily.TERRAIN,
        layout=area_layout(),
        effect=EffectRecipe(
            stage=EffectStage.TERRAIN,
            operator=operator,
            parameters=parameters,
        ),
    )


def raise_feature(feature_id: str, height_m: float) -> ResolvedFeature:
    return terrain_feature(feature_id, "raise", {"height_m": fp(height_m)})


def depress_feature(feature_id: str, depth_m: float) -> ResolvedFeature:
    return terrain_feature(feature_id, "depress", {"depth_m": fp(depth_m)})


def flatten_feature(
    feature_id: str,
    *,
    target_elevation_m: float,
    blend_width_km: float,
) -> ResolvedFeature:
    return terrain_feature(
        feature_id,
        "flatten",
        {
            "target_elevation_m": fp(target_elevation_m),
            "blend_width_km": fp(blend_width_km),
        },
    )


def make_plan(features: tuple[ResolvedFeature, ...], *, seed: int = 123456) -> GenerationPlan:
    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id="flatten-test",
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


def make_layout(plan: GenerationPlan, geometries: dict, *, attempt_index: int = 0) -> LayoutCandidate:
    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations=geometries,
        placement_reservations={},
    )


def whole_domain() -> AreaGeometry:
    return area(0.0, 0.0, 4.0, 4.0)


def test_depress_is_negative_additive_structural_contribution() -> None:
    base = raise_feature("a-base", 200.0)
    basin = depress_feature("b-basin", 75.0)
    plan = make_plan((base, basin))
    layout = make_layout(
        plan,
        {
            "a-base": whole_domain(),
            "b-basin": area(1.0, 1.0, 3.0, 3.0),
        },
    )

    state = generate_terrain(plan, layout, attempt_index=0, rng_factory=RngFactory(plan.seed))

    assert state.elevation_m.dtype == np.dtype(np.float32)
    assert state.elevation_m[0, 0] == np.float32(200.0)
    assert state.elevation_m[1, 1] == np.float32(125.0)
    assert state.elevation_m[2, 2] == np.float32(125.0)


def test_depress_and_raise_are_feature_order_independent() -> None:
    base = raise_feature("a-base", 200.0)
    basin = depress_feature("b-basin", 75.0)
    geometries = {"a-base": whole_domain(), "b-basin": area(1.0, 1.0, 3.0, 3.0)}
    plan_ab = make_plan((base, basin))
    plan_ba = make_plan((basin, base))

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


def test_flatten_zero_blend_replaces_structural_elevation_inside_area() -> None:
    base = raise_feature("a-base", 100.0)
    flat = flatten_feature("z-flat", target_elevation_m=25.0, blend_width_km=0.0)
    plan = make_plan((base, flat))
    layout = make_layout(
        plan,
        {"a-base": whole_domain(), "z-flat": area(1.0, 1.0, 3.0, 3.0)},
    )

    state = generate_terrain(plan, layout, attempt_index=0, rng_factory=RngFactory(plan.seed))

    expected = np.array(
        [
            [100.0, 100.0, 100.0, 100.0],
            [100.0, 25.0, 25.0, 100.0],
            [100.0, 25.0, 25.0, 100.0],
            [100.0, 100.0, 100.0, 100.0],
        ],
        dtype=np.float32,
    )
    assert np.array_equal(state.elevation_m, expected)


def test_flatten_blend_width_is_linear_and_entirely_inside_area() -> None:
    base = raise_feature("a-base", 100.0)
    flat = flatten_feature("z-flat", target_elevation_m=0.0, blend_width_km=2.0)
    plan = make_plan((base, flat))
    layout = make_layout(plan, {"a-base": whole_domain(), "z-flat": whole_domain()})

    state = generate_terrain(plan, layout, attempt_index=0, rng_factory=RngFactory(plan.seed))

    # Cell-center distances to domain boundary are 0.5 on the outer ring and 1.5
    # for the four central cells, so weights are 0.25 and 0.75 respectively.
    expected = np.array(
        [
            [75.0, 75.0, 75.0, 75.0],
            [75.0, 25.0, 25.0, 75.0],
            [75.0, 25.0, 25.0, 75.0],
            [75.0, 75.0, 75.0, 75.0],
        ],
        dtype=np.float32,
    )
    assert np.array_equal(state.elevation_m, expected)


def test_flatten_allows_negative_absolute_target_elevation() -> None:
    flat = flatten_feature("flat", target_elevation_m=-30.0, blend_width_km=0.0)
    plan = make_plan((flat,))
    layout = make_layout(plan, {"flat": whole_domain()})

    state = generate_terrain(plan, layout, attempt_index=0, rng_factory=RngFactory(plan.seed))

    assert np.array_equal(state.elevation_m, np.full((4, 4), -30.0, dtype=np.float32))


def test_touching_flatten_regions_are_compatible_and_order_independent() -> None:
    base = raise_feature("a-base", 100.0)
    left = flatten_feature("b-left", target_elevation_m=20.0, blend_width_km=0.0)
    right = flatten_feature("c-right", target_elevation_m=80.0, blend_width_km=0.0)
    geometries = {
        "a-base": whole_domain(),
        "b-left": area(0.0, 0.0, 2.0, 4.0),
        "c-right": area(2.0, 0.0, 4.0, 4.0),
    }
    plan_first = make_plan((base, left, right))
    plan_second = make_plan((right, base, left))

    first = generate_terrain(
        plan_first,
        make_layout(plan_first, geometries),
        attempt_index=0,
        rng_factory=RngFactory(plan_first.seed),
    )
    second = generate_terrain(
        plan_second,
        make_layout(plan_second, geometries),
        attempt_index=0,
        rng_factory=RngFactory(plan_second.seed),
    )

    assert flatten_conflicts(
        (
            FlattenSpec("b-left", geometries["b-left"], 20.0, 0.0),
            FlattenSpec("c-right", geometries["c-right"], 80.0, 0.0),
        )
    ) == ()
    assert np.array_equal(first.elevation_m, second.elevation_m)
    assert np.all(first.elevation_m[:, :2] == np.float32(20.0))
    assert np.all(first.elevation_m[:, 2:] == np.float32(80.0))


def test_overlapping_flatten_regions_reject_attempt_via_validation_not_capability_error() -> None:
    base = raise_feature("a-base", 100.0)
    first_flat = flatten_feature("b-flat", target_elevation_m=20.0, blend_width_km=0.0)
    second_flat = flatten_feature("c-flat", target_elevation_m=80.0, blend_width_km=0.0)
    plan = make_plan((base, first_flat, second_flat))
    layout = make_layout(
        plan,
        {
            "a-base": whole_domain(),
            "b-flat": area(0.5, 0.5, 2.5, 3.5),
            "c-flat": area(1.5, 0.5, 3.5, 3.5),
        },
    )
    candidate = CandidateState(attempt_index=0, layout=layout)
    context = AttemptContext(plan=plan, attempt_index=0, rng_factory=RngFactory(plan.seed))

    validation = terrain_stage(context, candidate)

    assert candidate.terrain is not None
    # Conflict state remains the frozen structural field for diagnostics.
    assert np.array_equal(candidate.terrain.elevation_m, np.full((4, 4), 100.0, dtype=np.float32))
    by_id = {item.id: item for item in validation.engine_invariants.results}
    assert by_id["terrain-shaping-regions-compatible"].passed is False
    assert by_id["terrain-shaping-regions-compatible"].measured["conflict_count"] == 1
    assert validation.engine_invariants.passed is False


def test_overlap_detection_is_world_space_not_raster_cell_dependent() -> None:
    # Both tiny areas are below the first cell-center at x=y=0.5, but overlap in world space.
    first = FlattenSpec("a", area(0.05, 0.05, 0.30, 0.30), 10.0, 0.0)
    second = FlattenSpec("b", area(0.20, 0.10, 0.40, 0.35), 20.0, 0.0)

    assert flatten_conflicts((first, second)) == (("a", "b"),)


def test_flatten_weight_is_zero_on_boundary() -> None:
    geometry = area(0.0, 0.0, 4.0, 4.0)
    boundary_point = PointGeometry(x_km=0.0, y_km=2.0)

    assert flatten_weight_at(boundary_point, geometry, blend_width_km=0.0) == 0.0
    assert flatten_weight_at(boundary_point, geometry, blend_width_km=2.0) == 0.0


def test_depress_rejects_nonpositive_depth() -> None:
    feature = depress_feature("basin", 0.0)
    plan = make_plan((feature,))

    with pytest.raises(TerrainCapabilityError, match="depth_m"):
        generate_terrain(
            plan,
            make_layout(plan, {"basin": whole_domain()}),
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )


def test_flatten_rejects_negative_blend_width() -> None:
    feature = flatten_feature("flat", target_elevation_m=10.0, blend_width_km=-0.1)
    plan = make_plan((feature,))

    with pytest.raises(TerrainCapabilityError, match="blend_width_km"):
        generate_terrain(
            plan,
            make_layout(plan, {"flat": whole_domain()}),
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )


def test_flatten_requires_area_geometry() -> None:
    feature = flatten_feature("flat", target_elevation_m=10.0, blend_width_km=1.0)
    plan = make_plan((feature,))

    with pytest.raises(TerrainCapabilityError, match="AreaGeometry"):
        generate_terrain(
            plan,
            make_layout(plan, {"flat": PointGeometry(x_km=2.0, y_km=2.0)}),
            attempt_index=0,
            rng_factory=RngFactory(plan.seed),
        )
