from __future__ import annotations

import json
from hashlib import sha256

from .compile import (
    CompilerError,
    compile_domain_spec as _compile_domain_spec_v01,
    semantic_plan_fingerprint as _semantic_plan_fingerprint_v01,
)
from ..contracts.plan import GenerationPlan, PlanClimate, PlanMarine
from ..contracts.spec import DomainSpec
from ..contracts.terrain import PlanTerrain, PlanTerrainNoiseLayer
from ..presets import PresetRegistry


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _legacy_shadow(spec: DomainSpec) -> DomainSpec:
    legacy_surface = spec.surface.model_copy(update={"climate": None})
    legacy_hydrology = spec.hydrology.model_copy(update={"marine": None})
    return spec.model_copy(
        update={
            "schema_version": "0.1",
            "terrain": None,
            "hydrology": legacy_hydrology,
            "surface": legacy_surface,
        }
    )


def domain_spec_fingerprint(spec: DomainSpec) -> str:
    if spec.schema_version == "0.1":
        payload = spec.model_dump(mode="json", by_alias=True, exclude_none=False)
        payload.pop("terrain", None)
        hydrology = payload.get("hydrology")
        if isinstance(hydrology, dict) and hydrology.get("marine") is None:
            hydrology.pop("marine", None)
        if isinstance(payload.get("surface"), dict):
            payload["surface"].pop("climate", None)
    else:
        payload = spec.model_dump(mode="json", by_alias=True, exclude_none=False)
        # C4 compatibility: the frozen prealpha 0.2 contract had no
        # climate.seasonality key. Preserve the exact historical fingerprint
        # when the additive seasonality recipe is absent, while retaining the
        # key as semantic input when it is explicitly configured.
        hydrology = payload.get("hydrology")
        if isinstance(hydrology, dict) and hydrology.get("marine") is None:
            hydrology.pop("marine", None)
        surface = payload.get("surface")
        if isinstance(surface, dict):
            climate = surface.get("climate")
            if isinstance(climate, dict):
                if climate.get("seasonality") is None:
                    climate.pop("seasonality", None)
                if climate.get("classification") is None:
                    climate.pop("classification", None)
    return "sha256:" + sha256(_canonical_json_bytes(payload)).hexdigest()


def semantic_plan_fingerprint(plan: GenerationPlan) -> str:
    if plan.plan_version == "0.1":
        return _semantic_plan_fingerprint_v01(plan)

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

    if plan.terrain is None:
        raise CompilerError("GenerationPlan 0.2 requires terrain plan")

    surface_payload = plan.surface.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    )
    climate_payload = surface_payload.get("climate")
    if isinstance(climate_payload, dict):
        if climate_payload.get("seasonality") is None:
            climate_payload.pop("seasonality", None)
        if climate_payload.get("classification") is None:
            climate_payload.pop("classification", None)

    hydrology_payload = plan.hydrology.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    )
    if hydrology_payload.get("marine") is None:
        hydrology_payload.pop("marine", None)

    payload = {
        "plan_version": plan.plan_version,
        "seed": plan.seed,
        "domain": plan.domain.model_dump(mode="json"),
        "grid": plan.grid.model_dump(mode="json"),
        "terrain": plan.terrain.model_dump(mode="json"),
        "hydrology": hydrology_payload,
        "surface": surface_payload,
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
    if spec.schema_version == "0.1":
        return _compile_domain_spec_v01(spec, registry=registry, generator_version=generator_version)

    if spec.terrain is None:
        raise CompilerError("DomainSpec 0.2 requires terrain configuration")

    legacy = _compile_domain_spec_v01(
        _legacy_shadow(spec),
        registry=registry,
        generator_version=generator_version,
    )
    if spec.surface.climate is None:
        raise CompilerError("DomainSpec 0.2 requires surface.climate configuration")

    terrain = PlanTerrain(
        base_elevation_m=spec.terrain.base_elevation_m,
        noise_layers=tuple(
            PlanTerrainNoiseLayer(
                id=layer.id,
                scale_km=layer.scale_km,
                amplitude_m=layer.amplitude_m,
            )
            for layer in spec.terrain.noise_layers
        ),
    )
    climate = PlanClimate(**spec.surface.climate.model_dump(mode="python"))
    surface = legacy.surface.model_copy(update={"climate": climate})
    marine = (
        PlanMarine(**spec.hydrology.marine.model_dump(mode="python"))
        if spec.hydrology.marine is not None
        else None
    )
    hydrology = legacy.hydrology.model_copy(update={"marine": marine})
    source = legacy.source.model_copy(
        update={
            "spec_schema_version": "0.2",
            "spec_fingerprint": domain_spec_fingerprint(spec),
        }
    )
    payload = legacy.model_dump(mode="python", by_alias=True, exclude_none=False)
    payload.update(
        {
            "plan_version": "0.2",
            "source": source,
            "terrain": terrain,
            "hydrology": hydrology,
            "surface": surface,
        }
    )
    return GenerationPlan.model_validate(payload)


__all__ = [
    "CompilerError",
    "compile_domain_spec",
    "domain_spec_fingerprint",
    "semantic_plan_fingerprint",
]
