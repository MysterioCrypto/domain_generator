from __future__ import annotations

from dataclasses import dataclass
from math import inf, isfinite

from ..contracts.plan import ParameterType, ResolvedFeature, SitePreference
from ..pipeline.rng import RngFactory, RngKey, RngStage
from ..pipeline.sampling import SamplingCapabilityError, sample_resolved_parameter
from .candidates import EvaluatedSite
from .site_metrics import SITE_METRIC_IDS


class PlacementSelectionCapabilityError(RuntimeError):
    """Final dependent-placement selection cannot evaluate the supplied recipe/sites."""


@dataclass(frozen=True, slots=True)
class ScoredSite:
    site: EvaluatedSite
    preference_scores: tuple[float, ...]
    suitability: float


def _validate_preference(preference: SitePreference) -> None:
    if preference.metric not in SITE_METRIC_IDS:
        raise PlacementSelectionCapabilityError(
            f"unknown site metric {preference.metric!r}"
        )
    if preference.evaluator not in ("maximize", "minimize", "preferred_range"):
        raise PlacementSelectionCapabilityError(
            f"unsupported site preference evaluator {preference.evaluator!r}"
        )
    if preference.evaluator in ("maximize", "minimize"):
        if preference.min is not None or preference.max is not None:
            raise PlacementSelectionCapabilityError(
                f"{preference.evaluator} preference must not define min/max"
            )
    else:
        if preference.min is None or preference.max is None:
            raise PlacementSelectionCapabilityError(
                "preferred_range preference requires min/max"
            )
        if preference.min > preference.max:
            raise PlacementSelectionCapabilityError(
                "preferred_range preference requires min <= max"
            )


def _metric_values(
    sites: tuple[EvaluatedSite, ...],
    metric: str,
) -> tuple[float, ...]:
    values: list[float] = []
    for site in sites:
        try:
            value = float(site.metrics[metric])
        except KeyError as exc:
            raise PlacementSelectionCapabilityError(
                f"candidate metrics are missing {metric!r}"
            ) from exc
        if value == float("-inf"):
            raise PlacementSelectionCapabilityError(
                f"site metric {metric!r} contains unsupported -inf"
            )
        values.append(value)
    return tuple(values)


def preference_scores(
    sites: tuple[EvaluatedSite, ...],
    preference: SitePreference,
) -> tuple[float, ...]:
    """Normalize one intrinsic preference over the current valid-site set."""
    _validate_preference(preference)
    if not sites:
        return ()

    values = _metric_values(sites, preference.metric)
    first = values[0]
    if all(value == first for value in values):
        if first == inf or isfinite(first):
            return (1.0,) * len(values)
        raise PlacementSelectionCapabilityError(
            f"site metric {preference.metric!r} contains unsupported non-finite values"
        )

    if not all(isfinite(value) for value in values):
        raise PlacementSelectionCapabilityError(
            f"site metric {preference.metric!r} mixes finite and non-finite values"
        )

    observed_min = min(values)
    observed_max = max(values)

    if preference.evaluator == "maximize":
        denominator = observed_max - observed_min
        return tuple((value - observed_min) / denominator for value in values)

    if preference.evaluator == "minimize":
        denominator = observed_max - observed_min
        return tuple((observed_max - value) / denominator for value in values)

    assert preference.min is not None and preference.max is not None
    preferred_min = float(preference.min)
    preferred_max = float(preference.max)
    scores: list[float] = []
    for value in values:
        if preferred_min <= value <= preferred_max:
            score = 1.0
        elif value < preferred_min:
            denominator = preferred_min - observed_min
            score = 1.0 if denominator <= 0.0 else (value - observed_min) / denominator
        else:
            denominator = observed_max - preferred_max
            score = 1.0 if denominator <= 0.0 else (observed_max - value) / denominator
        scores.append(min(1.0, max(0.0, score)))
    return tuple(scores)


def score_valid_sites(
    valid_sites: tuple[EvaluatedSite, ...],
    preferences: tuple[SitePreference, ...],
) -> tuple[ScoredSite, ...]:
    """Score canonical valid sites using weighted intrinsic preferences."""
    sites = tuple(
        sorted(
            valid_sites,
            key=lambda site: (site.point.x_km, site.point.y_km),
        )
    )
    if not sites:
        return ()

    for preference in preferences:
        _validate_preference(preference)

    if not preferences:
        return tuple(
            ScoredSite(site=site, preference_scores=(), suitability=1.0)
            for site in sites
        )

    columns = tuple(preference_scores(sites, preference) for preference in preferences)
    total_weight = sum(float(preference.weight) for preference in preferences)
    if not isfinite(total_weight) or total_weight <= 0.0:
        raise PlacementSelectionCapabilityError(
            "site preference total weight must be finite and > 0"
        )

    scored: list[ScoredSite] = []
    for index, site in enumerate(sites):
        scores = tuple(column[index] for column in columns)
        suitability = sum(
            score * float(preference.weight)
            for score, preference in zip(scores, preferences)
        ) / total_weight
        if not isfinite(suitability) or not 0.0 <= suitability <= 1.0:
            raise PlacementSelectionCapabilityError(
                "computed site suitability must be finite and in [0, 1]"
            )
        scored.append(
            ScoredSite(
                site=site,
                preference_scores=scores,
                suitability=suitability,
            )
        )
    return tuple(scored)


