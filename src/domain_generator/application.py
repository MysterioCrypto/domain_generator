from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import tempfile
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from . import __version__
from .assembly import DomainAssembly, assemble_domain
from .bundle_export import DomainBundleExportError, export_domain_bundle
from .capabilities import CORE_OPERATOR_IDS
from .compiler import compile_domain_spec
from .contracts import BundleManifest, GenerationConfig, GenerationRequest, ValidationStage
from .contracts.spec import DomainSpec
from .hydrology import hydrology_stage
from .layout import layout_stage
from .pipeline import StageStep, run_generation
from .pipeline.final import final_stage
from .poi import placement_stage
from .presets import PresetCatalog, PresetRegistry, PresetRegistryError
from .surface import surface_stage
from .terrain import terrain_stage


class ApplicationInputError(ValueError):
    """Application input cannot be parsed or converted into validated runtime contracts."""


class ApplicationOutputError(RuntimeError):
    """Requested application artifacts cannot be published safely."""


@dataclass(frozen=True, slots=True)
class GenerateApplicationResult:
    assembly: DomainAssembly
    output_dir: Path
    manifest: BundleManifest
    technical_preview: Path | None

    def __post_init__(self) -> None:
        if not isinstance(self.assembly, DomainAssembly):
            raise TypeError("assembly must be DomainAssembly")
        if not isinstance(self.output_dir, Path):
            raise TypeError("output_dir must be pathlib.Path")
        if not isinstance(self.manifest, BundleManifest):
            raise TypeError("manifest must be BundleManifest")
        if self.technical_preview is not None and not isinstance(self.technical_preview, Path):
            raise TypeError("technical_preview must be pathlib.Path or None")


_CANONICAL_STEPS: tuple[StageStep, ...] = (
    StageStep(stage=ValidationStage.LAYOUT, handler=layout_stage),
    StageStep(stage=ValidationStage.TERRAIN, handler=terrain_stage),
    StageStep(stage=ValidationStage.HYDROLOGY, handler=hydrology_stage),
    StageStep(stage=ValidationStage.SURFACE, handler=surface_stage),
    StageStep(stage=ValidationStage.PLACEMENT, handler=placement_stage),
    StageStep(stage=ValidationStage.FINAL, handler=final_stage),
)


ModelT = TypeVar("ModelT", bound=BaseModel)


