from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidencekit.canonical import manifest_digest
from evidencekit.collectors import collect_artifacts, collect_junit_checks
from evidencekit.config import load_config


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


def build_manifest(config_path: Path) -> tuple[dict[str, Any], Path]:
    config = load_config(config_path)
    config_dir = config_path.parent
    configured_workspace = Path(str(config["workspace"]))
    root = (
        configured_workspace.resolve()
        if configured_workspace.is_absolute()
        else (config_dir.parent / configured_workspace).resolve()
    )

    artifacts, warnings = collect_artifacts(
        root,
        list(config["include"]),
        list(config["exclude"]),
        int(config["max_artifact_bytes"]),
    )
    checks = collect_junit_checks(root, list(config["junit"]))

    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "run": {
            "id": str(uuid.uuid4()),
            "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_revision": _git_revision(root),
        },
        "environment": {
            "os": platform.system().lower(),
            "runtime": f"python-{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "checks": [item.to_dict() for item in checks],
        "artifacts": [item.to_dict() for item in artifacts],
        "warnings": warnings,
    }
    manifest["manifest_sha256"] = manifest_digest(manifest)

    output = Path(str(config["manifest"]))
    output_path = output if output.is_absolute() else root / output
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest, output_path
