from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from evidencekit.errors import ConfigError


HARD_MAX_ARTIFACT_BYTES = 268_435_456

DEFAULT_CONFIG = {
    "schema_version": "1.0",
    "workspace": ".",
    "manifest": "evidence.json",
    "include": ["artifacts/**/*"],
    "exclude": ["**/.git/**", "**/.evidencekit/**", "**/__pycache__/**"],
    "max_artifact_bytes": 10_485_760,
    "junit": [],
}

_PROTECTED_OUTPUT_PARTS = {".git", ".evidencekit"}
_CONTROL_CHARS = {"\x00", "\r", "\n"}


def _config_base_dir(config_path: Path) -> Path:
    parent = config_path.parent.resolve()
    return parent.parent if parent.name == ".evidencekit" else parent


def _validate_relative_path(
    value: Any,
    field: str,
    *,
    json_file: bool = False,
    allow_dot: bool = False,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field} must be a non-empty relative path")
    if any(char in value for char in _CONTROL_CHARS):
        raise ConfigError(f"{field} contains unsupported control characters")

    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ConfigError(f"{field} must be relative and must not contain '..'")
    if not path.parts and not allow_dot:
        raise ConfigError(f"{field} must name a file or subpath, not '.'")
    if json_file and path.suffix.lower() != ".json":
        raise ConfigError(f"{field} must point to a .json file")
    if json_file and any(part.lower() in _PROTECTED_OUTPUT_PARTS for part in path.parts):
        raise ConfigError(f"{field} must not write inside protected repository metadata")
    return value


def _validate_glob_patterns(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{field} must be a list of glob strings")

    result: list[str] = []
    for pattern in value:
        if not pattern.strip():
            raise ConfigError(f"{field} contains an empty glob")
        path = Path(pattern)
        if path.is_absolute() or ".." in path.parts:
            raise ConfigError(f"{field} globs must be relative and must not contain '..'")
        if any("**" in part and part != "**" for part in path.parts):
            raise ConfigError(f"invalid {field} glob: {pattern!r}")
        result.append(pattern)
    return result


def _write_config_posix(target_dir: Path, payload: bytes, *, force: bool) -> None:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC

    try:
        directory_fd = os.open(target_dir, directory_flags)
    except OSError as exc:
        raise ConfigError(f"unable to open configuration directory safely: {exc}") from exc

    file_flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        file_flags |= os.O_CLOEXEC
    file_flags |= os.O_TRUNC if force else os.O_EXCL

    try:
        try:
            descriptor = os.open("config.yml", file_flags, 0o644, dir_fd=directory_fd)
        except FileExistsError as exc:
            raise ConfigError(
                f"configuration already exists: {target_dir / 'config.yml'}"
            ) from exc
        except OSError as exc:
            raise ConfigError(f"unable to create configuration safely: {exc}") from exc

        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(directory_fd)


def _write_config_fallback(target_dir: Path, target: Path, payload: bytes, *, force: bool) -> None:
    if target.is_symlink():
        raise ConfigError(f"configuration path must not be a symlink: {target}")
    if target.exists() and not force:
        raise ConfigError(f"configuration already exists: {target}")

    before = target_dir.stat(follow_symlinks=False)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target_dir,
            prefix=".config-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        after = target_dir.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ConfigError("configuration directory changed during initialization")
        if target.is_symlink():
            raise ConfigError(f"configuration path became a symlink: {target}")
        os.replace(temp_name, target)
        temp_name = None
    except OSError as exc:
        raise ConfigError(f"unable to write configuration: {exc}") from exc
    finally:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass


def write_default_config(repo_root: Path, *, force: bool = False) -> Path:
    repo_root = repo_root.resolve()
    target_dir = repo_root / ".evidencekit"
    target = target_dir / "config.yml"

    try:
        if target_dir.is_symlink() or target.is_symlink():
            raise ConfigError(f"configuration path must not be a symlink: {target}")
        resolved_target = target.resolve(strict=False)
        resolved_target.relative_to(repo_root)
        target_dir.mkdir(parents=True, exist_ok=True)
        if target_dir.is_symlink() or target_dir.resolve() != target_dir:
            raise ConfigError(f"configuration directory changed unexpectedly: {target_dir}")
    except ConfigError:
        raise
    except (OSError, ValueError) as exc:
        raise ConfigError(f"unable to prepare configuration path: {exc}") from exc

    payload = yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False).encode("utf-8")
    secure_dir_fd = (
        os.open in getattr(os, "supports_dir_fd", set())
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
    )
    if secure_dir_fd:
        _write_config_posix(target_dir, payload, force=force)
    else:
        _write_config_fallback(target_dir, target, payload, force=force)
    return target


def load_config(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ConfigError(f"configuration must not be a symlink: {path}")
    if not path.exists():
        raise ConfigError(f"configuration not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ConfigError(f"invalid configuration: {exc}") from exc

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a mapping")

    merged = dict(DEFAULT_CONFIG)
    merged.update(raw)

    if merged["schema_version"] != "1.0":
        raise ConfigError("v0.1 only supports schema_version: 1.0")

    _validate_relative_path(merged["workspace"], "workspace", allow_dot=True)
    _validate_relative_path(merged["manifest"], "manifest", json_file=True)
    merged["include"] = _validate_glob_patterns(merged["include"], "include")
    merged["exclude"] = _validate_glob_patterns(merged["exclude"], "exclude")

    if not isinstance(merged["junit"], list) or not all(
        isinstance(item, str) for item in merged["junit"]
    ):
        raise ConfigError("junit must be a list of relative paths")
    for junit_path in merged["junit"]:
        _validate_relative_path(junit_path, "junit entry")

    max_bytes = merged["max_artifact_bytes"]
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ConfigError("max_artifact_bytes must be a positive integer")
    if max_bytes > HARD_MAX_ARTIFACT_BYTES:
        raise ConfigError(
            f"max_artifact_bytes must not exceed {HARD_MAX_ARTIFACT_BYTES} bytes"
        )

    return merged


def resolve_workspace(config_path: Path, config: dict[str, Any]) -> Path:
    base = _config_base_dir(config_path)
    workspace = Path(str(config["workspace"]))
    candidate = (base / workspace).resolve(strict=False)
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ConfigError("workspace must remain inside the configuration repository") from exc
    return candidate


def resolve_manifest_path(config_path: Path, config: dict[str, Any]) -> Path:
    root = resolve_workspace(config_path, config)
    relative = Path(str(config["manifest"]))
    candidate = root / relative

    if candidate.is_symlink():
        raise ConfigError(f"manifest output must not be a symlink: {candidate}")

    resolved = candidate.resolve(strict=False)
    try:
        rel = resolved.relative_to(root)
    except ValueError as exc:
        raise ConfigError("manifest output must remain inside the workspace") from exc

    if any(part.lower() in _PROTECTED_OUTPUT_PARTS for part in rel.parts):
        raise ConfigError("manifest output must not be inside protected repository metadata")
    return resolved
