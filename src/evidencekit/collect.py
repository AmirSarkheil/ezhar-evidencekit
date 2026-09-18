from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import uuid
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


def _atomic_write_json(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ConfigError(f"manifest parent must not be a symlink: {path.parent}")

    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".evidencekit-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except OSError as exc:
        raise ConfigError(f"unable to write manifest: {exc}") from exc
    finally:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass


def build_manifest(config_path: Path) -> tuple[dict[str, Any], Path]:
    config_path = config_path.resolve()
    config = load_config(config_path)
    root = resolve_workspace(config_path, config)
    if not root.exists() or not root.is_dir():
        raise ConfigError(f"workspace is not an existing directory: {root}")

    output_path = resolve_manifest_path(config_path, config)
    output_relative = output_path.relative_to(root).as_posix()

    artifacts, warnings = collect_artifacts(
        root,
        list(config["include"]),
        list(config["exclude"]),
        int(config["max_artifact_bytes"]),
        excluded_paths={output_relative},
    )
    checks, junit_warnings = collect_junit_checks(
        root,
        list(config["junit"]),
        int(config["max_artifact_bytes"]),
    )
    warnings.extend(junit_warnings)

    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "run": {
            "id": str(uuid.uuid4()),
            "started_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
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

    if output_path.is_symlink():
        raise ConfigError(f"manifest output must not be a symlink: {output_path}")
    _atomic_write_json(output_path, manifest)
    return manifest, output_path
