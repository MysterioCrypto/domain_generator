"""Core package for deterministic procedural domain generation."""

__version__ = "0.1.0.dev0"

from .application import (  # noqa: E402
    GenerateApplicationResult,
    generate_domain,
    generate_domain_bundle,
)

__all__ = [
    "GenerateApplicationResult",
    "__version__",
    "generate_domain",
    "generate_domain_bundle",
]
