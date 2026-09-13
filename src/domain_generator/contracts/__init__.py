"""Serializable Core 0.1 contracts and immutable value models."""

from .bundle import BundleFileEntry, BundleFileKind, BundleManifest
from .common import ConstraintStrength, DomainCompass, FeaturePart, Relation
from .config import GenerationConfig, ObservabilityConfig, SemanticGenerationConfig
from .data import DomainData, FieldDescriptor, FieldRole, RiverNetwork
from .geometry import AreaGeometry, BandGeometry, CorridorGeometry, Geometry, PointGeometry, RegionSet, WorldPoint
from .layout import LayoutCandidate, PlacementReservation
from .plan import GenerationPlan, PlanHydrology, PlanSurface, ResolvedFeature
from .spec import ConstraintSpec, DomainSpec, FeatureSpec, HydrologySpec, SurfaceSpec
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
    "Geometry",
    "HydrologySpec",
    "LayoutCandidate",
    "ObservabilityConfig",
    "PlacementReservation",
    "PlanHydrology",
    "PlanSurface",
    "PointGeometry",
    "RankingResult",
    "RegionSet",
    "Relation",
    "ResolvedFeature",
    "RiverNetwork",
    "SemanticGenerationConfig",
    "SurfaceSpec",
    "ValidationResult",
    "ValidationStage",
    "WorldPoint",
]
