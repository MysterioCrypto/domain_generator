from __future__ import annotations

from typing import Final


CORE_OPERATOR_IDS: Final[frozenset[str]] = frozenset(
    {
        "raise",
        "depress",
        "ridge",
        "flatten",
        "moisture_bias",
        "vegetation_bias",
        "suitability_placement",
    }
)


__all__ = ["CORE_OPERATOR_IDS"]
