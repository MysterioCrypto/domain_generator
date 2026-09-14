from .classification import classify_stream_mask, extract_lake_candidates
from .continuous import (
    build_continuous_river_network,
    choose_lake_outlets,
    continuous_routing_field,
    distributed_flow_accumulation_km2,
    generate_hydrology_v02,
    validate_hydrology_v02,
)
from .generate import (
    generate_hydrology as _generate_hydrology_v01,
    validate_hydrology as _validate_hydrology_v01,
)
from .ids import lake_feature_id
from .materialize import materialize_lake_features, validate_river_lake_references
from .network import build_river_network
from .routing import (
    D8_DIRECTIONS,
    HydrologyCapabilityError,
    PriorityFloodSurfaces,
    d8_flow_direction,
    flow_accumulation_km2,
    priority_flood_routing_surface,
    priority_flood_surfaces,
)
from .state import ContinuousRoutingField, HydrologyState, LakeCandidate, LakeOutlet
from .water import accepted_lake_cell_map, build_water_depth_m, river_depth_proxy_m


def generate_hydrology(plan, terrain):
    if plan.plan_version == "0.2":
        return generate_hydrology_v02(plan, terrain)
    return _generate_hydrology_v01(plan, terrain)


def validate_hydrology(plan, terrain, hydrology, *, attempt_index):
    if plan.plan_version == "0.2":
        return validate_hydrology_v02(
            plan,
            terrain,
            hydrology,
            attempt_index=attempt_index,
        )
    return _validate_hydrology_v01(
        plan,
        terrain,
        hydrology,
        attempt_index=attempt_index,
    )


def hydrology_stage(context, state):
    if state.terrain is None:
        return validate_hydrology(
            context.plan,
            None,
            None,
            attempt_index=context.attempt_index,
        )
    state.hydrology = generate_hydrology(context.plan, state.terrain)
    return validate_hydrology(
        context.plan,
        state.terrain,
        state.hydrology,
        attempt_index=context.attempt_index,
    )


__all__ = [
    "ContinuousRoutingField",
    "D8_DIRECTIONS",
    "HydrologyCapabilityError",
    "HydrologyState",
    "LakeCandidate",
    "LakeOutlet",
    "PriorityFloodSurfaces",
    "accepted_lake_cell_map",
    "build_continuous_river_network",
    "build_river_network",
    "build_water_depth_m",
    "choose_lake_outlets",
    "classify_stream_mask",
    "continuous_routing_field",
    "d8_flow_direction",
    "distributed_flow_accumulation_km2",
    "extract_lake_candidates",
    "flow_accumulation_km2",
    "generate_hydrology",
    "generate_hydrology_v02",
    "hydrology_stage",
    "lake_feature_id",
    "materialize_lake_features",
    "priority_flood_routing_surface",
    "priority_flood_surfaces",
    "river_depth_proxy_m",
    "validate_hydrology",
    "validate_hydrology_v02",
    "validate_river_lake_references",
]
