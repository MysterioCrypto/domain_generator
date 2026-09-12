from __future__ import annotations

from dataclasses import dataclass
from math import cos, hypot, inf, sin, tau

from ..contracts.geometry import AreaGeometry, PointGeometry, WorldPoint
from ..contracts.plan import GenerationPlan, GeometryLayoutRecipe, ParameterType
from ..pipeline.rng import RngFactory, RngKey, RngStage
from ..pipeline.sampling import sample_resolved_parameter

GEOMETRY_EPSILON_KM = 1e-12
AREA_EPSILON_KM2 = GEOMETRY_EPSILON_KM * GEOMETRY_EPSILON_KM


class AreaLayoutCapabilityError(RuntimeError):
    """A structurally valid area recipe/evaluation is unsupported by area layout v0.1."""


@dataclass(frozen=True, slots=True)
class AreaBoundaryView:
    geometry: AreaGeometry


def _area_stream_key(attempt_index: int, feature_id: str, purpose: str) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.LAYOUT,
        scope=("feature", feature_id, "geometry", "area"),
        purpose=purpose,
    )


def _parameter_stream_key(attempt_index: int, feature_id: str, parameter_name: str) -> RngKey:
    return RngKey(
        attempt_index=attempt_index,
        stage=RngStage.LAYOUT,
        scope=("feature", feature_id, "parameter", parameter_name),
        purpose="sample",
    )


