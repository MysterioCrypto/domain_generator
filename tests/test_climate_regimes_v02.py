from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from domain_generator.application import (
    generate_domain,
    load_preset_catalog,
    registry_for_request,
)
from domain_generator.compiler import (
    compile_domain_spec,
    domain_spec_fingerprint,
    semantic_plan_fingerprint,
)
from domain_generator.contracts import GenerationRequest
from domain_generator.contracts.data import FieldRole
from domain_generator.surface import (
    KOPPEN_GEIGER_CODE_TO_LABEL,
    KOPPEN_GEIGER_LABEL_TO_CODE,
    KOPPEN_GEIGER_SCHEME_ID,
    classify_koppen_geiger_local_season,
    local_cold_half_year_indices,
    local_warm_half_year_indices,
)


ROOT = Path(__file__).resolve().parents[1]
A08 = ROOT / "tests" / "acceptance" / "cases" / "a08-core-v02-integrated"


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _a08_request(*, classification: bool, seasonality: bool = True) -> GenerationRequest:
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    climate = payload["domain_spec"]["surface"]["climate"]
    if seasonality:
        climate["seasonality"] = {
            "temperature_seasonal_amplitude_c": 7.0,
            "temperature_peak_month": 7,
            "precipitation_seasonality_log_amplitude": 1.0,
            "precipitation_peak_month": 1,
        }
    if classification:
        climate["classification"] = {
            "scheme": KOPPEN_GEIGER_SCHEME_ID,
        }
    return GenerationRequest.model_validate(payload)


def _generate(request: GenerationRequest):
    catalog = load_preset_catalog(A08 / "presets.json")
    return generate_domain(
        spec=request.domain_spec,
        config=request.generation_config,
        registry=registry_for_request(request, catalog),
    )


def _label(
    monthly_temperature_c: list[float],
    monthly_precipitation_mm: list[float],
    *,
    peak_month: int = 7,
) -> str:
    temperature = np.asarray(monthly_temperature_c, dtype=np.float32).reshape(12, 1, 1)
    precipitation = np.asarray(monthly_precipitation_mm, dtype=np.float32).reshape(12, 1, 1)
    annual_temperature = np.mean(
        temperature.astype(np.float64),
        axis=0,
        dtype=np.float64,
    ).astype(np.float32)
    annual_precipitation = np.sum(
        precipitation.astype(np.float64),
        axis=0,
        dtype=np.float64,
    ).astype(np.float32)
    code = classify_koppen_geiger_local_season(
        monthly_mean_temperature_c=temperature,
        monthly_precipitation_mm=precipitation,
        annual_mean_temperature_c=annual_temperature,
        annual_precipitation_mm=annual_precipitation,
        temperature_peak_month=peak_month,
    )
    return KOPPEN_GEIGER_CODE_TO_LABEL[int(code[0, 0])]


C_TEMP_A = [5, 6, 8, 12, 17, 21, 24, 23, 18, 13, 8, 6]
C_TEMP_B = [3, 4, 6, 10, 14, 17, 19, 18, 14, 10, 6, 4]
C_TEMP_C = [2, 3, 4, 5, 7, 9, 12, 9, 7, 5, 4, 3]

D_TEMP_A = [-10, -8, -3, 5, 12, 18, 23, 21, 14, 6, -2, -8]
D_TEMP_B = [-15, -12, -5, 2, 8, 13, 18, 16, 11, 4, -5, -12]
D_TEMP_C = [-20, -18, -12, -5, 2, 7, 12, 8, 3, -4, -12, -18]
D_TEMP_D = [-45, -40, -30, -15, -2, 5, 12, 7, 0, -10, -25, -40]

P_F = [100] * 12
P_S = [100, 100, 100, 100, 100, 100, 10, 100, 100, 100, 100, 100]
P_W = [5, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]


def test_k01_classification_is_opt_in_only() -> None:
    assembly = _generate(_a08_request(classification=False))
    assert "climate_regime_koppen_geiger" not in assembly.data.fields
    assert "climate_regime_koppen_geiger" not in assembly.field_payloads


