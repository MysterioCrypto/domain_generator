import numpy as np
import pytest
from pydantic import ValidationError

from domain_generator.assembly import (
    DomainAssemblyError,
    assemble_domain,
    semantic_generation_config_fingerprint,
)
from domain_generator.compiler import domain_spec_fingerprint, semantic_plan_fingerprint
from domain_generator.contracts.config import GenerationConfig
from domain_generator.contracts.data import (
    GeneratedFeatureSource,
    HydroFeature,
    LakeProperties,
    RiverNetwork,
)
from domain_generator.contracts.geometry import RegionPolygon, RegionSet, WorldPoint
from domain_generator.contracts.layout import LayoutCandidate
from domain_generator.contracts.plan import GenerationPlan
from domain_generator.contracts.spec import DomainSpec
from domain_generator.contracts.validation import ValidationResult
from domain_generator.hydrology.state import HydrologyState
from domain_generator.pipeline.attempts import CandidateState, DomainCandidate
from domain_generator.poi.state import PlacementState
from domain_generator.surface.state import SurfaceState
from domain_generator.terrain.state import TerrainState


def _spec_data(*, feature_id: str = "hill", label: str = "Assembler Example") -> dict:
    return {
        "schema_version": "0.1",
        "id": "assembler-domain",
        "label": label,
        "seed": 7,
        "domain": {"size": {"width_km": 2.0, "height_km": 2.0}},
        "simulation": {"cell_size_km": 1.0},
        "hydrology": {
            "stream_threshold_km2": 1.0,
            "lake_min_area_km2": 1.0,
            "lake_min_depth_m": 1.0,
            "river_depth_at_threshold_m": 0.5,
            "river_depth_exponent": 0.3,
        },
        "surface": {
            "moisture_base": 0.25,
            "water_moisture_boost": 0.5,
            "water_moisture_decay_km": 2.0,
            "moisture_noise_amplitude": 0.1,
            "moisture_noise_scale_km": 3.0,
            "vegetation_slope_zero_deg": 45.0,
        },
        "features": [
            {
                "id": feature_id,
                "preset": "hill_preset",
                "label": "Hill",
                "tags": ["test"],
            }
        ],
        "constraints": [],
    }


def _spec() -> DomainSpec:
    return DomainSpec.model_validate(_spec_data())


def _plan(spec: DomainSpec) -> GenerationPlan:
    return GenerationPlan.model_validate(
        {
            "plan_version": "0.1",
            "source": {
                "spec_id": spec.id,
                "spec_schema_version": spec.schema_version,
                "spec_fingerprint": domain_spec_fingerprint(spec),
                "generator_version": "0.1.0.dev0",
            },
            "seed": spec.seed,
            "domain": {"width_km": 2.0, "height_km": 2.0},
            "grid": {"cell_size_km": 1.0, "rows": 2, "columns": 2},
            "hydrology": {
                "stream_threshold_km2": 1.0,
                "lake_min_area_km2": 1.0,
                "lake_min_depth_m": 1.0,
                "river_depth_at_threshold_m": 0.5,
                "river_depth_exponent": 0.3,
            },
            "surface": {
                "moisture_base": 0.25,
                "water_moisture_boost": 0.5,
                "water_moisture_decay_km": 2.0,
                "moisture_noise_amplitude": 0.1,
                "moisture_noise_scale_km": 3.0,
                "vegetation_slope_zero_deg": 45.0,
            },
            "features": [
                {
                    "id": "hill",
                    "metadata": {
                        "label": "Hill",
                        "tags": ["test"],
                        "source_preset": "hill_preset",
                    },
                    "family": "terrain",
                    "layout": {"mode": "geometry", "shape": "point", "parameters": {}},
                    "effect": {"stage": "terrain", "operator": "raise", "parameters": {}},
                }
            ],
            "constraints": [],
        }
    )


def _config(*, debug: bool = False, max_attempts: int = 4) -> GenerationConfig:
    return GenerationConfig.model_validate(
        {
            "generation_config_version": "0.1",
            "semantic": {"max_attempts": max_attempts, "target_valid_candidates": 1},
            "observability": {"debug": debug},
        }
    )


def _hydro_feature() -> HydroFeature:
    return HydroFeature(
        source=GeneratedFeatureSource(system="hydrology"),
        geometry=RegionSet(
            polygons=(
                RegionPolygon(
                    outer=(
                        WorldPoint(x_km=0.0, y_km=0.0),
                        WorldPoint(x_km=1.0, y_km=0.0),
                        WorldPoint(x_km=1.0, y_km=1.0),
                        WorldPoint(x_km=0.0, y_km=1.0),
                    )
                ),
            )
        ),
        properties=LakeProperties(
            area_km2=1.0,
            surface_elevation_m=0.0,
            max_depth_m=1.0,
        ),
    )