def _sample_area_parameters(
    layout: GeometryLayoutRecipe,
    *,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> tuple[int, float, float]:
    expected = {"vertex_count", "radial_extent", "radial_irregularity"}
    actual = set(layout.parameters)
    if actual != expected:
        raise AreaLayoutCapabilityError(
            f"area feature {feature_id!r} requires exactly layout parameters "
            f"{sorted(expected)}, got {sorted(actual)}"
        )

    if layout.parameters["vertex_count"].type is not ParameterType.INTEGER:
        raise AreaLayoutCapabilityError("area vertex_count must be an integer resolved parameter")
    for name in ("radial_extent", "radial_irregularity"):
        if layout.parameters[name].type is not ParameterType.FLOAT:
            raise AreaLayoutCapabilityError(f"area {name} must be a float resolved parameter")

    sampled: dict[str, object] = {}
    for name in sorted(expected):
        stream = rng_factory.stream(_parameter_stream_key(attempt_index, feature_id, name))
        sampled[name] = sample_resolved_parameter(layout.parameters[name], stream)

    vertex_count = sampled["vertex_count"]
    radial_extent = sampled["radial_extent"]
    radial_irregularity = sampled["radial_irregularity"]

    if isinstance(vertex_count, bool) or not isinstance(vertex_count, int):
        raise AreaLayoutCapabilityError("area vertex_count must resolve to integer")
    if vertex_count < 3:
        raise AreaLayoutCapabilityError("area vertex_count must resolve to >= 3")

    if isinstance(radial_extent, bool) or not isinstance(radial_extent, (int, float)):
        raise AreaLayoutCapabilityError("area radial_extent must resolve to numeric value")
    radial_extent_value = float(radial_extent)
    if not 0.0 < radial_extent_value <= 1.0:
        raise AreaLayoutCapabilityError("area radial_extent must resolve inside (0, 1]")

    if isinstance(radial_irregularity, bool) or not isinstance(radial_irregularity, (int, float)):
        raise AreaLayoutCapabilityError("area radial_irregularity must resolve to numeric value")
    radial_irregularity_value = float(radial_irregularity)
    if not 0.0 <= radial_irregularity_value <= 1.0:
        raise AreaLayoutCapabilityError("area radial_irregularity must resolve inside [0, 1]")

    return vertex_count, radial_extent_value, radial_irregularity_value


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


def generate_area_geometry(
    plan: GenerationPlan,
    layout: GeometryLayoutRecipe,
    *,
    feature_id: str,
    attempt_index: int,
    rng_factory: RngFactory,
) -> AreaGeometry:
    """Generate one star-shaped CCW area polygon without retry/repair."""
    vertex_count, radial_extent, radial_irregularity = _sample_area_parameters(
        layout,
        feature_id=feature_id,
        attempt_index=attempt_index,
        rng_factory=rng_factory,
    )

    center_stream = rng_factory.stream(_area_stream_key(attempt_index, feature_id, "center"))
    rotation_stream = rng_factory.stream(_area_stream_key(attempt_index, feature_id, "rotation"))
    radial_stream = rng_factory.stream(
        _area_stream_key(attempt_index, feature_id, "radial-variation")
    )

    center = WorldPoint(
        x_km=plan.domain.width_km * center_stream.uniform01(),
        y_km=plan.domain.height_km * center_stream.uniform01(),
    )
    rotation = tau * rotation_stream.uniform01()

    boundary: list[WorldPoint] = []
    for index in range(vertex_count):
        angle = rotation + tau * index / vertex_count
        dx = cos(angle)
        dy = sin(angle)
        available = _ray_distance_to_domain_boundary(
            center,
            dx=dx,
            dy=dy,
            width_km=plan.domain.width_km,
            height_km=plan.domain.height_km,
        )
        variation = radial_stream.uniform01()
        factor = radial_extent * (1.0 - radial_irregularity * variation)
        radius = available * factor
        boundary.append(
            WorldPoint(
                x_km=center.x_km + dx * radius,
                y_km=center.y_km + dy * radius,
            )
        )

    return AreaGeometry(boundary=tuple(boundary))


def area_signed_area(area: AreaGeometry) -> float:
    total = 0.0
    boundary = area.boundary
    for left, right in zip(boundary, boundary[1:] + boundary[:1]):
        total += left.x_km * right.y_km - right.x_km * left.y_km
    return 0.5 * total


def area_centroid(area: AreaGeometry) -> PointGeometry:
    boundary = area.boundary
    cross_sum = 0.0
    x_sum = 0.0
    y_sum = 0.0
    for left, right in zip(boundary, boundary[1:] + boundary[:1]):
        cross = left.x_km * right.y_km - right.x_km * left.y_km
        cross_sum += cross
        x_sum += (left.x_km + right.x_km) * cross
        y_sum += (left.y_km + right.y_km) * cross

    if abs(cross_sum) <= 2.0 * AREA_EPSILON_KM2:
        raise AreaLayoutCapabilityError("cannot resolve centroid of degenerate area")

    return PointGeometry(
        x_km=x_sum / (3.0 * cross_sum),
        y_km=y_sum / (3.0 * cross_sum),
    )


def _cross(a: WorldPoint, b: WorldPoint, c: WorldPoint) -> float:
    return (b.x_km - a.x_km) * (c.y_km - a.y_km) - (b.y_km - a.y_km) * (c.x_km - a.x_km)


def _point_on_segment(point: PointGeometry | WorldPoint, start: WorldPoint, end: WorldPoint) -> bool:
    if abs(_cross(start, end, point)) > GEOMETRY_EPSILON_KM:
        return False
    return (
        min(start.x_km, end.x_km) - GEOMETRY_EPSILON_KM <= point.x_km <= max(start.x_km, end.x_km) + GEOMETRY_EPSILON_KM
        and min(start.y_km, end.y_km) - GEOMETRY_EPSILON_KM <= point.y_km <= max(start.y_km, end.y_km) + GEOMETRY_EPSILON_KM
    )


def point_in_area(point: PointGeometry, area: AreaGeometry) -> bool:
    """Return True for polygon interior or boundary."""
    boundary = area.boundary
    inside = False
    for start, end in zip(boundary, boundary[1:] + boundary[:1]):
        if _point_on_segment(point, start, end):
            return True
        if (start.y_km > point.y_km) != (end.y_km > point.y_km):
            x_intersection = start.x_km + (
                (point.y_km - start.y_km)
                * (end.x_km - start.x_km)
                / (end.y_km - start.y_km)
            )
            if point.x_km < x_intersection:
                inside = not inside
    return inside


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


def distance_point_area_boundary(point: PointGeometry, area: AreaGeometry) -> float:
    boundary = area.boundary
    return min(
        _distance_point_segment(point, start, end)
        for start, end in zip(boundary, boundary[1:] + boundary[:1])
    )


def distance_point_area_whole(point: PointGeometry, area: AreaGeometry) -> float:
    if point_in_area(point, area):
        return 0.0
    return distance_point_area_boundary(point, area)


def area_inside_domain(area: AreaGeometry, *, width_km: float, height_km: float) -> bool:
    return all(
        0.0 <= point.x_km <= width_km and 0.0 <= point.y_km <= height_km
        for point in area.boundary
    )


def area_has_zero_length_edge(area: AreaGeometry) -> bool:
    boundary = area.boundary
    return any(
        hypot(end.x_km - start.x_km, end.y_km - start.y_km) <= GEOMETRY_EPSILON_KM
        for start, end in zip(boundary, boundary[1:] + boundary[:1])
    )


def _segments_intersect(a: WorldPoint, b: WorldPoint, c: WorldPoint, d: WorldPoint) -> bool:
    ab_c = _cross(a, b, c)
    ab_d = _cross(a, b, d)
    cd_a = _cross(c, d, a)
    cd_b = _cross(c, d, b)

    if (
        ((ab_c > GEOMETRY_EPSILON_KM and ab_d < -GEOMETRY_EPSILON_KM) or (ab_c < -GEOMETRY_EPSILON_KM and ab_d > GEOMETRY_EPSILON_KM))
        and ((cd_a > GEOMETRY_EPSILON_KM and cd_b < -GEOMETRY_EPSILON_KM) or (cd_a < -GEOMETRY_EPSILON_KM and cd_b > GEOMETRY_EPSILON_KM))
    ):
        return True

    if abs(ab_c) <= GEOMETRY_EPSILON_KM and _point_on_segment(c, a, b):
        return True
    if abs(ab_d) <= GEOMETRY_EPSILON_KM and _point_on_segment(d, a, b):
        return True
    if abs(cd_a) <= GEOMETRY_EPSILON_KM and _point_on_segment(a, c, d):
        return True
    if abs(cd_b) <= GEOMETRY_EPSILON_KM and _point_on_segment(b, c, d):
        return True
    return False


def area_self_intersects(area: AreaGeometry) -> bool:
    boundary = area.boundary
    count = len(boundary)
    for first_index in range(count):
        a = boundary[first_index]
        b = boundary[(first_index + 1) % count]
        for second_index in range(first_index + 1, count):
            if second_index == first_index:
                continue
            if (first_index + 1) % count == second_index:
                continue
            if (second_index + 1) % count == first_index:
                continue
            c = boundary[second_index]
            d = boundary[(second_index + 1) % count]
            if _segments_intersect(a, b, c, d):
                return True
    return False


def area_is_ccw_nondegenerate(area: AreaGeometry) -> bool:
    return area_signed_area(area) > AREA_EPSILON_KM2
