from __future__ import annotations

from math import inf

import numpy as np
import pytest

from domain_generator.contracts.data import (
    RiverNetwork,
    RiverNode,
    RiverNodeKind,
    RiverSegment,
    RiverSegmentProperties,
)
from domain_generator.contracts.geometry import PointGeometry, WorldPoint
from domain_generator.contracts.plan import (
    GenerationPlan,
    SitePreference,
    SiteRequirement,
)
from domain_generator.hydrology.state import HydrologyState
from domain_generator.poi import (
    CORE_V02_SITE_METRIC_IDS,
    SITE_METRIC_IDS,
    EvaluatedSite,
    PlacementCandidateCapabilityError,
    PlacementSelectionCapabilityError,
    SiteMetricContext,
    distance_to_river_network_km,
    evaluate_site_metrics,
    filter_valid_sites,
    score_valid_sites,
    site_metric_ids_for_plan_version,
)
from domain_generator.surface.state import SurfaceState
from domain_generator.terrain.state import TerrainState


def _plan(version: str, *, rows: int = 5, columns: int = 5) -> GenerationPlan:
    surface: dict[str, object] = {
        "moisture_base": 0.35,
        "water_moisture_boost": 0.55,
        "water_moisture_decay_km": 2.0,
        "moisture_noise_amplitude": 0.1,
        "moisture_noise_scale_km": 8.0,
        "vegetation_slope_zero_deg": 45.0,
    }
    payload: dict[str, object] = {
        "plan_version": version,
        "source": {
            "spec_id": f"p08-a-{version}",
            "spec_schema_version": version,
            "spec_fingerprint": "sha256:p08-a-test",
            "generator_version": "0.2-test",
        },
        "seed": 99117,
        "domain": {
            "width_km": float(columns),
            "height_km": float(rows),
        },
        "grid": {
            "cell_size_km": 1.0,
            "rows": rows,
            "columns": columns,
        },
        "hydrology": {
            "stream_threshold_km2": 10.0,
            "lake_min_area_km2": 1.0,
            "lake_min_depth_m": 0.5,
            "river_depth_at_threshold_m": 0.5,
            "river_depth_exponent": 0.3,
        },
        "surface": surface,
        "features": [],
        "constraints": [],
    }
    if version == "0.2":
        payload["terrain"] = {
            "base_elevation_m": 100.0,
            "noise_layers": [
                {"id": "test", "scale_km": 10.0, "amplitude_m": 1.0}
            ],
        }
        surface["climate"] = {
            "mean_temperature_c": 10.0,
            "north_minus_south_temperature_c": 0.0,
            "temperature_noise_amplitude_c": 0.0,
            "mean_annual_precipitation_mm": 900.0,
            "moisture_transport_bearing_deg": 90.0,
            "orographic_scale_km": 20.0,
            "orographic_strength": 0.0,
            "precipitation_noise_log_amplitude": 0.0,
            "climate_noise_scale_km": 24.0,
        }
    return GenerationPlan.model_validate(payload)


def _network(
    start: tuple[float, float] = (0.0, 0.0),
    end: tuple[float, float] = (5.0, 0.0),
) -> RiverNetwork:
    return RiverNetwork(
        nodes={
            "a": RiverNode(
                kind=RiverNodeKind.SOURCE,
                position=WorldPoint(x_km=start[0], y_km=start[1]),
            ),
            "b": RiverNode(
                kind=RiverNodeKind.SOURCE,
                position=WorldPoint(x_km=end[0], y_km=end[1]),
            ),
        },
        segments={
            "s": RiverSegment(
                **{
                    "from": "a",
                    "to": "b",
                    "centerline": (
                        WorldPoint(x_km=start[0], y_km=start[1]),
                        WorldPoint(x_km=end[0], y_km=end[1]),
                    ),
                    "properties": RiverSegmentProperties(catchment_area_km2=10.0),
                }
            )
        },
    )


