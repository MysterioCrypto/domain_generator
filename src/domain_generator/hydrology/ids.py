from __future__ import annotations


def lake_feature_id(index_zero_based: int) -> str:
    if isinstance(index_zero_based, bool) or not isinstance(index_zero_based, int):
        raise TypeError("lake feature index must be an integer")
    if index_zero_based < 0:
        raise ValueError("lake feature index must be >= 0")
    return f"lake-{index_zero_based + 1:04d}"
