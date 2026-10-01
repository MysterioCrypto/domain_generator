from __future__ import annotations

from pathlib import Path

import domain_generator

from domain_generator.application import (
    generate_domain_bundle,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.compiler import compile_domain_spec
from domain_generator.hydrology import hydrology_stage
from domain_generator.layout import layout_stage
from domain_generator.pipeline import CandidateState
from domain_generator.pipeline.attempts import AttemptContext, validation_passed
from domain_generator.pipeline.rng import RngFactory
from domain_generator.terrain import terrain_stage


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "terrain-v02" / "checkpoint"


def _run_representative_through_hydrology():
    request = load_generation_request(FIXTURE / "request.json")
    catalog = load_preset_catalog(FIXTURE / "presets.json")
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version=domain_generator.__version__,
    )
    state = CandidateState(attempt_index=0)
    context = AttemptContext(
        plan=plan,
        attempt_index=0,
        rng_factory=RngFactory(plan.seed),
    )
    for stage in (layout_stage, terrain_stage, hydrology_stage):
        result = stage(context, state)
        failed = [
            item.id
            for item in result.engine_invariants.results
            if not item.passed
        ]
        assert validation_passed(result), (
            f"representative Core 0.2 fixture failed {result.stage.value}: {failed}"
        )
    return request, catalog, state


def test_core_v02_representative_hydrology_stage_is_valid() -> None:
    request, _catalog, state = _run_representative_through_hydrology()

    assert request.domain_spec.schema_version == "0.2"
    assert state.hydrology is not None
    assert state.hydrology.routing_mode == "continuous"
    assert state.hydrology.continuous_routing is not None


def test_core_v02_request_reaches_canonical_bundle_boundary(tmp_path: Path) -> None:
    request = load_generation_request(FIXTURE / "request.json")
    catalog = load_preset_catalog(FIXTURE / "presets.json")
    output = tmp_path / "generated-v02"

    result = generate_domain_bundle(
        request=request,
        registry=registry_for_request(request, catalog),
        output_dir=output,
    )

    assert result.assembly.data.provenance.spec_schema_version == "0.2"
    assert result.assembly.data.identity.id == "terrain-v02-visual-checkpoint"
    assert (output / "domain.json").is_file()
    assert (output / "manifest.json").is_file()
    assert (output / "fields" / "elevation.npy").is_file()
