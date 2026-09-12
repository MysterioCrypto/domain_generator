from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from ..contracts.common import (
    ConstraintStrength,
    DomainCompass,
    FeaturePart,
    NumericRangeOverride,
    OneOfOverride,
    Relation,
)
from ..contracts.plan import (
    CategoricalSampler,
    ChoiceParameter,
    CompiledConstraint,
    CompiledEvaluator,
    CompiledFeatureRef,
    CompiledPoint,
    CompiledPredicate,
    CompiledRectangle,
    EffectRecipe,
    FeatureMetadata,
    FixedParameter,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
    ParameterType,
    PlanDomain,
    PlanGrid,
    PlanSource,
    RangeParameter,
    ReservationLayoutRecipe,
    ResolvedFeature,
    TriangularSampler,
)
from ..contracts.spec import (
    ConstraintSpec,
    DomainAnchorSelector,
    DomainRegionSelector,
    DomainSpec,
    FeatureSelector,
    KmPoint,
    KmRegion,
    NormalizedPoint,
    NormalizedRegion,
    PointSelector,
    RegionSelector,
    SpatialSelector,
)
from ..pipeline.rng import UINT64_MAX
from ..presets import PresetDefinition, PresetRegistry, PresetRegistryError


class CompilerError(ValueError):
    """DomainSpec is structurally valid but unsupported or semantically invalid."""


_PARTS_BY_SHAPE: dict[GeometryShape, frozenset[FeaturePart]] = {
    GeometryShape.POINT: frozenset({FeaturePart.WHOLE, FeaturePart.CENTER}),
    GeometryShape.CORRIDOR: frozenset(
        {
            FeaturePart.WHOLE,
            FeaturePart.CENTER,
            FeaturePart.START,
            FeaturePart.END,
            FeaturePart.ENDPOINTS,
        }
    ),
    GeometryShape.BAND: frozenset(
        {
            FeaturePart.WHOLE,
            FeaturePart.CENTER,
            FeaturePart.START,
            FeaturePart.END,
            FeaturePart.ENDPOINTS,
            FeaturePart.BOUNDARY,
        }
    ),
    GeometryShape.AREA: frozenset(
        {FeaturePart.WHOLE, FeaturePart.CENTER, FeaturePart.BOUNDARY}
    ),
}

_ANCHOR_NORMALIZED: dict[DomainCompass, tuple[float, float]] = {
    DomainCompass.SOUTHWEST: (0.0, 0.0),
    DomainCompass.SOUTH: (0.5, 0.0),
    DomainCompass.SOUTHEAST: (1.0, 0.0),
    DomainCompass.WEST: (0.0, 0.5),
    DomainCompass.CENTER: (0.5, 0.5),
    DomainCompass.EAST: (1.0, 0.5),
    DomainCompass.NORTHWEST: (0.0, 1.0),
    DomainCompass.NORTH: (0.5, 1.0),
    DomainCompass.NORTHEAST: (1.0, 1.0),
}

_REGION_INDEX: dict[DomainCompass, tuple[int, int]] = {
    DomainCompass.SOUTHWEST: (0, 0),
    DomainCompass.SOUTH: (1, 0),
    DomainCompass.SOUTHEAST: (2, 0),
    DomainCompass.WEST: (0, 1),
    DomainCompass.CENTER: (1, 1),
    DomainCompass.EAST: (2, 1),
    DomainCompass.NORTHWEST: (0, 2),
    DomainCompass.NORTH: (1, 2),
    DomainCompass.NORTHEAST: (2, 2),
}


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def domain_spec_fingerprint(spec: DomainSpec) -> str:
    payload = spec.model_dump(mode="json", by_alias=True, exclude_none=False)
    return "sha256:" + sha256(_canonical_json_bytes(payload)).hexdigest()


def semantic_plan_fingerprint(plan: GenerationPlan) -> str:
    """Fingerprint only executable Plan semantics, excluding provenance/metadata."""
    features: list[dict[str, object]] = []
    for feature in sorted(plan.features, key=lambda item: item.id):
        features.append(
            {
                "id": feature.id,
                "family": feature.family.value,
                "layout": feature.layout.model_dump(mode="json", by_alias=True, exclude_none=False),
                "effect": feature.effect.model_dump(mode="json", by_alias=True, exclude_none=False),
            }
        )

    constraints: list[dict[str, object]] = []
    for constraint in sorted(plan.constraints, key=lambda item: item.id):
        item = constraint.model_dump(mode="json", by_alias=True, exclude_none=False)
        item.pop("source_relation", None)
        constraints.append(item)

    payload = {
        "plan_version": plan.plan_version,
        "seed": plan.seed,
        "domain": plan.domain.model_dump(mode="json"),
        "grid": plan.grid.model_dump(mode="json"),
        "features": features,
        "constraints": constraints,
    }
    return "sha256:" + sha256(_canonical_json_bytes(payload)).hexdigest()


