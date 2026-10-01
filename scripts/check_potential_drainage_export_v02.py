from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import domain_generator
from domain_generator.application import (
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.assembly import assemble_domain
from domain_generator.compiler import compile_domain_spec
from domain_generator.contracts.validation import ValidationStage
from domain_generator.hydrology import hydrology_stage
from domain_generator.layout import layout_stage
from domain_generator.pipeline import StageStep, run_generation
from domain_generator.pipeline.final import final_stage
from domain_generator.poi import placement_stage
from domain_generator.surface import surface_stage
from domain_generator.terrain import terrain_stage


CANONICAL_STEPS = (
    StageStep(stage=ValidationStage.LAYOUT, handler=layout_stage),
    StageStep(stage=ValidationStage.TERRAIN, handler=terrain_stage),
    StageStep(stage=ValidationStage.HYDROLOGY, handler=hydrology_stage),
    StageStep(stage=ValidationStage.SURFACE, handler=surface_stage),
    StageStep(stage=ValidationStage.PLACEMENT, handler=placement_stage),
    StageStep(stage=ValidationStage.FINAL, handler=final_stage),
)


def _array_sha256(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    digest = sha256()
    digest.update(str(value.dtype).encode("ascii"))
    digest.update(str(tuple(value.shape)).encode("ascii"))
    digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def _network_counts(network) -> dict[str, int]:
    return {
        "nodes": len(network.nodes),
        "segments": len(network.segments),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    parser.add_argument("presets", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    request = load_generation_request(args.request)
    catalog = load_preset_catalog(args.presets)
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version=domain_generator.__version__,
    )
    if plan.plan_version != "0.2":
        raise RuntimeError("H11-A checkpoint requires Core 0.2")

    run = run_generation(
        plan=plan,
        config=request.generation_config,
        steps=CANONICAL_STEPS,
    )
    candidate = run.selected
    state = candidate.state
    if state.hydrology is None or state.surface is None or state.terrain is None:
        raise RuntimeError("representative candidate is missing upstream state")
    if state.hydrology.potential_river_network is None:
        raise RuntimeError("representative candidate is missing potential drainage")

    before_hashes = {
        "elevation": _array_sha256(state.terrain.elevation_m),
        "water_depth": _array_sha256(state.hydrology.water_depth_m),
        "stream_mask": _array_sha256(state.hydrology.stream_mask),
        "moisture": _array_sha256(state.surface.moisture),
        "vegetation_density": _array_sha256(state.surface.vegetation_density),
    }
    if state.surface.annual_mean_temperature_c is not None:
        before_hashes["temperature"] = _array_sha256(
            state.surface.annual_mean_temperature_c
        )
    if state.surface.annual_precipitation_mm is not None:
        before_hashes["annual_precipitation"] = _array_sha256(
            state.surface.annual_precipitation_mm
        )

    regional_runtime = state.hydrology.river_network
    potential_runtime = state.hydrology.potential_river_network

    assembly = assemble_domain(
        spec=request.domain_spec,
        plan=plan,
        config=request.generation_config,
        candidate=candidate,
    )

    after_hashes = {
        "elevation": _array_sha256(state.terrain.elevation_m),
        "water_depth": _array_sha256(state.hydrology.water_depth_m),
        "stream_mask": _array_sha256(state.hydrology.stream_mask),
        "moisture": _array_sha256(state.surface.moisture),
        "vegetation_density": _array_sha256(state.surface.vegetation_density),
    }
    if state.surface.annual_mean_temperature_c is not None:
        after_hashes["temperature"] = _array_sha256(
            state.surface.annual_mean_temperature_c
        )
    if state.surface.annual_precipitation_mm is not None:
        after_hashes["annual_precipitation"] = _array_sha256(
            state.surface.annual_precipitation_mm
        )

    exported_regional = assembly.data.networks["rivers"]
    exported_potential = assembly.data.networks["potential_drainage"]

    report = {
        "checkpoint": "H11-A",
        "accepted_attempt_index": candidate.attempt_index,
        "network_keys": list(assembly.data.networks),
        "regional_runtime": _network_counts(regional_runtime),
        "regional_export": _network_counts(exported_regional),
        "potential_runtime": _network_counts(potential_runtime),
        "potential_export": _network_counts(exported_potential),
        "regional_exact_equal": exported_regional == regional_runtime,
        "potential_exact_equal": exported_potential == potential_runtime,
        "upstream_field_hashes_unchanged": before_hashes == after_hashes,
        "upstream_field_hashes": before_hashes,
        "canonical_water_authority": "rivers",
        "potential_semantics": "drainage scaffold; not flow-permanence classification",
    }

    expected_keys = ["rivers", "potential_drainage"]
    if report["network_keys"] != expected_keys:
        raise RuntimeError(
            f"unexpected H11-A network keys: {report['network_keys']!r}"
        )
    if not report["regional_exact_equal"]:
        raise RuntimeError("regional network changed across H11-A assembly")
    if not report["potential_exact_equal"]:
        raise RuntimeError("potential network changed across H11-A assembly")
    if not report["upstream_field_hashes_unchanged"]:
        raise RuntimeError("H11-A assembly mutated upstream canonical state")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
