"""Dependent placement runtime primitives."""

from .candidates import (
    EvaluatedSite,
    PlacementCandidateCapabilityError,
    evaluate_candidate_sites,
    filter_valid_sites,
    generate_candidate_points,
    generate_valid_sites_for_feature,
    requirement_passes,
)
from .generate import generate_placement, placement_stage, validate_placement
from .selection import (
    PlacementSelectionCapabilityError,
    ScoredSite,
    choose_weighted_site,
    near_best_sites,
    preference_scores,
    sample_near_best_delta,
    score_valid_sites,
    select_final_site,
)
from .site_metrics import (
    CORE_V02_SITE_METRIC_IDS,
    SITE_METRIC_IDS,
    SiteMetricCapabilityError,
    SiteMetricContext,
    distance_to_river_network_km,
    evaluate_site_metrics,
    footprint_cells,
    site_metric_ids_for_plan_version,
)
from .state import PlacementState

__all__ = [
    "EvaluatedSite",
    "PlacementCandidateCapabilityError",
    "PlacementSelectionCapabilityError",
    "PlacementState",
    "CORE_V02_SITE_METRIC_IDS",
    "SITE_METRIC_IDS",
    "ScoredSite",
    "SiteMetricCapabilityError",
    "SiteMetricContext",
    "choose_weighted_site",
    "evaluate_candidate_sites",
    "distance_to_river_network_km",
    "evaluate_site_metrics",
    "filter_valid_sites",
    "footprint_cells",
    "generate_candidate_points",
    "generate_placement",
    "generate_valid_sites_for_feature",
    "near_best_sites",
    "placement_stage",
    "preference_scores",
    "requirement_passes",
    "sample_near_best_delta",
    "score_valid_sites",
    "select_final_site",
    "site_metric_ids_for_plan_version",
    "validate_placement",
]