def _normalize_fixed_value(value: object, parameter_type: ParameterType) -> object:
    if parameter_type is ParameterType.FLOAT:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CompilerError("float parameter override must be numeric")
        return float(value)
    if parameter_type is ParameterType.INTEGER:
        if isinstance(value, bool) or not isinstance(value, int):
            raise CompilerError("integer parameter override must be an integer")
        return value
    if parameter_type is ParameterType.BOOLEAN:
        if not isinstance(value, bool):
            raise CompilerError("boolean parameter override must be boolean")
        return value
    if parameter_type is ParameterType.ENUM:
        if not isinstance(value, str):
            raise CompilerError("enum parameter override must be a string")
        return value
    raise CompilerError(f"unsupported parameter type: {parameter_type}")


def _compile_parameter_override(name: str, default, override):
    if isinstance(override, NumericRangeOverride):
        if not isinstance(default, RangeParameter):
            raise CompilerError(f"parameter {name!r} does not expose a numeric range")

        minimum = override.min
        maximum = override.max
        if default.type is ParameterType.FLOAT:
            minimum = float(minimum)
            maximum = float(maximum)
        elif default.type is ParameterType.INTEGER:
            if (
                isinstance(minimum, bool)
                or isinstance(maximum, bool)
                or not isinstance(minimum, int)
                or not isinstance(maximum, int)
            ):
                raise CompilerError(f"integer parameter {name!r} requires integer min/max")

        if minimum < default.min or maximum > default.max:
            raise CompilerError(
                f"parameter {name!r} override range must stay inside preset range "
                f"[{default.min}, {default.max}]"
            )
        if isinstance(default.sampler, TriangularSampler):
            if not minimum <= default.sampler.mode <= maximum:
                raise CompilerError(
                    f"parameter {name!r} range excludes preset triangular sampler mode"
                )
        return RangeParameter(
            type=default.type,
            min=minimum,
            max=maximum,
            sampler=default.sampler,
        )

    if isinstance(override, OneOfOverride):
        if not isinstance(default, ChoiceParameter):
            raise CompilerError(f"parameter {name!r} does not expose enum choices")
        unknown = set(override.one_of) - set(default.values)
        if unknown:
            raise CompilerError(
                f"parameter {name!r} contains choices outside preset domain: {sorted(unknown)}"
            )
        return ChoiceParameter(
            values=override.one_of,
            sampler=CategoricalSampler(),
        )

    parameter_type = default.type
    value = _normalize_fixed_value(override, parameter_type)

    if isinstance(default, RangeParameter):
        if value < default.min or value > default.max:
            raise CompilerError(
                f"parameter {name!r} fixed override must stay inside preset range "
                f"[{default.min}, {default.max}]"
            )
    elif isinstance(default, ChoiceParameter):
        if value not in default.values:
            raise CompilerError(
                f"parameter {name!r} value {value!r} is outside preset choices"
            )

    return FixedParameter(type=parameter_type, value=value)


def _resolve_feature(feature, preset: PresetDefinition) -> ResolvedFeature:
    if isinstance(preset.layout, GeometryLayoutRecipe):
        layout_defaults = dict(preset.layout.parameters)
    else:
        layout_defaults = {}
    effect_defaults = dict(preset.effect.parameters)

    known_parameters = set(layout_defaults) | set(effect_defaults)
    unknown = set(feature.parameters) - known_parameters
    if unknown:
        raise CompilerError(
            f"feature {feature.id!r} has unknown parameters for preset {preset.id!r}: "
            f"{sorted(unknown)}"
        )

    resolved_layout = dict(layout_defaults)
    resolved_effect = dict(effect_defaults)
    for name, override in feature.parameters.items():
        if name in layout_defaults:
            resolved_layout[name] = _compile_parameter_override(
                name, layout_defaults[name], override
            )
        else:
            resolved_effect[name] = _compile_parameter_override(
                name, effect_defaults[name], override
            )

    layout = preset.layout
    if isinstance(layout, GeometryLayoutRecipe):
        layout = layout.model_copy(update={"parameters": resolved_layout})
    effect = preset.effect.model_copy(update={"parameters": resolved_effect})

    return ResolvedFeature(
        id=feature.id,
        metadata=FeatureMetadata(
            label=feature.label,
            tags=feature.tags,
            source_preset=feature.preset,
        ),
        family=preset.family,
        layout=layout,
        effect=effect,
    )


