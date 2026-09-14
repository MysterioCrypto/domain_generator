from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_numpy_dependency_stays_below_x86_64_v2_baseline_transition() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    numpy_requirements = [item for item in project["dependencies"] if item.startswith("numpy")]
    assert numpy_requirements == ["numpy>=2.0,<2.4"]


def test_local_python_and_generation_artifacts_are_ignored() -> None:
    entries = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    required = {
        ".venv/",
        "local-tests/",
        "*.egg-info/",
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
    }
    assert required <= entries
