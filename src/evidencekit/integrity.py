from __future__ import annotations

import hashlib
import mimetypes
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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def safe_artifact_path(root: Path, relative_path: str, *, require_exists: bool = True) -> Path:
    rel = Path(relative_path)
    if rel.is_absolute() or ".." in rel.parts:
        raise SecurityError(f"unsafe artifact path: {relative_path}")

    root_resolved = root.resolve()
    candidate = root / rel

    if require_exists and not candidate.exists():
        return candidate

    if candidate.is_symlink():
        raise SecurityError(f"symlink artifacts are not allowed: {relative_path}")

    resolved = candidate.resolve(strict=require_exists)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SecurityError(f"artifact escapes workspace: {relative_path}") from exc
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
