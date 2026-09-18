from __future__ import annotations

from pathlib import Path
from typing import Any

from evidencekit.config import load_config, resolve_manifest_path, resolve_workspace
from evidencekit.errors import ConfigError, SecurityError
from evidencekit.integrity import safe_artifact_path, sha256_file
from evidencekit.validate import load_and_validate


def _infer_workspace(path: Path) -> Path:
    resolved_manifest = path.resolve()
    for ancestor in (resolved_manifest.parent, *resolved_manifest.parent.parents):
        candidate = ancestor / ".evidencekit" / "config.yml"
        if not candidate.exists() or candidate.is_symlink():
            continue
        try:
            config = load_config(candidate)
            if resolve_manifest_path(candidate, config) == resolved_manifest:
                return resolve_workspace(candidate, config)
        except ConfigError:
            continue
    return resolved_manifest.parent


def verify_manifest(
    path: Path,
    workspace: Path | None = None,
    config_path: Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    manifest_path = path.resolve()
    manifest = load_and_validate(manifest_path)

    if workspace is not None and config_path is not None:
        raise ConfigError("use either workspace or config_path, not both")

    if config_path is not None:
        config = load_config(config_path)
        configured_manifest = resolve_manifest_path(config_path, config)
        if configured_manifest != manifest_path:
            raise ConfigError("manifest path does not match the supplied configuration")
        root = resolve_workspace(config_path, config)
    elif workspace is not None:
        root = workspace.resolve()
    else:
        root = _infer_workspace(manifest_path)

    problems: list[str] = []
    for artifact in manifest.get("artifacts", []):
        relative = artifact["path"]
        try:
            candidate = safe_artifact_path(root, relative, require_exists=False)
            if not candidate.exists():
                problems.append(f"missing artifact: {relative}")
                continue

            safe = safe_artifact_path(root, relative)
            if not safe.is_file():
                problems.append(f"non-regular artifact: {relative}")
                continue

            actual_size = safe.stat().st_size
            if actual_size != artifact["size"]:
                problems.append(
                    f"size mismatch: {relative} "
                    f"expected={artifact['size']} actual={actual_size}"
                )
            if sha256_file(safe) != artifact["sha256"]:
                problems.append(f"sha256 mismatch: {relative}")
        except (OSError, SecurityError) as exc:
            problems.append(str(exc))

    return manifest, problems
