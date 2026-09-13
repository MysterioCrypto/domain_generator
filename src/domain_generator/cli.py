from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .application import (
    ApplicationInputError,
    ApplicationOutputError,
    GenerateApplicationResult,
    generate_domain_bundle,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)
from .assembly import DomainAssemblyError
from .compiler import CompilerError
from .hydrology import HydrologyCapabilityError
from .layout import LayoutCapabilityError, ReservationCapabilityError
from .pipeline import GenerationFailure, PipelineInvariantError
from .pipeline.final import FinalValidationCapabilityError
from .poi import (
    PlacementCandidateCapabilityError,
    PlacementSelectionCapabilityError,
    SiteMetricCapabilityError,
)
from .surface import SurfaceCapabilityError
from .terrain import TerrainCapabilityError


EXIT_SUCCESS = 0
EXIT_INVALID_ARGUMENTS = 2
EXIT_INPUT_ERROR = 3
EXIT_GENERATION_ERROR = 4
EXIT_OUTPUT_ERROR = 5
EXIT_INTERNAL_ERROR = 70


_GENERATION_ERRORS = (
    CompilerError,
    GenerationFailure,
    LayoutCapabilityError,
    ReservationCapabilityError,
    TerrainCapabilityError,
    HydrologyCapabilityError,
    SurfaceCapabilityError,
    PlacementCandidateCapabilityError,
    PlacementSelectionCapabilityError,
    SiteMetricCapabilityError,
    FinalValidationCapabilityError,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="domain-generator",
        description="Deterministic procedural domain generation application",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="generate one domain bundle from a JSON request")
    generate.add_argument("request", type=Path, help="path to GenerationRequest v0.1 JSON")
    generate.add_argument("--presets", type=Path, default=None, help="path to PresetCatalog v0.1 JSON")
    generate.add_argument("--output", type=Path, required=True, help="new output directory to publish")
    generate.add_argument(
        "--preview",
        action="store_true",
        help="also render preview/technical-map.png (requires domain-generator[render])",
    )
    return parser


def _success_payload(result: GenerateApplicationResult) -> dict[str, object]:
    preview: str | None = None
    if result.technical_preview is not None:
        preview = result.technical_preview.relative_to(result.output_dir).as_posix()
    return {
        "accepted_attempt_index": result.assembly.data.provenance.accepted_attempt_index,
        "domain_id": result.assembly.data.identity.id,
        "output_dir": str(result.output_dir),
        "status": "ok",
        "technical_preview": preview,
    }


def _run_generate(args: argparse.Namespace) -> int:
    try:
        request = load_generation_request(args.request)
        catalog = load_preset_catalog(args.presets) if args.presets is not None else None
        registry = registry_for_request(request, catalog)
        result = generate_domain_bundle(
            request=request,
            registry=registry,
            output_dir=args.output,
            render_preview=args.preview,
        )
    except ApplicationInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except PipelineInvariantError as exc:
        print(f"internal error: {exc}", file=sys.stderr)
        return EXIT_INTERNAL_ERROR
    except _GENERATION_ERRORS as exc:
        print(f"generation error: {exc}", file=sys.stderr)
        return EXIT_GENERATION_ERROR
    except (DomainAssemblyError, ApplicationOutputError) as exc:
        print(f"output error: {exc}", file=sys.stderr)
        return EXIT_OUTPUT_ERROR
    except Exception as exc:
        print(f"internal error: {exc}", file=sys.stderr)
        return EXIT_INTERNAL_ERROR

    print(
        json.dumps(
            _success_payload(result),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return EXIT_SUCCESS


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "generate":
        return _run_generate(args)
    raise RuntimeError(f"unsupported command: {args.command!r}")


__all__ = [
    "EXIT_GENERATION_ERROR",
    "EXIT_INPUT_ERROR",
    "EXIT_INTERNAL_ERROR",
    "EXIT_INVALID_ARGUMENTS",
    "EXIT_OUTPUT_ERROR",
    "EXIT_SUCCESS",
    "main",
]
