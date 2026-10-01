from __future__ import annotations

from pathlib import Path
import tomllib

import domain_generator


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


def test_generator_version_matches_core_v02_development_line() -> None:
    project = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    assert project["version"] == "0.2.0.dev0"
    assert domain_generator.__version__ == project["version"]


def test_current_docs_identify_core_v02_as_active() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "Активная линия — Core 0.2" in readme
    assert "id: ARCH-CORE-0.2" in architecture
    assert "target: core-0.2" in architecture
