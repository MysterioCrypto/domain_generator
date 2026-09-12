from __future__ import annotations

from math import hypot, inf

from ..compiler.compile import semantic_plan_fingerprint
from ..contracts.common import FeaturePart
from ..contracts.geometry import (
    AreaGeometry,
    BandGeometry,
    CorridorGeometry,
    PointGeometry,
    WidthSample,
    WorldPoint,
)
from ..contracts.layout import LayoutCandidate, SourcePlanRef
from ..contracts.plan import (
    CompiledConstraint,
    CompiledFeatureRef,
    CompiledPoint,
    CompiledRectangle,
    CompiledSpatialRef,
    GenerationPlan,
    GeometryLayoutRecipe,
    GeometryShape,
    ParameterType,
)
from ..contracts.validation import (
    EngineInvariantGroup,
    EngineInvariantResult,
    HardConstraintGroup,
    HardConstraintResult,
    Measurement,
    PredicateSnapshot,
    SoftConstraintGroup,
    ValidationResult,
    ValidationStage,
)
from ..pipeline.attempts import AttemptContext, CandidateState
from ..pipeline.rng import RngFactory, RngKey, RngStage
from ..pipeline.sampling import sample_resolved_parameter
from .area import (
    AreaBoundaryView,
    AreaLayoutCapabilityError,
    area_centroid,
    area_has_zero_length_edge,
    area_inside_domain,
    area_is_ccw_nondegenerate,
    area_self_intersects,
    distance_point_area_boundary,
    distance_point_area_whole,
    generate_area_geometry,
    point_in_area,
)

GEOMETRY_EPSILON_KM = 1e-12


class LayoutCapabilityError(RuntimeError):
    """The current layout implementation cannot execute a valid Plan construct yet."""


def _point_stream_key(attempt_index: int, feature_id: str) -> RngKey:
    # Preserve the exact point-layout namespace accepted in point-layout v0.1.
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.LAYOUT,
        scope=("feature", feature_id, "geometry", "point"),
        purpose="position",
    )


def _corridor_stream_key(attempt_index: int, feature_id: str, purpose: str) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.LAYOUT,
        scope=("feature", feature_id, "geometry", "corridor"),
        purpose=purpose,
    )


def _band_stream_key(attempt_index: int, feature_id: str, purpose: str) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.LAYOUT,
        scope=("feature", feature_id, "geometry", "band"),
        purpose=purpose,
    )


def _parameter_stream_key(attempt_index: int, feature_id: str, parameter_name: str) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.LAYOUT,
        scope=("feature", feature_id, "parameter", parameter_name),
        purpose="sample",
    )