def test_k02_classification_requires_seasonality() -> None:
    payload = json.loads((A08 / "request.json").read_text(encoding="utf-8"))
    payload["domain_spec"]["surface"]["climate"]["classification"] = {
        "scheme": KOPPEN_GEIGER_SCHEME_ID,
    }
    with pytest.raises(
        ValidationError,
        match="climate classification requires climate.seasonality",
    ):
        GenerationRequest.model_validate(payload)


def test_k03_representative_classification_is_exhaustive_1_to_30() -> None:
    assembly = _generate(_a08_request(classification=True))
    values = assembly.field_payloads["climate_regime_koppen_geiger"]
    assert values.dtype == np.dtype(np.uint8)
    assert np.all((values >= 1) & (values <= 30))
    assert not np.any(values == 0)


def test_k04_classification_replay_is_bit_exact() -> None:
    request = _a08_request(classification=True)
    first = _generate(request)
    replay = _generate(request)
    np.testing.assert_array_equal(
        first.field_payloads["climate_regime_koppen_geiger"],
        replay.field_payloads["climate_regime_koppen_geiger"],
    )


def test_k05_arid_b_class_has_precedence_over_tropical_temperature() -> None:
    assert _label([25] * 12, [10] * 12) == "BWh"


@pytest.mark.parametrize(
    ("precipitation", "expected"),
    (
        ([100] * 12, "Af"),
        ([55] + [100] * 11, "Am"),
        ([20] + [100] * 11, "Aw"),
    ),
)
def test_k06_a_subtype_fixtures(
    precipitation: list[float],
    expected: str,
) -> None:
    assert _label([25] * 12, precipitation) == expected


@pytest.mark.parametrize(
    ("temperature", "precipitation", "expected"),
    (
        ([25] * 12, [10] * 12, "BWh"),
        ([10] * 12, [10] * 12, "BWk"),
        ([25] * 12, [40] * 12, "BSh"),
        ([10] * 12, [20] * 12, "BSk"),
    ),
)
def test_k07_b_subtype_fixtures(
    temperature: list[float],
    precipitation: list[float],
    expected: str,
) -> None:
    assert _label(temperature, precipitation) == expected


@pytest.mark.parametrize(
    ("temperature", "third"),
    (
        (C_TEMP_A, "a"),
        (C_TEMP_B, "b"),
        (C_TEMP_C, "c"),
    ),
)
@pytest.mark.parametrize(
    ("precipitation", "second"),
    (
        (P_S, "s"),
        (P_W, "w"),
        (P_F, "f"),
    ),
)
def test_k08_c_subtype_fixtures(
    temperature: list[float],
    third: str,
    precipitation: list[float],
    second: str,
) -> None:
    assert _label(temperature, precipitation) == f"C{second}{third}"


@pytest.mark.parametrize(
    ("temperature", "third"),
    (
        (D_TEMP_A, "a"),
        (D_TEMP_B, "b"),
        (D_TEMP_C, "c"),
        (D_TEMP_D, "d"),
    ),
)
@pytest.mark.parametrize(
    ("precipitation", "second"),
    (
        (P_S, "s"),
        (P_W, "w"),
        (P_F, "f"),
    ),
)
def test_k09_d_subtype_fixtures(
    temperature: list[float],
    third: str,
    precipitation: list[float],
    second: str,
) -> None:
    assert _label(temperature, precipitation) == f"D{second}{third}"


def test_k10_e_subtype_fixtures_and_exact_10c_boundary() -> None:
    assert _label([-10, -8, -5, -2, 1, 3, 5, 4, 2, 0, -4, -8], P_F) == "ET"
    assert _label([-20, -18, -15, -12, -8, -4, 0, -3, -7, -12, -16, -19], P_F) == "EF"
    assert _label([0, 1, 2, 4, 7, 9, 10, 9, 7, 4, 2, 1], P_F) == "ET"


def test_k11_local_warm_cold_half_year_indices_follow_explicit_peak() -> None:
    assert local_warm_half_year_indices(7) == (3, 4, 5, 6, 7, 8)
    assert local_cold_half_year_indices(7) == (0, 1, 2, 9, 10, 11)

    assert local_warm_half_year_indices(1) == (9, 10, 11, 0, 1, 2)
    assert local_cold_half_year_indices(1) == (3, 4, 5, 6, 7, 8)


