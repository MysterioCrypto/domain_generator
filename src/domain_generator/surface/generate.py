from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from ..contracts.geometry import AreaGeometry
from ..contracts.layout import LayoutCandidate
from ..contracts.plan import (
    EffectStage,
    FeatureFamily,
    GenerationPlan,
    ParameterType,
)
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from ..grid import GridAdapter
from ..hydrology.state import HydrologyState
from ..layout.area import point_in_area
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngFactory, RngKey, RngStage
from ..pipeline.sampling import SamplingCapabilityError, sample_resolved_parameter
from ..terrain.state import TerrainState
from .climate_regimes import (
    KOPPEN_GEIGER_SCHEME_ID,
    classify_koppen_geiger_local_season,
)
from .derive import (
    SurfaceCapabilityError,
    annual_mean_temperature_field,
    annual_precipitation_field,
    climate_aware_vegetation_components,
    effective_surface_moisture_components,
    monthly_precipitation_fields,
    monthly_temperature_fields,
    moisture_potential_field,
    slope_degrees,
    vegetation_potential_field,
)
from .state import SurfaceState


@dataclass(frozen=True, slots=True)
class _SurfaceBuildResult:
    state: SurfaceState
    applied_feature_ids: tuple[str, ...]


def _parameter_stream_key(
    attempt_index: int,
    feature_id: str,
    parameter_name: str,
) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.SURFACE,
        scope=("feature", feature_id, "parameter", parameter_name),
        purpose="sample",
    )


def _sample_float_parameter(
    feature,
    parameter_name: str,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> float:
    recipe = feature.effect.parameters[parameter_name]
    if recipe.type is not ParameterType.FLOAT:
        raise SurfaceCapabilityError(
            f"surface parameter {parameter_name!r} for feature {feature.id!r} "
            "must be a float resolved parameter"
        )

    stream = rng_factory.stream(
        _parameter_stream_key(attempt_index, feature.id, parameter_name)
    )
    try:
        sampled = sample_resolved_parameter(recipe, stream)
    except SamplingCapabilityError as exc:
        raise SurfaceCapabilityError(
            f"surface parameter {parameter_name!r} recipe is unsupported for feature "
            f"{feature.id!r}"
        ) from exc

    if isinstance(sampled, bool) or not isinstance(sampled, (int, float)):
        raise SurfaceCapabilityError(
            f"surface parameter {parameter_name!r} must resolve to a numeric value"
        )
    value = float(sampled)
    if not isfinite(value):
        raise SurfaceCapabilityError(
            f"surface parameter {parameter_name!r} must resolve to a finite value"
        )
    return value


def _rasterize_area_cell_centers(
    plan: GenerationPlan,
    area: AreaGeometry,
) -> np.ndarray:
    adapter = GridAdapter.from_plan(plan)
    mask = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.bool_)
    for row in range(plan.grid.rows):
        for column in range(plan.grid.columns):
            if point_in_area(adapter.cell_center(row, column), area):
                mask[row, column] = True
    return mask


