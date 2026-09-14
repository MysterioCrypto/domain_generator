from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np

import domain_generator
from domain_generator.application import (
    generate_domain_bundle,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.assembly import DomainAssembly, assemble_domain
from domain_generator.compiler import compile_domain_spec
from domain_generator.contracts import GenerationRequest, ValidationStage
from domain_generator.hydrology import hydrology_stage
from domain_generator.layout import layout_stage
from domain_generator.pipeline import GenerationRunResult, StageStep, run_generation
from domain_generator.pipeline.final import final_stage
from domain_generator.poi import placement_stage
from domain_generator.presets import PresetCatalog, PresetRegistry
from domain_generator.surface import surface_stage
from domain_generator.terrain import terrain_stage


CASE_IDS = (
    "a01-minimal",
    "a02-terrain-ridge",
    "a03-hydrology-lake-river",
    "a04-surface",
    "a05-dependent-poi",
    "a06-constraints-ranking",
    "a07-complex-mixed",
)

CASES_ROOT = Path(__file__).resolve().parent / "cases"

_CANONICAL_TEST_STEPS = (
    StageStep(stage=ValidationStage.LAYOUT, handler=layout_stage),
    StageStep(stage=ValidationStage.TERRAIN, handler=terrain_stage),
    StageStep(stage=ValidationStage.HYDROLOGY, handler=hydrology_stage),
    StageStep(stage=ValidationStage.SURFACE, handler=surface_stage),
    StageStep(stage=ValidationStage.PLACEMENT, handler=placement_stage),
    StageStep(stage=ValidationStage.FINAL, handler=final_stage),
)


@dataclass(frozen=True, slots=True)
class AcceptanceCase:
    case_id: str
    root: Path
    request: GenerationRequest
    catalog: PresetCatalog | None
    expected: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DetailedGeneration:
    case: AcceptanceCase
    registry: PresetRegistry
    plan: Any
    run: GenerationRunResult
    assembly: DomainAssembly


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_case(case_id: str) -> AcceptanceCase:
    if case_id not in CASE_IDS:
        raise ValueError(f"unknown acceptance case: {case_id}")
    root = CASES_ROOT / case_id
    request = load_generation_request(root / "request.json")
    catalog_path = root / "presets.json"
    catalog = load_preset_catalog(catalog_path) if catalog_path.is_file() else None
    expected = _read_json(root / "expected.json")
    if expected.get("case_version") != "0.1":
        raise AssertionError(f"{case_id}: expected.json case_version must be 0.1")
    return AcceptanceCase(
        case_id=case_id,
        root=root,
        request=request,
        catalog=catalog,
        expected=expected,
    )


def run_detailed(case: AcceptanceCase) -> DetailedGeneration:
    registry = registry_for_request(case.request, case.catalog)
    plan = compile_domain_spec(
        case.request.domain_spec,
        registry=registry,
        generator_version=domain_generator.__version__,
    )
    run = run_generation(
        plan=plan,
        config=case.request.generation_config,
        steps=_CANONICAL_TEST_STEPS,
    )
    assembly = assemble_domain(
        spec=case.request.domain_spec,
        plan=plan,
        config=case.request.generation_config,
        candidate=run.selected,
    )
    return DetailedGeneration(
        case=case,
        registry=registry,
        plan=plan,
        run=run,
        assembly=assembly,
    )


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def domain_data_sha256(assembly: DomainAssembly) -> str:
    payload = assembly.data.model_dump(mode="json", by_alias=True, exclude_none=False)
    return "sha256:" + sha256(canonical_json_bytes(payload)).hexdigest()


def field_semantic_sha256(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    header = {
        "dtype": str(contiguous.dtype),
        "shape": list(contiguous.shape),
    }
    digest = sha256()
    digest.update(canonical_json_bytes(header))
    digest.update(b"\0")
    digest.update(contiguous.tobytes(order="C"))
    return "sha256:" + digest.hexdigest()


def baseline_snapshot(result: DetailedGeneration) -> dict[str, Any]:
    assembly = result.assembly
    data = assembly.data
    fields: dict[str, Any] = {}
    for field_id in sorted(assembly.field_payloads):
        array = assembly.field_payloads[field_id]
        fields[field_id] = {
            "sha256": field_semantic_sha256(array),
            "dtype": str(array.dtype),
            "shape": list(array.shape),
            "min": float(np.min(array)),
            "max": float(np.max(array)),
        }

    features = {
        feature_id: {
            "family": feature.family.value,
            "geometry_type": feature.geometry.type,
            "source_type": feature.source.type,
        }
        for feature_id, feature in sorted(data.features.items())
    }
    rivers = data.networks.get("rivers")
    river_summary = {
        "nodes": len(rivers.nodes) if rivers is not None else 0,
        "segments": len(rivers.segments) if rivers is not None else 0,
    }

    provenance = data.provenance
    return {
        "accepted_attempt_index": provenance.accepted_attempt_index,
        "attempts_executed": result.run.attempts_executed,
        "valid_candidate_attempts": [candidate.attempt_index for candidate in result.run.valid_candidates],
        "spec_fingerprint": provenance.spec_fingerprint,
        "plan_fingerprint": provenance.plan_fingerprint,
        "generation_config_fingerprint": provenance.generation_config_fingerprint,
        "domain_data_sha256": domain_data_sha256(assembly),
        "fields": fields,
        "features": features,
        "rivers": river_summary,
        "validation": data.validation.model_dump(mode="json", by_alias=True, exclude_none=False),
    }


def assert_or_report_baseline(result: DetailedGeneration) -> None:
    actual = baseline_snapshot(result)
    expected = result.case.expected.get("baseline")
    if expected == "PENDING":
        marker = json.dumps(actual, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        raise AssertionError(f"ACCEPTANCE_BASELINE::{result.case.case_id}::{marker}")
    assert actual == expected


def assert_exact_replay(first: DetailedGeneration, second: DetailedGeneration) -> None:
    assert first.run.selected.attempt_index == second.run.selected.attempt_index
    assert first.assembly.data.model_dump(mode="json", by_alias=True, exclude_none=False) == second.assembly.data.model_dump(
        mode="json", by_alias=True, exclude_none=False
    )
    assert set(first.assembly.field_payloads) == set(second.assembly.field_payloads)
    for field_id in sorted(first.assembly.field_payloads):
        assert np.array_equal(
            first.assembly.field_payloads[field_id],
            second.assembly.field_payloads[field_id],
        )
    assert baseline_snapshot(first) == baseline_snapshot(second)


def verify_bundle(case: AcceptanceCase, tmp_path: Path, *, render_preview: bool = False):
    registry = registry_for_request(case.request, case.catalog)
    target = tmp_path / case.case_id
    result = generate_domain_bundle(
        request=case.request,
        registry=registry,
        output_dir=target,
        render_preview=render_preview,
    )
    assert (target / "domain.json").is_file()
    assert (target / "manifest.json").is_file()
    manifest = result.manifest
    for entry in manifest.canonical_files:
        path = target / entry.path
        assert path.is_file()
        digest = sha256(path.read_bytes()).hexdigest()
        assert entry.sha256 == "sha256:" + digest
        assert entry.size_bytes == path.stat().st_size
    return result
