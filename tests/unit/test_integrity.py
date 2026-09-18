from pathlib import Path

import pytest

from evidencekit.errors import SecurityError
from evidencekit.integrity import (
    looks_sensitive,
    media_type_for,
    safe_artifact_path,
    sha256_file,
)


def test_sha256_file_is_stable(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("evidence\n", encoding="utf-8")
    assert sha256_file(artifact) == sha256_file(artifact)


def test_parent_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        safe_artifact_path(tmp_path, "../outside.txt", require_exists=False)


def test_symlink_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("x", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(SecurityError):
        safe_artifact_path(tmp_path, "link.txt")


def test_empty_artifact_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(SecurityError, match="non-empty"):
        safe_artifact_path(tmp_path, "", require_exists=False)


def test_control_character_artifact_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(SecurityError, match="control"):
        safe_artifact_path(tmp_path, "bad\nname.txt", require_exists=False)


def test_sha256_rejects_nonpositive_chunk_size(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("x", encoding="utf-8")
    with pytest.raises(SecurityError, match="positive"):
        sha256_file(artifact, chunk_size=0)


def test_sensitive_name_and_media_type_helpers(tmp_path: Path) -> None:
    assert looks_sensitive(tmp_path / ".env")
    assert looks_sensitive(tmp_path / "service_api_token.txt")
    assert not looks_sensitive(tmp_path / "report.txt")
    assert media_type_for(tmp_path / "report.json") == "application/json"
