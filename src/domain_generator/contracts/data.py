from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import Field, StrictFloat, StrictInt, StrictStr, model_validator

from .common import FrozenStrictModel, NonNegativeFloat
from .geometry import AreaGeometry, BandGeometry, CorridorGeometry, PointGeometry, RegionSet, WorldPoint
from .validation import RankingResult


class FieldRole(StrEnum):
    CANONICAL = "canonical"
    DERIVED = "derived"


class OutputFeatureFamily(StrEnum):
    TERRAIN = "terrain"
    SURFACE = "surface"
    POI = "poi"
    HYDRO = "hydro"


class DomainIdentity(FrozenStrictModel):
    id: Annotated[StrictStr, Field(min_length=1)]
    label: StrictStr | None = None


class GeneratorIdentity(FrozenStrictModel):
    name: Annotated[StrictStr, Field(min_length=1)]
    version: Annotated[StrictStr, Field(min_length=1)]


class DomainProvenance(FrozenStrictModel):
    spec_schema_version: Literal["0.1", "0.2"]
    spec_fingerprint: Annotated[StrictStr, Field(min_length=1)]
    plan_fingerprint: Annotated[StrictStr, Field(min_length=1)]
    generation_config_fingerprint: Annotated[StrictStr, Field(min_length=1)]
    root_seed: StrictInt
    accepted_attempt_index: Annotated[StrictInt, Field(ge=0)]
    generator: GeneratorIdentity
    rng_version: Annotated[StrictInt, Field(ge=1)]


class DomainExtent(FrozenStrictModel):
    width_km: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    height_km: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]


class GridDescriptor(FrozenStrictModel):
    cell_size_km: Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
    rows: Annotated[StrictInt, Field(gt=0)]
    columns: Annotated[StrictInt, Field(gt=0)]


