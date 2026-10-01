from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

import domain_generator
from domain_generator.application import (
    generate_domain,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.assembly import DomainAssemblyError, assemble_domain
from domain_generator.bundle_export import export_domain_bundle
from domain_generator.compiler import compile_domain_spec
from domain_generator.contracts.validation import ValidationStage
from domain_generator.hydrology import hydrology_stage
from domain_generator.layout import layout_stage
from domain_generator.pipeline import CandidateState, DomainCandidate, StageStep, run_generation
from domain_generator.pipeline.final import final_stage
from domain_generator.poi import placement_stage
from domain_generator.surface import surface_stage
from domain_generator.terrain import terrain_stage


ROOT = Path(__file__).resolve().parents[1]
V02_FIXTURE = ROOT / "examples" / "terrain-v02" / "checkpoint"
V01_FIXTURE = ROOT / "tests" / "acceptance" / "cases" / "a05-dependent-poi"

CANONICAL_STEPS = (
    StageStep(stage=ValidationStage.LAYOUT, handler=layout_stage),
    StageStep(stage=ValidationStage.TERRAIN, handler=terrain_stage),
    StageStep(stage=ValidationStage.HYDROLOGY, handler=hydrology_stage),
    StageStep(stage=ValidationStage.SURFACE, handler=surface_stage),
    StageStep(stage=ValidationStage.PLACEMENT, handler=placement_stage),
    StageStep(stage=ValidationStage.FINAL, handler=final_stage),
)


@pytest.fixture(scope="module")
def representative_v02():
    request = load_generation_request(V02_FIXTURE / "request.json")
    catalog = load_preset_catalog(V02_FIXTURE / "presets.json")
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version=domain_generator.__version__,
    )
    run = run_generation(
        plan=plan,
        config=request.generation_config,
        steps=CANONICAL_STEPS,
    )
    candidate = run.selected
    assert candidate.state.hydrology is not None
    assert candidate.state.hydrology.potential_river_network is not None
    return request, plan, candidate


def _assemble_v02(representative_v02):
    request, plan, candidate = representative_v02
    return assemble_domain(
        spec=request.domain_spec,
        plan=plan,
        config=request.generation_config,
        candidate=candidate,
    )


def test_x01_regional_network_export_is_runtime_network(representative_v02) -> None:
    _request, _plan, candidate = representative_v02
    assembly = _assemble_v02(representative_v02)
    hydrology = candidate.state.hydrology
    assert hydrology is not None
    assert assembly.data.networks["rivers"] == hydrology.river_network


def test_x02_potential_network_export_is_runtime_network(representative_v02) -> None:
    _request, _plan, candidate = representative_v02
    assembly = _assemble_v02(representative_v02)
    hydrology = candidate.state.hydrology
    assert hydrology is not None
    assert hydrology.potential_river_network is not None
    assert (
        assembly.data.networks["potential_drainage"]
        == hydrology.potential_river_network
    )


def test_x03_core_v01_network_boundary_is_unchanged() -> None:
    request = load_generation_request(V01_FIXTURE / "request.json")
    catalog = load_preset_catalog(V01_FIXTURE / "presets.json")
    assembly = generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry_for_request(request, catalog),
    )
    assert request.domain_spec.schema_version == "0.1"
    assert list(assembly.data.networks) == ["rivers"]


def test_x04_export_does_not_promote_potential_drainage_to_canonical_water(
    representative_v02,
) -> None:
    _request, _plan, candidate = representative_v02
    hydrology = candidate.state.hydrology
    assert hydrology is not None

    water_before = hydrology.water_depth_m.copy()
    stream_mask_before = hydrology.stream_mask.copy()
    regional_before = hydrology.river_network
    lakes_before = dict(hydrology.lake_features)

    assembly = _assemble_v02(representative_v02)

    np.testing.assert_array_equal(hydrology.water_depth_m, water_before)
    np.testing.assert_array_equal(hydrology.stream_mask, stream_mask_before)
    assert hydrology.river_network == regional_before
    assert hydrology.lake_features == lakes_before
    assert assembly.data.networks["rivers"] == regional_before


def test_x05_assembly_does_not_mutate_or_reconstruct_networks(
    representative_v02,
) -> None:
    _request, _plan, candidate = representative_v02
    hydrology = candidate.state.hydrology
    assert hydrology is not None
    assert hydrology.potential_river_network is not None

    regional_before = hydrology.river_network.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    )
    potential_before = hydrology.potential_river_network.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    )

    assembly = _assemble_v02(representative_v02)

    assert hydrology.river_network.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    ) == regional_before
    assert hydrology.potential_river_network.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    ) == potential_before
    assert assembly.data.networks["rivers"].model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    ) == regional_before
    assert assembly.data.networks["potential_drainage"].model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    ) == potential_before


def test_x06_network_serialization_is_byte_stable(
    representative_v02,
    tmp_path: Path,
) -> None:
    assembly = _assemble_v02(representative_v02)
    first = tmp_path / "first"
    second = tmp_path / "second"

    export_domain_bundle(assembly=assembly, output_dir=first)
    export_domain_bundle(assembly=assembly, output_dir=second)

    assert (first / "domain.json").read_bytes() == (second / "domain.json").read_bytes()


def test_x07_core_v02_missing_potential_network_fails_explicitly(
    representative_v02,
) -> None:
    request, plan, candidate = representative_v02
    hydrology = candidate.state.hydrology
    assert hydrology is not None

    missing_potential = replace(hydrology, potential_river_network=None)
    state = CandidateState(
        attempt_index=candidate.state.attempt_index,
        layout=candidate.state.layout,
        terrain=candidate.state.terrain,
        hydrology=missing_potential,
        surface=candidate.state.surface,
        placement=candidate.state.placement,
    )
    invalid_candidate = DomainCandidate(
        attempt_index=candidate.attempt_index,
        state=state,
        validations=candidate.validations,
    )

    with pytest.raises(
        DomainAssemblyError,
        match="missing accepted potential drainage network",
    ):
        assemble_domain(
            spec=request.domain_spec,
            plan=plan,
            config=request.generation_config,
            candidate=invalid_candidate,
        )


def test_x08_public_network_ids_are_exact_and_bounded(representative_v02) -> None:
    assembly = _assemble_v02(representative_v02)
    assert list(assembly.data.networks) == ["rivers", "potential_drainage"]
    assert "streams" not in assembly.data.networks
    assert "minor_rivers" not in assembly.data.networks
    assert "seasonal_rivers" not in assembly.data.networks