def near_best_sites(
    scored_sites: tuple[ScoredSite, ...],
    near_best_delta: float,
) -> tuple[ScoredSite, ...]:
    if isinstance(near_best_delta, bool):
        raise PlacementSelectionCapabilityError("near_best_delta must be in [0, 1]")
    delta = float(near_best_delta)
    if not isfinite(delta) or not 0.0 <= delta <= 1.0:
        raise PlacementSelectionCapabilityError("near_best_delta must be in [0, 1]")
    if not scored_sites:
        return ()

    best = max(site.suitability for site in scored_sites)
    threshold = best - delta
    return tuple(site for site in scored_sites if site.suitability >= threshold)


def _parameter_key(
    *,
    attempt_index: int,
    feature_id: str,
    parameter_name: str,
) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.PLACEMENT,
        scope=("feature", feature_id, "parameter", parameter_name),
        purpose="sample",
    )


def sample_near_best_delta(
    feature: ResolvedFeature,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> float:
    expected_parameters = {"candidate_spacing_km", "near_best_delta"}
    actual_parameters = set(feature.effect.parameters)
    if actual_parameters != expected_parameters:
        raise PlacementSelectionCapabilityError(
            f"placement feature {feature.id!r} requires exactly effect parameters "
            f"{sorted(expected_parameters)!r}"
        )

    recipe = feature.effect.parameters["near_best_delta"]
    if recipe.type is not ParameterType.FLOAT:
        raise PlacementSelectionCapabilityError(
            "placement parameter 'near_best_delta' must be a float resolved parameter"
        )
    stream = rng_factory.stream(
        _parameter_key(
            attempt_index=attempt_index,
            feature_id=feature.id,
            parameter_name="near_best_delta",
        )
    )
    try:
        sampled = sample_resolved_parameter(recipe, stream)
    except SamplingCapabilityError as exc:
        raise PlacementSelectionCapabilityError(
            f"placement parameter 'near_best_delta' recipe is unsupported for feature "
            f"{feature.id!r}"
        ) from exc
    if isinstance(sampled, bool) or not isinstance(sampled, (int, float)):
        raise PlacementSelectionCapabilityError(
            "placement parameter 'near_best_delta' must resolve to a numeric value"
        )
    delta = float(sampled)
    if not isfinite(delta) or not 0.0 <= delta <= 1.0:
        raise PlacementSelectionCapabilityError(
            "placement parameter 'near_best_delta' must resolve to [0, 1]"
        )
    return delta


def _selection_key(*, attempt_index: int, feature_id: str) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.PLACEMENT,
        scope=("feature", feature_id, "site-selection"),
        purpose="weighted-choice",
    )


def choose_weighted_site(
    near_best: tuple[ScoredSite, ...],
    *,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> ScoredSite:
    if not near_best:
        raise PlacementSelectionCapabilityError(
            "weighted site selection requires a non-empty near-best set"
        )

    canonical = tuple(
        sorted(
            near_best,
            key=lambda scored: (scored.site.point.x_km, scored.site.point.y_km),
        )
    )
    weights = tuple(float(site.suitability) for site in canonical)
    if any(not isfinite(weight) or weight < 0.0 for weight in weights):
        raise PlacementSelectionCapabilityError(
            "weighted site selection requires finite non-negative suitability"
        )

    stream = rng_factory.stream(
        _selection_key(attempt_index=attempt_index, feature_id=feature_id)
    )
    total = sum(weights)
    if total == 0.0:
        return stream.choice(canonical)

    target = stream.uniform01() * total
    cumulative = 0.0
    for site, weight in zip(canonical, weights):
        cumulative += weight
        if target < cumulative:
            return site
    return canonical[-1]


def select_final_site(
    feature: ResolvedFeature,
    valid_sites: tuple[EvaluatedSite, ...],
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> ScoredSite | None:
    """Score, near-best filter and deterministically select one valid site."""
    if not valid_sites:
        return None
    if feature.effect.site_profile is None:
        raise PlacementSelectionCapabilityError(
            f"placement feature {feature.id!r} requires site_profile"
        )

    delta = sample_near_best_delta(
        feature,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
    scored = score_valid_sites(valid_sites, feature.effect.site_profile.preferences)
    near_best = near_best_sites(scored, delta)
    if not near_best:
        raise PlacementSelectionCapabilityError(
            "non-empty scored site set produced an empty near-best set"
        )
    return choose_weighted_site(
        near_best,
        feature_id=feature.id,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )
