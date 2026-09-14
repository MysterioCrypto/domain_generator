from __future__ import annotations

from pathlib import Path

import numpy as np

from domain_generator.application import (
    generate_domain_bundle,
    load_generation_request,
    load_preset_catalog,
    registry_for_request,
)


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "guide-renderer" / "demo-region"


def test_guide_demo_generates_visible_terrain_water_rivers_and_poi(tmp_path: Path) -> None:
    request = load_generation_request(DEMO / "request.json")
    catalog = load_preset_catalog(DEMO / "presets.json")
    output = tmp_path / "guide-demo"

    result = generate_domain_bundle(
        request=request,
        registry=registry_for_request(request, catalog),
        output_dir=output,
        render_guide_preview=True,
    )

    assert result.guide_preview == output / "preview" / "guide-map.png"
    assert result.guide_preview.is_file()
    assert result.guide_preview.stat().st_size > 10_000

    data = result.assembly.data
    assert data.identity.id == "guide-demo-region"
    assert {"ridge-01", "basin-01", "wetland-01", "settlement-01"}.issubset(data.features)
    assert any(feature.family.value == "hydro" for feature in data.features.values())
    assert data.networks["rivers"].segments

    elevation = result.assembly.field_payloads["elevation"]
    water = result.assembly.field_payloads["water_depth"]
    vegetation = result.assembly.field_payloads["vegetation_density"]
    assert float(np.max(elevation) - np.min(elevation)) > 300.0
    assert int(np.count_nonzero(water > 0.0)) > 0
    assert float(np.std(vegetation)) > 0.02
