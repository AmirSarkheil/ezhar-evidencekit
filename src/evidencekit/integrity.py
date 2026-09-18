from __future__ import annotations

import hashlib
import mimetypes
import os
import stat
from contextlib import suppress
from pathlib import Path

from evidencekit.errors import SecurityError


SENSITIVE_BASENAMES = {
    ".env",
    ".env.local",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}

_CONTROL_MAX = 31
_READ_CHUNK = 1024 * 1024


def _validate_relative_artifact_path(relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise SecurityError("artifact path must be a non-empty string")
    if any(ord(char) <= _CONTROL_MAX or ord(char) == 127 for char in relative_path):
        raise SecurityError("artifact path contains control characters")

    try:
        rel = Path(relative_path)
    except (TypeError, ValueError) as exc:
        raise SecurityError("invalid artifact path") from exc

    if not rel.parts or rel.is_absolute() or ".." in rel.parts:
        raise SecurityError(f"unsafe artifact path: {relative_path}")
    return rel


def _base_open_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _open_regular_artifact(root: Path, relative_path: str) -> tuple[int, Path]:
    rel = _validate_relative_artifact_path(relative_path)
    root_resolved = root.resolve()

    if not root_resolved.exists() or not root_resolved.is_dir():
        raise SecurityError(f"workspace is not an existing directory: {root_resolved}")

    supports_dir_fd = os.open in getattr(os, "supports_dir_fd", set())
    supports_nofollow = hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")

    if supports_dir_fd and supports_nofollow:
        directory_flags = _base_open_flags() | os.O_DIRECTORY | os.O_NOFOLLOW
        file_flags = _base_open_flags() | os.O_NOFOLLOW
        if hasattr(os, "O_NONBLOCK"):
            file_flags |= os.O_NONBLOCK

        directory_fds: list[int] = []
        try:
            current_fd = os.open(root_resolved, directory_flags)
            directory_fds.append(current_fd)
            for part in rel.parts[:-1]:
                current_fd = os.open(part, directory_flags, dir_fd=current_fd)
                directory_fds.append(current_fd)

            descriptor = os.open(rel.parts[-1], file_flags, dir_fd=current_fd)
        except FileNotFoundError as exc:
            raise SecurityError(f"artifact does not exist: {relative_path}") from exc
        except OSError as exc:
            raise SecurityError(f"unable to open artifact safely: {relative_path}") from exc
        finally:
            for directory_fd in reversed(directory_fds):
                with suppress(OSError):
                    os.close(directory_fd)
    else:
        candidate = safe_artifact_path(root_resolved, relative_path)
        flags = _base_open_flags()
        if hasattr(os, "O_NONBLOCK"):
            flags |= os.O_NONBLOCK
        try:
            descriptor = os.open(candidate, flags)
        except FileNotFoundError as exc:
            raise SecurityError(f"artifact does not exist: {relative_path}") from exc
        except OSError as exc:
            raise SecurityError(f"unable to open artifact: {relative_path}") from exc

    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise SecurityError(f"cannot read non-regular artifact: {relative_path}")
    except Exception:
        os.close(descriptor)
        raise

    return descriptor, root_resolved / rel


def _read_bounded(
    descriptor: int,
    relative_path: str,
    *,
    max_bytes: int | None,
    collect_bytes: bool,
) -> tuple[int, str, bytes | None]:
    digest = hashlib.sha256()
    total = 0
    payload = bytearray() if collect_bytes else None

    try:
        with os.fdopen(descriptor, "rb") as handle:
            while True:
                remaining = None if max_bytes is None else max_bytes - total
                if remaining is not None and remaining < 0:
                    raise SecurityError(
                        f"artifact exceeds maximum size of {max_bytes} bytes: {relative_path}"
                    )
                request = _READ_CHUNK if remaining is None else min(_READ_CHUNK, remaining + 1)
                chunk = handle.read(request)
                if not chunk:
                    break
                total += len(chunk)
                if max_bytes is not None and total > max_bytes:
                    raise SecurityError(
                        f"artifact exceeds maximum size of {max_bytes} bytes: {relative_path}"
                    )
                digest.update(chunk)
                if payload is not None:
                    payload.extend(chunk)
    except SecurityError:
        raise
    except OSError as exc:
        raise SecurityError(f"unable to read artifact: {relative_path}") from exc

    return total, digest.hexdigest(), bytes(payload) if payload is not None else None


def hash_artifact(
    root: Path,
    relative_path: str,
    *,
    max_bytes: int | None,
) -> tuple[Path, int, str]:
    descriptor, display_path = _open_regular_artifact(root, relative_path)
    size, digest, _payload = _read_bounded(
        descriptor,
        relative_path,
        max_bytes=max_bytes,
        collect_bytes=False,
    )
    return display_path, size, digest


def read_artifact_bytes(
    root: Path,
    relative_path: str,
    *,
    max_bytes: int,
) -> tuple[Path, bytes, str]:
    descriptor, display_path = _open_regular_artifact(root, relative_path)
    _size, digest, payload = _read_bounded(
        descriptor,
        relative_path,
        max_bytes=max_bytes,
        collect_bytes=True,
    )
    assert payload is not None
    return display_path, payload, digest


def sha256_file(path: Path, chunk_size: int = _READ_CHUNK) -> str:
    if chunk_size <= 0:
        raise SecurityError("hash chunk size must be positive")
    if path.is_symlink():
        raise SecurityError(f"cannot hash symlink artifact: {path}")

    flags = _base_open_flags()
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK

    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SecurityError(f"unable to open artifact: {path}") from exc

    digest = hashlib.sha256()
    try:
        with os.fdopen(descriptor, "rb") as handle:
            mode = os.fstat(handle.fileno()).st_mode
            if not stat.S_ISREG(mode):
                raise SecurityError(f"cannot hash non-regular artifact: {path}")
            while chunk := handle.read(chunk_size):
                digest.update(chunk)
    except SecurityError:
        raise
    except OSError as exc:
        raise SecurityError(f"unable to read artifact: {path}") from exc
    return digest.hexdigest()


def safe_artifact_path(root: Path, relative_path: str, *, require_exists: bool = True) -> Path:
    rel = _validate_relative_artifact_path(relative_path)
    root_resolved = root.resolve()
    candidate = root_resolved / rel

    try:
        if candidate.is_symlink():
            raise SecurityError(f"symlink artifacts are not allowed: {relative_path}")
        resolved = candidate.resolve(strict=False)
    except (OSError, ValueError) as exc:
        raise SecurityError(f"unable to resolve artifact path: {relative_path}") from exc

    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SecurityError(f"artifact escapes workspace: {relative_path}") from exc

    if require_exists and not resolved.exists():
        raise SecurityError(f"artifact does not exist: {relative_path}")
    return resolved


def media_type_for(path: Path) -> str | None:
    guessed, _encoding = mimetypes.guess_type(path.name)
    return guessed


def looks_sensitive(path: Path) -> bool:
    name = path.name.lower()
    if name in SENSITIVE_BASENAMES:
        return True
    sensitive_tokens = ("secret", "credential", "private_key", "apikey", "api_key", "token")
    return any(token in name for token in sensitive_tokens)
