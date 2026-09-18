from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evidencekit.canonical import manifest_digest
from evidencekit.collectors import collect_artifacts, collect_junit_checks
from evidencekit.config import load_config, resolve_manifest_path, resolve_workspace
from evidencekit.errors import ConfigError


def _git_revision(root: Path) -> str | None:
    from_env = os.environ.get("GITHUB_SHA") or os.environ.get("CI_COMMIT_SHA")
    if from_env:
        return from_env
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    revision = result.stdout.strip()
    return revision or None


def _manifest_payload(manifest: dict[str, Any]) -> bytes:
    try:
        return (
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ConfigError(f"unable to serialize manifest: {exc}") from exc


def _write_manifest_posix(root: Path, relative: Path, payload: bytes) -> None:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC

    file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        file_flags |= os.O_CLOEXEC

    directory_fds: list[int] = []
    temp_name = f".evidencekit-{uuid.uuid4().hex}.tmp"
    temp_created = False
    try:
        current_fd = os.open(root, directory_flags)
        directory_fds.append(current_fd)

        for part in relative.parts[:-1]:
            try:
                next_fd = os.open(part, directory_flags, dir_fd=current_fd)
            except FileNotFoundError:
                with suppress(FileExistsError):
                    os.mkdir(part, 0o755, dir_fd=current_fd)
                next_fd = os.open(part, directory_flags, dir_fd=current_fd)
            current_fd = next_fd
            directory_fds.append(current_fd)

        descriptor = os.open(temp_name, file_flags, 0o644, dir_fd=current_fd)
        temp_created = True
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise ConfigError(f"unable to write temporary manifest: {exc}") from exc

        try:
            os.rename(
                temp_name,
                relative.parts[-1],
                src_dir_fd=current_fd,
                dst_dir_fd=current_fd,
            )
        except OSError as exc:
            raise ConfigError(f"unable to replace manifest atomically: {exc}") from exc
        temp_created = False
        with suppress(OSError):
            os.fsync(current_fd)
    except ConfigError:
        raise
    except OSError as exc:
        raise ConfigError(f"unable to write manifest safely: {exc}") from exc
    finally:
        if directory_fds:
            current_fd = directory_fds[-1]
            if temp_created:
                with suppress(OSError):
                    os.unlink(temp_name, dir_fd=current_fd)
        for directory_fd in reversed(directory_fds):
            with suppress(OSError):
                os.close(directory_fd)


def _write_manifest_fallback(path: Path, payload: bytes) -> None:
    temp_name: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.is_symlink() or path.is_symlink():
            raise ConfigError(f"manifest output path must not contain a symlink: {path}")

        before = path.parent.stat(follow_symlinks=False)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=".evidencekit-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        after = path.parent.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ConfigError("manifest directory changed during write")
        if path.parent.is_symlink() or path.is_symlink():
            raise ConfigError(f"manifest output path became a symlink: {path}")

        os.replace(temp_name, path)
        temp_name = None
    except ConfigError:
        raise
    except OSError as exc:
        raise ConfigError(f"unable to write manifest: {exc}") from exc
    finally:
        if temp_name is not None:
            with suppress(OSError):
                Path(temp_name).unlink(missing_ok=True)


def _atomic_write_json(root: Path, relative: Path, manifest: dict[str, Any]) -> None:
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise ConfigError("manifest output must be a safe relative path")

    payload = _manifest_payload(manifest)
    secure_dir_fd = (
        os.open in getattr(os, "supports_dir_fd", set())
        and os.mkdir in getattr(os, "supports_dir_fd", set())
        and os.rename in getattr(os, "supports_dir_fd", set())
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
    )
    if secure_dir_fd:
        _write_manifest_posix(root, relative, payload)
    else:
        _write_manifest_fallback(root / relative, payload)


def build_manifest(config_path: Path) -> tuple[dict[str, Any], Path]:
    started_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    config_path = config_path.absolute()
    config = load_config(config_path)
    root = resolve_workspace(config_path, config)
    if not root.exists() or not root.is_dir():
        raise ConfigError(f"workspace is not an existing directory: {root}")

    output_path = resolve_manifest_path(config_path, config)
    output_relative = output_path.relative_to(root)

    artifacts, warnings = collect_artifacts(
        root,
        list(config["include"]),
        list(config["exclude"]),
        int(config["max_artifact_bytes"]),
        excluded_paths={output_relative.as_posix()},
    )
    artifact_digests = {item.path: item.sha256 for item in artifacts}
    junit_paths = [Path(item).as_posix() for item in config["junit"]]
    checks, junit_warnings = collect_junit_checks(
        root,
        junit_paths,
        int(config["max_artifact_bytes"]),
        artifact_digests,
    )
    warnings.extend(junit_warnings)

    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "run": {
            "id": str(uuid.uuid4()),
            "started_at": started_at,
            "source_revision": _git_revision(root),
        },
        "environment": {
            "os": platform.system().lower(),
            "runtime": (
                f"python-{sys.version_info.major}."
                f"{sys.version_info.minor}.{sys.version_info.micro}"
            ),
        },
        "checks": [item.to_dict() for item in checks],
        "artifacts": [item.to_dict() for item in artifacts],
        "warnings": warnings,
    }
    manifest["manifest_sha256"] = manifest_digest(manifest)

    _atomic_write_json(root, output_relative, manifest)
    return manifest, output_path
