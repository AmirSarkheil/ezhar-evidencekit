from pathlib import Path

import pytest

from evidencekit.errors import SecurityError
from evidencekit.integrity import safe_artifact_path, sha256_file


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
