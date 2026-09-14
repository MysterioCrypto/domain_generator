from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


TRANSPORT_ERROR = 64


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_json_path(workspace: Path, raw: str, *, label: str) -> Path:
    if not raw:
        raise ValueError(f"{label} path is empty")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ValueError(f"{label} path must be repository-relative")
    if candidate.suffix.lower() != ".json":
        raise ValueError(f"{label} path must end in .json")

    root = workspace.resolve(strict=True)
    resolved = (root / candidate).resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} path escapes repository workspace") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} path must reference a regular file")
    return resolved


def load_run_manifest(workspace: Path, raw_path: str) -> tuple[str, str | None, bool, bool]:
    manifest_path = safe_json_path(workspace, raw_path, label="manifest")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid run manifest JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("run manifest must be a JSON object")
    allowed = {"run_version", "request_path", "presets_path", "preview", "guide_preview"}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(f"run manifest has unknown keys: {sorted(unknown)}")
    if payload.get("run_version") != "0.1":
        raise ValueError("run manifest run_version must be '0.1'")
    request_path = payload.get("request_path")
    presets_path = payload.get("presets_path")
    preview = payload.get("preview", False)
    guide_preview = payload.get("guide_preview", False)
    if not isinstance(request_path, str) or not request_path:
        raise ValueError("run manifest request_path must be a non-empty string")
    if presets_path is not None and not isinstance(presets_path, str):
        raise ValueError("run manifest presets_path must be a string or null")
    if not isinstance(preview, bool):
        raise ValueError("run manifest preview must be boolean")
    if not isinstance(guide_preview, bool):
        raise ValueError("run manifest guide_preview must be boolean")
    return request_path, presets_path, preview, guide_preview


def _execution_metadata(
    *,
    request_rel: str | None,
    presets_rel: str | None,
    preview: bool,
    guide_preview: bool,
) -> dict[str, Any]:
    github_sha = os.getenv("GITHUB_SHA")
    return {
        "execution_version": "0.1",
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "generator_commit": os.getenv("GENERATOR_COMMIT") or github_sha,
        "github_sha": github_sha,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "event_name": os.getenv("GITHUB_EVENT_NAME"),
        "request_path": request_rel,
        "request_sha256": None,
        "presets_path": presets_rel,
        "presets_sha256": None,
        "preview": preview,
        "guide_preview": guide_preview,
        "cli_exit_code": None,
        "transport_error": None,
    }


def execute_remote_generation(
    *,
    workspace: Path,
    work_dir: Path,
    request_path: str,
    presets_path: str | None,
    preview: bool,
    guide_preview: bool = False,
    runner: Any = subprocess.run,
) -> int:
    if work_dir.exists():
        raise ValueError(f"work directory already exists: {work_dir}")
    execution_dir = work_dir / "execution"
    bundle_dir = work_dir / "bundle"
    execution_dir.mkdir(parents=True)

    metadata = _execution_metadata(
        request_rel=request_path,
        presets_rel=presets_path,
        preview=preview,
        guide_preview=guide_preview,
    )
    stdout_text = ""
    stderr_text = ""

    try:
        request = safe_json_path(workspace, request_path, label="request")
        presets = safe_json_path(workspace, presets_path, label="presets") if presets_path else None

        metadata["request_sha256"] = _sha256(request)
        if presets is not None:
            metadata["presets_sha256"] = _sha256(presets)

        shutil.copyfile(request, execution_dir / "request.json")
        if presets is not None:
            shutil.copyfile(presets, execution_dir / "presets.json")

        command = [
            "domain-generator",
            "generate",
            str(request),
            "--output",
            str(bundle_dir),
        ]
        if presets is not None:
            command.extend(["--presets", str(presets)])
        if preview:
            command.append("--preview")
        if guide_preview:
            command.append("--guide-preview")

        completed = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        stdout_text = completed.stdout or ""
        stderr_text = completed.stderr or ""
        metadata["cli_exit_code"] = int(completed.returncode)
        return int(completed.returncode)
    except Exception as exc:
        stderr_text = f"remote generation transport error: {exc}\n"
        metadata["transport_error"] = str(exc)
        return TRANSPORT_ERROR
    finally:
        (execution_dir / "stdout.txt").write_text(stdout_text, encoding="utf-8")
        (execution_dir / "stderr.txt").write_text(stderr_text, encoding="utf-8")
        (execution_dir / "remote-execution.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected boolean value")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remote GitHub Actions wrapper for domain-generator")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest")
    source.add_argument("--request-path")
    parser.add_argument("--presets-path")
    parser.add_argument("--preview", type=_parse_bool, default=False)
    parser.add_argument("--guide-preview", type=_parse_bool, default=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request_path = args.request_path
    presets_path = args.presets_path
    preview = args.preview
    guide_preview = args.guide_preview

    if args.manifest:
        try:
            request_path, presets_path, preview, guide_preview = load_run_manifest(
                args.workspace,
                args.manifest,
            )
        except Exception as exc:
            work_dir = args.work_dir
            if work_dir.exists():
                print(f"remote generation transport error: {exc}", file=sys.stderr)
                return TRANSPORT_ERROR
            execution_dir = work_dir / "execution"
            execution_dir.mkdir(parents=True)
            metadata = _execution_metadata(
                request_rel=None,
                presets_rel=None,
                preview=False,
                guide_preview=False,
            )
            metadata["transport_error"] = str(exc)
            (execution_dir / "stdout.txt").write_text("", encoding="utf-8")
            (execution_dir / "stderr.txt").write_text(
                f"remote generation transport error: {exc}\n", encoding="utf-8"
            )
            (execution_dir / "remote-execution.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return TRANSPORT_ERROR

    assert request_path is not None
    return execute_remote_generation(
        workspace=args.workspace,
        work_dir=args.work_dir,
        request_path=request_path,
        presets_path=presets_path,
        preview=preview,
        guide_preview=guide_preview,
    )


if __name__ == "__main__":
    raise SystemExit(main())
