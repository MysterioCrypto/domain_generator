from __future__ import annotations

import pytest

from domain_generator.compiler import (
    CompilerError,
    compile_domain_spec,
    domain_spec_fingerprint,
    semantic_plan_fingerprint,
)
from domain_generator.contracts.plan import (
    CompiledFeatureRef,
    CompiledPoint,
    CompiledRectangle,
    GeometryLayoutRecipe,
    RangeParameter,
)
from domain_generator.contracts.spec import DomainSpec
from domain_generator.presets import PresetDefinition, PresetRegistry, PresetRegistryError


def mountain_preset() -> PresetDefinition:
    return PresetDefinition.model_validate(
        {
            "id": "mountain_range",
            "family": "terrain",
            "layout": {
                "mode": "geometry",
                "shape": "band",
                "parameters": {
                    "width_km": {
                        "kind": "range",
                        "type": "float",
                        "min": 10.0,
                        "max": 40.0,
                        "sampler": {"type": "triangular", "mode": 24.0},
                    },
                    "curvature": {
                        "kind": "range",
                        "type": "float",
                        "min": 0.05,
                        "max": 0.30,
                        "sampler": {"type": "uniform"},
                    },
                },
            },
            "effect": {
                "stage": "terrain",
                "operator": "ridge",
                "parameters": {
                    "roughness": {
                        "kind": "fixed",
                        "type": "float",
                        "value": 0.7,
                    }
                },
            },
        }
    )


def forest_preset() -> PresetDefinition:
    return PresetDefinition.model_validate(
        {
            "id": "forest",
            "family": "surface",
            "layout": {
                "mode": "geometry",
                "shape": "area",
                "parameters": {},
            },
            "effect": {
                "stage": "surface",
                "operator": "vegetation_bias",
                "parameters": {},
            },
        }
    )


def dependent_preset(preset_id: str) -> PresetDefinition:
    return PresetDefinition.model_validate(
        {
            "id": preset_id,
            "family": "poi",
            "layout": {"mode": "reservation", "final_shape": "point"},
            "effect": {
                "stage": "dependent_placement",
                "operator": "suitability_placement",
                "parameters": {},
                "site_profile": {
                    "footprint_radius_km": 0.5,
                    "requirements": [],
                    "preferences": [],
                },
            },
        }
    )


def registry() -> PresetRegistry:
    return PresetRegistry(
        [
            mountain_preset(),
            forest_preset(),
            dependent_preset("fort"),
            dependent_preset("village"),
        ],
        operator_ids={"ridge", "vegetation_bias", "suitability_placement"},
    )


def base_spec() -> dict:
    return {
        "schema_version": "0.1",
        "id": "compiler-test",
        "label": "Compiler test domain",
        "seed": 123456,
        "domain": {"size": {"width_km": 120.0, "height_km": 90.0}},
        "simulation": {"cell_size_km": 0.5},
        "hydrology": {
            "stream_threshold_km2": 25.0,
            "lake_min_area_km2": 1.0,
            "lake_min_depth_m": 2.0,
            "river_depth_at_threshold_m": 0.5,
            "river_depth_exponent": 0.3,
        },
        "features": [
            {
                "id": "mountain-01",
                "label": "Mountains",
                "preset": "mountain_range",
                "parameters": {"width_km": {"min": 15.0, "max": 30.0}},
                "tags": ["major_landform"],
            },
            {"id": "fort-01", "preset": "fort"},
        ],
        "constraints": [
            {
                "id": "fort-near-mountain-end",
                "relation": "near",
                "subject": {"feature": "fort-01"},
                "target": {"feature": "mountain-01", "part": "endpoints"},
                "strength": "hard",
                "parameters": {"max_distance_km": 3.0},
            },
            {
                "id": "mountains-start-sw",
                "relation": "inside",
                "subject": {"feature": "mountain-01", "part": "start"},
                "target": {"domain_region": "southwest"},
                "strength": "hard",
            },
        ],
    }


def test_registry_rejects_duplicate_and_unknown_operator() -> None:
    with pytest.raises(PresetRegistryError, match="duplicate preset"):
        PresetRegistry(
            [mountain_preset(), mountain_preset()],
            operator_ids={"ridge"},
        )

    with pytest.raises(PresetRegistryError, match="unknown operator"):
        PresetRegistry([mountain_preset()], operator_ids=set())