def _shape_of_feature(feature: ResolvedFeature) -> GeometryShape:
    if isinstance(feature.layout, GeometryLayoutRecipe):
        return feature.layout.shape
    if isinstance(feature.layout, ReservationLayoutRecipe):
        return feature.layout.final_shape
    raise CompilerError(f"unsupported layout recipe for feature {feature.id!r}")


def _is_deferred(feature: ResolvedFeature) -> bool:
    return isinstance(feature.layout, ReservationLayoutRecipe)


def _compile_selector(
    selector: SpatialSelector,
    *,
    features_by_id: dict[str, ResolvedFeature],
    width_km: float,
    height_km: float,
):
    if isinstance(selector, FeatureSelector):
        try:
            feature = features_by_id[selector.feature]
        except KeyError as exc:
            raise CompilerError(f"unknown feature reference: {selector.feature!r}") from exc
        shape = _shape_of_feature(feature)
        if selector.part not in _PARTS_BY_SHAPE[shape]:
            raise CompilerError(
                f"feature {selector.feature!r} shape {shape.value!r} does not support "
                f"part {selector.part.value!r}"
            )
        return CompiledFeatureRef(feature_id=selector.feature, part=selector.part)

    if isinstance(selector, DomainAnchorSelector):
        nx, ny = _ANCHOR_NORMALIZED[selector.domain_anchor]
        return CompiledPoint(x_km=width_km * nx, y_km=height_km * ny)

    if isinstance(selector, DomainRegionSelector):
        ix, iy = _REGION_INDEX[selector.domain_region]
        return CompiledRectangle(
            min_x_km=width_km * ix / 3.0,
            max_x_km=width_km * (ix + 1) / 3.0,
            min_y_km=height_km * iy / 3.0,
            max_y_km=height_km * (iy + 1) / 3.0,
        )

    if isinstance(selector, PointSelector):
        if isinstance(selector.point, KmPoint):
            return CompiledPoint(x_km=selector.point.x_km, y_km=selector.point.y_km)
        if isinstance(selector.point, NormalizedPoint):
            return CompiledPoint(
                x_km=width_km * selector.point.normalized.x,
                y_km=height_km * selector.point.normalized.y,
            )

    if isinstance(selector, RegionSelector):
        if isinstance(selector.region, KmRegion):
            return CompiledRectangle(
                min_x_km=float(selector.region.x_km.min),
                max_x_km=float(selector.region.x_km.max),
                min_y_km=float(selector.region.y_km.min),
                max_y_km=float(selector.region.y_km.max),
            )
        if isinstance(selector.region, NormalizedRegion):
            region = selector.region.normalized
            return CompiledRectangle(
                min_x_km=width_km * region.x.min,
                max_x_km=width_km * region.x.max,
                min_y_km=height_km * region.y.min,
                max_y_km=height_km * region.y.max,
            )

    raise CompilerError(f"unsupported spatial selector: {selector!r}")


def _referenced_feature_id(selector: SpatialSelector) -> str | None:
    return selector.feature if isinstance(selector, FeatureSelector) else None


def _validate_deferred_dependency(
    constraint: ConstraintSpec,
    *,
    features_by_id: dict[str, ResolvedFeature],
) -> None:
    subject_id = _referenced_feature_id(constraint.subject)
    target_id = _referenced_feature_id(constraint.target)
    if subject_id is None or target_id is None:
        return
    if subject_id not in features_by_id or target_id not in features_by_id:
        return
    if _is_deferred(features_by_id[subject_id]) and _is_deferred(features_by_id[target_id]):
        raise CompilerError(
            f"constraint {constraint.id!r} creates unsupported deferred-to-deferred dependency"
        )


