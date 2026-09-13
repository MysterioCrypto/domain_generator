from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Annotated, Any, Literal, Protocol

from pydantic import Field, StrictBool, StrictInt, StrictStr, TypeAdapter, ValidationError, model_validator

from .. import __version__
from ..application import (
    ApplicationInputError,
    ApplicationOutputError,
    GenerateApplicationResult,
    generate_domain_bundle,
    registry_from_catalog,
)
from ..compiler import CompilerError, compile_domain_spec
from ..contracts.application import GenerationRequest
from ..contracts.common import FrozenStrictModel
from ..contracts.plan import ChoiceParameter, FixedParameter, GeometryLayoutRecipe, RangeParameter
from ..pipeline import GenerationFailure
from ..presets import PresetCatalog, PresetRegistry


class LocalModelAdapterError(RuntimeError):
    """Base error for the provider-neutral local model integration layer."""


class LocalModelAdapterInputError(LocalModelAdapterError):
    """Caller-provided adapter inputs are invalid or internally inconsistent."""


class LocalModelHostError(LocalModelAdapterError):
    """The injected model host failed before producing a usable draft."""


class LocalModelEditPolicyError(LocalModelAdapterError):
    """A ready draft changed fields forbidden by the caller edit policy."""


class PresetGuideEntry(FrozenStrictModel):
    id: Annotated[StrictStr, Field(min_length=1)]
    summary: Annotated[StrictStr, Field(min_length=1)]
    keywords: tuple[StrictStr, ...] = ()
    parameter_notes: dict[StrictStr, StrictStr] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_keywords(self) -> "PresetGuideEntry":
        if len(set(self.keywords)) != len(self.keywords):
            raise ValueError("guide keywords must be unique")
        return self


class PresetGuideCatalog(FrozenStrictModel):
    preset_guide_version: Literal["0.1"]
    presets: tuple[PresetGuideEntry, ...] = ()

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "PresetGuideCatalog":
        ids = [entry.id for entry in self.presets]
        if len(ids) != len(set(ids)):
            raise ValueError("guide preset ids must be unique")
        return self


class ModelPresetParameter(FrozenStrictModel):
    name: Annotated[StrictStr, Field(min_length=1)]
    owner: Literal["layout", "effect"]
    kind: Literal["fixed", "range", "choice"]
    parameter_type: Annotated[StrictStr, Field(min_length=1)]
    value: bool | int | float | str | None = None
    min: int | float | None = None
    max: int | float | None = None
    values: tuple[StrictStr, ...] = ()
    sampler: StrictStr | None = None


class ModelPresetView(FrozenStrictModel):
    id: Annotated[StrictStr, Field(min_length=1)]
    family: Annotated[StrictStr, Field(min_length=1)]
    layout_mode: Annotated[StrictStr, Field(min_length=1)]
    geometry: Annotated[StrictStr, Field(min_length=1)]
    stage: Annotated[StrictStr, Field(min_length=1)]
    operator: Annotated[StrictStr, Field(min_length=1)]
    parameters: tuple[ModelPresetParameter, ...] = ()


class LocalModelEditPolicy(FrozenStrictModel):
    allow_domain_size: StrictBool = True
    allow_seed: StrictBool = False
    allow_simulation: StrictBool = False
    allow_hydrology: StrictBool = False
    allow_surface: StrictBool = False
    allow_generation_config: StrictBool = False


class PreflightDiagnostic(FrozenStrictModel):
    draft_index: Annotated[StrictInt, Field(ge=0, le=2)]
    code: Annotated[StrictStr, Field(min_length=1)]
    message: Annotated[StrictStr, Field(min_length=1)]


class ReadyDecision(FrozenStrictModel):
    decision_version: Literal["0.1"]
    status: Literal["ready"]
    request: GenerationRequest
    assumptions: tuple[StrictStr, ...] = ()


class NeedsClarificationDecision(FrozenStrictModel):
    decision_version: Literal["0.1"]
    status: Literal["needs_clarification"]
    questions: tuple[StrictStr, ...] = Field(min_length=1)


LocalModelDecision = Annotated[
    ReadyDecision | NeedsClarificationDecision,
    Field(discriminator="status"),
]
_DECISION_ADAPTER = TypeAdapter(LocalModelDecision)


class ModelAuthoringContext(FrozenStrictModel):
    context_version: Literal["0.1"] = "0.1"
    user_intent: Annotated[StrictStr, Field(min_length=1)]
    base_request: GenerationRequest
    presets: tuple[ModelPresetView, ...]
    guides: tuple[PresetGuideEntry, ...] = ()
    edit_policy: LocalModelEditPolicy
    draft_index: Annotated[StrictInt, Field(ge=0, le=2)]
    diagnostics: tuple[PreflightDiagnostic, ...] = ()


