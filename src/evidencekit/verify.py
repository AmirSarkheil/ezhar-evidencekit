from __future__ import annotations

from pathlib import Path
from typing import Any

from evidencekit.integrity import safe_artifact_path, sha256_file
from evidencekit.validate import load_and_validate


def verify_manifest(path: Path, workspace: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    manifest = load_and_validate(path)
    root = workspace.resolve() if workspace is not None else path.parent.resolve()
    problems: list[str] = []

    for artifact in manifest.get("artifacts", []):
        relative = artifact["path"]
        candidate = safe_artifact_path(root, relative, require_exists=False)
        if not candidate.exists():
            problems.append(f"missing artifact: {relative}")
            continue
        try:
            safe = safe_artifact_path(root, relative)
        except Exception as exc:
            problems.append(str(exc))
            continue
        actual_size = safe.stat().st_size
        if actual_size != artifact["size"]:
            problems.append(
                f"size mismatch: {relative} expected={artifact['size']} actual={actual_size}"
            )
        if sha256_file(safe) != artifact["sha256"]:
            problems.append(f"sha256 mismatch: {relative}")
    return manifest, problems