def _load_json_model(path: Path, model: type[ModelT], *, description: str) -> ModelT:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    if not path.is_file():
        raise ApplicationInputError(f"{description} file does not exist or is not a file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ApplicationInputError(f"{description} must be UTF-8 JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ApplicationInputError(
            f"{description} contains invalid JSON at line {exc.lineno}, column {exc.colno}: {path}"
        ) from exc
    except OSError as exc:
        raise ApplicationInputError(f"failed to read {description}: {path}") from exc

    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise ApplicationInputError(f"{description} failed contract validation: {exc}") from exc


def load_generation_request(path: Path) -> GenerationRequest:
    return _load_json_model(path, GenerationRequest, description="generation request")


def load_preset_catalog(path: Path) -> PresetCatalog:
    return _load_json_model(path, PresetCatalog, description="preset catalog")


def registry_from_catalog(catalog: PresetCatalog) -> PresetRegistry:
    if not isinstance(catalog, PresetCatalog):
        raise TypeError("catalog must be PresetCatalog")
    try:
        return PresetRegistry(catalog.presets, operator_ids=CORE_OPERATOR_IDS)
    except PresetRegistryError as exc:
        raise ApplicationInputError(f"preset catalog is incompatible with Core capabilities: {exc}") from exc


def registry_for_request(
    request: GenerationRequest,
    catalog: PresetCatalog | None,
) -> PresetRegistry:
    if not isinstance(request, GenerationRequest):
        raise TypeError("request must be GenerationRequest")
    if request.domain_spec.features and catalog is None:
        raise ApplicationInputError("--presets is required when domain_spec.features is non-empty")
    if catalog is None:
        catalog = PresetCatalog(preset_catalog_version="0.1", presets=())
    return registry_from_catalog(catalog)


def generate_domain(
    *,
    spec: DomainSpec,
    config: GenerationConfig,
    registry: PresetRegistry,
) -> DomainAssembly:
    """Run the canonical in-memory Core pipeline and assemble the selected domain."""
    if not isinstance(spec, DomainSpec):
        raise TypeError("spec must be DomainSpec")
    if not isinstance(config, GenerationConfig):
        raise TypeError("config must be GenerationConfig")
    if not isinstance(registry, PresetRegistry):
        raise TypeError("registry must be PresetRegistry")

    plan = compile_domain_spec(
        spec,
        registry=registry,
        generator_version=__version__,
    )
    run = run_generation(
        plan=plan,
        config=config,
        steps=_CANONICAL_STEPS,
    )
    return assemble_domain(
        spec=spec,
        plan=plan,
        config=config,
        candidate=run.selected,
    )


def _validate_output_target(output_dir: Path) -> None:
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be pathlib.Path")
    if output_dir.exists():
        raise ApplicationOutputError("output directory already exists")
    parent = output_dir.parent
    if not parent.exists() or not parent.is_dir():
        raise ApplicationOutputError("output parent must already exist and be a directory")
    if not output_dir.name:
        raise ApplicationOutputError("output directory name must be non-empty")


def generate_domain_bundle(
    *,
    request: GenerationRequest,
    registry: PresetRegistry,
    output_dir: Path,
    render_preview: bool = False,
) -> GenerateApplicationResult:
    """Generate and atomically publish the complete requested application result."""
    if not isinstance(request, GenerationRequest):
        raise TypeError("request must be GenerationRequest")
    if not isinstance(registry, PresetRegistry):
        raise TypeError("registry must be PresetRegistry")
    if not isinstance(render_preview, bool):
        raise TypeError("render_preview must be bool")

    _validate_output_target(output_dir)
    assembly = generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry,
    )

    staging_parent: Path | None = None
    try:
        staging_parent = Path(
            tempfile.mkdtemp(
                prefix=f".{output_dir.name}.app-tmp-",
                dir=output_dir.parent,
            )
        )
        bundle_root = staging_parent / "bundle"
        try:
            exported = export_domain_bundle(assembly=assembly, output_dir=bundle_root)
        except DomainBundleExportError as exc:
            raise ApplicationOutputError("failed to export canonical domain bundle") from exc

        preview_was_rendered = False
        if render_preview:
            try:
                from .technical_renderer import TechnicalRenderError, render_technical_map

                render_technical_map(
                    assembly=assembly,
                    output_path=bundle_root / "preview" / "technical-map.png",
                )
                preview_was_rendered = True
            except ImportError as exc:
                raise ApplicationOutputError(
                    "technical preview requires optional render dependencies; install domain-generator[render]"
                ) from exc
            except TechnicalRenderError as exc:
                raise ApplicationOutputError("failed to render requested technical preview") from exc

        if output_dir.exists():
            raise ApplicationOutputError("output directory appeared during generation; refusing to overwrite")
        try:
            bundle_root.rename(output_dir)
        except OSError as exc:
            raise ApplicationOutputError("failed to publish generated application output") from exc

        preview_path = output_dir / "preview" / "technical-map.png" if preview_was_rendered else None
        return GenerateApplicationResult(
            assembly=assembly,
            output_dir=output_dir,
            manifest=exported.manifest,
            technical_preview=preview_path,
        )
    except ApplicationOutputError:
        raise
    except OSError as exc:
        raise ApplicationOutputError("failed to create or clean application staging directory") from exc
    finally:
        if staging_parent is not None and staging_parent.exists():
            shutil.rmtree(staging_parent, ignore_errors=True)


__all__ = [
    "ApplicationInputError",
    "ApplicationOutputError",
    "GenerateApplicationResult",
    "generate_domain",
    "generate_domain_bundle",
    "load_generation_request",
    "load_preset_catalog",
    "registry_for_request",
    "registry_from_catalog",
]
