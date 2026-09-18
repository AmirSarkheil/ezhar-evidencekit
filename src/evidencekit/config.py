from __future__ import annotations

import os
import stat
import tempfile
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any

import yaml

from evidencekit.errors import ConfigError


HARD_MAX_ARTIFACT_BYTES = 268_435_456
MAX_CONFIG_BYTES = 1_048_576

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


def _ensure_config_location(config_path: Path) -> Path:
    absolute = config_path.absolute()
    parent = absolute.parent
    base = parent.parent if parent.name == ".evidencekit" else parent

    try:
        if parent.is_symlink() or base.is_symlink():
            raise ConfigError("configuration parent directories must not be symlinks")
        parent.resolve(strict=False)
        base.resolve(strict=False)
    except ConfigError:
        raise
    except (OSError, RuntimeError) as exc:
        raise ConfigError(f"unable to resolve configuration location: {exc}") from exc
    return absolute


def _config_base_dir(config_path: Path) -> Path:
    absolute = _ensure_config_location(config_path)
    parent = absolute.parent
    base = parent.parent if parent.name == ".evidencekit" else parent
    try:
        return base.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ConfigError(f"unable to resolve configuration base: {exc}") from exc


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

    try:
        path = Path(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field} is not a valid path") from exc

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
        try:
            path = Path(pattern)
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"invalid {field} glob: {pattern!r}") from exc
        if path.is_absolute() or ".." in path.parts:
            raise ConfigError(f"{field} globs must be relative and must not contain '..'")
        if any("**" in part and part != "**" for part in path.parts):
            raise ConfigError(f"invalid {field} glob: {pattern!r}")
        result.append(pattern)
    return result


def _open_flags(read_only: bool = True) -> int:
    flags = os.O_RDONLY if read_only else os.O_WRONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    return flags