def _states(
    *,
    version: str,
    temperature: np.ndarray | None = None,
    precipitation: np.ndarray | None = None,
    water: np.ndarray | None = None,
    potential: RiverNetwork | None = None,
) -> tuple[GenerationPlan, TerrainState, HydrologyState, SurfaceState]:
    rows = columns = 5
    plan = _plan(version, rows=rows, columns=columns)
    shape = (rows, columns)
    elevation = np.arange(rows * columns, dtype=np.float64).reshape(shape)
    if water is None:
        water = np.zeros(shape, dtype=np.float32)
    if version == "0.2" and potential is None:
        potential = _network()

    hydrology = HydrologyState(
        routing_elevation_m=np.zeros(shape, dtype=np.float64),
        fill_elevation_m=np.zeros(shape, dtype=np.float64),
        flow_direction=np.full(shape, -1, dtype=np.int8),
        flow_accumulation_km2=np.ones(shape, dtype=np.float64),
        stream_mask=np.zeros(shape, dtype=np.bool_),
        lake_candidates=(),
        river_network=RiverNetwork(),
        water_depth_m=water.astype(np.float32, copy=False),
        potential_river_network=potential,
    )

    moisture = np.linspace(0.2, 0.8, rows * columns, dtype=np.float32).reshape(shape)
    vegetation = np.linspace(0.1, 0.5, rows * columns, dtype=np.float32).reshape(shape)

    if version == "0.2":
        if temperature is None:
            temperature = np.arange(rows * columns, dtype=np.float32).reshape(shape)
        if precipitation is None:
            precipitation = (
                100.0 + 10.0 * np.arange(rows * columns, dtype=np.float32)
            ).reshape(shape)
    else:
        temperature = None
        precipitation = None

    return (
        plan,
        TerrainState(elevation_m=elevation),
        hydrology,
        SurfaceState(
            moisture=moisture,
            vegetation_density=vegetation,
            annual_mean_temperature_c=temperature,
            annual_precipitation_mm=precipitation,
        ),
    )


def _context(**kwargs) -> SiteMetricContext:
    plan, terrain, hydrology, surface = _states(**kwargs)
    return SiteMetricContext.from_states(plan, terrain, hydrology, surface)


def test_p01_core_v01_registry_is_exactly_historical_eight() -> None:
    assert SITE_METRIC_IDS == (
        "slope_mean",
        "water_fraction",
        "elevation_mean",
        "local_relief",
        "relative_elevation",
        "moisture_mean",
        "vegetation_density_mean",
        "distance_to_water",
    )
    assert site_metric_ids_for_plan_version("0.1") == SITE_METRIC_IDS
    assert _context(version="0.1").metric_ids == SITE_METRIC_IDS


def test_p02_core_v02_registry_is_exact_extension() -> None:
    assert CORE_V02_SITE_METRIC_IDS == SITE_METRIC_IDS + (
        "temperature_mean",
        "annual_precipitation_mean",
        "distance_to_potential_drainage",
    )
    assert site_metric_ids_for_plan_version("0.2") == CORE_V02_SITE_METRIC_IDS
    assert _context(version="0.2").metric_ids == CORE_V02_SITE_METRIC_IDS


def test_p03_temperature_mean_uses_existing_footprint_cells() -> None:
    temperature = np.arange(25, dtype=np.float32).reshape(5, 5)
    context = _context(version="0.2", temperature=temperature)
    candidate = PointGeometry(x_km=2.5, y_km=2.5)

    metrics = evaluate_site_metrics(context, candidate, 1.01)

    expected_cells = ((1, 2), (2, 1), (2, 2), (2, 3), (3, 2))
    expected = float(
        np.mean(
            np.asarray([temperature[cell] for cell in expected_cells]),
            dtype=np.float64,
        )
    )
    assert metrics["temperature_mean"] == pytest.approx(expected)


def test_p04_precipitation_mean_uses_existing_footprint_cells() -> None:
    precipitation = (
        100.0 + 10.0 * np.arange(25, dtype=np.float32)
    ).reshape(5, 5)
    context = _context(version="0.2", precipitation=precipitation)
    candidate = PointGeometry(x_km=2.5, y_km=2.5)

    metrics = evaluate_site_metrics(context, candidate, 1.01)

    expected_cells = ((1, 2), (2, 1), (2, 2), (2, 3), (3, 2))
    expected = float(
        np.mean(
            np.asarray([precipitation[cell] for cell in expected_cells]),
            dtype=np.float64,
        )
    )
    assert metrics["annual_precipitation_mean"] == pytest.approx(expected)


def test_p05_potential_drainage_distance_uses_exact_polyline_and_footprint_radius() -> None:
    network = _network(start=(0.0, 0.0), end=(10.0, 0.0))
    candidate = PointGeometry(x_km=3.0, y_km=4.0)

    assert distance_to_river_network_km(network, candidate, 0.0) == pytest.approx(4.0)
    assert distance_to_river_network_km(network, candidate, 1.5) == pytest.approx(2.5)
    assert distance_to_river_network_km(network, candidate, 5.0) == pytest.approx(0.0)


def test_p06_empty_potential_drainage_returns_positive_infinity() -> None:
    context = _context(version="0.2", potential=RiverNetwork())
    metrics = evaluate_site_metrics(
        context,
        PointGeometry(x_km=2.5, y_km=2.5),
        0.5,
    )
    assert metrics["distance_to_potential_drainage"] == inf


