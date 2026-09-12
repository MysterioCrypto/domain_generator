from __future__ import annotations

import pytest

from domain_generator.compiler.compile import CompilerError, compile_domain_spec
from domain_generator.constraints import score_measurement
from domain_generator.contracts.plan import (
    CompiledScoring,
    EffectRecipe,
    EffectStage,
    FeatureFamily,
    ReservationLayoutRecipe,
    SiteProfile,
)
from domain_generator.contracts.spec import DomainSpec
from domain_generator.presets import PresetDefinition, PresetRegistry


def _base_spec(*, constraints, features=()) -> DomainSpec:
    return DomainSpec.model_validate(
        {
            "schema_version": "0.1",
            "id": "soft-test",
            "seed": 7,
            "domain": {"size": {"width_km": 20.0, "height_km": 20.0}},
            "simulation": {"cell_size_km": 1.0},
            "hydrology": {
                "stream_threshold_km2": 2.0,
                "lake_min_area_km2": 1.0,
                "lake_min_depth_m": 1.0,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
            },
            "surface": {
                "moisture_base": 0.3,
                "water_moisture_boost": 0.5,
                "water_moisture_decay_km": 5.0,
                "moisture_noise_amplitude": 0.0,
                "moisture_noise_scale_km": 5.0,
                "vegetation_slope_zero_deg": 45.0,
            },
            "features": list(features),
            "constraints": list(constraints),
        }
    )


def _empty_registry() -> PresetRegistry:
    return PresetRegistry((), operator_ids=())


def _poi_registry() -> PresetRegistry:
    preset = PresetDefinition(
        id="poi",
        family=FeatureFamily.POI,
        layout=ReservationLayoutRecipe(),
        effect=EffectRecipe(
            stage=EffectStage.DEPENDENT_PLACEMENT,
            operator="place",
            site_profile=SiteProfile(),
        ),
    )
    return PresetRegistry((preset,), operator_ids=("place",))


def test_compiler_maps_soft_near_to_linear_decreasing_scoring() -> None:
    spec = _base_spec(
        constraints=(
            {
                "id": "near-center",
                "relation": "near",
                "subject": {"point": {"x_km": 2.0, "y_km": 2.0}},
                "target": {"domain_anchor": "center"},
                "strength": "soft",
                "parameters": {"max_distance_km": 10.0},
                "weight": 0.25,
            },
        )
    )

    plan = compile_domain_spec(
        spec,
        registry=_empty_registry(),
        generator_version="test",
    )

    compiled = plan.constraints[0]
    assert compiled.strength.value == "soft"
    assert compiled.evaluator.type == "distance"
    assert compiled.scoring is not None
    assert compiled.scoring.type == "linear_decreasing"
    assert compiled.scoring.ideal == 0.0
    assert compiled.scoring.worst == 10.0
    assert compiled.weight == 0.25
    assert compiled.predicate is None
    assert compiled.unit == "km"


def test_compiler_maps_zero_crossing_to_positive_scoring() -> None:
    spec = _base_spec(
        constraints=(
            {
                "id": "cross",
                "relation": "crosses",
                "subject": {"point": {"x_km": 2.0, "y_km": 2.0}},
                "target": {"point": {"x_km": 3.0, "y_km": 3.0}},
                "strength": "soft",
                "parameters": {"minimum_crossing_length_km": 0.0},
            },
        )
    )

    plan = compile_domain_spec(
        spec,
        registry=_empty_registry(),
        generator_version="test",
    )

    scoring = plan.constraints[0].scoring
    assert scoring is not None
    assert scoring.type == "positive"
    assert scoring.ideal is None
    assert scoring.worst is None
    assert plan.constraints[0].weight == 1.0


def test_soft_deferred_to_deferred_constraint_compiles() -> None:
    features = (
        {"id": "a", "preset": "poi"},
        {"id": "b", "preset": "poi"},
    )
    spec = _base_spec(
        features=features,
        constraints=(
            {
                "id": "a-near-b",
                "relation": "near",
                "subject": {"feature": "a"},
                "target": {"feature": "b"},
                "strength": "soft",
                "parameters": {"max_distance_km": 5.0},
            },
        ),
    )

    plan = compile_domain_spec(
        spec,
        registry=_poi_registry(),
        generator_version="test",
    )
    assert plan.constraints[0].scoring is not None


def test_hard_deferred_to_deferred_constraint_remains_rejected() -> None:
    features = (
        {"id": "a", "preset": "poi"},
        {"id": "b", "preset": "poi"},
    )
    spec = _base_spec(
        features=features,
        constraints=(
            {
                "id": "a-near-b",
                "relation": "near",
                "subject": {"feature": "a"},
                "target": {"feature": "b"},
                "strength": "hard",
                "parameters": {"max_distance_km": 5.0},
            },
        ),
    )

    with pytest.raises(CompilerError, match="deferred-to-deferred"):
        compile_domain_spec(
            spec,
            registry=_poi_registry(),
            generator_version="test",
        )


@pytest.mark.parametrize(
    ("measured", "expected"),
    [(-1.0, 0.0), (0.0, 0.0), (5.0, 0.5), (10.0, 1.0), (20.0, 1.0)],
)
def test_linear_increasing_scoring_saturates(measured: float, expected: float) -> None:
    scoring = CompiledScoring(type="linear_increasing", ideal=10.0, worst=0.0)
    assert score_measurement(scoring, measured) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("measured", "expected"),
    [(-1.0, 1.0), (0.0, 1.0), (5.0, 0.5), (10.0, 0.0), (20.0, 0.0)],
)
def test_linear_decreasing_scoring_saturates(measured: float, expected: float) -> None:
    scoring = CompiledScoring(type="linear_decreasing", ideal=0.0, worst=10.0)
    assert score_measurement(scoring, measured) == pytest.approx(expected)


def test_equal_threshold_scoring_is_step_function() -> None:
    increasing = CompiledScoring(type="linear_increasing", ideal=3.0, worst=3.0)
    decreasing = CompiledScoring(type="linear_decreasing", ideal=3.0, worst=3.0)

    assert score_measurement(increasing, 2.999) == 0.0
    assert score_measurement(increasing, 3.0) == 1.0
    assert score_measurement(decreasing, 3.0) == 1.0
    assert score_measurement(decreasing, 3.001) == 0.0


def test_positive_scoring_preserves_strict_crossing_semantics() -> None:
    scoring = CompiledScoring(type="positive")
    assert score_measurement(scoring, 0.0) == 0.0
    assert score_measurement(scoring, 1e-12) == 1.0


def test_invalid_linear_direction_is_capability_error() -> None:
    scoring = CompiledScoring(type="linear_increasing", ideal=0.0, worst=1.0)

    with pytest.raises(RuntimeError, match="ideal >= worst"):
        score_measurement(scoring, 0.5)
