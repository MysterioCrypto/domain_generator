from __future__ import annotations

from dataclasses import replace

from ..contracts.data import (
    RiverNetwork,
    RiverNode,
    RiverNodeKind,
    RiverSegment,
    RiverSegmentProperties,
)
from .routing import HydrologyCapabilityError


def _degrees(network: RiverNetwork) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    incoming = {node_id: [] for node_id in network.nodes}
    outgoing = {node_id: [] for node_id in network.nodes}
    for segment_id, segment in network.segments.items():
        incoming[segment.to_node].append(segment_id)
        outgoing[segment.from_node].append(segment_id)
    for values in incoming.values():
        values.sort()
    for values in outgoing.values():
        values.sort()
    return incoming, outgoing


def _merge_through_false_confluence(
    *,
    node_id: str,
    incoming_id: str,
    outgoing_id: str,
    nodes: dict[str, RiverNode],
    segments: dict[str, RiverSegment],
) -> None:
    incoming = segments[incoming_id]
    outgoing = segments[outgoing_id]
    node = nodes[node_id]
    if incoming.to_node != node_id or outgoing.from_node != node_id:
        raise HydrologyCapabilityError("semantic confluence merge has inconsistent segment endpoints")
    if incoming.centerline[-1] != node.position or outgoing.centerline[0] != node.position:
        raise HydrologyCapabilityError("semantic confluence merge requires endpoint-exact centerlines")
    if incoming.from_node == outgoing.to_node:
        raise HydrologyCapabilityError("suppressing false confluence would create a self-loop")

    merged_points = incoming.centerline + outgoing.centerline[1:]
    if len(merged_points) < 2:
        raise HydrologyCapabilityError("suppressed confluence produced an empty river segment")
    merged_catchment = max(
        float(incoming.properties.catchment_area_km2),
        float(outgoing.properties.catchment_area_km2),
    )
    segments[incoming_id] = RiverSegment(
        **{"from": incoming.from_node, "to": outgoing.to_node},
        centerline=merged_points,
        properties=RiverSegmentProperties(catchment_area_km2=merged_catchment),
    )
    del segments[outgoing_id]
    del nodes[node_id]


def normalize_semantic_confluences(network: RiverNetwork) -> RiverNetwork:
    """Project distributed-flow confluence candidates onto the actual traced river graph.

    Weighted D∞ support may identify a raster cell with multiple fractional upstream
    contributors even though only one semantic river trace reaches that location. Such a
    cell is not a river confluence and must not survive as a serialized confluence node.

    The normalization is deterministic and topology-only: it never moves or smooths
    river geometry. One-input candidates are suppressed by concatenating the exact
    upstream/downstream centerlines. Zero-input candidates become sources if they own one
    downstream river, because the visible channel genuinely starts there.
    """
    if not isinstance(network, RiverNetwork):
        raise TypeError("network must be RiverNetwork")

    nodes = dict(network.nodes)
    segments = dict(network.segments)

    while True:
        current = RiverNetwork(nodes=nodes, segments=segments)
        incoming, outgoing = _degrees(current)
        changed = False

        for node_id in sorted(nodes):
            node = nodes[node_id]
            if node.kind is not RiverNodeKind.CONFLUENCE:
                continue
            indegree = len(incoming[node_id])
            outdegree = len(outgoing[node_id])
            if indegree >= 2:
                if outdegree > 1:
                    raise HydrologyCapabilityError(
                        "ordinary semantic confluence cannot bifurcate downstream"
                    )
                continue

            if indegree == 1:
                if outdegree != 1:
                    raise HydrologyCapabilityError(
                        "false confluence with one upstream river must have one downstream river"
                    )
                _merge_through_false_confluence(
                    node_id=node_id,
                    incoming_id=incoming[node_id][0],
                    outgoing_id=outgoing[node_id][0],
                    nodes=nodes,
                    segments=segments,
                )
                changed = True
                break

            # No semantic river reached this weighted-flow candidate. If it owns a
            # downstream trace, the visible channel begins here; otherwise it is unused.
            if outdegree > 1:
                raise HydrologyCapabilityError(
                    "zero-input semantic channel candidate cannot bifurcate downstream"
                )
            if outdegree == 1:
                nodes[node_id] = RiverNode(
                    kind=RiverNodeKind.SOURCE,
                    position=node.position,
                )
            else:
                del nodes[node_id]
            changed = True
            break

        if not changed:
            break

    normalized = RiverNetwork(nodes=nodes, segments=segments)
    incoming, outgoing = _degrees(normalized)
    for node_id, node in normalized.nodes.items():
        if node.kind is RiverNodeKind.CONFLUENCE and len(incoming[node_id]) < 2:
            raise HydrologyCapabilityError("semantic confluence normalization did not converge")
        if node.kind is RiverNodeKind.SOURCE and incoming[node_id]:
            raise HydrologyCapabilityError("semantic source has upstream river after normalization")
        if node.kind not in {RiverNodeKind.DOMAIN_OUTLET, RiverNodeKind.LAKE_INFLOW}:
            if len(outgoing[node_id]) > 1:
                raise HydrologyCapabilityError("semantic river graph contains downstream bifurcation")
    return normalized


__all__ = ["normalize_semantic_confluences"]
