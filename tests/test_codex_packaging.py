from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_PATH = ROOT / "AGENTS.md"
SKILL_DIR = ROOT / ".codex" / "skills" / "domain-generator-authoring"
SKILL_PATH = SKILL_DIR / "SKILL.md"
INTEGRATION_PATH = ROOT / "docs" / "integrations" / "codex.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    assert lines and lines[0] == "---"
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError("SKILL.md frontmatter must have a closing ---") from exc

    values: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        assert separator, f"invalid frontmatter line: {line!r}"
        key = key.strip()
        value = value.strip()
        assert key
        assert value
        assert key not in values
        values[key] = value
    return values


def test_codex_packaging_files_exist() -> None:
    assert AGENTS_PATH.is_file()
    assert SKILL_PATH.is_file()
    assert INTEGRATION_PATH.is_file()


def test_skill_frontmatter_is_minimal_and_matches_directory() -> None:
    metadata = _frontmatter(_read(SKILL_PATH))

    assert set(metadata) == {"name", "description"}
    assert metadata["name"] == SKILL_DIR.name == "domain-generator-authoring"
    assert "procedural domain" in metadata["description"].lower()
    assert "GenerationRequest" in metadata["description"]


def test_agents_routes_domain_authoring_to_skill_and_project_status() -> None:
    text = _read(AGENTS_PATH)

    assert "PROJECT.md" in text
    assert ".codex/skills/domain-generator-authoring/SKILL.md" in text
    assert "domain-generator generate" in text
    assert "python -m pytest" in text
    assert "INV-006" in text


def test_skill_references_existing_canonical_documents() -> None:
    text = _read(SKILL_PATH)
    references = (
        "PROJECT.md",
        "docs/skills/local-model-authoring-v0.1.md",
        "docs/design/codex-integration-packaging-v0.1.md",
        "docs/design/canonical-cli-python-entrypoint-v0.1.md",
    )

    for reference in references:
        assert reference in text
        assert (ROOT / reference).exists(), reference


def test_skill_uses_canonical_application_boundary() -> None:
    text = _read(SKILL_PATH)

    assert "domain-generator generate" in text
    assert "one semantic generation run" in text
    assert "at most two technical repair drafts" in text
    assert "do not autonomously replan or reroll" in text.lower()
    assert "Do not call `layout_stage`" in text
    for stage in (
        "layout_stage",
        "terrain_stage",
        "hydrology_stage",
        "surface_stage",
        "placement_stage",
        "final_stage",
    ):
        assert stage in text


def test_skill_protects_canonical_outputs_from_manual_world_editing() -> None:
    text = _read(SKILL_PATH)

    assert "Do not edit generated canonical `.npy` fields or `domain.json`" in text
    assert "Change the request/preset inputs" in text


def test_integration_note_documents_local_and_user_level_installation() -> None:
    text = _read(INTEGRATION_PATH)

    assert ".codex/skills/domain-generator-authoring/SKILL.md" in text
    assert "$skill-installer" in text
    assert "$CODEX_HOME/skills" in text
    assert "https://github.com/MysterioCrypto/domain_generator/tree/main/.codex/skills/domain-generator-authoring" in text
    assert "Restart Codex" in text
