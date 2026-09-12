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
from .site_metrics import (
    SITE_METRIC_IDS,
    SiteMetricCapabilityError,
    SiteMetricContext,
    evaluate_site_metrics,
    footprint_cells,
)

__all__ = [
    "EvaluatedSite",
    "PlacementCandidateCapabilityError",
    "SITE_METRIC_IDS",
    "SiteMetricCapabilityError",
    "SiteMetricContext",
    "evaluate_candidate_sites",
    "evaluate_site_metrics",
    "filter_valid_sites",
    "footprint_cells",
    "generate_candidate_points",
    "generate_valid_sites_for_feature",
    "requirement_passes",
]
