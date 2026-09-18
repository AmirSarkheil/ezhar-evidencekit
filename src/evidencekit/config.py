from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from evidencekit.errors import ConfigError


DEFAULT_CONFIG = {
    "schema_version": "1.0",
    "workspace": ".",
    "manifest": "evidence.json",
    "include": ["artifacts/**/*"],
    "exclude": ["**/.git/**", "**/.evidencekit/**", "**/__pycache__/**"],
    "max_artifact_bytes": 10_485_760,
    "junit": [],
}


def write_default_config(repo_root: Path, *, force: bool = False) -> Path:
    target_dir = repo_root / ".evidencekit"
    target = target_dir / "config.yml"
    if target.exists() and not force:
        raise ConfigError(f"configuration already exists: {target}")
    target_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False), encoding="utf-8")
    return target


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"configuration not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a mapping")

    merged = dict(DEFAULT_CONFIG)
    merged.update(raw)

    if merged["schema_version"] != "1.0":
        raise ConfigError("v0.1 only supports schema_version: 1.0")
    if not isinstance(merged["include"], list) or not all(
        isinstance(item, str) for item in merged["include"]
    ):
        raise ConfigError("include must be a list of glob strings")
    if not isinstance(merged["exclude"], list) or not all(
        isinstance(item, str) for item in merged["exclude"]
    ):
        raise ConfigError("exclude must be a list of glob strings")
    if not isinstance(merged["junit"], list) or not all(
        isinstance(item, str) for item in merged["junit"]
    ):
        raise ConfigError("junit must be a list of relative paths")
    if not isinstance(merged["max_artifact_bytes"], int) or merged["max_artifact_bytes"] <= 0:
        raise ConfigError("max_artifact_bytes must be a positive integer")
    return merged