class LocalModelHost(Protocol):
    def create_decision(self, context: ModelAuthoringContext) -> object:
        """Return a JSON string, mapping, or typed LocalModelDecision draft."""
        ...


class LocalModelAudit(FrozenStrictModel):
    audit_version: Literal["0.1"] = "0.1"
    status: Literal["success", "needs_clarification", "preflight_failed", "generation_failed"]
    draft_count: Annotated[StrictInt, Field(ge=1, le=3)]
    repair_count: Annotated[StrictInt, Field(ge=0, le=2)]
    base_request_sha256: Annotated[StrictStr, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
    preset_catalog_sha256: Annotated[StrictStr, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
    preset_guide_sha256: Annotated[StrictStr, Field(pattern=r"^sha256:[0-9a-f]{64}$")] | None = None
    final_request_sha256: Annotated[StrictStr, Field(pattern=r"^sha256:[0-9a-f]{64}$")] | None = None
    diagnostics: tuple[PreflightDiagnostic, ...] = ()
    output_dir: StrictStr | None = None


@dataclass(frozen=True, slots=True)
class LocalModelAdapterResult:
    status: Literal["success", "needs_clarification", "preflight_failed", "generation_failed"]
    decision: ReadyDecision | NeedsClarificationDecision | None
    final_request: GenerationRequest | None
    generation: GenerateApplicationResult | None
    audit: LocalModelAudit


def _digest_model(model: object) -> str:
    if hasattr(model, "model_dump"):
        payload = model.model_dump(mode="json", by_alias=True, exclude_none=False)  # type: ignore[attr-defined]
    else:
        payload = model
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _parameter_names(preset: object) -> set[str]:
    layout = preset.layout
    names = set(layout.parameters) if isinstance(layout, GeometryLayoutRecipe) else set()
    names.update(preset.effect.parameters)
    return names


def validate_preset_guide(catalog: PresetCatalog, guide: PresetGuideCatalog | None) -> None:
    if guide is None:
        return
    canonical = {preset.id: preset for preset in catalog.presets}
    for entry in guide.presets:
        preset = canonical.get(entry.id)
        if preset is None:
            raise LocalModelAdapterInputError(
                f"guide references unknown canonical preset {entry.id!r}"
            )
        unknown = set(entry.parameter_notes) - _parameter_names(preset)
        if unknown:
            raise LocalModelAdapterInputError(
                f"guide for preset {entry.id!r} references unknown parameters: {sorted(unknown)}"
            )


def _parameter_view(name: str, owner: Literal["layout", "effect"], parameter: object) -> ModelPresetParameter:
    if isinstance(parameter, FixedParameter):
        return ModelPresetParameter(
            name=name,
            owner=owner,
            kind="fixed",
            parameter_type=parameter.type.value,
            value=parameter.value,
        )
    if isinstance(parameter, RangeParameter):
        return ModelPresetParameter(
            name=name,
            owner=owner,
            kind="range",
            parameter_type=parameter.type.value,
            min=parameter.min,
            max=parameter.max,
            sampler=parameter.sampler.type,
        )
    if isinstance(parameter, ChoiceParameter):
        return ModelPresetParameter(
            name=name,
            owner=owner,
            kind="choice",
            parameter_type=parameter.type.value,
            values=parameter.values,
            sampler=parameter.sampler.type,
        )
    raise TypeError(f"unsupported resolved parameter type: {type(parameter).__name__}")


def build_model_preset_projection(catalog: PresetCatalog) -> tuple[ModelPresetView, ...]:
    views: list[ModelPresetView] = []
    for preset in sorted(catalog.presets, key=lambda item: item.id):
        parameters: list[ModelPresetParameter] = []
        if isinstance(preset.layout, GeometryLayoutRecipe):
            for name in sorted(preset.layout.parameters):
                parameters.append(_parameter_view(name, "layout", preset.layout.parameters[name]))
            geometry = preset.layout.shape.value
        else:
            geometry = preset.layout.final_shape.value
        for name in sorted(preset.effect.parameters):
            parameters.append(_parameter_view(name, "effect", preset.effect.parameters[name]))
        views.append(
            ModelPresetView(
                id=preset.id,
                family=preset.family.value,
                layout_mode=preset.layout.mode,
                geometry=geometry,
                stage=preset.effect.stage.value,
                operator=preset.effect.operator,
                parameters=tuple(parameters),
            )
        )
    return tuple(views)


def _guide_entries(guide: PresetGuideCatalog | None) -> tuple[PresetGuideEntry, ...]:
    if guide is None:
        return ()
    return tuple(sorted(guide.presets, key=lambda entry: entry.id))


def build_model_authoring_context(
    *,
    user_intent: str,
    base_request: GenerationRequest,
    catalog: PresetCatalog,
    guide: PresetGuideCatalog | None = None,
    edit_policy: LocalModelEditPolicy | None = None,
    draft_index: int = 0,
    diagnostics: tuple[PreflightDiagnostic, ...] = (),
) -> ModelAuthoringContext:
    if not isinstance(user_intent, str) or not user_intent.strip():
        raise LocalModelAdapterInputError("user_intent must be a non-empty string")
    validate_preset_guide(catalog, guide)
    return ModelAuthoringContext(
        user_intent=user_intent,
        base_request=base_request,
        presets=build_model_preset_projection(catalog),
        guides=_guide_entries(guide),
        edit_policy=edit_policy or LocalModelEditPolicy(),
        draft_index=draft_index,
        diagnostics=diagnostics,
    )


def parse_local_model_decision(payload: object) -> ReadyDecision | NeedsClarificationDecision:
    if isinstance(payload, (ReadyDecision, NeedsClarificationDecision)):
        return payload
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise LocalModelAdapterError(
                f"model decision is invalid JSON at line {exc.lineno}, column {exc.colno}"
            ) from exc
    if isinstance(payload, Mapping):
        payload = dict(payload)
    try:
        return _DECISION_ADAPTER.validate_python(payload)
    except ValidationError as exc:
        raise LocalModelAdapterError(f"model decision failed contract validation: {exc}") from exc


def validate_request_edit_policy(
    *,
    base_request: GenerationRequest,
    request: GenerationRequest,
    policy: LocalModelEditPolicy,
) -> None:
    base = base_request.domain_spec
    candidate = request.domain_spec
    forbidden: list[str] = []
    if not policy.allow_domain_size and candidate.domain != base.domain:
        forbidden.append("domain_spec.domain")
    if not policy.allow_seed and candidate.seed != base.seed:
        forbidden.append("domain_spec.seed")
    if not policy.allow_simulation and candidate.simulation != base.simulation:
        forbidden.append("domain_spec.simulation")
    if not policy.allow_hydrology and candidate.hydrology != base.hydrology:
        forbidden.append("domain_spec.hydrology")
    if not policy.allow_surface and candidate.surface != base.surface:
        forbidden.append("domain_spec.surface")
    if not policy.allow_generation_config and request.generation_config != base_request.generation_config:
        forbidden.append("generation_config")
    if forbidden:
        raise LocalModelEditPolicyError(
            "model draft changed fields forbidden by edit policy: " + ", ".join(forbidden)
        )


def _preflight(
    *,
    base_request: GenerationRequest,
    request: GenerationRequest,
    catalog: PresetCatalog,
    policy: LocalModelEditPolicy,
) -> PresetRegistry:
    validate_request_edit_policy(base_request=base_request, request=request, policy=policy)
    try:
        registry = registry_from_catalog(catalog)
    except ApplicationInputError as exc:
        raise LocalModelAdapterInputError(str(exc)) from exc
    compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version=__version__,
    )
    return registry


def _diagnostic(draft_index: int, exc: Exception) -> PreflightDiagnostic:
    if isinstance(exc, LocalModelEditPolicyError):
        code = "edit_policy"
    elif isinstance(exc, CompilerError):
        code = "compiler"
    elif isinstance(exc, LocalModelAdapterError):
        code = "decision_validation"
    else:
        code = "preflight"
    return PreflightDiagnostic(draft_index=draft_index, code=code, message=str(exc))


def _audit(
    *,
    status: Literal["success", "needs_clarification", "preflight_failed", "generation_failed"],
    draft_count: int,
    base_request: GenerationRequest,
    catalog: PresetCatalog,
    guide: PresetGuideCatalog | None,
    final_request: GenerationRequest | None,
    diagnostics: tuple[PreflightDiagnostic, ...],
    output_dir: Path | None = None,
) -> LocalModelAudit:
    return LocalModelAudit(
        status=status,
        draft_count=draft_count,
        repair_count=max(0, draft_count - 1),
        base_request_sha256=_digest_model(base_request),
        preset_catalog_sha256=_digest_model(catalog),
        preset_guide_sha256=_digest_model(guide) if guide is not None else None,
        final_request_sha256=_digest_model(final_request) if final_request is not None else None,
        diagnostics=diagnostics,
        output_dir=str(output_dir) if output_dir is not None else None,
    )


def run_local_model_adapter(
    *,
    user_intent: str,
    base_request: GenerationRequest,
    catalog: PresetCatalog,
    model: LocalModelHost,
    output_dir: Path,
    guide: PresetGuideCatalog | None = None,
    edit_policy: LocalModelEditPolicy | None = None,
    render_preview: bool = False,
    max_repairs: int = 2,
) -> LocalModelAdapterResult:
    """Author, preflight, and execute one semantic generation through the canonical application API."""
    if isinstance(max_repairs, bool) or not isinstance(max_repairs, int) or not 0 <= max_repairs <= 2:
        raise LocalModelAdapterInputError("max_repairs must be an integer in [0, 2]")
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be pathlib.Path")
    if not isinstance(render_preview, bool):
        raise TypeError("render_preview must be bool")

    policy = edit_policy or LocalModelEditPolicy()
    validate_preset_guide(catalog, guide)
    try:
        registry_from_catalog(catalog)
    except ApplicationInputError as exc:
        raise LocalModelAdapterInputError(str(exc)) from exc

    diagnostics: tuple[PreflightDiagnostic, ...] = ()
    last_decision: ReadyDecision | NeedsClarificationDecision | None = None

    for draft_index in range(max_repairs + 1):
        context = build_model_authoring_context(
            user_intent=user_intent,
            base_request=base_request,
            catalog=catalog,
            guide=guide,
            edit_policy=policy,
            draft_index=draft_index,
            diagnostics=diagnostics,
        )
        try:
            raw = model.create_decision(context)
        except Exception as exc:  # provider boundary: preserve cause, do not retry hidden host failures
            raise LocalModelHostError("local model host failed while producing a decision") from exc

        try:
            decision = parse_local_model_decision(raw)
            last_decision = decision
            if isinstance(decision, NeedsClarificationDecision):
                audit = _audit(
                    status="needs_clarification",
                    draft_count=draft_index + 1,
                    base_request=base_request,
                    catalog=catalog,
                    guide=guide,
                    final_request=None,
                    diagnostics=diagnostics,
                )
                return LocalModelAdapterResult(
                    status="needs_clarification",
                    decision=decision,
                    final_request=None,
                    generation=None,
                    audit=audit,
                )

            registry = _preflight(
                base_request=base_request,
                request=decision.request,
                catalog=catalog,
                policy=policy,
            )
        except (LocalModelAdapterError, CompilerError) as exc:
            diagnostics = diagnostics + (_diagnostic(draft_index, exc),)
            if draft_index < max_repairs:
                continue
            audit = _audit(
                status="preflight_failed",
                draft_count=draft_index + 1,
                base_request=base_request,
                catalog=catalog,
                guide=guide,
                final_request=last_decision.request if isinstance(last_decision, ReadyDecision) else None,
                diagnostics=diagnostics,
            )
            return LocalModelAdapterResult(
                status="preflight_failed",
                decision=last_decision,
                final_request=last_decision.request if isinstance(last_decision, ReadyDecision) else None,
                generation=None,
                audit=audit,
            )

        try:
            generation = generate_domain_bundle(
                request=decision.request,
                registry=registry,
                output_dir=output_dir,
                render_preview=render_preview,
            )
        except (GenerationFailure, ApplicationOutputError) as exc:
            generation_diagnostic = PreflightDiagnostic(
                draft_index=draft_index,
                code="generation",
                message=str(exc),
            )
            final_diagnostics = diagnostics + (generation_diagnostic,)
            audit = _audit(
                status="generation_failed",
                draft_count=draft_index + 1,
                base_request=base_request,
                catalog=catalog,
                guide=guide,
                final_request=decision.request,
                diagnostics=final_diagnostics,
            )
            return LocalModelAdapterResult(
                status="generation_failed",
                decision=decision,
                final_request=decision.request,
                generation=None,
                audit=audit,
            )

        audit = _audit(
            status="success",
            draft_count=draft_index + 1,
            base_request=base_request,
            catalog=catalog,
            guide=guide,
            final_request=decision.request,
            diagnostics=diagnostics,
            output_dir=generation.output_dir,
        )
        return LocalModelAdapterResult(
            status="success",
            decision=decision,
            final_request=decision.request,
            generation=generation,
            audit=audit,
        )

    raise AssertionError("repair loop must return from a bounded range")


__all__ = [
    "LocalModelAdapterError",
    "LocalModelAdapterInputError",
    "LocalModelAdapterResult",
    "LocalModelAudit",
    "LocalModelDecision",
    "LocalModelEditPolicy",
    "LocalModelEditPolicyError",
    "LocalModelHost",
    "LocalModelHostError",
    "ModelAuthoringContext",
    "ModelPresetParameter",
    "ModelPresetView",
    "NeedsClarificationDecision",
    "PreflightDiagnostic",
    "PresetGuideCatalog",
    "PresetGuideEntry",
    "ReadyDecision",
    "build_model_authoring_context",
    "build_model_preset_projection",
    "parse_local_model_decision",
    "run_local_model_adapter",
    "validate_preset_guide",
    "validate_request_edit_policy",
]