def _compile_hard_constraint(
    constraint: ConstraintSpec,
    *,
    features_by_id: dict[str, ResolvedFeature],
    width_km: float,
    height_km: float,
) -> CompiledConstraint:
    if constraint.strength is not ConstraintStrength.HARD:
        raise CompilerError(
            f"soft constraint compilation is not implemented in this compiler slice: {constraint.id!r}"
        )

    _validate_deferred_dependency(constraint, features_by_id=features_by_id)
    subject = _compile_selector(
        constraint.subject,
        features_by_id=features_by_id,
        width_km=width_km,
        height_km=height_km,
    )
    target = _compile_selector(
        constraint.target,
        features_by_id=features_by_id,
        width_km=width_km,
        height_km=height_km,
    )

    params = constraint.parameters
    relation = constraint.relation
    if relation is Relation.NEAR:
        evaluator_type, predicate_type, value, unit = (
            "distance",
            "less_or_equal",
            params["max_distance_km"],
            "km",
        )
    elif relation is Relation.FAR_FROM:
        evaluator_type, predicate_type, value, unit = (
            "distance",
            "greater_or_equal",
            params["min_distance_km"],
            "km",
        )
    elif relation is Relation.INSIDE:
        evaluator_type, predicate_type, value, unit = (
            "contained_fraction",
            "greater_or_equal",
            1.0,
            None,
        )
    elif relation is Relation.OUTSIDE:
        evaluator_type, predicate_type, value, unit = (
            "overlap_fraction",
            "less_or_equal",
            0.0,
            None,
        )
    elif relation is Relation.CROSSES:
        minimum = params.get("minimum_crossing_length_km")
        evaluator_type = "crossing_length"
        if minimum is None or minimum == 0.0:
            predicate_type, value = "greater_than", 0.0
        else:
            predicate_type, value = "greater_or_equal", minimum
        unit = "km"
    elif relation is Relation.OVERLAPS:
        evaluator_type, predicate_type, value, unit = (
            "overlap_fraction",
            "greater_or_equal",
            params["minimum_fraction"],
            None,
        )
    elif relation is Relation.ADJACENT:
        evaluator_type, predicate_type, value, unit = (
            "boundary_gap",
            "less_or_equal",
            params["max_gap_km"],
            "km",
        )
    else:
        raise CompilerError(f"unsupported relation: {relation.value!r}")

    return CompiledConstraint(
        id=constraint.id,
        source_relation=relation,
        strength=ConstraintStrength.HARD,
        evaluator=CompiledEvaluator(
            type=evaluator_type,
            subject=subject,
            target=target,
        ),
        predicate=CompiledPredicate(type=predicate_type, value=value),
        unit=unit,
    )


def compile_domain_spec(
    spec: DomainSpec,
    *,
    registry: PresetRegistry,
    generator_version: str,
) -> GenerationPlan:
    """Compile a structurally valid DomainSpec into an immutable resolved plan."""
    if not isinstance(generator_version, str) or not generator_version:
        raise CompilerError("generator_version must be a non-empty string")
    if isinstance(spec.seed, bool) or not 0 <= spec.seed <= UINT64_MAX:
        raise CompilerError("DomainSpec seed must be in unsigned uint64 range for RNG v1")

    resolved_features: list[ResolvedFeature] = []
    for feature in spec.features:
        try:
            preset = registry.get(feature.preset)
        except PresetRegistryError as exc:
            raise CompilerError(str(exc)) from exc
        resolved_features.append(_resolve_feature(feature, preset))

    features_by_id = {feature.id: feature for feature in resolved_features}
    width_km = spec.domain.size.width_km
    height_km = spec.domain.size.height_km
    compiled_constraints = tuple(
        _compile_hard_constraint(
            constraint,
            features_by_id=features_by_id,
            width_km=width_km,
            height_km=height_km,
        )
        for constraint in spec.constraints
    )

    cell = Decimal(str(spec.simulation.cell_size_km))
    columns = int(Decimal(str(width_km)) / cell)
    rows = int(Decimal(str(height_km)) / cell)

    return GenerationPlan(
        plan_version="0.1",
        source=PlanSource(
            spec_id=spec.id,
            spec_schema_version="0.1",
            spec_fingerprint=domain_spec_fingerprint(spec),
            generator_version=generator_version,
        ),
        seed=spec.seed,
        domain=PlanDomain(width_km=width_km, height_km=height_km),
        grid=PlanGrid(
            cell_size_km=spec.simulation.cell_size_km,
            rows=rows,
            columns=columns,
        ),
        features=tuple(resolved_features),
        constraints=compiled_constraints,
    )