def _area_bias_contribution(
    plan: GenerationPlan,
    feature,
    geometry,
    *,
    parameter_name: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> np.ndarray:
    if not isinstance(geometry, AreaGeometry):
        raise SurfaceCapabilityError(
            f"surface feature {feature.id!r} requires AreaGeometry"
        )
    if set(feature.effect.parameters) != {parameter_name}:
        raise SurfaceCapabilityError(
            f"surface {feature.effect.operator} feature {feature.id!r} requires exactly "
            f"effect parameter [{parameter_name!r}]"
        )

    delta = _sample_float_parameter(
        feature,
        parameter_name,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    if not -1.0 <= delta <= 1.0:
        raise SurfaceCapabilityError(
            f"surface {parameter_name} must resolve to a finite value in [-1, 1]"
        )

    contribution = np.zeros((plan.grid.rows, plan.grid.columns), dtype=np.float64)
    contribution[_rasterize_area_cell_centers(plan, geometry)] = delta
    return contribution


def _build_surface(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    terrain: TerrainState,
    hydrology: HydrologyState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> _SurfaceBuildResult:
    expected_shape = (plan.grid.rows, plan.grid.columns)
    elevation = terrain.elevation_m
    water_depth = hydrology.water_depth_m

    if layout.attempt_index != attempt_index:
        raise SurfaceCapabilityError("surface layout attempt index must match current attempt")
    if not isinstance(elevation, np.ndarray) or elevation.shape != expected_shape:
        raise SurfaceCapabilityError("terrain elevation shape must match plan grid")
    if not isinstance(water_depth, np.ndarray) or water_depth.shape != expected_shape:
        raise SurfaceCapabilityError("hydrology water depth shape must match plan grid")
    if not np.isfinite(elevation).all():
        raise SurfaceCapabilityError("terrain elevation must contain only finite values")
    if not np.isfinite(water_depth).all() or bool(np.any(water_depth < 0.0)):
        raise SurfaceCapabilityError("hydrology water depth must be finite and non-negative")

    climate_normalization_water_depth = (
        hydrology.climate_normalization_water_depth_m
        if hydrology.climate_normalization_water_depth_m is not None
        else water_depth
    )
    if (
        not isinstance(climate_normalization_water_depth, np.ndarray)
        or climate_normalization_water_depth.shape != expected_shape
        or not np.isfinite(climate_normalization_water_depth).all()
        or bool(np.any(climate_normalization_water_depth < 0.0))
    ):
        raise SurfaceCapabilityError(
            "climate normalization water depth must be finite, non-negative, and match grid"
        )

    adapter = GridAdapter.from_plan(plan)
    legacy_moisture_potential: np.ndarray | None = None
    if plan.plan_version == "0.1":
        legacy_moisture_potential = moisture_potential_field(
            adapter=adapter,
            water_depth_m=water_depth,
            moisture_base=plan.surface.moisture_base,
            water_moisture_boost=plan.surface.water_moisture_boost,
            water_moisture_decay_km=plan.surface.water_moisture_decay_km,
            moisture_noise_amplitude=plan.surface.moisture_noise_amplitude,
            moisture_noise_scale_km=plan.surface.moisture_noise_scale_km,
            rng_factory=rng_factory,
            attempt_index=attempt_index,
        )

    moisture_bias = np.zeros(expected_shape, dtype=np.float64)
    vegetation_bias = np.zeros(expected_shape, dtype=np.float64)
    applied: list[str] = []

    surface_features = sorted(
        (feature for feature in plan.features if feature.family is FeatureFamily.SURFACE),
        key=lambda feature: feature.id,
    )
    for feature in surface_features:
        if feature.effect.stage is not EffectStage.SURFACE:
            raise SurfaceCapabilityError(
                f"surface feature {feature.id!r} must use surface effect stage"
            )
        try:
            geometry = layout.geometry_realizations[feature.id]
        except KeyError as exc:
            raise SurfaceCapabilityError(
                f"surface feature {feature.id!r} has no materialized layout geometry"
            ) from exc

        operator = feature.effect.operator
        if operator == "moisture_bias":
            moisture_bias += _area_bias_contribution(
                plan,
                feature,
                geometry,
                parameter_name="delta_moisture",
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        elif operator == "vegetation_bias":
            vegetation_bias += _area_bias_contribution(
                plan,
                feature,
                geometry,
                parameter_name="delta_vegetation",
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        else:
            raise SurfaceCapabilityError(
                f"surface operator {operator!r} is unsupported"
            )
        applied.append(feature.id)

    temperature64: np.ndarray | None = None
    precipitation64: np.ndarray | None = None
    monthly_temperature64: np.ndarray | None = None
    monthly_precipitation64: np.ndarray | None = None
    climate_regime: np.ndarray | None = None
    if plan.plan_version == "0.2":
        climate = plan.surface.climate
        if climate is None:
            raise SurfaceCapabilityError("Core 0.2 surface requires climate plan")
        temperature64 = annual_mean_temperature_field(
            adapter=adapter,
            elevation_m=elevation,
            mean_temperature_c=climate.mean_temperature_c,
            north_minus_south_temperature_c=climate.north_minus_south_temperature_c,
            temperature_noise_amplitude_c=climate.temperature_noise_amplitude_c,
            climate_noise_scale_km=climate.climate_noise_scale_km,
            rng_factory=rng_factory,
            attempt_index=attempt_index,
        )
        precipitation64 = annual_precipitation_field(
            adapter=adapter,
            elevation_m=elevation,
            water_depth_m=climate_normalization_water_depth,
            mean_annual_precipitation_mm=climate.mean_annual_precipitation_mm,
            moisture_transport_bearing_deg=climate.moisture_transport_bearing_deg,
            orographic_scale_km=climate.orographic_scale_km,
            orographic_strength=climate.orographic_strength,
            precipitation_noise_log_amplitude=climate.precipitation_noise_log_amplitude,
            climate_noise_scale_km=climate.climate_noise_scale_km,
            rng_factory=rng_factory,
            attempt_index=attempt_index,
        )
        if climate.seasonality is not None:
            seasonality = climate.seasonality
            monthly_temperature64 = monthly_temperature_fields(
                annual_mean_temperature_c=temperature64,
                temperature_seasonal_amplitude_c=(
                    seasonality.temperature_seasonal_amplitude_c
                ),
                temperature_peak_month=seasonality.temperature_peak_month,
            )
            monthly_precipitation64 = monthly_precipitation_fields(
                annual_precipitation_mm=precipitation64,
                precipitation_seasonality_log_amplitude=(
                    seasonality.precipitation_seasonality_log_amplitude
                ),
                precipitation_peak_month=seasonality.precipitation_peak_month,
            )
            if climate.classification is not None:
                if (
                    climate.classification.scheme
                    != KOPPEN_GEIGER_SCHEME_ID
                ):
                    raise SurfaceCapabilityError(
                        "unsupported Core 0.2 climate classification scheme"
                    )
                climate_regime = classify_koppen_geiger_local_season(
                    monthly_mean_temperature_c=monthly_temperature64.astype(
                        np.float32
                    ),
                    monthly_precipitation_mm=monthly_precipitation64.astype(
                        np.float32
                    ),
                    annual_mean_temperature_c=temperature64.astype(np.float32),
                    annual_precipitation_mm=precipitation64.astype(np.float32),
                    temperature_peak_month=seasonality.temperature_peak_month,
                )

    water_mask = water_depth > 0.0
    legacy_moisture64: np.ndarray | None = None
    if plan.plan_version == "0.1":
        if legacy_moisture_potential is None:
            raise SurfaceCapabilityError("Core 0.1 legacy moisture was not generated")
        legacy_moisture64 = np.clip(
            legacy_moisture_potential + moisture_bias,
            0.0,
            1.0,
        )
        legacy_moisture64[water_mask] = 1.0

    slope64 = slope_degrees(
        elevation,
        cell_size_km=plan.grid.cell_size_km,
    )

    if plan.plan_version == "0.2":
        if temperature64 is None or precipitation64 is None:
            raise SurfaceCapabilityError("Core 0.2 climate fields were not generated")
        effective = effective_surface_moisture_components(
            adapter=adapter,
            annual_mean_temperature_c=temperature64,
            annual_precipitation_mm=precipitation64,
            flow_accumulation_km2=hydrology.flow_accumulation_km2,
            water_depth_m=water_depth,
            slope_deg=slope64,
            stream_threshold_km2=plan.hydrology.stream_threshold_km2,
            water_moisture_boost=plan.surface.water_moisture_boost,
            water_moisture_decay_km=plan.surface.water_moisture_decay_km,
        )
        moisture64 = np.clip(
            effective.effective_moisture + moisture_bias,
            0.0,
            1.0,
        )
        moisture64[water_mask] = 1.0
    else:
        if legacy_moisture64 is None:
            raise SurfaceCapabilityError("Core 0.1 legacy moisture was not generated")
        moisture64 = legacy_moisture64

    if plan.plan_version == "0.2":
        if temperature64 is None:
            raise SurfaceCapabilityError("Core 0.2 temperature field was not generated")
        vegetation = climate_aware_vegetation_components(
            moisture=moisture64,
            annual_mean_temperature_c=temperature64,
        )
        vegetation_potential = vegetation.vegetation_potential
    else:
        if legacy_moisture64 is None:
            raise SurfaceCapabilityError("Core 0.1 legacy moisture was not generated")
        vegetation_potential = vegetation_potential_field(
            moisture=legacy_moisture64,
            slope_deg=slope64,
            vegetation_slope_zero_deg=plan.surface.vegetation_slope_zero_deg,
        )

    vegetation64 = np.clip(vegetation_potential + vegetation_bias, 0.0, 1.0)
    vegetation64[water_mask] = 0.0

    return _SurfaceBuildResult(
        state=SurfaceState(
            moisture=moisture64.astype(np.float32),
            vegetation_density=vegetation64.astype(np.float32),
            annual_mean_temperature_c=(
                temperature64.astype(np.float32) if temperature64 is not None else None
            ),
            annual_precipitation_mm=(
                precipitation64.astype(np.float32) if precipitation64 is not None else None
            ),
            monthly_mean_temperature_c=(
                monthly_temperature64.astype(np.float32)
                if monthly_temperature64 is not None
                else None
            ),
            monthly_precipitation_mm=(
                monthly_precipitation64.astype(np.float32)
                if monthly_precipitation64 is not None
                else None
            ),
            climate_regime_koppen_geiger=(
                climate_regime.astype(np.uint8)
                if climate_regime is not None
                else None
            ),
        ),
        applied_feature_ids=tuple(applied),
    )


def generate_surface(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    terrain: TerrainState,
    hydrology: HydrologyState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> SurfaceState:
    return _build_surface(
        plan,
        layout,
        terrain,
        hydrology,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    ).state


def _expected_surface_feature_ids(plan: GenerationPlan) -> tuple[str, ...]:
    return tuple(
        sorted(feature.id for feature in plan.features if feature.family is FeatureFamily.SURFACE)
    )


def _recomputed_surface_matches(
    plan: GenerationPlan,
    layout: LayoutCandidate,
    terrain: TerrainState,
    hydrology: HydrologyState,
    surface: SurfaceState,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> bool:
    try:
        expected = generate_surface(
            plan,
            layout,
            terrain,
            hydrology,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )
    except SurfaceCapabilityError:
        return False
    return (
        np.array_equal(surface.moisture, expected.moisture)
        and np.array_equal(surface.vegetation_density, expected.vegetation_density)
        and (
            surface.annual_mean_temperature_c is None
            and expected.annual_mean_temperature_c is None
            or isinstance(surface.annual_mean_temperature_c, np.ndarray)
            and isinstance(expected.annual_mean_temperature_c, np.ndarray)
            and np.array_equal(
                surface.annual_mean_temperature_c,
                expected.annual_mean_temperature_c,
            )
        )
        and (
            surface.annual_precipitation_mm is None
            and expected.annual_precipitation_mm is None
            or isinstance(surface.annual_precipitation_mm, np.ndarray)
            and isinstance(expected.annual_precipitation_mm, np.ndarray)
            and np.array_equal(
                surface.annual_precipitation_mm,
                expected.annual_precipitation_mm,
            )
        )
        and (
            surface.monthly_mean_temperature_c is None
            and expected.monthly_mean_temperature_c is None
            or isinstance(surface.monthly_mean_temperature_c, np.ndarray)
            and isinstance(expected.monthly_mean_temperature_c, np.ndarray)
            and np.array_equal(
                surface.monthly_mean_temperature_c,
                expected.monthly_mean_temperature_c,
            )
        )
        and (
            surface.monthly_precipitation_mm is None
            and expected.monthly_precipitation_mm is None
            or isinstance(surface.monthly_precipitation_mm, np.ndarray)
            and isinstance(expected.monthly_precipitation_mm, np.ndarray)
            and np.array_equal(
                surface.monthly_precipitation_mm,
                expected.monthly_precipitation_mm,
            )
        )
        and (
            surface.climate_regime_koppen_geiger is None
            and expected.climate_regime_koppen_geiger is None
            or isinstance(surface.climate_regime_koppen_geiger, np.ndarray)
            and isinstance(expected.climate_regime_koppen_geiger, np.ndarray)
            and np.array_equal(
                surface.climate_regime_koppen_geiger,
                expected.climate_regime_koppen_geiger,
            )
        )
    )


def validate_surface(
    plan: GenerationPlan,
    layout: LayoutCandidate | None,
    terrain: TerrainState | None,
    hydrology: HydrologyState | None,
    surface: SurfaceState | None,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
    applied_feature_ids: tuple[str, ...] = (),
) -> ValidationResult:
    expected_shape = (plan.grid.rows, plan.grid.columns)
    expected_features = _expected_surface_feature_ids(plan)

    layout_exists = layout is not None
    layout_attempt_matches = layout_exists and layout.attempt_index == attempt_index
    terrain_exists = terrain is not None
    hydrology_exists = hydrology is not None
    surface_exists = surface is not None

    terrain_shape = terrain_finite = False
    water_shape = water_finite = water_nonnegative = False
    moisture_shape = vegetation_shape = False
    moisture_dtype = vegetation_dtype = False
    moisture_finite = vegetation_finite = False
    moisture_range = vegetation_range = False
    water_moisture_exact = water_vegetation_exact = False
    climate_contract = False
    temperature_shape = precipitation_shape = False
    temperature_dtype = precipitation_dtype = False
    temperature_finite = precipitation_finite = False
    precipitation_positive = False
    seasonality_contract = False
    monthly_temperature_shape = monthly_precipitation_shape = False
    monthly_temperature_dtype = monthly_precipitation_dtype = False
    monthly_temperature_finite = monthly_precipitation_finite = False
    monthly_precipitation_positive = False
    classification_contract = False
    classification_shape = False
    classification_dtype = False
    classification_range = False
    deterministic_recompute = False

    if terrain_exists:
        elevation = terrain.elevation_m
        terrain_shape = isinstance(elevation, np.ndarray) and elevation.shape == expected_shape
        terrain_finite = isinstance(elevation, np.ndarray) and bool(np.isfinite(elevation).all())

    if hydrology_exists:
        water = hydrology.water_depth_m
        water_shape = isinstance(water, np.ndarray) and water.shape == expected_shape
        water_finite = isinstance(water, np.ndarray) and bool(np.isfinite(water).all())
        water_nonnegative = water_finite and bool(np.all(water >= 0.0))

    if surface_exists:
        moisture = surface.moisture
        vegetation = surface.vegetation_density
        moisture_shape = isinstance(moisture, np.ndarray) and moisture.shape == expected_shape
        vegetation_shape = isinstance(vegetation, np.ndarray) and vegetation.shape == expected_shape
        moisture_dtype = isinstance(moisture, np.ndarray) and moisture.dtype == np.dtype(np.float32)
        vegetation_dtype = isinstance(vegetation, np.ndarray) and vegetation.dtype == np.dtype(np.float32)
        moisture_finite = isinstance(moisture, np.ndarray) and bool(np.isfinite(moisture).all())
        vegetation_finite = isinstance(vegetation, np.ndarray) and bool(np.isfinite(vegetation).all())
        moisture_range = moisture_finite and bool(np.all((moisture >= 0.0) & (moisture <= 1.0)))
        vegetation_range = vegetation_finite and bool(
            np.all((vegetation >= 0.0) & (vegetation <= 1.0))
        )

        temperature = surface.annual_mean_temperature_c
        precipitation = surface.annual_precipitation_mm
        if plan.plan_version == "0.2":
            climate_contract = isinstance(temperature, np.ndarray) and isinstance(
                precipitation, np.ndarray
            )
            if climate_contract:
                temperature_shape = temperature.shape == expected_shape
                precipitation_shape = precipitation.shape == expected_shape
                temperature_dtype = temperature.dtype == np.dtype(np.float32)
                precipitation_dtype = precipitation.dtype == np.dtype(np.float32)
                temperature_finite = bool(np.isfinite(temperature).all())
                precipitation_finite = bool(np.isfinite(precipitation).all())
                precipitation_positive = precipitation_finite and bool(
                    np.all(precipitation > 0.0)
                )
        else:
            climate_contract = temperature is None and precipitation is None
            temperature_shape = precipitation_shape = True
            temperature_dtype = precipitation_dtype = True
            temperature_finite = precipitation_finite = True
            precipitation_positive = True

        monthly_temperature = surface.monthly_mean_temperature_c
        monthly_precipitation = surface.monthly_precipitation_mm
        seasonality_expected = (
            plan.plan_version == "0.2"
            and plan.surface.climate is not None
            and plan.surface.climate.seasonality is not None
        )
        if seasonality_expected:
            seasonality_contract = isinstance(
                monthly_temperature, np.ndarray
            ) and isinstance(monthly_precipitation, np.ndarray)
            if seasonality_contract:
                expected_monthly_shape = (12, *expected_shape)
                monthly_temperature_shape = (
                    monthly_temperature.shape == expected_monthly_shape
                )
                monthly_precipitation_shape = (
                    monthly_precipitation.shape == expected_monthly_shape
                )
                monthly_temperature_dtype = (
                    monthly_temperature.dtype == np.dtype(np.float32)
                )
                monthly_precipitation_dtype = (
                    monthly_precipitation.dtype == np.dtype(np.float32)
                )
                monthly_temperature_finite = bool(
                    np.isfinite(monthly_temperature).all()
                )
                monthly_precipitation_finite = bool(
                    np.isfinite(monthly_precipitation).all()
                )
                monthly_precipitation_positive = (
                    monthly_precipitation_finite
                    and bool(np.all(monthly_precipitation > 0.0))
                )
        else:
            seasonality_contract = (
                monthly_temperature is None and monthly_precipitation is None
            )
            monthly_temperature_shape = monthly_precipitation_shape = True
            monthly_temperature_dtype = monthly_precipitation_dtype = True
            monthly_temperature_finite = monthly_precipitation_finite = True
            monthly_precipitation_positive = True

        classification = surface.climate_regime_koppen_geiger
        classification_expected = (
            plan.plan_version == "0.2"
            and plan.surface.climate is not None
            and plan.surface.climate.classification is not None
        )
        if classification_expected:
            classification_contract = isinstance(classification, np.ndarray)
            if classification_contract:
                classification_shape = classification.shape == expected_shape
                classification_dtype = (
                    classification.dtype == np.dtype(np.uint8)
                )
                classification_range = bool(
                    np.all((classification >= 1) & (classification <= 30))
                )
        else:
            classification_contract = classification is None
            classification_shape = True
            classification_dtype = True
            classification_range = True

        if hydrology_exists and water_shape and moisture_shape and vegetation_shape:
            water_mask = hydrology.water_depth_m > 0.0
            water_moisture_exact = bool(
                np.all(surface.moisture[water_mask] == np.float32(1.0))
            )
            water_vegetation_exact = bool(
                np.all(surface.vegetation_density[water_mask] == np.float32(0.0))
            )

    applied_complete = (
        tuple(sorted(applied_feature_ids)) == expected_features
        and len(applied_feature_ids) == len(set(applied_feature_ids))
    )

    if (
        layout_exists
        and layout_attempt_matches
        and terrain_exists
        and hydrology_exists
        and surface_exists
        and terrain_shape
        and terrain_finite
        and water_shape
        and water_finite
        and water_nonnegative
        and moisture_shape
        and vegetation_shape
        and moisture_dtype
        and vegetation_dtype
    ):
        deterministic_recompute = _recomputed_surface_matches(
            plan,
            layout,
            terrain,
            hydrology,
            surface,
            attempt_index=attempt_index,
            rng_factory=rng_factory,
        )

    results = (
        EngineInvariantResult(id="surface-upstream-layout-exists", passed=layout_exists),
        EngineInvariantResult(id="surface-layout-attempt-index-matches", passed=layout_attempt_matches),
        EngineInvariantResult(id="surface-upstream-terrain-exists", passed=terrain_exists),
        EngineInvariantResult(id="surface-upstream-hydrology-exists", passed=hydrology_exists),
        EngineInvariantResult(id="surface-terrain-shape-matches-grid", passed=terrain_shape),
        EngineInvariantResult(id="surface-terrain-finite", passed=terrain_finite),
        EngineInvariantResult(id="surface-water-depth-shape-matches-grid", passed=water_shape),
        EngineInvariantResult(id="surface-water-depth-finite", passed=water_finite),
        EngineInvariantResult(id="surface-water-depth-nonnegative", passed=water_nonnegative),
        EngineInvariantResult(id="surface-state-exists", passed=surface_exists),
        EngineInvariantResult(id="surface-moisture-shape-matches-grid", passed=moisture_shape),
        EngineInvariantResult(id="surface-moisture-dtype-float32", passed=moisture_dtype),
        EngineInvariantResult(id="surface-moisture-finite", passed=moisture_finite),
        EngineInvariantResult(id="surface-moisture-range", passed=moisture_range),
        EngineInvariantResult(id="surface-vegetation-shape-matches-grid", passed=vegetation_shape),
        EngineInvariantResult(id="surface-vegetation-dtype-float32", passed=vegetation_dtype),
        EngineInvariantResult(id="surface-vegetation-finite", passed=vegetation_finite),
        EngineInvariantResult(id="surface-vegetation-range", passed=vegetation_range),
        EngineInvariantResult(id="surface-water-moisture-is-one", passed=water_moisture_exact),
        EngineInvariantResult(id="surface-water-vegetation-is-zero", passed=water_vegetation_exact),
        EngineInvariantResult(id="surface-climate-contract-matches-version", passed=climate_contract),
        EngineInvariantResult(id="surface-temperature-shape-matches-grid", passed=temperature_shape),
        EngineInvariantResult(id="surface-temperature-dtype-float32", passed=temperature_dtype),
        EngineInvariantResult(id="surface-temperature-finite", passed=temperature_finite),
        EngineInvariantResult(id="surface-precipitation-shape-matches-grid", passed=precipitation_shape),
        EngineInvariantResult(id="surface-precipitation-dtype-float32", passed=precipitation_dtype),
        EngineInvariantResult(id="surface-precipitation-finite", passed=precipitation_finite),
        EngineInvariantResult(id="surface-precipitation-positive", passed=precipitation_positive),
        EngineInvariantResult(
            id="surface-seasonality-contract-matches-plan",
            passed=seasonality_contract,
        ),
        EngineInvariantResult(
            id="surface-monthly-temperature-shape-matches-plan",
            passed=monthly_temperature_shape,
        ),
        EngineInvariantResult(
            id="surface-monthly-temperature-dtype-float32",
            passed=monthly_temperature_dtype,
        ),
        EngineInvariantResult(
            id="surface-monthly-temperature-finite",
            passed=monthly_temperature_finite,
        ),
        EngineInvariantResult(
            id="surface-monthly-precipitation-shape-matches-plan",
            passed=monthly_precipitation_shape,
        ),
        EngineInvariantResult(
            id="surface-monthly-precipitation-dtype-float32",
            passed=monthly_precipitation_dtype,
        ),
        EngineInvariantResult(
            id="surface-monthly-precipitation-finite",
            passed=monthly_precipitation_finite,
        ),
        EngineInvariantResult(
            id="surface-monthly-precipitation-positive",
            passed=monthly_precipitation_positive,
        ),
        EngineInvariantResult(
            id="surface-climate-classification-contract-matches-plan",
            passed=classification_contract,
        ),
        EngineInvariantResult(
            id="surface-climate-classification-shape-matches-plan",
            passed=classification_shape,
        ),
        EngineInvariantResult(
            id="surface-climate-classification-dtype-uint8",
            passed=classification_dtype,
        ),
        EngineInvariantResult(
            id="surface-climate-classification-code-range",
            passed=classification_range,
        ),
        EngineInvariantResult(
            id="surface-feature-effects-applied-exactly",
            passed=applied_complete,
            measured={
                "expected_feature_count": len(expected_features),
                "applied_feature_count": len(applied_feature_ids),
            },
        ),
        EngineInvariantResult(id="surface-deterministic-recompute", passed=deterministic_recompute),
    )
    passed = all(item.passed for item in results)
    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.SURFACE,
        engine_invariants=EngineInvariantGroup(passed=passed, results=results),
        hard_constraints=HardConstraintGroup(passed=True, results=()),
        soft_constraints=SoftConstraintGroup(results=()),
        ranking=None,
    )


def surface_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    if state.layout is None or state.terrain is None or state.hydrology is None:
        return validate_surface(
            context.plan,
            state.layout,
            state.terrain,
            state.hydrology,
            None,
            attempt_index=context.attempt_index,
            rng_factory=context.rng_factory,
            applied_feature_ids=(),
        )

    build = _build_surface(
        context.plan,
        state.layout,
        state.terrain,
        state.hydrology,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
    state.surface = build.state
    return validate_surface(
        context.plan,
        state.layout,
        state.terrain,
        state.hydrology,
        state.surface,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
        applied_feature_ids=build.applied_feature_ids,
    )
