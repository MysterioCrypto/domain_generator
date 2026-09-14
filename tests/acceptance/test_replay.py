from __future__ import annotations

import pytest

from .support import CASE_IDS, assert_exact_replay, load_case, run_detailed


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_acceptance_world_exact_replay(case_id: str) -> None:
    case = load_case(case_id)
    first = run_detailed(case)
    second = run_detailed(case)
    assert_exact_replay(first, second)
