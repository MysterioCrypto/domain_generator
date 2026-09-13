from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

import numpy as np
from pydantic import ValidationError

from .compiler import domain_spec_fingerprint, semantic_plan_fingerprint
from .contracts.config import GenerationConfig
from .contracts.data import (
    DomainData,
    DomainExtent,
    DomainIdentity,
    DomainProvenance,
    FieldDescriptor,
    FieldRole,
    GeneratorIdentity,
    HydroFeature,
    PoiFeature,
    SpecifiedFeatureSource,
    SurfaceFeature,
    TerrainFeature,
    ValidationSummary,
)
from .contracts.plan import FeatureFamily, GenerationPlan
from .contracts.spec import DomainSpec
from .contracts.validation import ValidationStage
from .pipeline.attempts import DomainCandidate
from .pipeline.rng import RNG_VERSION


class DomainAssemblyError(RuntimeError):
    """A final candidate cannot be assembled without violating Core output invariants."""


@dataclass(frozen=True, slots=True)
class DomainAssembly:
    """In-memory boundary between generation and persistence/export."""

    data: DomainData
    field_payloads: Mapping[str, np.ndarray]

    def __post_init__(self) -> None:
        if not isinstance(self.data, DomainData):
            raise TypeError("data must be DomainData")
        normalized = dict(self.field_payloads)
        if any(not isinstance(name, str) or not name for name in normalized):
            raise TypeError("field payload ids must be non-empty strings")
        if any(not isinstance(array, np.ndarray) for array in normalized.values()):
            raise TypeError("field payloads must be numpy arrays")
        object.__setattr__(self, "field_payloads", MappingProxyType(normalized))


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def semantic_generation_config_fingerprint(config: GenerationConfig) -> str:
    """Fingerprint semantic execution config while intentionally excluding observability."""
    if not isinstance(config, GenerationConfig):
        raise TypeError("config must be GenerationConfig")
    payload = {
        "generation_config_version": config.generation_config_version,
        "semantic": config.semantic.model_dump(mode="json", by_alias=True, exclude_none=False),
    }
    return "sha256:" + sha256(_canonical_json_bytes(payload)).hexdigest()


def _require_valid_candidate(candidate: DomainCandidate) -> None:
    if not isinstance(candidate, DomainCandidate):
        raise TypeError("candidate must be DomainCandidate")
    final = candidate.final_validation
    if final.stage is not ValidationStage.FINAL:
        raise DomainAssemblyError("candidate final validation must be stage 'final'")
    if final.attempt_index != candidate.attempt_index:
        raise DomainAssemblyError("candidate/final validation attempt index mismatch")
    if candidate.state.attempt_index != candidate.attempt_index:
        raise DomainAssemblyError("candidate/runtime state attempt index mismatch")
    if not final.engine_invariants.passed or not final.hard_constraints.passed:
        raise DomainAssemblyError("candidate must pass final engine invariants and hard constraints")
    if final.ranking is None:
        raise DomainAssemblyError("candidate must have final ranking")


def _require_runtime_state(candidate: DomainCandidate):
    state = candidate.state
    missing = [
        name
        for name in ("layout", "terrain", "hydrology", "surface", "placement")
        if getattr(state, name) is None
    ]
    if missing:
        raise DomainAssemblyError(f"candidate is missing runtime state: {missing}")
    assert state.layout is not None
    assert state.terrain is not None
    assert state.hydrology is not None
    assert state.surface is not None
    assert state.placement is not None
    return state


def _require_spec_plan_match(spec: DomainSpec, plan: GenerationPlan) -> None:
    if spec.id != plan.source.spec_id:
        raise DomainAssemblyError("DomainSpec id does not match plan source")
    if spec.schema_version != plan.source.spec_schema_version:
        raise DomainAssemblyError("DomainSpec schema version does not match plan source")
    actual = domain_spec_fingerprint(spec)
    if actual != plan.source.spec_fingerprint:
        raise DomainAssemblyError("DomainSpec fingerprint does not match plan source")


def _final_geometry_by_id(plan: GenerationPlan, state) -> dict[str, object]:
    structural = dict(state.layout.geometry_realizations)
    deferred = dict(state.placement.final_points)
    overlap = set(structural) & set(deferred)
    if overlap:
        raise DomainAssemblyError(f"final geometry sources overlap: {sorted(overlap)}")
    geometries = structural | deferred
    expected = {feature.id for feature in plan.features}
    actual = set(geometries)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise DomainAssemblyError(
            f"final feature geometry set mismatch: missing={missing}, extra={extra}"
        )
    return geometries


def _specified_features(plan: GenerationPlan, geometries: Mapping[str, object]) -> dict[str, object]:
    output: dict[str, object] = {}
    for feature in sorted(plan.features, key=lambda item: item.id):
        common = {
            "label": feature.metadata.label,
            "tags": feature.metadata.tags,
            "source": SpecifiedFeatureSource(preset=feature.metadata.source_preset),
            "geometry": geometries[feature.id],
        }
        try:
            if feature.family is FeatureFamily.TERRAIN:
                value = TerrainFeature(**common)
            elif feature.family is FeatureFamily.SURFACE:
                value = SurfaceFeature(**common)
            elif feature.family is FeatureFamily.POI:
                value = PoiFeature(**common)
            else:
                raise DomainAssemblyError(f"unsupported output feature family: {feature.family!r}")
        except ValidationError as exc:
            raise DomainAssemblyError(
                f"feature {feature.id!r} geometry is incompatible with family {feature.family.value!r}"
            ) from exc
        output[feature.id] = value
    return output


