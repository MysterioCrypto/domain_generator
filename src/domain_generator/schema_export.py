from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from pydantic import BaseModel

from .contracts import (
    BundleManifest,
    DomainData,
    DomainSpec,
    GenerationConfig,
    GenerationPlan,
    GenerationRequest,
    LayoutCandidate,
    ValidationResult,
)
from .presets import PresetCatalog

JSON_SCHEMA_DIALECT: Final = "https://json-schema.org/draft/2020-12/schema"

ROOT_CONTRACT_MODELS: Final[dict[str, type[BaseModel]]] = {
    "domain-spec.schema.json": DomainSpec,
    "generation-plan.schema.json": GenerationPlan,
    "layout-candidate.schema.json": LayoutCandidate,
    "validation-result.schema.json": ValidationResult,
    "generation-config.schema.json": GenerationConfig,
    "domain-data.schema.json": DomainData,
    "bundle-manifest.schema.json": BundleManifest,
    "generation-request.schema.json": GenerationRequest,
    "preset-catalog.schema.json": PresetCatalog,
}


def generate_schema_documents() -> dict[str, dict[str, object]]:
    """Generate JSON Schema documents for the public Core/Application 0.1 root contracts."""
    documents: dict[str, dict[str, object]] = {}
    for filename, model in ROOT_CONTRACT_MODELS.items():
        schema = model.model_json_schema(by_alias=True, mode="validation")
        schema["$schema"] = JSON_SCHEMA_DIALECT
        documents[filename] = schema
    return documents


def render_schema_document(schema: dict[str, object]) -> str:
    """Return a deterministic UTF-8 JSON representation suitable for snapshots."""
    return json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def write_schema_snapshots(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, schema in generate_schema_documents().items():
        (output_dir / filename).write_text(render_schema_document(schema), encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    write_schema_snapshots(repo_root / "schemas" / "v0.1")


if __name__ == "__main__":
    main()