def _read_config_text(path: Path) -> str:
    path = _ensure_config_location(path)
    flags = _open_flags()
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ConfigError(f"unable to open configuration safely: {exc}") from exc

    try:
        with os.fdopen(descriptor, "rb") as handle:
            metadata = os.fstat(handle.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise ConfigError("configuration must be a regular file")
            payload = handle.read(MAX_CONFIG_BYTES + 1)
            if len(payload) > MAX_CONFIG_BYTES:
                raise ConfigError(
                    f"configuration exceeds maximum size of {MAX_CONFIG_BYTES} bytes"
                )
    except ConfigError:
        raise
    except OSError as exc:
        raise ConfigError(f"unable to read configuration: {exc}") from exc

    try:
        return payload.decode("utf-8")
    except UnicodeError as exc:
        raise ConfigError(f"configuration is not valid UTF-8: {exc}") from exc


def _inspect_existing_config(directory_fd: int) -> None:
    flags = _open_flags()
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        descriptor = os.open("config.yml", flags, dir_fd=directory_fd)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ConfigError(f"unable to inspect existing configuration safely: {exc}") from exc

    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ConfigError("existing configuration must be a regular file")
        if metadata.st_nlink != 1:
            raise ConfigError("refusing to replace a hard-linked configuration file")
    finally:
        os.close(descriptor)


def _write_config_posix(target_dir: Path, payload: bytes, *, force: bool) -> None:
    directory_flags = _open_flags() | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        directory_fd = os.open(target_dir, directory_flags)
    except OSError as exc:
        raise ConfigError(f"unable to open configuration directory safely: {exc}") from exc

    temp_name = f".config-{uuid.uuid4().hex}.tmp"
    temp_created = False
    try:
        temp_flags = _open_flags(read_only=False) | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        try:
            descriptor = os.open(temp_name, temp_flags, 0o644, dir_fd=directory_fd)
            temp_created = True
        except OSError as exc:
            raise ConfigError(f"unable to create temporary configuration: {exc}") from exc

        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise ConfigError(f"unable to write temporary configuration: {exc}") from exc

        if force:
            _inspect_existing_config(directory_fd)
            try:
                os.replace(
                    temp_name,
                    "config.yml",
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                )
            except OSError as exc:
                raise ConfigError(f"unable to replace configuration atomically: {exc}") from exc
            temp_created = False
        else:
            try:
                os.link(
                    temp_name,
                    "config.yml",
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise ConfigError(
                    f"configuration already exists: {target_dir / 'config.yml'}"
                ) from exc
            except OSError as exc:
                raise ConfigError(f"unable to install configuration atomically: {exc}") from exc
            try:
                os.unlink(temp_name, dir_fd=directory_fd)
            except OSError as exc:
                raise ConfigError(f"unable to remove temporary configuration: {exc}") from exc
            temp_created = False

        with suppress(OSError):
            os.fsync(directory_fd)
    finally:
        if temp_created:
            with suppress(OSError):
                os.unlink(temp_name, dir_fd=directory_fd)
        os.close(directory_fd)


def _write_config_fallback(target_dir: Path, target: Path, payload: bytes, *, force: bool) -> None:
    try:
        if target.is_symlink():
            raise ConfigError(f"configuration path must not be a symlink: {target}")
        if target.exists():
            metadata = target.stat(follow_symlinks=False)
            if not stat.S_ISREG(metadata.st_mode):
                raise ConfigError("existing configuration must be a regular file")
            if metadata.st_nlink != 1:
                raise ConfigError("refusing to replace a hard-linked configuration file")
            if not force:
                raise ConfigError(f"configuration already exists: {target}")
        before = target_dir.stat(follow_symlinks=False)
    except ConfigError:
        raise
    except OSError as exc:
        raise ConfigError(f"unable to inspect configuration path: {exc}") from exc

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

        if force:
            if target.exists():
                metadata = target.stat(follow_symlinks=False)
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                    raise ConfigError("refusing to replace unsafe configuration target")
            os.replace(temp_name, target)
        else:
            try:
                os.link(temp_name, target, follow_symlinks=False)
            except FileExistsError as exc:
                raise ConfigError(f"configuration already exists: {target}") from exc
            os.unlink(temp_name)
        temp_name = None
    except ConfigError:
        raise
    except OSError as exc:
        raise ConfigError(f"unable to write configuration: {exc}") from exc
    finally:
        if temp_name is not None:
            with suppress(OSError):
                Path(temp_name).unlink(missing_ok=True)


def write_default_config(repo_root: Path, *, force: bool = False) -> Path:
    try:
        repo_root = repo_root.resolve()
    except (OSError, RuntimeError) as exc:
        raise ConfigError(f"unable to resolve repository root: {exc}") from exc

    target_dir = repo_root / ".evidencekit"
    target = target_dir / "config.yml"

    try:
        if target_dir.is_symlink() or target.is_symlink():
            raise ConfigError(f"configuration path must not be a symlink: {target}")
        target.resolve(strict=False).relative_to(repo_root)
        target_dir.mkdir(parents=True, exist_ok=True)
        if target_dir.is_symlink() or target_dir.resolve() != target_dir:
            raise ConfigError(f"configuration directory changed unexpectedly: {target_dir}")
    except ConfigError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise ConfigError(f"unable to prepare configuration path: {exc}") from exc

    payload = yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False).encode("utf-8")
    secure_dir_fd = (
        os.open in getattr(os, "supports_dir_fd", set())
        and os.link in getattr(os, "supports_dir_fd", set())
        and os.replace in getattr(os, "supports_dir_fd", set())
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
    )
    if secure_dir_fd:
        _write_config_posix(target_dir, payload, force=force)
    else:
        _write_config_fallback(target_dir, target, payload, force=force)
    return target


def load_config(path: Path) -> dict[str, Any]:
    text = _read_config_text(path)
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid configuration YAML: {exc}") from exc

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
    if any(part.lower() in _PROTECTED_OUTPUT_PARTS for part in workspace.parts):
        raise ConfigError("workspace must not be inside protected repository metadata")

    try:
        candidate = (base / workspace).resolve(strict=False)
        relative = candidate.relative_to(base)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ConfigError(f"unable to resolve workspace safely: {exc}") from exc

    if any(part.lower() in _PROTECTED_OUTPUT_PARTS for part in relative.parts):
        raise ConfigError("workspace must not be inside protected repository metadata")
    return candidate


def resolve_manifest_path(config_path: Path, config: dict[str, Any]) -> Path:
    root = resolve_workspace(config_path, config)
    relative = Path(str(config["manifest"]))
    candidate = root / relative

    try:
        if candidate.is_symlink():
            raise ConfigError(f"manifest output must not be a symlink: {candidate}")
        resolved = candidate.resolve(strict=False)
        rel = resolved.relative_to(root)
    except ConfigError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise ConfigError(f"unable to resolve manifest output safely: {exc}") from exc

    if any(part.lower() in _PROTECTED_OUTPUT_PARTS for part in rel.parts):
        raise ConfigError("manifest output must not be inside protected repository metadata")
    return resolved
