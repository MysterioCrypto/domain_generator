from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .derive import SurfaceCapabilityError


KOPPEN_GEIGER_SCHEME_ID = "koppen_geiger_local_season_v1"

KOPPEN_GEIGER_CODE_TO_LABEL: dict[int, str] = {
    1: "Af",
    2: "Am",
    3: "Aw",
    4: "BWh",
    5: "BWk",
    6: "BSh",
    7: "BSk",
    8: "Csa",
    9: "Csb",
    10: "Csc",
    11: "Cwa",
    12: "Cwb",
    13: "Cwc",
    14: "Cfa",
    15: "Cfb",
    16: "Cfc",
    17: "Dsa",
    18: "Dsb",
    19: "Dsc",
    20: "Dsd",
    21: "Dwa",
    22: "Dwb",
    23: "Dwc",
    24: "Dwd",
    25: "Dfa",
    26: "Dfb",
    27: "Dfc",
    28: "Dfd",
    29: "ET",
    30: "EF",
}

KOPPEN_GEIGER_LABEL_TO_CODE: dict[str, int] = {
    label: code for code, label in KOPPEN_GEIGER_CODE_TO_LABEL.items()
}


@dataclass(frozen=True, slots=True)
class KoppenGeigerDiagnostics:
    warm_half_year_indices: tuple[int, ...]
    cold_half_year_indices: tuple[int, ...]
    annual_mean_temperature_c: np.ndarray
    annual_precipitation_mm: np.ndarray
    hottest_month_temperature_c: np.ndarray
    coldest_month_temperature_c: np.ndarray
    months_above_10c: np.ndarray
    driest_month_precipitation_mm: np.ndarray
    warm_half_year_precipitation_mm: np.ndarray
    cold_half_year_precipitation_mm: np.ndarray
    warm_driest_month_precipitation_mm: np.ndarray
    warm_wettest_month_precipitation_mm: np.ndarray
    cold_driest_month_precipitation_mm: np.ndarray
    cold_wettest_month_precipitation_mm: np.ndarray


def local_warm_half_year_indices(temperature_peak_month: int) -> tuple[int, ...]:
    if (
        isinstance(temperature_peak_month, bool)
        or not isinstance(temperature_peak_month, int)
        or not 1 <= temperature_peak_month <= 12
    ):
        raise SurfaceCapabilityError(
            "temperature_peak_month must be an integer in [1, 12]"
        )
    peak = temperature_peak_month - 1
    return tuple((peak + offset) % 12 for offset in range(-3, 3))


def local_cold_half_year_indices(temperature_peak_month: int) -> tuple[int, ...]:
    warm = set(local_warm_half_year_indices(temperature_peak_month))
    return tuple(index for index in range(12) if index not in warm)


def _require_monthly_field(
    name: str,
    value: np.ndarray,
    *,
    positive: bool,
) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.ndim != 3 or value.shape[0] != 12:
        raise SurfaceCapabilityError(
            f"{name} must be a numpy array with shape (12, rows, columns)"
        )
    array = value.astype(np.float64, copy=False)
    if not bool(np.isfinite(array).all()):
        raise SurfaceCapabilityError(f"{name} must be finite")
    if positive and bool(np.any(array <= 0.0)):
        raise SurfaceCapabilityError(f"{name} must be strictly positive")
    return array


def _require_annual_field(
    name: str,
    value: np.ndarray,
    *,
    expected_shape: tuple[int, int],
    positive: bool,
) -> np.ndarray:
    if (
        not isinstance(value, np.ndarray)
        or value.ndim != 2
        or value.shape != expected_shape
    ):
        raise SurfaceCapabilityError(
            f"{name} must be a 2D array matching the monthly grid"
        )
    array = value.astype(np.float64, copy=False)
    if not bool(np.isfinite(array).all()):
        raise SurfaceCapabilityError(f"{name} must be finite")
    if positive and bool(np.any(array <= 0.0)):
        raise SurfaceCapabilityError(f"{name} must be strictly positive")
    return array


