from __future__ import annotations

import hashlib
import mimetypes
import os
import stat
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


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    if chunk_size <= 0:
        raise SecurityError("hash chunk size must be positive")
    if path.is_symlink():
        raise SecurityError(f"cannot hash symlink artifact: {path}")

    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

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
    rel = Path(relative_path)
    if rel.is_absolute() or ".." in rel.parts:
        raise SecurityError(f"unsafe artifact path: {relative_path}")

    root_resolved = root.resolve()
    candidate = root_resolved / rel

    if candidate.is_symlink():
        raise SecurityError(f"symlink artifacts are not allowed: {relative_path}")

    resolved = candidate.resolve(strict=False)
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
