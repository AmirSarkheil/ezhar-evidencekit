from __future__ import annotations

from pathlib import Path

import pytest

from evidencekit.errors import ValidationFailure
from evidencekit.validate import MAX_JSON_DEPTH, MAX_MANIFEST_BYTES, load_and_validate


def test_oversized_manifest_is_rejected_before_json_parse(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    path.write_bytes(b" " * (MAX_MANIFEST_BYTES + 1))
    with pytest.raises(ValidationFailure, match="maximum size"):
        load_and_validate(path)


def test_deep_manifest_is_rejected_before_json_parse(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    payload = "[" * (MAX_JSON_DEPTH + 1) + "0" + "]" * (MAX_JSON_DEPTH + 1)
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValidationFailure, match="nesting"):
        load_and_validate(path)


def test_manifest_symlink_is_not_followed_when_supported(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "evidence.json"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(ValidationFailure):
        load_and_validate(link)
