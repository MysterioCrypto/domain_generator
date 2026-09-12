from __future__ import annotations

from decimal import Decimal

from ..contracts.plan import GenerationPlan, PlanDomain, PlanGrid, PlanHydrology, PlanSource, ResolvedFeature
from ..contracts.spec import DomainSpec
from ..pipeline.rng import UINT64_MAX
from ..presets import PresetRegistry, PresetRegistryError
from .compile import (
    CompilerError,
    _canonical_json_bytes,
    _compile_hard_constraint,
    _resolve_feature,
    domain_spec_fingerprint,
)
from hashlib import sha256


def semantic_plan_fingerprint(plan: GenerationPlan) -> str:
    """Fingerprint executable Plan semantics, including root hydrology recipe."""
    features: list[dict[str, object]] = []
    for feature in sorted(plan.features, key=lambda item: item.id):
        features.append(
            {
                "id": feature.id,
                "family": feature.family.value,
                "layout": feature.layout.model_dump(mode="json", by_alias=True, exclude_none=False),
                "effect": feature.effect.model_dump(mode="json", by_alias=True, exclude_none=False),
            }
        )

    constraints: list[dict[str, object]] = []
    for constraint in sorted(plan.constraints, key=lambda item: item.id):
        item = constraint.model_dump(mode="json", by_alias=True, exclude_none=False)
        item.pop("source_relation", None)
        constraints.append(item)

    payload = {
        "plan_version": plan.plan_version,
        "seed": plan.seed,
        "domain": plan.domain.model_dump(mode="json"),
        "grid": plan.grid.model_dump(mode="json"),
        "hydrology": plan.hydrology.model_dump(mode="json"),
        "features": features,
        "constraints": constraints,
    }
    return "sha256:" + sha256(_canonical_json_bytes(payload)).hexdigest()


def compile_domain_spec(
    spec: DomainSpec,
    *,
    registry: PresetRegistry,
    generator_version: str,
) -> GenerationPlan:
    """Compile a structurally valid DomainSpec into an immutable resolved plan."""
    if not isinstance(generator_version, str) or not generator_version:
        raise CompilerError("generator_version must be a non-empty string")
    if isinstance(spec.seed, bool) or not 0 <= spec.seed <= UINT64_MAX:
        raise CompilerError("DomainSpec seed must be in unsigned uint64 range for RNG v1")

    resolved_features: list[ResolvedFeature] = []
    for feature in spec.features:
        try:
            preset = registry.get(feature.preset)
        except PresetRegistryError as exc:
            raise CompilerError(str(exc)) from exc
        resolved_features.append(_resolve_feature(feature, preset))

    features_by_id = {feature.id: feature for feature in resolved_features}
    width_km = spec.domain.size.width_km
    height_km = spec.domain.size.height_km
    compiled_constraints = tuple(
        _compile_hard_constraint(
            constraint,
            features_by_id=features_by_id,
            width_km=width_km,
            height_km=height_km,
        )
        for constraint in spec.constraints
    )

    cell = Decimal(str(spec.simulation.cell_size_km))
    columns = int(Decimal(str(width_km)) / cell)
    rows = int(Decimal(str(height_km)) / cell)

    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id=spec.id,
            spec_schema_version="0.1",
            spec_fingerprint=domain_spec_fingerprint(spec),
            generator_version=generator_version,
        ),
        seed=spec.seed,
        domain=PlanDomain(width_km=width_km, height_km=height_km),
        grid=PlanGrid(
            cell_size_km=spec.simulation.cell_size_km,
            rows=rows,
            columns=columns,
        ),
        hydrology=PlanHydrology(
            stream_threshold_km2=spec.hydrology.stream_threshold_km2,
            lake_min_area_km2=spec.hydrology.lake_min_area_km2,
            lake_min_depth_m=spec.hydrology.lake_min_depth_m,
        ),
        features=tuple(resolved_features),
        constraints=compiled_constraints,
    )