def test_compile_resolves_grid_feature_recipes_and_hard_constraints() -> None:
    spec = DomainSpec.model_validate(base_spec())
    plan = compile_domain_spec(spec, registry=registry(), generator_version="0.1.0.dev0")

    assert plan.grid.rows == 180
    assert plan.grid.columns == 240
    assert plan.source.spec_fingerprint == domain_spec_fingerprint(spec)
    assert plan.hydrology.stream_threshold_km2 == 25.0
    assert plan.hydrology.lake_min_area_km2 == 1.0
    assert plan.hydrology.lake_min_depth_m == 2.0
    assert plan.hydrology.river_depth_at_threshold_m == 0.5
    assert plan.hydrology.river_depth_exponent == 0.3

    mountain = plan.features[0]
    assert mountain.id == "mountain-01"
    assert mountain.metadata.source_preset == "mountain_range"
    assert mountain.metadata.label == "Mountains"
    assert isinstance(mountain.layout, GeometryLayoutRecipe)
    width = mountain.layout.parameters["width_km"]
    assert isinstance(width, RangeParameter)
    assert width.min == 15.0
    assert width.max == 30.0
    assert width.sampler.type == "triangular"
    assert width.sampler.mode == 24.0

    near = plan.constraints[0]
    assert near.evaluator.type == "distance"
    assert isinstance(near.evaluator.subject, CompiledFeatureRef)
    assert near.evaluator.subject.feature_id == "fort-01"
    assert near.evaluator.target.part == "endpoints"
    assert near.predicate.type == "less_or_equal"
    assert near.predicate.value == 3.0
    assert near.unit == "km"

    inside = plan.constraints[1]
    assert isinstance(inside.evaluator.target, CompiledRectangle)
    assert inside.evaluator.target.min_x_km == 0.0
    assert inside.evaluator.target.max_x_km == 40.0
    assert inside.evaluator.target.min_y_km == 0.0
    assert inside.evaluator.target.max_y_km == 30.0


def test_anchor_and_normalized_selectors_compile_to_physical_coordinates() -> None:
    data = base_spec()
    data["constraints"] = [
        {
            "id": "near-center",
            "relation": "near",
            "subject": {"point": {"normalized": {"x": 0.25, "y": 0.50}}},
            "target": {"domain_anchor": "center"},
            "strength": "hard",
            "parameters": {"max_distance_km": 50.0},
        }
    ]
    plan = compile_domain_spec(
        DomainSpec.model_validate(data),
        registry=registry(),
        generator_version="0.1.0.dev0",
    )
    constraint = plan.constraints[0]
    assert isinstance(constraint.evaluator.subject, CompiledPoint)
    assert constraint.evaluator.subject.x_km == 30.0
    assert constraint.evaluator.subject.y_km == 45.0
    assert isinstance(constraint.evaluator.target, CompiledPoint)
    assert constraint.evaluator.target.x_km == 60.0
    assert constraint.evaluator.target.y_km == 45.0


def test_compiler_rejects_unknown_preset_and_parameter() -> None:
    data = base_spec()
    data["features"][0]["preset"] = "unknown"
    with pytest.raises(CompilerError, match="unknown preset"):
        compile_domain_spec(
            DomainSpec.model_validate(data),
            registry=registry(),
            generator_version="0.1.0.dev0",
        )

    data = base_spec()
    data["features"][0]["parameters"]["not_a_parameter"] = 1.0
    with pytest.raises(CompilerError, match="unknown parameters"):
        compile_domain_spec(
            DomainSpec.model_validate(data),
            registry=registry(),
            generator_version="0.1.0.dev0",
        )


def test_parameter_override_must_stay_inside_preset_domain_and_sampler_mode() -> None:
    data = base_spec()
    data["features"][0]["parameters"]["width_km"] = {"min": 20.0, "max": 45.0}
    with pytest.raises(CompilerError, match="inside preset range"):
        compile_domain_spec(
            DomainSpec.model_validate(data),
            registry=registry(),
            generator_version="0.1.0.dev0",
        )

    data = base_spec()
    data["features"][0]["parameters"]["width_km"] = {"min": 25.0, "max": 30.0}
    with pytest.raises(CompilerError, match="excludes preset triangular sampler mode"):
        compile_domain_spec(
            DomainSpec.model_validate(data),
            registry=registry(),
            generator_version="0.1.0.dev0",
        )


