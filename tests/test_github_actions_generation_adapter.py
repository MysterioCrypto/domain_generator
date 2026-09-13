from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from domain_generator.contracts import GenerationRequest


ROOT = Path(__file__).resolve().parents[1]
GENERATION_WORKFLOW = ROOT / ".github" / "workflows" / "generate-domain.yml"
CLEANUP_WORKFLOW = ROOT / ".github" / "workflows" / "cleanup-remote-generation.yml"
HELPER_PATH = ROOT / "scripts" / "remote_generation.py"
EXAMPLE_REQUEST = ROOT / "remote-requests" / "example" / "request.json"
EXAMPLE_RUN = ROOT / "remote-requests" / "example" / "run.json"
INTEGRATION_DOC = ROOT / "docs" / "integrations" / "github-actions-generation.md"


def _load_helper():
    spec = importlib.util.spec_from_file_location("remote_generation", HELPER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_remote_generation_packaging_files_exist() -> None:
    for path in (
        GENERATION_WORKFLOW,
        CLEANUP_WORKFLOW,
        HELPER_PATH,
        EXAMPLE_REQUEST,
        EXAMPLE_RUN,
        INTEGRATION_DOC,
    ):
        assert path.is_file(), path


def test_generation_workflow_has_bounded_read_only_contract() -> None:
    text = GENERATION_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "pull_request:" in text
    assert '"remote-requests/**"' in text
    assert "request_path:" in text
    assert "presets_path:" in text
    assert "preview:" in text
    assert "seed:" not in text
    assert "width_km:" not in text
    assert "height_km:" not in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "github.event.pull_request.head.sha" in text
    assert "fetch-depth: 0" in text
    assert "actions/upload-artifact@v4" in text
    assert "domain-bundle" in text
    assert "technical-preview" in text
    assert "generation-diagnostics" in text
    assert "git push" not in text
    assert "--force" not in text


def test_cleanup_workflow_is_isolated_and_prefix_guarded() -> None:
    text = CLEANUP_WORKFLOW.read_text(encoding="utf-8")

    assert "types: [closed]" in text
    assert "contents: write" in text
    assert "remote-generation/" in text
    assert "head.repo.full_name == github.repository" in text
    assert "head.ref != github.event.repository.default_branch" in text
    assert "head.ref != github.event.pull_request.base.ref" in text
    assert "gh api --method DELETE" in text
    assert "actions/checkout" not in text
    assert "domain-generator" not in text


def test_example_request_and_manifest_are_valid() -> None:
    request_payload = json.loads(EXAMPLE_REQUEST.read_text(encoding="utf-8"))
    request = GenerationRequest.model_validate(request_payload)
    manifest = json.loads(EXAMPLE_RUN.read_text(encoding="utf-8"))

    assert request.domain_spec.id == "remote-example"
    assert manifest == {
        "run_version": "0.1",
        "request_path": "remote-requests/example/request.json",
        "presets_path": None,
        "preview": True,
    }


def test_safe_json_path_rejects_absolute_and_traversal(tmp_path: Path) -> None:
    helper = _load_helper()
    workspace = tmp_path / "repo"
    workspace.mkdir()
    inside = workspace / "inside.json"
    inside.write_text("{}", encoding="utf-8")
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")

    assert helper.safe_json_path(workspace, "inside.json", label="request") == inside.resolve()

    with pytest.raises(ValueError, match="repository-relative"):
        helper.safe_json_path(workspace, str(outside.resolve()), label="request")
    with pytest.raises(ValueError, match="escapes repository workspace"):
        helper.safe_json_path(workspace, "../outside.json", label="request")


def test_manifest_resolution_supports_optional_presets(tmp_path: Path) -> None:
    helper = _load_helper()
    workspace = tmp_path / "repo"
    workspace.mkdir()
    manifest = workspace / "run.json"
    manifest.write_text(
        json.dumps(
            {
                "run_version": "0.1",
                "request_path": "request.json",
                "presets_path": None,
                "preview": True,
            }
        ),
        encoding="utf-8",
    )

    assert helper.load_run_manifest(workspace, "run.json") == ("request.json", None, True)


def test_helper_invokes_canonical_cli_exactly_once_and_writes_diagnostics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    helper = _load_helper()
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / "request.json").write_text("{}", encoding="utf-8")
    work_dir = tmp_path / "work"
    calls: list[list[str]] = []

    def fake_runner(command, *, check, capture_output, text):
        calls.append(command)
        output_dir = Path(command[command.index("--output") + 1])
        (output_dir / "fields").mkdir(parents=True)
        (output_dir / "domain.json").write_text("{}", encoding="utf-8")
        (output_dir / "manifest.json").write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout='{"status":"ok"}\n', stderr="")

    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("GITHUB_RUN_ID", "99")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")

    code = helper.execute_remote_generation(
        workspace=workspace,
        work_dir=work_dir,
        request_path="request.json",
        presets_path=None,
        preview=False,
        runner=fake_runner,
    )

    assert code == 0
    assert len(calls) == 1
    assert calls[0][0:2] == ["domain-generator", "generate"]
    assert "--presets" not in calls[0]
    assert "--preview" not in calls[0]
    assert (work_dir / "bundle" / "domain.json").is_file()
    assert (work_dir / "execution" / "request.json").is_file()
    assert (work_dir / "execution" / "stdout.txt").read_text(encoding="utf-8") == '{"status":"ok"}\n'

    metadata = json.loads((work_dir / "execution" / "remote-execution.json").read_text(encoding="utf-8"))
    assert metadata["generator_commit"] == "abc123"
    assert metadata["cli_exit_code"] == 0
    assert metadata["transport_error"] is None
    assert metadata["request_sha256"]


