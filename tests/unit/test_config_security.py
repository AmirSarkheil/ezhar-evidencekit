from __future__ import annotations

import os
from pathlib import Path

import pytest

from evidencekit.config import (
    _write_config_fallback,
    load_config,
    resolve_manifest_path,
    resolve_workspace,
    write_default_config,
)
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


def test_manifest_cannot_target_evidencekit_metadata(tmp_path: Path) -> None:
    path = _write_config(tmp_path, 'manifest: ".evidencekit/config.json"\n')
    with pytest.raises(ConfigError):
        load_config(path)


def test_junit_dot_path_is_rejected(tmp_path: Path) -> None:
    path = _write_config(tmp_path, 'junit: ["."]\n')
    with pytest.raises(ConfigError):
        load_config(path)


def test_non_utf8_config_becomes_config_error(tmp_path: Path) -> None:
    config_dir = tmp_path / ".evidencekit"
    config_dir.mkdir()
    path = config_dir / "config.yml"
    path.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(ConfigError):
        load_config(path)


def test_excessive_artifact_limit_is_rejected(tmp_path: Path) -> None:
    path = _write_config(tmp_path, "max_artifact_bytes: 999999999\n")
    with pytest.raises(ConfigError):
        load_config(path)


def test_fallback_config_writer_creates_and_replaces(tmp_path: Path) -> None:
    target_dir = tmp_path / ".evidencekit"
    target_dir.mkdir()
    target = target_dir / "config.yml"

    _write_config_fallback(target_dir, target, b"first\n", force=False)
    assert target.read_bytes() == b"first\n"

    _write_config_fallback(target_dir, target, b"second\n", force=True)
    assert target.read_bytes() == b"second\n"


def test_write_default_config_refuses_existing_file(tmp_path: Path) -> None:
    first = write_default_config(tmp_path)
    assert first.exists()
    with pytest.raises(ConfigError, match="already exists"):
        write_default_config(tmp_path)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO creation unavailable")
def test_config_fifo_is_rejected_without_blocking(tmp_path: Path) -> None:
    config_dir = tmp_path / ".evidencekit"
    config_dir.mkdir()
    path = config_dir / "config.yml"
    os.mkfifo(path)
    with pytest.raises(ConfigError, match="regular file"):
        load_config(path)


def test_force_init_rejects_hard_linked_config(tmp_path: Path) -> None:
    config = write_default_config(tmp_path)
    external = tmp_path / "external-config-link.yml"
    try:
        os.link(config, external)
    except OSError:
        pytest.skip("hard links unavailable")

    original = external.read_bytes()
    with pytest.raises(ConfigError, match="hard-linked"):
        write_default_config(tmp_path, force=True)
    assert external.read_bytes() == original


def test_workspace_cannot_be_git_metadata(tmp_path: Path) -> None:
    path = _write_config(tmp_path, 'workspace: ".git"\n')
    config = load_config(path)
    with pytest.raises(ConfigError, match="protected"):
        resolve_workspace(path, config)


def test_workspace_symlink_loop_becomes_config_error(tmp_path: Path) -> None:
    loop = tmp_path / "loop"
    try:
        loop.symlink_to(loop, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")

    path = _write_config(tmp_path, 'workspace: "loop"\n')
    config = load_config(path)
    with pytest.raises(ConfigError):
        resolve_workspace(path, config)


def test_symlinked_config_base_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    config_dir = real / ".evidencekit"
    config_dir.mkdir()
    (config_dir / "config.yml").write_text("workspace: .\n", encoding="utf-8")

    alias = tmp_path / "alias"
    try:
        alias.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(ConfigError, match="symlinks"):
        load_config(alias / ".evidencekit" / "config.yml")
