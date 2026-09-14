from . import generate as _legacy_generate
from .generate import TerrainCapabilityError, rasterize_area_cell_centers
from .v02 import generate_terrain, terrain_stage, validate_terrain
from .state import TerrainState

# Keep direct imports from ``terrain.generate`` coherent with the 0.2 dispatcher.
# v02.py retains stable references to the original 0.1 functions for legacy requests.
_legacy_generate.generate_terrain = generate_terrain
_legacy_generate.terrain_stage = terrain_stage
_legacy_generate.validate_terrain = validate_terrain

__all__ = [
    "TerrainCapabilityError",
    "TerrainState",
    "generate_terrain",
    "rasterize_area_cell_centers",
    "terrain_stage",
    "validate_terrain",
]
