from __future__ import annotations

from collections.abc import Iterable

from .definitions import PresetDefinition


class PresetRegistryError(ValueError):
    """Preset registry construction or lookup failed."""


class PresetRegistry:
    """Immutable in-memory registry boundary used by the compiler.

    Loading YAML/files is deliberately outside this class. The registry owns
    duplicate-id checks and verifies that every preset references a known
    operator id.
    """

    __slots__ = ("_presets", "_operator_ids")

    def __init__(
        self,
        presets: Iterable[PresetDefinition],
        *,
        operator_ids: Iterable[str],
    ) -> None:
        normalized_operator_ids = frozenset(operator_ids)
        if any(not isinstance(operator_id, str) or not operator_id for operator_id in normalized_operator_ids):
            raise PresetRegistryError("operator ids must be non-empty strings")

        resolved: dict[str, PresetDefinition] = {}
        for preset in presets:
            if preset.id in resolved:
                raise PresetRegistryError(f"duplicate preset id: {preset.id!r}")
            if preset.effect.operator not in normalized_operator_ids:
                raise PresetRegistryError(
                    f"preset {preset.id!r} references unknown operator {preset.effect.operator!r}"
                )
            resolved[preset.id] = preset

        self._presets = resolved
        self._operator_ids = normalized_operator_ids

    @property
    def preset_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._presets))

    @property
    def operator_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._operator_ids))

    def get(self, preset_id: str) -> PresetDefinition:
        try:
            return self._presets[preset_id]
        except KeyError as exc:
            raise PresetRegistryError(f"unknown preset id: {preset_id!r}") from exc

    def __contains__(self, preset_id: object) -> bool:
        return preset_id in self._presets
