"""Serializable Core contracts and immutable value models."""

from .application import GenerationRequest
from .bundle import BundleFileEntry, BundleFileKind, BundleManifest
from .common import ConstraintStrength, DomainCompass, FeaturePart, Relation
from .config import GenerationConfig, ObservabilityConfig, SemanticGenerationConfig
from .data import DomainData, FieldDescriptor, FieldRole, RiverNetwork
from .geometry import AreaGeometry, BandGeometry, CorridorGeometry, Geometry, PointGeometry, RegionSet, WorldPoint
from .layout import LayoutCandidate, PlacementReservation
from .plan import GenerationPlan, PlanHydrology, PlanSurface, ResolvedFeature
from .spec import (
    ConstraintSpec,
    DomainSpec,
    FeatureSpec,
    HydrologySpec,
    SurfaceSpec,
    TerrainNoiseLayerSpec,
    TerrainSpec,
)
from .terrain import PlanTerrain, PlanTerrainNoiseLayer
from .validation import RankingResult, ValidationResult, ValidationStage

__all__ = [
    "AreaGeometry",
    "BandGeometry",
    "BundleFileEntry",
    "BundleFileKind",
    "BundleManifest",
    "ConstraintSpec",
    "ConstraintStrength",
    "CorridorGeometry",
    "DomainCompass",
    "DomainData",
    "DomainSpec",
    "FeaturePart",
    "FeatureSpec",
    "FieldDescriptor",
    "FieldRole",
    "GenerationConfig",
    "GenerationPlan",
    "GenerationRequest",
    "Geometry",
    "HydrologySpec",
    "LayoutCandidate",
    "ObservabilityConfig",
    "PlacementReservation",
    "PlanHydrology",
    "PlanSurface",
    "PlanTerrain",
    "PlanTerrainNoiseLayer",
    "PointGeometry",
    "RankingResult",
    "RegionSet",
    "Relation",
    "ResolvedFeature",
    "RiverNetwork",
    "SemanticGenerationConfig",
    "SurfaceSpec",
    "TerrainNoiseLayerSpec",
    "TerrainSpec",
    "ValidationResult",
    "ValidationStage",
    "WorldPoint",
]
