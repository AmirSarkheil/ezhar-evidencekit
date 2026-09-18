from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from evidencekit.canonical import manifest_digest
from evidencekit.collect import build_manifest
from evidencekit.collectors.files import collect_artifacts
from evidencekit.verify import verify_manifest


def test_nested_manifest_recollects_and_verifies(tmp_path: Path) -> None:
    config_dir = tmp_path / ".evidencekit"
    config_dir.mkdir()
    config = config_dir / "config.yml"
    config.write_text(
        "\n".join(
            [
                'schema_version: "1.0"',
                'workspace: "."',
                'manifest: "reports/evidence.json"',
                'include: ["**/*"]',
                "exclude: []",
                "max_artifact_bytes: 10485760",
                "junit: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "result.txt").write_text("ok\n", encoding="utf-8")

    _, first_path = build_manifest(config)
    _, second_path = build_manifest(config)

    assert first_path == second_path == (tmp_path / "reports/evidence.json").resolve()
    _, problems = verify_manifest(second_path)
    assert problems == []

    manifest = json.loads(second_path.read_text(encoding="utf-8"))
    collected = {artifact["path"] for artifact in manifest["artifacts"]}
    assert "reports/evidence.json" not in collected
    assert not any(path.startswith(".git/") for path in collected)
    assert not any(path.startswith(".evidencekit/") for path in collected)


def test_repository_root_config_uses_repository_as_workspace(tmp_path: Path) -> None:
    config = tmp_path / "evidencekit.yml"
    config.write_text(
        'workspace: "."\nmanifest: "evidence.json"\ninclude: ["artifacts/**/*"]\n',
        encoding="utf-8",
    )
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "result.txt").write_text("ok", encoding="utf-8")

    manifest, output = build_manifest(config)
    assert output == (tmp_path / "evidence.json").resolve()
    assert [item["path"] for item in manifest["artifacts"]] == ["artifacts/result.txt"]


def test_verify_reports_directory_artifact_as_problem(tmp_path: Path) -> None:
    directory = tmp_path / "artifact-dir"
    directory.mkdir()
    manifest = {
        "schema_version": "1.0",
        "run": {
            "id": "run",
            "started_at": "2026-09-18T00:00:00Z",
            "source_revision": None,
        },
        "environment": {"os": "linux", "runtime": "python-3.12"},
        "checks": [],
        "artifacts": [
            {
                "path": "artifact-dir",
                "sha256": "0" * 64,
                "size": 0,
            }
        ],
    }
    manifest["manifest_sha256"] = manifest_digest(manifest)
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    _, problems = verify_manifest(path, workspace=tmp_path)
    assert any("non-regular artifact" in problem for problem in problems)


def test_git_metadata_is_never_collected(tmp_path: Path) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("secret-ish-history", encoding="utf-8")
    (tmp_path / "normal.txt").write_text("ok", encoding="utf-8")

    artifacts, _ = collect_artifacts(
        tmp_path,
        includes=["**/*"],
        excludes=[],
        max_artifact_bytes=1_000_000,
    )
    assert [artifact.path for artifact in artifacts] == ["normal.txt"]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO creation unavailable")
def test_fifo_is_skipped_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "artifact.pipe"
    os.mkfifo(fifo)
    artifacts, warnings = collect_artifacts(
        tmp_path,
        includes=["*"],
        excludes=[],
        max_artifact_bytes=1_000_000,
    )
    assert artifacts == []
    assert any("non-regular" in warning for warning in warnings)