def _merge_features(specified: dict[str, object], hydro: Mapping[str, HydroFeature]) -> dict[str, object]:
    overlap = set(specified) & set(hydro)
    if overlap:
        raise DomainAssemblyError(f"specified/generated feature ids collide: {sorted(overlap)}")
    output = dict(specified)
    for feature_id in sorted(hydro):
        feature = hydro[feature_id]
        if not isinstance(feature, HydroFeature):
            raise DomainAssemblyError(f"hydrology feature {feature_id!r} is not HydroFeature")
        output[feature_id] = feature
    return output


def _readonly_payload(array: np.ndarray, *, field_id: str, shape: tuple[int, int]) -> np.ndarray:
    if not isinstance(array, np.ndarray):
        raise DomainAssemblyError(f"field {field_id!r} payload must be numpy ndarray")
    if array.shape != shape:
        raise DomainAssemblyError(
            f"field {field_id!r} shape must be {shape}, got {array.shape}"
        )
    if array.dtype != np.dtype(np.float32):
        raise DomainAssemblyError(
            f"field {field_id!r} dtype must be float32, got {array.dtype}"
        )
    payload = np.array(array, copy=True, order="C", subok=False)
    payload.setflags(write=False)
    return payload


def _field_descriptors(shape: tuple[int, int]) -> dict[str, FieldDescriptor]:
    return {
        "elevation": FieldDescriptor(role=FieldRole.CANONICAL, path="fields/elevation.npy", dtype="float32", shape=shape, unit="m"),
        "water_depth": FieldDescriptor(role=FieldRole.CANONICAL, path="fields/water_depth.npy", dtype="float32", shape=shape, unit="m"),
        "moisture": FieldDescriptor(role=FieldRole.CANONICAL, path="fields/moisture.npy", dtype="float32", shape=shape, unit="normalized"),
        "vegetation_density": FieldDescriptor(role=FieldRole.CANONICAL, path="fields/vegetation_density.npy", dtype="float32", shape=shape, unit="normalized"),
    }


def assemble_domain(*, spec: DomainSpec, plan: GenerationPlan, config: GenerationConfig, candidate: DomainCandidate) -> DomainAssembly:
    """Package one already-selected final-valid candidate without generating new world state."""
    if not isinstance(spec, DomainSpec):
        raise TypeError("spec must be DomainSpec")
    if not isinstance(plan, GenerationPlan):
        raise TypeError("plan must be GenerationPlan")
    if not isinstance(config, GenerationConfig):
        raise TypeError("config must be GenerationConfig")

    _require_valid_candidate(candidate)
    _require_spec_plan_match(spec, plan)
    state = _require_runtime_state(candidate)

    plan_fingerprint = semantic_plan_fingerprint(plan)
    if state.layout.source_plan.fingerprint != plan_fingerprint:
        raise DomainAssemblyError("layout source plan fingerprint does not match GenerationPlan")
    if state.layout.attempt_index != candidate.attempt_index:
        raise DomainAssemblyError("layout attempt index does not match selected candidate")

    geometries = _final_geometry_by_id(plan, state)
    specified = _specified_features(plan, geometries)
    features = _merge_features(specified, state.hydrology.lake_features)

    shape = (plan.grid.rows, plan.grid.columns)
    payloads = {
        "elevation": _readonly_payload(state.terrain.elevation_m, field_id="elevation", shape=shape),
        "water_depth": _readonly_payload(state.hydrology.water_depth_m, field_id="water_depth", shape=shape),
        "moisture": _readonly_payload(state.surface.moisture, field_id="moisture", shape=shape),
        "vegetation_density": _readonly_payload(state.surface.vegetation_density, field_id="vegetation_density", shape=shape),
    }

    final = candidate.final_validation
    assert final.ranking is not None
    try:
        data = DomainData(
            domain_data_version="0.1",
            identity=DomainIdentity(id=spec.id, label=spec.label),
            provenance=DomainProvenance(
                spec_schema_version=plan.source.spec_schema_version,
                spec_fingerprint=plan.source.spec_fingerprint,
                plan_fingerprint=plan_fingerprint,
                generation_config_fingerprint=semantic_generation_config_fingerprint(config),
                root_seed=plan.seed,
                accepted_attempt_index=candidate.attempt_index,
                generator=GeneratorIdentity(name="domain_generator", version=plan.source.generator_version),
                rng_version=RNG_VERSION,
            ),
            domain=DomainExtent(width_km=plan.domain.width_km, height_km=plan.domain.height_km),
            grid={"cell_size_km": plan.grid.cell_size_km, "rows": plan.grid.rows, "columns": plan.grid.columns},
            fields=_field_descriptors(shape),
            features=features,
            networks={"rivers": state.hydrology.river_network},
            validation=ValidationSummary(
                engine_invariants_passed=True,
                hard_constraints_passed=True,
                soft=final.ranking,
            ),
        )
    except ValidationError as exc:
        raise DomainAssemblyError("assembled DomainData failed serialized contract validation") from exc

    return DomainAssembly(data=data, field_payloads=payloads)


__all__ = ["DomainAssembly", "DomainAssemblyError", "assemble_domain", "semantic_generation_config_fingerprint"]