def _generate_point(
    plan: GenerationPlan,
    *,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> PointGeometry:
    stream = rng_factory.stream(_point_stream_key(attempt_index, feature_id))
    return PointGeometry(
        x_km=plan.domain.width_km * stream.uniform01(),
        y_km=plan.domain.height_km * stream.uniform01(),
    )


def _sample_corridor_parameters(
    layout: GeometryLayoutRecipe,
    *,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> tuple[int, float]:
    expected = {"control_point_count", "curvature"}
    actual = set(layout.parameters)
    if actual != expected:
        raise LayoutCapabilityError(
            f"corridor feature {feature_id!r} requires exactly layout parameters "
            f"{sorted(expected)}, got {sorted(actual)}"
        )

    sampled: dict[str, object] = {}
    for name in sorted(expected):
        stream = rng_factory.stream(_parameter_stream_key(attempt_index, feature_id, name))
        sampled[name] = sample_resolved_parameter(layout.parameters[name], stream)

    control_point_count = sampled["control_point_count"]
    curvature = sampled["curvature"]
    if isinstance(control_point_count, bool) or not isinstance(control_point_count, int):
        raise LayoutCapabilityError("corridor control_point_count must resolve to integer")
    if control_point_count < 0:
        raise LayoutCapabilityError("corridor control_point_count must be >= 0")
    if isinstance(curvature, bool) or not isinstance(curvature, (int, float)):
        raise LayoutCapabilityError("corridor curvature must resolve to numeric value")
    curvature_value = float(curvature)
    if not 0.0 <= curvature_value <= 1.0:
        raise LayoutCapabilityError("corridor curvature must resolve inside [0, 1]")
    return control_point_count, curvature_value


def _sample_band_parameters(
    layout: GeometryLayoutRecipe,
    *,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> tuple[int, float, int]:
    expected = {"control_point_count", "curvature", "width_km", "width_sample_count"}
    actual = set(layout.parameters)
    if actual != expected:
        raise LayoutCapabilityError(
            f"band feature {feature_id!r} requires exactly layout parameters "
            f"{sorted(expected)}, got {sorted(actual)}"
        )

    width_recipe = layout.parameters["width_km"]
    if width_recipe.type is not ParameterType.FLOAT:
        raise LayoutCapabilityError("band width_km must be a float resolved parameter")

    sampled: dict[str, object] = {}
    for name in ("control_point_count", "curvature", "width_sample_count"):
        stream = rng_factory.stream(_parameter_stream_key(attempt_index, feature_id, name))
        sampled[name] = sample_resolved_parameter(layout.parameters[name], stream)

    control_point_count = sampled["control_point_count"]
    curvature = sampled["curvature"]
    width_sample_count = sampled["width_sample_count"]

    if isinstance(control_point_count, bool) or not isinstance(control_point_count, int):
        raise LayoutCapabilityError("band control_point_count must resolve to integer")
    if control_point_count < 0:
        raise LayoutCapabilityError("band control_point_count must be >= 0")
    if isinstance(curvature, bool) or not isinstance(curvature, (int, float)):
        raise LayoutCapabilityError("band curvature must resolve to numeric value")
    curvature_value = float(curvature)
    if not 0.0 <= curvature_value <= 1.0:
        raise LayoutCapabilityError("band curvature must resolve inside [0, 1]")
    if isinstance(width_sample_count, bool) or not isinstance(width_sample_count, int):
        raise LayoutCapabilityError("band width_sample_count must resolve to integer")
    if width_sample_count < 2:
        raise LayoutCapabilityError("band width_sample_count must be >= 2")

    return control_point_count, curvature_value, width_sample_count


def _sample_band_width(recipe, stream) -> float:
    sampled = sample_resolved_parameter(recipe, stream)
    if isinstance(sampled, bool) or not isinstance(sampled, (int, float)):
        raise LayoutCapabilityError("band width_km must resolve to numeric value")
    value = float(sampled)
    if value <= 0.0:
        raise LayoutCapabilityError("band width_km must resolve to > 0")
    return value


def _ray_distance_to_domain_boundary(
    point: WorldPoint,
    *,
    dx: float,
    dy: float,
    width_km: float,
    height_km: float,
) -> float:
    distances: list[float] = []
    if dx > 0.0:
        distances.append((width_km - point.x_km) / dx)
    elif dx < 0.0:
        distances.append((0.0 - point.x_km) / dx)

    if dy > 0.0:
        distances.append((height_km - point.y_km) / dy)
    elif dy < 0.0:
        distances.append((0.0 - point.y_km) / dy)

    positive = [value for value in distances if value >= 0.0]
    return min(positive) if positive else inf


def _generate_corridor(
    plan: GenerationPlan,
    layout: GeometryLayoutRecipe,
    *,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> CorridorGeometry:
    control_point_count, curvature = _sample_corridor_parameters(
        layout,
        feature_id=feature_id,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )

    start_stream = rng_factory.stream(_corridor_stream_key(attempt_index, feature_id, "start"))
    end_stream = rng_factory.stream(_corridor_stream_key(attempt_index, feature_id, "end"))
    control_stream = rng_factory.stream(
        _corridor_stream_key(attempt_index, feature_id, "control-points")
    )

    start = WorldPoint(
        x_km=plan.domain.width_km * start_stream.uniform01(),
        y_km=plan.domain.height_km * start_stream.uniform01(),
    )
    end = WorldPoint(
        x_km=plan.domain.width_km * end_stream.uniform01(),
        y_km=plan.domain.height_km * end_stream.uniform01(),
    )

    vx = end.x_km - start.x_km
    vy = end.y_km - start.y_km
    length = hypot(vx, vy)

    points: list[WorldPoint] = [start]
    if length <= GEOMETRY_EPSILON_KM:
        points.extend(start for _ in range(control_point_count))
        points.append(end)
        return CorridorGeometry(centerline=tuple(points))

    nx = -vy / length
    ny = vx / length

    for index in range(1, control_point_count + 1):
        t = index / (control_point_count + 1)
        base = WorldPoint(
            x_km=start.x_km + vx * t,
            y_km=start.y_km + vy * t,
        )
        envelope = 4.0 * t * (1.0 - t)
        strength = curvature * envelope
        random_signed = control_stream.uniform(-1.0, 1.0)

        if random_signed >= 0.0:
            available = _ray_distance_to_domain_boundary(
                base,
                dx=nx,
                dy=ny,
                width_km=plan.domain.width_km,
                height_km=plan.domain.height_km,
            )
            offset = random_signed * strength * available
        else:
            available = _ray_distance_to_domain_boundary(
                base,
                dx=-nx,
                dy=-ny,
                width_km=plan.domain.width_km,
                height_km=plan.domain.height_km,
            )
            offset = -((-random_signed) * strength * available)

        points.append(
            WorldPoint(
                x_km=base.x_km + nx * offset,
                y_km=base.y_km + ny * offset,
            )
        )

    points.append(end)
    return CorridorGeometry(centerline=tuple(points))


def _generate_band(
    plan: GenerationPlan,
    layout: GeometryLayoutRecipe,
    *,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> BandGeometry:
    control_point_count, curvature, width_sample_count = _sample_band_parameters(
        layout,
        feature_id=feature_id,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )

    start_stream = rng_factory.stream(_band_stream_key(attempt_index, feature_id, "start"))
    end_stream = rng_factory.stream(_band_stream_key(attempt_index, feature_id, "end"))
    control_stream = rng_factory.stream(
        _band_stream_key(attempt_index, feature_id, "control-points")
    )

    start = WorldPoint(
        x_km=plan.domain.width_km * start_stream.uniform01(),
        y_km=plan.domain.height_km * start_stream.uniform01(),
    )
    end = WorldPoint(
        x_km=plan.domain.width_km * end_stream.uniform01(),
        y_km=plan.domain.height_km * end_stream.uniform01(),
    )

    vx = end.x_km - start.x_km
    vy = end.y_km - start.y_km
    length = hypot(vx, vy)
    points: list[WorldPoint] = [start]

    if length <= GEOMETRY_EPSILON_KM:
        points.extend(start for _ in range(control_point_count))
        points.append(end)
    else:
        nx = -vy / length
        ny = vx / length
        for index in range(1, control_point_count + 1):
            t = index / (control_point_count + 1)
            base = WorldPoint(
                x_km=start.x_km + vx * t,
                y_km=start.y_km + vy * t,
            )
            envelope = 4.0 * t * (1.0 - t)
            strength = curvature * envelope
            random_signed = control_stream.uniform(-1.0, 1.0)

            if random_signed >= 0.0:
                available = _ray_distance_to_domain_boundary(
                    base,
                    dx=nx,
                    dy=ny,
                    width_km=plan.domain.width_km,
                    height_km=plan.domain.height_km,
                )
                offset = random_signed * strength * available
            else:
                available = _ray_distance_to_domain_boundary(
                    base,
                    dx=-nx,
                    dy=-ny,
                    width_km=plan.domain.width_km,
                    height_km=plan.domain.height_km,
                )
                offset = -((-random_signed) * strength * available)

            points.append(
                WorldPoint(
                    x_km=base.x_km + nx * offset,
                    y_km=base.y_km + ny * offset,
                )
            )
        points.append(end)

    width_recipe = layout.parameters["width_km"]
    width_start_stream = rng_factory.stream(
        _band_stream_key(attempt_index, feature_id, "width-start")
    )
    width_end_stream = rng_factory.stream(
        _band_stream_key(attempt_index, feature_id, "width-end")
    )
    width_internal_stream = rng_factory.stream(
        _band_stream_key(attempt_index, feature_id, "width-internal")
    )

    width_profile: list[WidthSample] = []
    for index in range(width_sample_count):
        t = index / (width_sample_count - 1)
        if index == 0:
            stream = width_start_stream
        elif index == width_sample_count - 1:
            stream = width_end_stream
        else:
            stream = width_internal_stream
        width_profile.append(
            WidthSample(
                t=t,
                width_km=_sample_band_width(width_recipe, stream),
            )
        )

    return BandGeometry(
        centerline=tuple(points),
        width_profile=tuple(width_profile),
    )


def generate_geometry_layout(
    plan: GenerationPlan,
    *,
    attempt_index: int,
    rng_factory: RngFactory,
) -> LayoutCandidate:
    """Realize supported geometry-mode features with isolated semantic RNG streams."""
    geometries: dict[str, PointGeometry | CorridorGeometry | BandGeometry | AreaGeometry] = {}

    for feature in sorted(plan.features, key=lambda item: item.id):
        layout = feature.layout
        if not isinstance(layout, GeometryLayoutRecipe):
            raise LayoutCapabilityError(
                f"placement reservation layout is not implemented yet: {feature.id!r}"
            )

        if layout.shape is GeometryShape.POINT:
            if layout.parameters:
                raise LayoutCapabilityError(
                    f"point layout v0.1 does not define layout parameters: {feature.id!r}"
                )
            geometries[feature.id] = _generate_point(
                plan,
                feature_id=feature.id,
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        elif layout.shape is GeometryShape.CORRIDOR:
            geometries[feature.id] = _generate_corridor(
                plan,
                layout,
                feature_id=feature.id,
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        elif layout.shape is GeometryShape.BAND:
            geometries[feature.id] = _generate_band(
                plan,
                layout,
                feature_id=feature.id,
                attempt_index=attempt_index,
                rng_factory=rng_factory,
            )
        elif layout.shape is GeometryShape.AREA:
            try:
                geometries[feature.id] = generate_area_geometry(
                    plan,
                    layout,
                    feature_id=feature.id,
                    attempt_index=attempt_index,
                    rng_factory=rng_factory,
                )
            except AreaLayoutCapabilityError as exc:
                raise LayoutCapabilityError(str(exc)) from exc
        else:
            raise LayoutCapabilityError(
                f"geometry shape {layout.shape.value!r} is not implemented yet: {feature.id!r}"
            )

    return LayoutCandidate(
        layout_version="0.1",
        source_plan=SourcePlanRef(fingerprint=semantic_plan_fingerprint(plan)),
        attempt_index=attempt_index,
        geometry_realizations=geometries,
        placement_reservations={},
    )


def _polyline_arc_center(centerline: tuple[WorldPoint, ...], *, geometry_name: str) -> PointGeometry:
    segments: list[tuple[WorldPoint, WorldPoint, float]] = []
    total = 0.0
    for left, right in zip(centerline, centerline[1:]):
        length = hypot(right.x_km - left.x_km, right.y_km - left.y_km)
        segments.append((left, right, length))
        total += length

    if total <= GEOMETRY_EPSILON_KM:
        raise LayoutCapabilityError(f"cannot resolve center of degenerate {geometry_name}")

    target = total * 0.5
    traversed = 0.0
    for left, right, length in segments:
        if traversed + length >= target and length > 0.0:
            local = (target - traversed) / length
            return PointGeometry(
                x_km=left.x_km + (right.x_km - left.x_km) * local,
                y_km=left.y_km + (right.y_km - left.y_km) * local,
            )
        traversed += length

    last = centerline[-1]
    return PointGeometry(x_km=last.x_km, y_km=last.y_km)


def _corridor_arc_center(corridor: CorridorGeometry) -> PointGeometry:
    return _polyline_arc_center(corridor.centerline, geometry_name="corridor")


def _band_arc_center(band: BandGeometry) -> PointGeometry:
    return _polyline_arc_center(band.centerline, geometry_name="band")


def _resolve_ref(ref: CompiledSpatialRef, candidate: LayoutCandidate):
    if isinstance(ref, CompiledPoint):
        return PointGeometry(x_km=ref.x_km, y_km=ref.y_km)
    if isinstance(ref, CompiledRectangle):
        return ref
    if not isinstance(ref, CompiledFeatureRef):
        raise LayoutCapabilityError(f"unsupported compiled spatial ref: {ref!r}")

    geometry = candidate.geometry_realizations.get(ref.feature_id)
    if isinstance(geometry, PointGeometry):
        if ref.part not in (FeaturePart.WHOLE, FeaturePart.CENTER):
            raise LayoutCapabilityError(f"point feature does not support part {ref.part.value!r}")
        return geometry

    if isinstance(geometry, CorridorGeometry):
        if ref.part is FeaturePart.WHOLE:
            return geometry
        if ref.part is FeaturePart.START:
            point = geometry.centerline[0]
            return PointGeometry(x_km=point.x_km, y_km=point.y_km)
        if ref.part is FeaturePart.END:
            point = geometry.centerline[-1]
            return PointGeometry(x_km=point.x_km, y_km=point.y_km)
        if ref.part is FeaturePart.CENTER:
            return _corridor_arc_center(geometry)
        raise LayoutCapabilityError(
            f"corridor part {ref.part.value!r} is not implemented in corridor slice"
        )

    if isinstance(geometry, BandGeometry):
        if ref.part is FeaturePart.START:
            point = geometry.centerline[0]
            return PointGeometry(x_km=point.x_km, y_km=point.y_km)
        if ref.part is FeaturePart.END:
            point = geometry.centerline[-1]
            return PointGeometry(x_km=point.x_km, y_km=point.y_km)
        if ref.part is FeaturePart.CENTER:
            return _band_arc_center(geometry)
        if ref.part in (FeaturePart.WHOLE, FeaturePart.BOUNDARY):
            raise LayoutCapabilityError(
                f"band part {ref.part.value!r} requires footprint materialization, not implemented yet"
            )
        raise LayoutCapabilityError(
            f"band part {ref.part.value!r} is not implemented in band slice"
        )

    if isinstance(geometry, AreaGeometry):
        if ref.part is FeaturePart.WHOLE:
            return geometry
        if ref.part is FeaturePart.BOUNDARY:
            return AreaBoundaryView(geometry)
        if ref.part is FeaturePart.CENTER:
            try:
                return area_centroid(geometry)
            except AreaLayoutCapabilityError as exc:
                raise LayoutCapabilityError(str(exc)) from exc
        raise LayoutCapabilityError(
            f"area part {ref.part.value!r} is not supported by area layout v0.1"
        )

    raise LayoutCapabilityError(
        f"feature reference {ref.feature_id!r} does not resolve to supported geometry"
    )


def _point_in_rectangle(point: PointGeometry, rectangle: CompiledRectangle) -> bool:
    return (
        rectangle.min_x_km <= point.x_km <= rectangle.max_x_km
        and rectangle.min_y_km <= point.y_km <= rectangle.max_y_km
    )


def _distance_point_rectangle(point: PointGeometry, rectangle: CompiledRectangle) -> float:
    dx = max(rectangle.min_x_km - point.x_km, 0.0, point.x_km - rectangle.max_x_km)
    dy = max(rectangle.min_y_km - point.y_km, 0.0, point.y_km - rectangle.max_y_km)
    return hypot(dx, dy)


def _distance_point_segment(point: PointGeometry, start: WorldPoint, end: WorldPoint) -> float:
    vx = end.x_km - start.x_km
    vy = end.y_km - start.y_km
    length_sq = vx * vx + vy * vy
    if length_sq <= GEOMETRY_EPSILON_KM * GEOMETRY_EPSILON_KM:
        return hypot(point.x_km - start.x_km, point.y_km - start.y_km)

    wx = point.x_km - start.x_km
    wy = point.y_km - start.y_km
    t = (wx * vx + wy * vy) / length_sq
    t = max(0.0, min(1.0, t))
    closest_x = start.x_km + t * vx
    closest_y = start.y_km + t * vy
    return hypot(point.x_km - closest_x, point.y_km - closest_y)


def _distance_point_corridor(point: PointGeometry, corridor: CorridorGeometry) -> float:
    return min(
        _distance_point_segment(point, start, end)
        for start, end in zip(corridor.centerline, corridor.centerline[1:])
    )


def _measure(constraint: CompiledConstraint, candidate: LayoutCandidate) -> tuple[float, str | None]:
    evaluator = constraint.evaluator
    subject = _resolve_ref(evaluator.subject, candidate)
    target = _resolve_ref(evaluator.target, candidate)

    if evaluator.type == "distance":
        if isinstance(subject, PointGeometry) and isinstance(target, PointGeometry):
            return hypot(subject.x_km - target.x_km, subject.y_km - target.y_km), "km"
        if isinstance(subject, PointGeometry) and isinstance(target, CompiledRectangle):
            return _distance_point_rectangle(subject, target), "km"
        if isinstance(subject, PointGeometry) and isinstance(target, CorridorGeometry):
            return _distance_point_corridor(subject, target), "km"
        if isinstance(subject, CorridorGeometry) and isinstance(target, PointGeometry):
            return _distance_point_corridor(target, subject), "km"
        if isinstance(subject, PointGeometry) and isinstance(target, AreaGeometry):
            return distance_point_area_whole(subject, target), "km"
        if isinstance(subject, AreaGeometry) and isinstance(target, PointGeometry):
            return distance_point_area_whole(target, subject), "km"
        if isinstance(subject, PointGeometry) and isinstance(target, AreaBoundaryView):
            return distance_point_area_boundary(subject, target.geometry), "km"
        if isinstance(subject, AreaBoundaryView) and isinstance(target, PointGeometry):
            return distance_point_area_boundary(target, subject.geometry), "km"
        raise LayoutCapabilityError(
            f"distance evaluator does not support {type(subject).__name__} -> {type(target).__name__}"
        )

    if evaluator.type in ("contained_fraction", "overlap_fraction"):
        if not isinstance(subject, PointGeometry):
            raise LayoutCapabilityError(
                f"{evaluator.type} area slice currently requires a point subject"
            )
        if isinstance(target, CompiledRectangle):
            contained = _point_in_rectangle(subject, target)
        elif isinstance(target, AreaGeometry):
            contained = point_in_area(subject, target)
        else:
            raise LayoutCapabilityError(
                f"{evaluator.type} does not support target {type(target).__name__}"
            )
        return (1.0 if contained else 0.0), None

    raise LayoutCapabilityError(
        f"layout evaluator {evaluator.type!r} is not implemented in geometry slice"
    )


def _predicate_satisfied(predicate_type: str, measured: float, threshold: float) -> bool:
    if predicate_type == "less_or_equal":
        return measured <= threshold
    if predicate_type == "greater_or_equal":
        return measured >= threshold
    if predicate_type == "greater_than":
        return measured > threshold
    raise LayoutCapabilityError(f"predicate {predicate_type!r} is not implemented")


def _geometry_inside_domain(geometry, plan: GenerationPlan) -> bool:
    if isinstance(geometry, PointGeometry):
        points = (geometry,)
    elif isinstance(geometry, (CorridorGeometry, BandGeometry)):
        points = geometry.centerline
    elif isinstance(geometry, AreaGeometry):
        return area_inside_domain(
            geometry,
            width_km=plan.domain.width_km,
            height_km=plan.domain.height_km,
        )
    else:
        return False
    return all(
        0.0 <= point.x_km <= plan.domain.width_km
        and 0.0 <= point.y_km <= plan.domain.height_km
        for point in points
    )


def _corridor_nondegenerate(geometry) -> bool:
    if not isinstance(geometry, CorridorGeometry):
        return True
    start = geometry.centerline[0]
    end = geometry.centerline[-1]
    return hypot(end.x_km - start.x_km, end.y_km - start.y_km) > GEOMETRY_EPSILON_KM


def _band_nondegenerate(geometry) -> bool:
    if not isinstance(geometry, BandGeometry):
        return True
    start = geometry.centerline[0]
    end = geometry.centerline[-1]
    return hypot(end.x_km - start.x_km, end.y_km - start.y_km) > GEOMETRY_EPSILON_KM


def _band_width_profile_valid(geometry) -> bool:
    if not isinstance(geometry, BandGeometry):
        return True
    samples = geometry.width_profile
    return (
        len(samples) >= 2
        and samples[0].t == 0.0
        and samples[-1].t == 1.0
        and all(left.t < right.t for left, right in zip(samples, samples[1:]))
        and all(sample.width_km > 0.0 for sample in samples)
    )


def _area_boundary_size_valid(geometry) -> bool:
    return not isinstance(geometry, AreaGeometry) or len(geometry.boundary) >= 3


def _area_zero_length_edge_free(geometry) -> bool:
    return not isinstance(geometry, AreaGeometry) or not area_has_zero_length_edge(geometry)


def _area_simple(geometry) -> bool:
    return not isinstance(geometry, AreaGeometry) or not area_self_intersects(geometry)


def _area_ccw_nondegenerate(geometry) -> bool:
    return not isinstance(geometry, AreaGeometry) or area_is_ccw_nondegenerate(geometry)


def validate_geometry_layout(
    plan: GenerationPlan,
    candidate: LayoutCandidate,
    *,
    attempt_index: int,
) -> ValidationResult:
    """Observe supported point/corridor/band/area layout without mutation or repair."""
    expected_ids = {
        feature.id
        for feature in plan.features
        if isinstance(feature.layout, GeometryLayoutRecipe)
        and feature.layout.shape in (
            GeometryShape.POINT,
            GeometryShape.CORRIDOR,
            GeometryShape.BAND,
            GeometryShape.AREA,
        )
    }
    actual_ids = set(candidate.geometry_realizations)
    expected_fingerprint = semantic_plan_fingerprint(plan)

    invariant_results = (
        EngineInvariantResult(
            id="layout-plan-fingerprint-matches",
            passed=candidate.source_plan.fingerprint == expected_fingerprint,
        ),
        EngineInvariantResult(
            id="layout-attempt-index-matches",
            passed=candidate.attempt_index == attempt_index,
        ),
        EngineInvariantResult(
            id="layout-supported-feature-set-complete",
            passed=actual_ids == expected_ids,
            measured={"expected_count": len(expected_ids), "actual_count": len(actual_ids)},
        ),
        EngineInvariantResult(
            id="layout-geometry-inside-domain",
            passed=all(
                _geometry_inside_domain(geometry, plan)
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
        EngineInvariantResult(
            id="layout-corridor-nondegenerate",
            passed=all(
                _corridor_nondegenerate(geometry)
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
        EngineInvariantResult(
            id="layout-band-nondegenerate",
            passed=all(
                _band_nondegenerate(geometry)
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
        EngineInvariantResult(
            id="layout-band-width-profile-valid",
            passed=all(
                _band_width_profile_valid(geometry)
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
        EngineInvariantResult(
            id="layout-area-boundary-size-valid",
            passed=all(
                _area_boundary_size_valid(geometry)
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
        EngineInvariantResult(
            id="layout-area-zero-length-edge-free",
            passed=all(
                _area_zero_length_edge_free(geometry)
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
        EngineInvariantResult(
            id="layout-area-simple",
            passed=all(
                _area_simple(geometry)
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
        EngineInvariantResult(
            id="layout-area-ccw-nondegenerate",
            passed=all(
                _area_ccw_nondegenerate(geometry)
                for geometry in candidate.geometry_realizations.values()
            ),
        ),
    )
    engine_passed = all(item.passed for item in invariant_results)

    hard_results: list[HardConstraintResult] = []
    if engine_passed:
        for constraint in plan.constraints:
            if constraint.predicate is None:
                raise LayoutCapabilityError(
                    f"geometry layout cannot evaluate soft constraint {constraint.id!r}"
                )
            value, measured_unit = _measure(constraint, candidate)
            threshold = float(constraint.predicate.value)
            satisfied = _predicate_satisfied(constraint.predicate.type, value, threshold)
            hard_results.append(
                HardConstraintResult(
                    constraint_id=constraint.id,
                    satisfied=satisfied,
                    measurement=Measurement(
                        type=constraint.evaluator.type,
                        value=value,
                        unit=constraint.unit or measured_unit,
                    ),
                    predicate=PredicateSnapshot(
                        type=constraint.predicate.type,
                        threshold=constraint.predicate.value,
                    ),
                )
            )

    hard_passed = all(item.satisfied for item in hard_results)
    return ValidationResult(
        validation_version="0.1",
        attempt_index=attempt_index,
        stage=ValidationStage.LAYOUT,
        engine_invariants=EngineInvariantGroup(passed=engine_passed, results=invariant_results),
        hard_constraints=HardConstraintGroup(passed=hard_passed, results=tuple(hard_results)),
        soft_constraints=SoftConstraintGroup(results=()),
        ranking=None,
    )


def geometry_layout_stage(context: AttemptContext, state: CandidateState) -> ValidationResult:
    """Point/corridor/band/area layout StageHandler for the attempt orchestrator."""
    candidate = generate_geometry_layout(
        context.plan,
        attempt_index=context.attempt_index,
        rng_factory=context.rng_factory,
    )
    state.layout = candidate
    return validate_geometry_layout(
        context.plan,
        candidate,
        attempt_index=context.attempt_index,
    )