def _candidate(
    plan: GenerationPlan,
    *,
    dtype=np.float32,
    hydro_features: dict[str, HydroFeature] | None = None,
) -> DomainCandidate:
    shape = (2, 2)
    elevation = np.zeros(shape, dtype=dtype)
    water = np.zeros(shape, dtype=dtype)
    moisture = np.full(shape, 0.5, dtype=dtype)
    vegetation = np.full(shape, 0.25, dtype=dtype)

    layout = LayoutCandidate.model_validate(
        {
            "layout_version": "0.1",
            "source_plan": {"fingerprint": semantic_plan_fingerprint(plan)},
            "attempt_index": 0,
            "geometry_realizations": {
                "hill": {"type": "point", "x_km": 0.5, "y_km": 0.5}
            },
            "placement_reservations": {},
        }
    )
    state = CandidateState(
        attempt_index=0,
        layout=layout,
        terrain=TerrainState(elevation_m=elevation),
        hydrology=HydrologyState(
            routing_elevation_m=elevation.copy(),
            fill_elevation_m=elevation.copy(),
            flow_direction=np.full(shape, -1, dtype=np.int8),
            flow_accumulation_km2=np.ones(shape, dtype=np.float32),
            stream_mask=np.zeros(shape, dtype=bool),
            lake_candidates=(),
            river_network=RiverNetwork(),
            water_depth_m=water,
            lake_features={} if hydro_features is None else hydro_features,
        ),
        surface=SurfaceState(moisture=moisture, vegetation_density=vegetation),
        placement=PlacementState(final_points={}),
    )
    final = ValidationResult.model_validate(
        {
            "validation_version": "0.1",
            "attempt_index": 0,
            "stage": "final",
            "engine_invariants": {"passed": True, "results": []},
            "hard_constraints": {"passed": True, "results": []},
            "soft_constraints": {"results": []},
            "ranking": {
                "worst_effective_violation": 0.0,
                "weighted_mean_score": 1.0,
            },
        }
    )
    return DomainCandidate(attempt_index=0, state=state, validations=(final,))


def test_semantic_generation_config_fingerprint_ignores_observability() -> None:
    assert semantic_generation_config_fingerprint(_config(debug=False)) == semantic_generation_config_fingerprint(
        _config(debug=True)
    )
    assert semantic_generation_config_fingerprint(_config(max_attempts=4)) != semantic_generation_config_fingerprint(
        _config(max_attempts=5)
    )


def test_domain_spec_rejects_generated_lake_namespace() -> None:
    with pytest.raises(ValidationError, match="reserved generated hydro namespace"):
        DomainSpec.model_validate(_spec_data(feature_id="lake-0001"))
    with pytest.raises(ValidationError, match="reserved generated hydro namespace"):
        DomainSpec.model_validate(_spec_data(feature_id="lake-10000"))

    allowed = DomainSpec.model_validate(_spec_data(feature_id="lake-123"))
    assert allowed.features[0].id == "lake-123"


def test_assemble_domain_packages_canonical_data_and_readonly_copies() -> None:
    spec = _spec()
    plan = _plan(spec)
    candidate = _candidate(plan, hydro_features={"lake-0001": _hydro_feature()})

    assembly = assemble_domain(
        spec=spec,
        plan=plan,
        config=_config(debug=True),
        candidate=candidate,
    )

    assert assembly.data.identity.id == "assembler-domain"
    assert assembly.data.identity.label == "Assembler Example"
    assert assembly.data.provenance.spec_fingerprint == domain_spec_fingerprint(spec)
    assert assembly.data.provenance.plan_fingerprint == semantic_plan_fingerprint(plan)
    assert assembly.data.provenance.accepted_attempt_index == 0
    assert assembly.data.provenance.generator.name == "domain_generator"
    assert assembly.data.provenance.rng_version == 1
    assert list(assembly.data.fields) == [
        "elevation",
        "water_depth",
        "moisture",
        "vegetation_density",
    ]
    assert list(assembly.data.features) == ["hill", "lake-0001"]
    assert assembly.data.features["hill"].source.preset == "hill_preset"
    assert list(assembly.data.networks) == ["rivers"]

    source = candidate.state.terrain.elevation_m
    payload = assembly.field_payloads["elevation"]
    assert payload.dtype == np.dtype(np.float32)
    assert payload.shape == (2, 2)
    assert not payload.flags.writeable
    assert not np.shares_memory(source, payload)

    source[0, 0] = 9.0
    assert payload[0, 0] == 0.0
    with pytest.raises(ValueError):
        payload[0, 0] = 1.0
    with pytest.raises(TypeError):
        assembly.field_payloads["extra"] = np.zeros((2, 2), dtype=np.float32)


def test_assemble_domain_rejects_wrong_field_dtype() -> None:
    spec = _spec()
    plan = _plan(spec)
    with pytest.raises(DomainAssemblyError, match="dtype must be float32"):
        assemble_domain(spec=spec, plan=plan, config=_config(), candidate=_candidate(plan, dtype=np.float64))


def test_assemble_domain_rejects_spec_plan_provenance_mismatch() -> None:
    spec = _spec()
    plan = _plan(spec)
    changed_spec = DomainSpec.model_validate(_spec_data(label="Changed"))
    with pytest.raises(DomainAssemblyError, match="fingerprint"):
        assemble_domain(spec=changed_spec, plan=plan, config=_config(), candidate=_candidate(plan))


def test_assemble_domain_rejects_specified_generated_feature_collision() -> None:
    spec = _spec()
    plan = _plan(spec)
    candidate = _candidate(plan, hydro_features={"hill": _hydro_feature()})
    with pytest.raises(DomainAssemblyError, match="feature ids collide"):
        assemble_domain(spec=spec, plan=plan, config=_config(), candidate=candidate)