def koppen_geiger_diagnostics(
    *,
    monthly_mean_temperature_c: np.ndarray,
    monthly_precipitation_mm: np.ndarray,
    annual_mean_temperature_c: np.ndarray,
    annual_precipitation_mm: np.ndarray,
    temperature_peak_month: int,
) -> KoppenGeigerDiagnostics:
    temperature = _require_monthly_field(
        "monthly_mean_temperature_c",
        monthly_mean_temperature_c,
        positive=False,
    )
    precipitation = _require_monthly_field(
        "monthly_precipitation_mm",
        monthly_precipitation_mm,
        positive=True,
    )
    if temperature.shape != precipitation.shape:
        raise SurfaceCapabilityError(
            "monthly temperature and precipitation shapes must match"
        )

    shape = (temperature.shape[1], temperature.shape[2])
    annual_temperature = _require_annual_field(
        "annual_mean_temperature_c",
        annual_mean_temperature_c,
        expected_shape=shape,
        positive=False,
    )
    annual_precipitation = _require_annual_field(
        "annual_precipitation_mm",
        annual_precipitation_mm,
        expected_shape=shape,
        positive=True,
    )

    warm = local_warm_half_year_indices(temperature_peak_month)
    cold = local_cold_half_year_indices(temperature_peak_month)

    warm_precipitation = precipitation[np.asarray(warm, dtype=np.intp)]
    cold_precipitation = precipitation[np.asarray(cold, dtype=np.intp)]

    return KoppenGeigerDiagnostics(
        warm_half_year_indices=warm,
        cold_half_year_indices=cold,
        annual_mean_temperature_c=annual_temperature,
        annual_precipitation_mm=annual_precipitation,
        hottest_month_temperature_c=np.max(temperature, axis=0),
        coldest_month_temperature_c=np.min(temperature, axis=0),
        months_above_10c=np.count_nonzero(temperature > 10.0, axis=0),
        driest_month_precipitation_mm=np.min(precipitation, axis=0),
        warm_half_year_precipitation_mm=np.sum(
            warm_precipitation, axis=0, dtype=np.float64
        ),
        cold_half_year_precipitation_mm=np.sum(
            cold_precipitation, axis=0, dtype=np.float64
        ),
        warm_driest_month_precipitation_mm=np.min(
            warm_precipitation, axis=0
        ),
        warm_wettest_month_precipitation_mm=np.max(
            warm_precipitation, axis=0
        ),
        cold_driest_month_precipitation_mm=np.min(
            cold_precipitation, axis=0
        ),
        cold_wettest_month_precipitation_mm=np.max(
            cold_precipitation, axis=0
        ),
    )


