from __future__ import annotations

from pathlib import Path

from domain_generator.application import (
    generate_domain_bundle,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "terrain-v02" / "checkpoint"


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
