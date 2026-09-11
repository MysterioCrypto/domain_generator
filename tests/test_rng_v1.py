import pytest

from domain_generator.pipeline.rng import (
    RNG_VERSION,
    RngFactory,
    RngKey,
    RngStage,
    Xoshiro256StarStar,
    encode_rng_namespace,
)


def golden_key() -> RngKey:
    return RngKey(
        attempt_index=0,
        stage=RngStage.LAYOUT,
        scope=("feature", "mountain-01", "parameter", "width_km"),
        purpose="sample",
    )


def test_rng_v1_golden_namespace_digest_state_and_outputs() -> None:
    factory = RngFactory(0)
    key = golden_key()

    assert factory.namespace_bytes(key).hex() == (
        "646f6d61696e2d67656e657261746f722d726e6700"
        "0001"
        "0000000000000000"
        "0000000000000000"
        "000000066c61796f7574"
        "00000004"
        "0000000766656174757265"
        "0000000b6d6f756e7461696e2d3031"
        "00000009706172616d65746572"
        "0000000877696474685f6b6d"
        "0000000673616d706c65"
    )
    assert factory.derive_digest(key).hex() == "a9650faedb3383ebdbbd1e590c253dfb0a5ca0aacd47c83add122d9840eac5e9"
    assert factory.derive_state(key) == (
        12206179608733909995,
        15833845232709221883,
        746648293685577786,
        15929844963910272489,
    )

    stream = factory.stream(key)
    assert [stream.next_u64() for _ in range(5)] == [
        2245839985094856909,
        12220146847978795669,
        6171050466582408925,
        816886419350713454,
        7963190519562089210,
    ]

    uniform_stream = factory.stream(key)
    assert [uniform_stream.uniform01() for _ in range(5)] == [
        0.12174722954473283,
        0.6624554880335249,
        0.3345333161193166,
        0.044283501526697355,
        0.43168542306125945,
    ]


def test_xoshiro_reference_state_vector() -> None:
    stream = Xoshiro256StarStar(1, 2, 3, 4)
    assert [stream.next_u64() for _ in range(5)] == [
        11520,
        0,
        1509978240,
        1215971899390074240,
        1216172134540287360,
    ]


def test_same_key_recreates_same_stream() -> None:
    factory = RngFactory(123456)
    key = RngKey(3, RngStage.TERRAIN, ("feature", "mountain-01", "noise"), "macro")

    first = factory.stream(key)
    second = factory.stream(key)
    assert [first.next_u64() for _ in range(8)] == [second.next_u64() for _ in range(8)]


def test_neighbor_stream_draws_do_not_shift_another_stream() -> None:
    factory = RngFactory(123456)
    mountain = RngKey(2, RngStage.LAYOUT, ("feature", "mountain-01", "geometry"), "centerline")
    forest = RngKey(2, RngStage.LAYOUT, ("feature", "forest-01", "geometry"), "boundary")

    expected_mountain = [factory.stream(mountain).next_u64() for _ in range(1)]

    forest_stream = factory.stream(forest)
    for _ in range(100):
        forest_stream.next_u64()

    actual_mountain_stream = factory.stream(mountain)
    actual_mountain = [actual_mountain_stream.next_u64() for _ in range(1)]
    assert actual_mountain == expected_mountain


def test_stream_order_is_irrelevant() -> None:
    factory = RngFactory(77)
    key_a = RngKey(1, RngStage.LAYOUT, ("feature", "a"), "geometry")
    key_b = RngKey(1, RngStage.LAYOUT, ("feature", "b"), "geometry")

    a_first = [factory.stream(key_a).next_u64() for _ in range(1)]
    b_second = [factory.stream(key_b).next_u64() for _ in range(1)]

    b_first = [factory.stream(key_b).next_u64() for _ in range(1)]
    a_second = [factory.stream(key_a).next_u64() for _ in range(1)]

    assert a_first == a_second
    assert b_first == b_second


def test_length_prefix_prevents_scope_concatenation_collision() -> None:
    left = RngKey(0, RngStage.GLOBAL, ("a", "bc"), "x")
    right = RngKey(0, RngStage.GLOBAL, ("ab", "c"), "x")
    assert encode_rng_namespace(1, left) != encode_rng_namespace(1, right)


def test_integer_uniform_and_choice_are_deterministic() -> None:
    factory = RngFactory(999)
    key = RngKey(0, RngStage.PLACEMENT, ("feature", "fort-01"), "site-selection")

    first = factory.stream(key)
    second = factory.stream(key)
    ints_a = [first.integer_uniform(-3, 7) for _ in range(20)]
    ints_b = [second.integer_uniform(-3, 7) for _ in range(20)]
    assert ints_a == ints_b
    assert all(-3 <= value <= 7 for value in ints_a)

    choice_a = factory.stream(key).choice(("a", "b", "c"))
    choice_b = factory.stream(key).choice(("a", "b", "c"))
    assert choice_a == choice_b


def test_uniform_bounds_and_degenerate_range() -> None:
    stream = Xoshiro256StarStar(1, 2, 3, 4)
    value = stream.uniform(5.0, 5.0)
    assert value == 5.0

    with pytest.raises(ValueError):
        stream.uniform(2.0, 1.0)


def test_protocol_rejects_invalid_key_and_seed_ranges() -> None:
    with pytest.raises(ValueError, match="root_seed"):
        RngFactory(-1)
    with pytest.raises(ValueError, match="root_seed"):
        RngFactory(1 << 64)
    with pytest.raises(ValueError, match="attempt_index"):
        RngKey(1 << 64, RngStage.LAYOUT, ("feature", "x"), "sample")
    with pytest.raises(ValueError, match="scope"):
        RngKey(0, RngStage.LAYOUT, (), "sample")
    with pytest.raises(ValueError, match="purpose"):
        RngKey(0, RngStage.LAYOUT, ("feature", "x"), "")
    with pytest.raises(ValueError, match="rng_version"):
        RngFactory(0, rng_version=RNG_VERSION + 1)


def test_xoshiro_rejects_all_zero_state() -> None:
    with pytest.raises(ValueError, match="all zero"):
        Xoshiro256StarStar(0, 0, 0, 0)