def classify_koppen_geiger_local_season(
    *,
    monthly_mean_temperature_c: np.ndarray,
    monthly_precipitation_mm: np.ndarray,
    annual_mean_temperature_c: np.ndarray,
    annual_precipitation_mm: np.ndarray,
    temperature_peak_month: int,
) -> np.ndarray:
    diagnostics = koppen_geiger_diagnostics(
        monthly_mean_temperature_c=monthly_mean_temperature_c,
        monthly_precipitation_mm=monthly_precipitation_mm,
        annual_mean_temperature_c=annual_mean_temperature_c,
        annual_precipitation_mm=annual_precipitation_mm,
        temperature_peak_month=temperature_peak_month,
    )

    mat = diagnostics.annual_mean_temperature_c
    map_mm = diagnostics.annual_precipitation_mm
    thot = diagnostics.hottest_month_temperature_c
    tcold = diagnostics.coldest_month_temperature_c
    tmon10 = diagnostics.months_above_10c
    pdry = diagnostics.driest_month_precipitation_mm
    pwarm = diagnostics.warm_half_year_precipitation_mm
    pcold = diagnostics.cold_half_year_precipitation_mm
    psdry = diagnostics.warm_driest_month_precipitation_mm
    pswet = diagnostics.warm_wettest_month_precipitation_mm
    pwdry = diagnostics.cold_driest_month_precipitation_mm
    pwwet = diagnostics.cold_wettest_month_precipitation_mm

    warm_fraction = pwarm / map_mm
    cold_fraction = pcold / map_mm

    pthreshold = np.where(
        warm_fraction >= 0.70,
        2.0 * mat + 28.0,
        np.where(
            cold_fraction >= 0.70,
            2.0 * mat,
            2.0 * mat + 14.0,
        ),
    )

    codes = np.zeros(map_mm.shape, dtype=np.uint8)

    # B climates have precedence over A/C/D/E.
    b_mask = map_mm < 10.0 * pthreshold
    desert = b_mask & (map_mm < 5.0 * pthreshold)
    steppe = b_mask & ~desert
    hot = mat >= 18.0

    codes[desert & hot] = KOPPEN_GEIGER_LABEL_TO_CODE["BWh"]
    codes[desert & ~hot] = KOPPEN_GEIGER_LABEL_TO_CODE["BWk"]
    codes[steppe & hot] = KOPPEN_GEIGER_LABEL_TO_CODE["BSh"]
    codes[steppe & ~hot] = KOPPEN_GEIGER_LABEL_TO_CODE["BSk"]

    remaining = ~b_mask

    # A climates.
    a_mask = remaining & (tcold >= 18.0)
    af = a_mask & (pdry >= 60.0)
    am = a_mask & ~af & (pdry >= (100.0 - map_mm / 25.0))
    aw = a_mask & ~af & ~am
    codes[af] = KOPPEN_GEIGER_LABEL_TO_CODE["Af"]
    codes[am] = KOPPEN_GEIGER_LABEL_TO_CODE["Am"]
    codes[aw] = KOPPEN_GEIGER_LABEL_TO_CODE["Aw"]

    # E climates use the exact Beck/Peel 10 C boundary.
    e_mask = remaining & ~a_mask & (thot <= 10.0)
    et = e_mask & (thot > 0.0)
    ef = e_mask & ~et
    codes[et] = KOPPEN_GEIGER_LABEL_TO_CODE["ET"]
    codes[ef] = KOPPEN_GEIGER_LABEL_TO_CODE["EF"]

    c_mask = remaining & ~a_mask & ~e_mask & (tcold > 0.0) & (tcold < 18.0)
    d_mask = remaining & ~a_mask & ~e_mask & (tcold <= 0.0)

    summer_dry = (psdry < 40.0) & (psdry < pwwet / 3.0)
    winter_dry = pwdry < pswet / 10.0
    overlap = summer_dry & winter_dry
    s_mask = (summer_dry & ~winter_dry) | (overlap & (pcold > pwarm))
    w_mask = (winter_dry & ~summer_dry) | (overlap & ~(pcold > pwarm))
    f_mask = ~s_mask & ~w_mask

    temp_a = thot >= 22.0
    temp_b = ~temp_a & (tmon10 >= 4)
    temp_d = ~temp_a & ~temp_b & (tcold < -38.0)
    temp_c_for_c = ~temp_a & ~temp_b
    temp_c_for_d = ~temp_a & ~temp_b & ~temp_d

    for climate_mask, prefix, c_temp_mask in (
        (c_mask, "C", temp_c_for_c),
        (d_mask, "D", temp_c_for_d),
    ):
        for precipitation_mask, second in (
            (s_mask, "s"),
            (w_mask, "w"),
            (f_mask, "f"),
        ):
            codes[climate_mask & precipitation_mask & temp_a] = (
                KOPPEN_GEIGER_LABEL_TO_CODE[f"{prefix}{second}a"]
            )
            codes[climate_mask & precipitation_mask & temp_b] = (
                KOPPEN_GEIGER_LABEL_TO_CODE[f"{prefix}{second}b"]
            )
            codes[climate_mask & precipitation_mask & c_temp_mask] = (
                KOPPEN_GEIGER_LABEL_TO_CODE[f"{prefix}{second}c"]
            )
            if prefix == "D":
                codes[climate_mask & precipitation_mask & temp_d] = (
                    KOPPEN_GEIGER_LABEL_TO_CODE[f"{prefix}{second}d"]
                )

    if bool(np.any(codes == 0)):
        raise SurfaceCapabilityError(
            "Köppen-Geiger classification left one or more cells unclassified"
        )
    if bool(np.any(codes > 30)):
        raise SurfaceCapabilityError(
            "Köppen-Geiger classification produced an invalid code"
        )
    return codes


__all__ = [
    "KOPPEN_GEIGER_CODE_TO_LABEL",
    "KOPPEN_GEIGER_LABEL_TO_CODE",
    "KOPPEN_GEIGER_SCHEME_ID",
    "KoppenGeigerDiagnostics",
    "classify_koppen_geiger_local_season",
    "koppen_geiger_diagnostics",
    "local_cold_half_year_indices",
    "local_warm_half_year_indices",
]