def test_p07_canonical_water_and_potential_drainage_distances_are_independent() -> None:
    candidate = PointGeometry(x_km=2.5, y_km=2.5)
    dry_water = np.zeros((5, 5), dtype=np.float32)

    far = _context(
        version="0.2",
        water=dry_water,
        potential=_network(start=(0.0, 0.0), end=(5.0, 0.0)),
    )
    near = _context(
        version="0.2",
        water=dry_water,
        potential=_network(start=(0.0, 2.5), end=(5.0, 2.5)),
    )
    far_metrics = evaluate_site_metrics(far, candidate, 0.0)
    near_metrics = evaluate_site_metrics(near, candidate, 0.0)

    assert far_metrics["distance_to_water"] == inf
    assert near_metrics["distance_to_water"] == inf
    assert far_metrics["distance_to_potential_drainage"] > 0.0
    assert near_metrics["distance_to_potential_drainage"] == pytest.approx(0.0)

    wet_water = np.zeros((5, 5), dtype=np.float32)
    wet_water[2, 2] = 1.0
    wet = _context(
        version="0.2",
        water=wet_water,
        potential=_network(start=(0.0, 2.5), end=(5.0, 2.5)),
    )
    wet_metrics = evaluate_site_metrics(wet, candidate, 0.0)

    assert wet_metrics["distance_to_water"] == pytest.approx(0.0)
    assert wet_metrics["distance_to_potential_drainage"] == pytest.approx(
        near_metrics["distance_to_potential_drainage"]
    )


def test_p08_metric_evaluation_does_not_mutate_upstream_state() -> None:
    plan, terrain, hydrology, surface = _states(version="0.2")
    elevation_before = terrain.elevation_m.copy()
    water_before = hydrology.water_depth_m.copy()
    moisture_before = surface.moisture.copy()
    vegetation_before = surface.vegetation_density.copy()
    temperature_before = surface.annual_mean_temperature_c.copy()
    precipitation_before = surface.annual_precipitation_mm.copy()
    potential_before = hydrology.potential_river_network

    context = SiteMetricContext.from_states(plan, terrain, hydrology, surface)
    evaluate_site_metrics(
        context,
        PointGeometry(x_km=2.5, y_km=2.5),
        1.5,
    )

    np.testing.assert_array_equal(terrain.elevation_m, elevation_before)
    np.testing.assert_array_equal(hydrology.water_depth_m, water_before)
    np.testing.assert_array_equal(surface.moisture, moisture_before)
    np.testing.assert_array_equal(surface.vegetation_density, vegetation_before)
    np.testing.assert_array_equal(
        surface.annual_mean_temperature_c,
        temperature_before,
    )
    np.testing.assert_array_equal(
        surface.annual_precipitation_mm,
        precipitation_before,
    )
    assert hydrology.potential_river_network == potential_before


def test_p09_metric_evaluation_is_exactly_replayable_without_rng() -> None:
    context = _context(version="0.2")
    candidate = PointGeometry(x_km=1.75, y_km=3.25)

    first = evaluate_site_metrics(context, candidate, 1.25)
    replay = evaluate_site_metrics(context, candidate, 1.25)

    assert first == replay


def test_p10_existing_preference_scoring_is_unchanged_for_existing_metric() -> None:
    sites = (
        EvaluatedSite(
            point=PointGeometry(x_km=1.0, y_km=1.0),
            metrics={
                "moisture_mean": 0.2,
                **{metric_id: 0.0 for metric_id in CORE_V02_SITE_METRIC_IDS if metric_id != "moisture_mean"},
            },
        ),
        EvaluatedSite(
            point=PointGeometry(x_km=2.0, y_km=2.0),
            metrics={
                "moisture_mean": 0.8,
                **{metric_id: 0.0 for metric_id in CORE_V02_SITE_METRIC_IDS if metric_id != "moisture_mean"},
            },
        ),
    )
    preference = SitePreference(
        metric="moisture_mean",
        evaluator="maximize",
        weight=1.0,
    )

    legacy = score_valid_sites(
        sites,
        (preference,),
        metric_ids=SITE_METRIC_IDS,
    )
    current = score_valid_sites(
        sites,
        (preference,),
        metric_ids=CORE_V02_SITE_METRIC_IDS,
    )

    assert tuple(site.suitability for site in current) == tuple(
        site.suitability for site in legacy
    )


def test_p11_core_v01_rejects_v02_only_requirement_and_preference() -> None:
    site = EvaluatedSite(
        point=PointGeometry(x_km=1.0, y_km=1.0),
        metrics={metric_id: 0.0 for metric_id in SITE_METRIC_IDS},
    )
    requirement = SiteRequirement(
        metric="temperature_mean",
        evaluator="greater_or_equal",
        value=0.0,
    )
    preference = SitePreference(
        metric="temperature_mean",
        evaluator="maximize",
        weight=1.0,
    )

    with pytest.raises(PlacementCandidateCapabilityError, match="unknown site metric"):
        filter_valid_sites(
            (site,),
            (requirement,),
            metric_ids=SITE_METRIC_IDS,
        )

    with pytest.raises(PlacementSelectionCapabilityError, match="unknown site metric"):
        score_valid_sites(
            (site,),
            (preference,),
            metric_ids=SITE_METRIC_IDS,
        )