def test_helper_passes_optional_presets_and_preview(tmp_path: Path) -> None:
    helper = _load_helper()
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / "request.json").write_text("{}", encoding="utf-8")
    (workspace / "presets.json").write_text("{}", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_runner(command, *, check, capture_output, text):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    code = helper.execute_remote_generation(
        workspace=workspace,
        work_dir=tmp_path / "work",
        request_path="request.json",
        presets_path="presets.json",
        preview=True,
        runner=fake_runner,
    )

    assert code == 0
    assert len(calls) == 1
    assert "--presets" in calls[0]
    assert "--preview" in calls[0]


def test_cli_failure_is_not_retried_and_diagnostics_survive(tmp_path: Path) -> None:
    helper = _load_helper()
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / "request.json").write_text("{}", encoding="utf-8")
    calls = 0

    def failing_runner(command, *, check, capture_output, text):
        nonlocal calls
        calls += 1
        return SimpleNamespace(returncode=4, stdout="", stderr="generation failed\n")

    work_dir = tmp_path / "work"
    code = helper.execute_remote_generation(
        workspace=workspace,
        work_dir=work_dir,
        request_path="request.json",
        presets_path=None,
        preview=False,
        runner=failing_runner,
    )

    assert code == 4
    assert calls == 1
    assert not (work_dir / "bundle").exists()
    assert (work_dir / "execution" / "stderr.txt").read_text(encoding="utf-8") == "generation failed\n"
    metadata = json.loads((work_dir / "execution" / "remote-execution.json").read_text(encoding="utf-8"))
    assert metadata["cli_exit_code"] == 4
    assert metadata["transport_error"] is None


def test_transport_failure_does_not_invoke_generator(tmp_path: Path) -> None:
    helper = _load_helper()
    workspace = tmp_path / "repo"
    workspace.mkdir()
    calls = 0

    def forbidden_runner(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("runner must not be invoked")

    work_dir = tmp_path / "work"
    code = helper.execute_remote_generation(
        workspace=workspace,
        work_dir=work_dir,
        request_path="missing.json",
        presets_path=None,
        preview=False,
        runner=forbidden_runner,
    )

    assert code == helper.TRANSPORT_ERROR
    assert calls == 0
    metadata = json.loads((work_dir / "execution" / "remote-execution.json").read_text(encoding="utf-8"))
    assert metadata["cli_exit_code"] is None
    assert metadata["transport_error"]


def test_integration_doc_records_branch_cleanup_and_artifact_retention() -> None:
    text = INTEGRATION_DOC.read_text(encoding="utf-8")

    assert "remote-generation/<request-id>" in text
    assert "close generation PR without merge" in text
    assert "cleanup-remote-generation" in text
    assert "contents: read" in text
    assert "contents: write" in text
    assert "retention 7" in text
