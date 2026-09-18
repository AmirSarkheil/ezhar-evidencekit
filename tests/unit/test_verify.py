from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidencekit.canonical import manifest_digest
from evidencekit.errors import ConfigError
from evidencekit.integrity import sha256_file
from evidencekit.verify import verify_manifest


def _write_manifest(
    root: Path,
    *,
    artifact_path: str,
    sha256: str,
    size: int,
    name: str = "evidence.json",
) -> Path:
    manifest = {
        "schema_version": "1.0",
        "run": {
            "id": "verify-test",
            "started_at": "2026-09-18T00:00:00Z",
            "source_revision": None,
        },
        "environment": {"os": "linux", "runtime": "python-3.12"},
        "checks": [],
        "artifacts": [
            {
                "path": artifact_path,
                "sha256": sha256,
                "size": size,
            }
        ],
        "warnings": [],
    }
    manifest["manifest_sha256"] = manifest_digest(manifest)
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_verify_reports_missing_artifact(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        artifact_path="missing.txt",
        sha256="0" * 64,
        size=0,
    )
    _, problems = verify_manifest(manifest, workspace=tmp_path)
    assert any("does not exist" in problem for problem in problems)


def test_verify_reports_size_and_digest_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("old", encoding="utf-8")
    original_digest = sha256_file(artifact)
    manifest = _write_manifest(
        tmp_path,
        artifact_path="artifact.txt",
        sha256=original_digest,
        size=3,
    )

    artifact.write_text("new-content", encoding="utf-8")
    _, problems = verify_manifest(manifest, workspace=tmp_path)
    assert any("size mismatch" in problem for problem in problems)
    assert any("sha256 mismatch" in problem for problem in problems)


def test_verify_rejects_workspace_and_config_together(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("ok", encoding="utf-8")
    manifest = _write_manifest(
        tmp_path,
        artifact_path="artifact.txt",
        sha256=sha256_file(artifact),
        size=2,
    )
    config = tmp_path / "config.yml"
    config.write_text("workspace: .\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="either workspace or config_path"):
        verify_manifest(manifest, workspace=tmp_path, config_path=config)


def test_verify_rejects_config_for_different_manifest(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("ok", encoding="utf-8")
    manifest = _write_manifest(
        tmp_path,
        artifact_path="artifact.txt",
        sha256=sha256_file(artifact),
        size=2,
    )
    config = tmp_path / "config.yml"
    config.write_text(
        "workspace: .\nmanifest: other.json\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="does not match"):
        verify_manifest(manifest, config_path=config)
