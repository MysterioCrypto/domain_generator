"""Deterministic DomainSpec to GenerationPlan compilation."""

from . import compile as _legacy_compile
from .v02 import (
    CompilerError,
    compile_domain_spec,
    domain_spec_fingerprint,
    semantic_plan_fingerprint,
)

# A few Core 0.1 modules import fingerprint helpers from ``compiler.compile``
# directly. Keep those imports coherent during the 0.2 transition without
# duplicating layout code; v02.py keeps stable references to the original 0.1
# implementations for legacy requests before these aliases are replaced.
_legacy_compile.compile_domain_spec = compile_domain_spec
_legacy_compile.domain_spec_fingerprint = domain_spec_fingerprint
_legacy_compile.semantic_plan_fingerprint = semantic_plan_fingerprint

__all__ = [
    "CompilerError",
    "compile_domain_spec",
    "domain_spec_fingerprint",
    "semantic_plan_fingerprint",
]
