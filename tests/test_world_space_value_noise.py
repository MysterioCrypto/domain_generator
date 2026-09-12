from __future__ import annotations

import pytest

from domain_generator.fields import value_noise_2d
from domain_generator.pipeline.rng import RngFactory, RngStage


def ridge_scope(feature_id: str) -> tuple[str, ...]:
    return ("feature", feature_id, "ridge-noise")


def test_value_noise_v1_golden_vector() -> None:
    value = value_noise_2d(
        x_km=2.5,
        y_km=3.5,
        scale_km=4.0,
        rng_factory=RngFactory(123456),
        attempt_index=2,
        stage=RngStage.TERRAIN,
        scope=ridge_scope("ridge-01"),
    )

    assert value == pytest.approx(0.8731038256959056, abs=1e-15)


def test_value_noise_replays_and_varies_by_attempt() -> None:
    factory = RngFactory(123456)
    kwargs = dict(
        x_km=2.5,
        y_km=3.5,
        scale_km=4.0,
        rng_factory=factory,
        stage=RngStage.TERRAIN,
        scope=ridge_scope("ridge-01"),
    )

    first = value_noise_2d(attempt_index=2, **kwargs)
    replay = value_noise_2d(attempt_index=2, **kwargs)
    other = value_noise_2d(attempt_index=3, **kwargs)

    assert first == replay
    assert first != other


def test_value_noise_node_addressing_is_random_access() -> None:
    factory = RngFactory(99)
    kwargs = dict(
        scale_km=2.0,
        rng_factory=factory,
        attempt_index=0,
        stage=RngStage.TERRAIN,
        scope=ridge_scope("ridge-a"),
    )
    first = value_noise_2d(x_km=0.0, y_km=0.0, **kwargs)
    _ = value_noise_2d(x_km=100.0, y_km=100.0, **kwargs)
    replay = value_noise_2d(x_km=0.0, y_km=0.0, **kwargs)

    assert first == replay


def test_value_noise_namespace_is_caller_controlled() -> None:
    factory = RngFactory(99)
    common = dict(
        x_km=1.25,
        y_km=2.75,
        scale_km=2.0,
        rng_factory=factory,
        attempt_index=0,
        stage=RngStage.TERRAIN,
    )

    ridge = value_noise_2d(scope=("feature", "same", "ridge-noise"), **common)
    other = value_noise_2d(scope=("feature", "same", "other-field"), **common)

    assert ridge != other
