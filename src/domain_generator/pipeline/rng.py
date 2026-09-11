from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import blake2b
from math import isfinite
from struct import pack
from typing import Sequence, TypeVar

RNG_VERSION = 1
UINT64_MAX = (1 << 64) - 1
UINT64_MODULUS = 1 << 64
UINT32_MAX = (1 << 32) - 1
MASK64 = UINT64_MAX
MAGIC = b"domain-generator-rng\x00"
BLAKE2_PERSON = b"dg-rng-v1"
ZERO_STATE_FALLBACK = 0x9E3779B97F4A7C15

T = TypeVar("T")


class RngStage(StrEnum):
    GLOBAL = "global"
    LAYOUT = "layout"
    TERRAIN = "terrain"
    HYDROLOGY = "hydrology"
    SURFACE = "surface"
    PLACEMENT = "placement"


def _require_uint64(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if not 0 <= value <= UINT64_MAX:
        raise ValueError(f"{name} must be in [0, 2^64-1]")
    return value


def _encode_string(value: str, *, name: str) -> bytes:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    payload = value.encode("utf-8")
    if len(payload) > UINT32_MAX:
        raise ValueError(f"{name} UTF-8 payload is too long")
    return pack(">I", len(payload)) + payload


@dataclass(frozen=True, slots=True)
class RngKey:
    attempt_index: int
    stage: RngStage
    scope: tuple[str, ...]
    purpose: str

    def __post_init__(self) -> None:
        _require_uint64(self.attempt_index, name="attempt_index")

        if not isinstance(self.stage, RngStage):
            try:
                object.__setattr__(self, "stage", RngStage(self.stage))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"unsupported RNG stage: {self.stage!r}") from exc

        if not isinstance(self.scope, tuple):
            raise TypeError("scope must be a tuple of strings")
        if not self.scope:
            raise ValueError("scope must contain at least one component")
        for index, component in enumerate(self.scope):
            _encode_string(component, name=f"scope[{index}]")

        _encode_string(self.purpose, name="purpose")


def encode_rng_namespace(root_seed: int, key: RngKey, *, rng_version: int = RNG_VERSION) -> bytes:
    """Encode one RNG stream address exactly as specified by RNG protocol v1."""
    _require_uint64(root_seed, name="root_seed")
    if rng_version != RNG_VERSION:
        raise ValueError(f"unsupported rng_version: {rng_version}")
    if len(key.scope) > UINT32_MAX:
        raise ValueError("scope contains too many components")

    parts = [
        MAGIC,
        pack(">H", rng_version),
        pack(">Q", root_seed),
        pack(">Q", key.attempt_index),
        _encode_string(key.stage.value, name="stage"),
        pack(">I", len(key.scope)),
    ]
    parts.extend(_encode_string(component, name="scope component") for component in key.scope)
    parts.append(_encode_string(key.purpose, name="purpose"))
    return b"".join(parts)


def _rotl64(value: int, shift: int) -> int:
    value &= MASK64
    return ((value << shift) & MASK64) | (value >> (64 - shift))


class Xoshiro256StarStar:
    """Small deterministic xoshiro256** implementation with explicit uint64 semantics."""

    __slots__ = ("_s0", "_s1", "_s2", "_s3")

    def __init__(self, s0: int, s1: int, s2: int, s3: int) -> None:
        words = tuple(_require_uint64(word, name=f"s{index}") for index, word in enumerate((s0, s1, s2, s3)))
        if words == (0, 0, 0, 0):
            raise ValueError("xoshiro256** state must not be all zero")
        self._s0, self._s1, self._s2, self._s3 = words

    @property
    def state(self) -> tuple[int, int, int, int]:
        return self._s0, self._s1, self._s2, self._s3

    def next_u64(self) -> int:
        result = _rotl64((self._s1 * 5) & MASK64, 7)
        result = (result * 9) & MASK64

        t = (self._s1 << 17) & MASK64

        self._s2 ^= self._s0
        self._s3 ^= self._s1
        self._s1 ^= self._s2
        self._s0 ^= self._s3
        self._s2 ^= t
        self._s3 = _rotl64(self._s3, 45)

        self._s0 &= MASK64
        self._s1 &= MASK64
        self._s2 &= MASK64
        self._s3 &= MASK64
        return result

    def uniform01(self) -> float:
        return (self.next_u64() >> 11) / float(1 << 53)

    def uniform(self, low: float, high: float) -> float:
        low_value = float(low)
        high_value = float(high)
        if not isfinite(low_value) or not isfinite(high_value):
            raise ValueError("uniform bounds must be finite")
        if low_value > high_value:
            raise ValueError("uniform low must be <= high")
        u = self.uniform01()
        return low_value + (high_value - low_value) * u

    def integer_uniform(self, low: int, high: int) -> int:
        if isinstance(low, bool) or isinstance(high, bool) or not isinstance(low, int) or not isinstance(high, int):
            raise TypeError("integer_uniform bounds must be integers")
        if low > high:
            raise ValueError("integer_uniform low must be <= high")

        span = high - low + 1
        if span > UINT64_MODULUS:
            raise ValueError("integer_uniform range cannot contain more than 2^64 values")

        limit = UINT64_MODULUS - (UINT64_MODULUS % span)
        while True:
            value = self.next_u64()
            if value < limit:
                return low + (value % span)

    def choice(self, values: Sequence[T]) -> T:
        if len(values) == 0:
            raise ValueError("choice requires a non-empty sequence")
        index = self.integer_uniform(0, len(values) - 1)
        return values[index]


class RngFactory:
    """Derive independent deterministic RNG streams from root seed + semantic RngKey."""

    __slots__ = ("root_seed", "rng_version")

    def __init__(self, root_seed: int, *, rng_version: int = RNG_VERSION) -> None:
        self.root_seed = _require_uint64(root_seed, name="root_seed")
        if rng_version != RNG_VERSION:
            raise ValueError(f"unsupported rng_version: {rng_version}")
        self.rng_version = rng_version

    def namespace_bytes(self, key: RngKey) -> bytes:
        return encode_rng_namespace(self.root_seed, key, rng_version=self.rng_version)

    def derive_digest(self, key: RngKey) -> bytes:
        return blake2b(
            self.namespace_bytes(key),
            digest_size=32,
            person=BLAKE2_PERSON,
        ).digest()

    def derive_state(self, key: RngKey) -> tuple[int, int, int, int]:
        digest = self.derive_digest(key)
        state = tuple(int.from_bytes(digest[offset : offset + 8], "big") for offset in range(0, 32, 8))
        if state == (0, 0, 0, 0):
            state = (0, 0, 0, ZERO_STATE_FALLBACK)
        return state

    def stream(self, key: RngKey) -> Xoshiro256StarStar:
        return Xoshiro256StarStar(*self.derive_state(key))
