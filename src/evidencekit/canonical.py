from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


def canonical_bytes(manifest: dict[str, Any]) -> bytes:
    """Return deterministic UTF-8 JSON bytes, excluding the self-digest field."""
    normalized = copy.deepcopy(manifest)
    normalized.pop("manifest_sha256", None)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def manifest_digest(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(manifest)).hexdigest()