def test_k12_s_w_overlap_is_resolved_by_total_half_year_precipitation() -> None:
    overlap_s = [
        5, 100, 100,
        5, 20, 20, 20, 20, 100,
        100, 100, 100,
    ]
    overlap_w = [
        5, 20, 20,
        5, 100, 100, 100, 100, 100,
        20, 20, 100,
    ]
    assert _label(C_TEMP_A, overlap_s) == "Csa"
    assert _label(C_TEMP_A, overlap_w) == "Cwa"


def test_k13_enabling_classification_does_not_change_upstream_world_state() -> None:
    c4 = _generate(_a08_request(classification=False))
    c5 = _generate(_a08_request(classification=True))

    for field_id in c4.field_payloads:
        np.testing.assert_array_equal(
            c5.field_payloads[field_id],
            c4.field_payloads[field_id],
        )
    assert c5.data.features == c4.data.features
    assert c5.data.networks == c4.data.networks


def test_k14_public_classification_field_contract_and_codebook_are_exact() -> None:
    assembly = _generate(_a08_request(classification=True))
    descriptor = assembly.data.fields["climate_regime_koppen_geiger"]
    payload = assembly.field_payloads["climate_regime_koppen_geiger"]

    assert descriptor.role is FieldRole.DERIVED
    assert descriptor.dtype == "uint8"
    assert descriptor.unit == KOPPEN_GEIGER_SCHEME_ID
    assert descriptor.shape == (
        assembly.data.grid.rows,
        assembly.data.grid.columns,
    )
    assert payload.dtype == np.dtype(np.uint8)
    assert set(KOPPEN_GEIGER_CODE_TO_LABEL) == set(range(1, 31))
    assert len(KOPPEN_GEIGER_LABEL_TO_CODE) == 30
    assert {
        KOPPEN_GEIGER_LABEL_TO_CODE[label]: label
        for label in KOPPEN_GEIGER_LABEL_TO_CODE
    } == KOPPEN_GEIGER_CODE_TO_LABEL


def test_k15_absent_classification_preserves_c4_fingerprint_semantics() -> None:
    request = _a08_request(classification=False)
    spec_payload = request.domain_spec.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    )
    climate_payload = spec_payload["surface"]["climate"]
    climate_payload.pop("classification", None)
    expected_spec_fingerprint = "sha256:" + sha256(
        _canonical_json_bytes(spec_payload)
    ).hexdigest()

    assert domain_spec_fingerprint(request.domain_spec) == expected_spec_fingerprint

    catalog = load_preset_catalog(A08 / "presets.json")
    registry = registry_for_request(request, catalog)
    plan = compile_domain_spec(
        request.domain_spec,
        registry=registry,
        generator_version="0.2-test",
    )

    features = []
    for feature in sorted(plan.features, key=lambda item: item.id):
        features.append(
            {
                "id": feature.id,
                "family": feature.family.value,
                "layout": feature.layout.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=False,
                ),
                "effect": feature.effect.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=False,
                ),
            }
        )
    constraints = []
    for constraint in sorted(plan.constraints, key=lambda item: item.id):
        item = constraint.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=False,
        )
        item.pop("source_relation", None)
        constraints.append(item)

    assert plan.terrain is not None
    surface_payload = plan.surface.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=False,
    )
    assert isinstance(surface_payload["climate"], dict)
    surface_payload["climate"].pop("classification", None)
    expected_plan_payload = {
        "plan_version": plan.plan_version,
        "seed": plan.seed,
        "domain": plan.domain.model_dump(mode="json"),
        "grid": plan.grid.model_dump(mode="json"),
        "terrain": plan.terrain.model_dump(mode="json"),
        "hydrology": plan.hydrology.model_dump(mode="json"),
        "surface": surface_payload,
        "features": features,
        "constraints": constraints,
    }
    expected_plan_fingerprint = "sha256:" + sha256(
        _canonical_json_bytes(expected_plan_payload)
    ).hexdigest()

    assert semantic_plan_fingerprint(plan) == expected_plan_fingerprint

    classified = _a08_request(classification=True)
    classified_registry = registry_for_request(classified, catalog)
    classified_plan = compile_domain_spec(
        classified.domain_spec,
        registry=classified_registry,
        generator_version="0.2-test",
    )
    assert domain_spec_fingerprint(classified.domain_spec) != expected_spec_fingerprint
    assert semantic_plan_fingerprint(classified_plan) != expected_plan_fingerprint
