from __future__ import annotations

from pathlib import Path

import pytest

from evidencekit.config import load_config, resolve_manifest_path, resolve_workspace
from evidencekit.errors import ConfigError


def _write_config(tmp_path: Path, text: str) -> Path:
    config_dir = tmp_path / ".evidencekit"
    config_dir.mkdir()
    path = config_dir / "config.yml"
    path.write_text(text, encoding="utf-8")
    return path


def test_boolean_max_artifact_bytes_is_rejected(tmp_path: Path) -> None:
    path = _write_config(tmp_path, "max_artifact_bytes: true\n")
    with pytest.raises(ConfigError):
        load_config(path)


def test_manifest_cannot_target_git_metadata(tmp_path: Path) -> None:
    path = _write_config(tmp_path, 'manifest: ".git/evidence.json"\n')
    with pytest.raises(ConfigError):
        load_config(path)


def test_invalid_recursive_glob_is_rejected(tmp_path: Path) -> None:
    path = _write_config(tmp_path, 'include: ["**.txt"]\n')
    with pytest.raises(ConfigError):
        load_config(path)


def test_malformed_yaml_becomes_config_error(tmp_path: Path) -> None:
    path = _write_config(tmp_path, "include: [\n")
    with pytest.raises(ConfigError):
        load_config(path)


def test_repo_root_config_resolves_workspace_to_repo(tmp_path: Path) -> None:
    path = tmp_path / "evidencekit.yml"
    path.write_text("workspace: .\nmanifest: reports/evidence.json\n", encoding="utf-8")
    config = load_config(path)
    assert resolve_workspace(path, config) == tmp_path.resolve()
    assert resolve_manifest_path(path, config) == (tmp_path / "reports/evidence.json").resolve()


def test_manifest_parent_symlink_escape_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "reports"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")

    path = _write_config(tmp_path, "manifest: reports/evidence.json\n")
    config = load_config(path)
    with pytest.raises(ConfigError):
        resolve_manifest_path(path, config)
