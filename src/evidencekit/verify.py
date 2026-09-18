from __future__ import annotations

from pathlib import Path
from typing import Any

from evidencekit.config import (
    HARD_MAX_ARTIFACT_BYTES,
    load_config,
    resolve_manifest_path,
    resolve_workspace,
)
from evidencekit.errors import ConfigError, SecurityError
from evidencekit.integrity import hash_artifact
from evidencekit.validate import load_and_validate


def _infer_workspace(path: Path) -> tuple[Path, int]:
    resolved_manifest = path.resolve()
    for ancestor in (resolved_manifest.parent, *resolved_manifest.parent.parents):
        candidate = ancestor / ".evidencekit" / "config.yml"
        if not candidate.exists() or candidate.is_symlink():
            continue
        try:
            config = load_config(candidate)
            if resolve_manifest_path(candidate, config) == resolved_manifest:
                return (
                    resolve_workspace(candidate, config),
                    int(config["max_artifact_bytes"]),
                )
        except ConfigError:
            continue
    return resolved_manifest.parent, HARD_MAX_ARTIFACT_BYTES


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
        config_path = config_path.absolute()
        config = load_config(config_path)
        configured_manifest = resolve_manifest_path(config_path, config)
        if configured_manifest != manifest_path:
            raise ConfigError("manifest path does not match the supplied configuration")
        root = resolve_workspace(config_path, config)
        max_bytes = int(config["max_artifact_bytes"])
    elif workspace is not None:
        root = workspace.resolve()
        max_bytes = HARD_MAX_ARTIFACT_BYTES
    else:
        root, max_bytes = _infer_workspace(manifest_path)

    problems: list[str] = []
    for artifact in manifest.get("artifacts", []):
        relative = artifact["path"]
        try:
            _path, actual_size, actual_digest = hash_artifact(
                root,
                relative,
                max_bytes=max_bytes,
            )
        except (OSError, SecurityError) as exc:
            problems.append(str(exc))
            continue

        if actual_size != artifact["size"]:
            problems.append(
                f"size mismatch: {relative} "
                f"expected={artifact['size']} actual={actual_size}"
            )
        if actual_digest != artifact["sha256"]:
            problems.append(f"sha256 mismatch: {relative}")

    return manifest, problems