class FieldDescriptor(FrozenStrictModel):
    role: FieldRole
    format: Literal["npy"] = "npy"
    path: Annotated[StrictStr, Field(min_length=1)]
    dtype: Annotated[StrictStr, Field(min_length=1)]
    shape: tuple[Annotated[StrictInt, Field(gt=0)], Annotated[StrictInt, Field(gt=0)]]
    unit: Annotated[StrictStr, Field(min_length=1)]

    @model_validator(mode="after")
    def validate_path(self) -> "FieldDescriptor":
        if "\\" in self.path:
            raise ValueError("field path must use POSIX separators")
        path = PurePosixPath(self.path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("field path must be relative and must not contain '..'")
        return self


class SpecifiedFeatureSource(FrozenStrictModel):
    type: Literal["specified"] = "specified"
    preset: Annotated[StrictStr, Field(min_length=1)]


class GeneratedFeatureSource(FrozenStrictModel):
    type: Literal["generated"] = "generated"
    system: Annotated[StrictStr, Field(min_length=1)]


FeatureSource = SpecifiedFeatureSource | GeneratedFeatureSource


class TerrainFeature(FrozenStrictModel):
    label: StrictStr | None = None
    tags: tuple[StrictStr, ...] = ()
    source: FeatureSource
    family: Literal[OutputFeatureFamily.TERRAIN] = OutputFeatureFamily.TERRAIN
    geometry: PointGeometry | CorridorGeometry | BandGeometry | AreaGeometry


class SurfaceFeature(FrozenStrictModel):
    label: StrictStr | None = None
    tags: tuple[StrictStr, ...] = ()
    source: FeatureSource
    family: Literal[OutputFeatureFamily.SURFACE] = OutputFeatureFamily.SURFACE
    geometry: AreaGeometry


class PoiFeature(FrozenStrictModel):
    label: StrictStr | None = None
    tags: tuple[StrictStr, ...] = ()
    source: FeatureSource
    family: Literal[OutputFeatureFamily.POI] = OutputFeatureFamily.POI
    geometry: PointGeometry


class LakeProperties(FrozenStrictModel):
    area_km2: NonNegativeFloat
    surface_elevation_m: Annotated[StrictFloat, Field(allow_inf_nan=False)]
    max_depth_m: NonNegativeFloat


class HydroFeature(FrozenStrictModel):
    label: StrictStr | None = None
    tags: tuple[StrictStr, ...] = ()
    source: GeneratedFeatureSource
    family: Literal[OutputFeatureFamily.HYDRO] = OutputFeatureFamily.HYDRO
    geometry: RegionSet
    properties: LakeProperties


SemanticFeature = TerrainFeature | SurfaceFeature | PoiFeature | HydroFeature


class RiverNodeKind(StrEnum):
    SOURCE = "source"
    CONFLUENCE = "confluence"
    DOMAIN_OUTLET = "domain_outlet"
    LAKE_INFLOW = "lake_inflow"
    LAKE_OUTLET = "lake_outlet"


class BoundarySide(StrEnum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class RiverNode(FrozenStrictModel):
    kind: RiverNodeKind
    position: WorldPoint
    boundary_side: BoundarySide | None = None
    feature_id: StrictStr | None = None

    @model_validator(mode="after")
    def validate_kind_fields(self) -> "RiverNode":
        if self.kind is RiverNodeKind.DOMAIN_OUTLET:
            if self.boundary_side is None:
                raise ValueError("domain_outlet node requires boundary_side")
        elif self.boundary_side is not None:
            raise ValueError("boundary_side is only valid for domain_outlet nodes")

        lake_kind = self.kind in {RiverNodeKind.LAKE_INFLOW, RiverNodeKind.LAKE_OUTLET}
        if lake_kind and not self.feature_id:
            raise ValueError("lake inflow/outlet nodes require feature_id")
        if not lake_kind and self.feature_id is not None:
            raise ValueError("feature_id is only valid for lake inflow/outlet nodes")
        return self


class RiverSegmentProperties(FrozenStrictModel):
    catchment_area_km2: NonNegativeFloat


class RiverSegment(FrozenStrictModel):
    from_node: Annotated[StrictStr, Field(alias="from", min_length=1)]
    to_node: Annotated[StrictStr, Field(alias="to", min_length=1)]
    centerline: tuple[WorldPoint, ...] = Field(min_length=2)
    properties: RiverSegmentProperties

    @model_validator(mode="after")
    def validate_direction(self) -> "RiverSegment":
        if self.from_node == self.to_node:
            raise ValueError("river segment endpoints must differ")
        return self


class RiverNetwork(FrozenStrictModel):
    type: Literal["directed"] = "directed"
    nodes: dict[StrictStr, RiverNode] = Field(default_factory=dict)
    segments: dict[StrictStr, RiverSegment] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references(self) -> "RiverNetwork":
        node_ids = set(self.nodes)
        for segment_id, segment in self.segments.items():
            if not segment_id:
                raise ValueError("river segment ids must be non-empty")
            if segment.from_node not in node_ids or segment.to_node not in node_ids:
                raise ValueError("river segment references unknown node")
        if any(not node_id for node_id in self.nodes):
            raise ValueError("river node ids must be non-empty")
        return self


class ValidationSummary(FrozenStrictModel):
    engine_invariants_passed: Literal[True]
    hard_constraints_passed: Literal[True]
    soft: RankingResult


class DomainData(FrozenStrictModel):
    domain_data_version: Literal["0.1"]
    identity: DomainIdentity
    provenance: DomainProvenance
    domain: DomainExtent
    grid: GridDescriptor
    fields: dict[StrictStr, FieldDescriptor]
    features: dict[StrictStr, SemanticFeature] = Field(default_factory=dict)
    networks: dict[StrictStr, RiverNetwork] = Field(default_factory=dict)
    validation: ValidationSummary

    @model_validator(mode="after")
    def validate_domain_data(self) -> "DomainData":
        if self.grid.columns * self.grid.cell_size_km != self.domain.width_km:
            raise ValueError("grid columns must exactly match domain width")
        if self.grid.rows * self.grid.cell_size_km != self.domain.height_km:
            raise ValueError("grid rows must exactly match domain height")

        expected_shape = (self.grid.rows, self.grid.columns)
        for name, descriptor in self.fields.items():
            if not name:
                raise ValueError("field ids must be non-empty")
            if descriptor.shape != expected_shape:
                raise ValueError(f"field {name!r} shape must match grid")

        canonical = {
            "elevation": "m",
            "water_depth": "m",
            "moisture": "normalized",
            "vegetation_density": "normalized",
        }
        missing = set(canonical) - set(self.fields)
        if missing:
            raise ValueError(f"missing canonical fields: {sorted(missing)}")
        for name, unit in canonical.items():
            descriptor = self.fields[name]
            if descriptor.role is not FieldRole.CANONICAL:
                raise ValueError(f"{name} must be canonical")
            if descriptor.dtype != "float32":
                raise ValueError(f"{name} must persist as float32")
            if descriptor.unit != unit:
                raise ValueError(f"{name} unit must be {unit!r}")

        if any(not feature_id for feature_id in self.features):
            raise ValueError("feature ids must be non-empty")
        if set(self.networks) - {"rivers"}:
            raise ValueError("Core 0.1 only defines the 'rivers' network")

        for network in self.networks.values():
            for node in network.nodes.values():
                if node.feature_id is not None:
                    feature = self.features.get(node.feature_id)
                    if not isinstance(feature, HydroFeature):
                        raise ValueError("river lake node feature_id must reference a hydro feature")
        return self