def test_selector_part_compatibility_is_checked_after_preset_resolution() -> None:
    data = base_spec()
    data["constraints"] = [
        {
            "id": "bad-part",
            "relation": "near",
            "subject": {"feature": "fort-01", "part": "boundary"},
            "target": {"feature": "mountain-01"},
            "strength": "hard",
            "parameters": {"max_distance_km": 2.0},
        }
    ]
    with pytest.raises(CompilerError, match="does not support part"):
        compile_domain_spec(
            DomainSpec.model_validate(data),
            registry=registry(),
            generator_version="0.1.0.dev0",
        )


def test_deferred_to_deferred_hard_dependency_is_rejected() -> None:
    data = base_spec()
    data["features"].append({"id": "village-01", "preset": "village"})
    data["constraints"] = [
        {
            "id": "village-near-fort",
            "relation": "near",
            "subject": {"feature": "village-01"},
            "target": {"feature": "fort-01"},
            "strength": "hard",
            "parameters": {"max_distance_km": 2.0},
        }
    ]
    with pytest.raises(CompilerError, match="deferred-to-deferred"):
        compile_domain_spec(
            DomainSpec.model_validate(data),
            registry=registry(),
            generator_version="0.1.0.dev0",
        )


def test_rng_v1_seed_boundary_is_enforced_by_compiler() -> None:
    data = base_spec()
    data["seed"] = -1
    spec = DomainSpec.model_validate(data)
    with pytest.raises(CompilerError, match="unsigned uint64"):
        compile_domain_spec(spec, registry=registry(), generator_version="0.1.0.dev0")

    data["seed"] = 1 << 64
    spec = DomainSpec.model_validate(data)
    with pytest.raises(CompilerError, match="unsigned uint64"):
        compile_domain_spec(spec, registry=registry(), generator_version="0.1.0.dev0")


def test_soft_constraints_are_explicitly_not_implemented_in_this_slice() -> None:
    data = base_spec()
    data["constraints"] = [
        {
            "id": "soft-near-center",
            "relation": "near",
            "subject": {"feature": "mountain-01", "part": "center"},
            "target": {"domain_anchor": "center"},
            "strength": "soft",
            "parameters": {"max_distance_km": 20.0},
        }
    ]
    with pytest.raises(CompilerError, match="soft constraint compilation is not implemented"):
        compile_domain_spec(
            DomainSpec.model_validate(data),
            registry=registry(),
            generator_version="0.1.0.dev0",
        )


def test_semantic_plan_fingerprint_ignores_presentation_metadata_and_source_provenance() -> None:
    spec_a = DomainSpec.model_validate(base_spec())
    plan_a = compile_domain_spec(spec_a, registry=registry(), generator_version="0.1.0.dev0")

    changed = base_spec()
    changed["id"] = "renamed-domain-document"
    changed["label"] = "Different display label"
    changed["features"][0]["label"] = "Renamed mountain label"
    changed["features"][0]["tags"] = ["different", "metadata"]
    spec_b = DomainSpec.model_validate(changed)
    plan_b = compile_domain_spec(spec_b, registry=registry(), generator_version="0.1.0.dev0")

    assert domain_spec_fingerprint(spec_a) != domain_spec_fingerprint(spec_b)
    assert semantic_plan_fingerprint(plan_a) == semantic_plan_fingerprint(plan_b)


def test_semantic_plan_fingerprint_includes_hydrology_recipe() -> None:
    spec_a = DomainSpec.model_validate(base_spec())
    changed = base_spec()
    changed["hydrology"]["river_depth_exponent"] = 0.45
    spec_b = DomainSpec.model_validate(changed)

    plan_a = compile_domain_spec(spec_a, registry=registry(), generator_version="0.1.0.dev0")
    plan_b = compile_domain_spec(spec_b, registry=registry(), generator_version="0.1.0.dev0")

    assert semantic_plan_fingerprint(plan_a) != semantic_plan_fingerprint(plan_b)


def test_compilation_is_deterministic() -> None:
    spec = DomainSpec.model_validate(base_spec())
    plan_a = compile_domain_spec(spec, registry=registry(), generator_version="0.1.0.dev0")
    plan_b = compile_domain_spec(spec, registry=registry(), generator_version="0.1.0.dev0")

    assert plan_a.model_dump(mode="json") == plan_b.model_dump(mode="json")
    assert semantic_plan_fingerprint(plan_a) == semantic_plan_fingerprint(plan_b)
