import pytest
from pydantic import ValidationError

from domain_generator.contracts import DomainSpec


def minimal_spec() -> dict:
    return {
        "schema_version": "0.1",
        "id": "test-domain",
        "seed": 123,
        "domain": {"size": {"width_km": 120.0, "height_km": 100.0}},
        "simulation": {"cell_size_km": 0.25},
        "hydrology": {
            "stream_threshold_km2": 25.0,
            "lake_min_area_km2": 1.0,
            "lake_min_depth_m": 2.0,
        },
        "features": [],
        "constraints": [],
    }


def test_minimal_domain_spec_parses() -> None:
    spec = DomainSpec.model_validate(minimal_spec())
    assert spec.domain.size.width_km == 120.0
    assert spec.simulation.cell_size_km == 0.25
    assert spec.hydrology.stream_threshold_km2 == 25.0


def test_hydrology_recipe_is_required() -> None:
    data = minimal_spec()
    del data["hydrology"]
    with pytest.raises(ValidationError):
        DomainSpec.model_validate(data)


def test_hydrology_thresholds_must_be_positive() -> None:
    data = minimal_spec()
    data["hydrology"]["lake_min_depth_m"] = 0.0
    with pytest.raises(ValidationError):
        DomainSpec.model_validate(data)


def test_unknown_fields_are_rejected() -> None:
    data = minimal_spec()
    data["unexpected"] = True
    with pytest.raises(ValidationError):
        DomainSpec.model_validate(data)


def test_grid_must_divide_exactly() -> None:
    data = minimal_spec()
    data["simulation"]["cell_size_km"] = 0.3
    with pytest.raises(ValidationError, match="exactly divisible"):
        DomainSpec.model_validate(data)


def test_connects_relation_is_not_part_of_v01() -> None:
    data = minimal_spec()
    data["constraints"] = [
        {
            "id": "bad-relation",
            "relation": "connects",
            "subject": {"domain_anchor": "west"},
            "target": {"domain_anchor": "east"},
            "strength": "hard",
        }
    ]
    with pytest.raises(ValidationError):
        DomainSpec.model_validate(data)


def test_hard_constraint_rejects_weight() -> None:
    data = minimal_spec()
    data["constraints"] = [
        {
            "id": "near-center",
            "relation": "near",
            "subject": {"domain_anchor": "west"},
            "target": {"domain_anchor": "center"},
            "strength": "hard",
            "weight": 0.5,
            "parameters": {"max_distance_km": 20.0},
        }
    ]
    with pytest.raises(ValidationError, match="weight is only allowed"):
        DomainSpec.model_validate(data)


def test_literal_km_point_must_be_inside_domain() -> None:
    data = minimal_spec()
    data["constraints"] = [
        {
            "id": "point-check",
            "relation": "near",
            "subject": {"point": {"x_km": 121.0, "y_km": 20.0}},
            "target": {"domain_anchor": "center"},
            "strength": "hard",
            "parameters": {"max_distance_km": 5.0},
        }
    ]
    with pytest.raises(ValidationError, match="inside the domain"):
        DomainSpec.model_validate(data)


def test_soft_constraint_defaults_weight_to_one() -> None:
    data = minimal_spec()
    data["constraints"] = [
        {
            "id": "soft-near-center",
            "relation": "near",
            "subject": {"domain_anchor": "west"},
            "target": {"domain_anchor": "center"},
            "strength": "soft",
            "parameters": {"max_distance_km": 20.0},
        }
    ]
    spec = DomainSpec.model_validate(data)
    assert spec.constraints[0].weight == 1.0
