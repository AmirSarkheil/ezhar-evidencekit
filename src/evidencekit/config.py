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

_PROTECTED_OUTPUT_PARTS = {".git"}
_CONTROL_CHARS = {"\x00", "\r", "\n"}


def _config_base_dir(config_path: Path) -> Path:
    parent = config_path.parent.resolve()
    return parent.parent if parent.name == ".evidencekit" else parent


def _validate_relative_path(value: Any, field: str, *, json_file: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field} must be a non-empty relative path")
    if any(char in value for char in _CONTROL_CHARS):
        raise ConfigError(f"{field} contains unsupported control characters")

    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ConfigError(f"{field} must be relative and must not contain '..'")
    if json_file and path.suffix.lower() != ".json":
        raise ConfigError(f"{field} must point to a .json file")
    if json_file and any(part.lower() in _PROTECTED_OUTPUT_PARTS for part in path.parts):
        raise ConfigError(f"{field} must not write inside protected repository metadata")
    return value


def _validate_glob_patterns(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{field} must be a list of glob strings")

    result: list[str] = []
    for pattern in value:
        if not pattern.strip():
            raise ConfigError(f"{field} contains an empty glob")
        path = Path(pattern)
        if path.is_absolute() or ".." in path.parts:
            raise ConfigError(f"{field} globs must be relative and must not contain '..'")
        if any("**" in part and part != "**" for part in path.parts):
            raise ConfigError(f"invalid {field} glob: {pattern!r}")
        result.append(pattern)
    return result


def write_default_config(repo_root: Path, *, force: bool = False) -> Path:
    repo_root = repo_root.resolve()
    target_dir = repo_root / ".evidencekit"
    target = target_dir / "config.yml"

    if target_dir.is_symlink() or target.is_symlink():
        raise ConfigError(f"configuration path must not be a symlink: {target}")

    resolved_target = target.resolve(strict=False)
    try:
        resolved_target.relative_to(repo_root)
    except ValueError as exc:
        raise ConfigError(f"configuration path must remain inside repository: {target}") from exc

    if target.exists() and not force:
        raise ConfigError(f"configuration already exists: {target}")

    target_dir.mkdir(parents=True, exist_ok=True)
    if target_dir.resolve() != target_dir:
        raise ConfigError(f"configuration directory changed unexpectedly: {target_dir}")

    try:
        target.write_text(yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False), encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"unable to write configuration: {exc}") from exc
    return target


def load_config(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ConfigError(f"configuration must not be a symlink: {path}")
    if not path.exists():
        raise ConfigError(f"configuration not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"invalid configuration: {exc}") from exc

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a mapping")

    merged = dict(DEFAULT_CONFIG)
    merged.update(raw)

    if merged["schema_version"] != "1.0":
        raise ConfigError("v0.1 only supports schema_version: 1.0")

    _validate_relative_path(merged["workspace"], "workspace")
    _validate_relative_path(merged["manifest"], "manifest", json_file=True)
    merged["include"] = _validate_glob_patterns(merged["include"], "include")
    merged["exclude"] = _validate_glob_patterns(merged["exclude"], "exclude")

    if not isinstance(merged["junit"], list) or not all(
        isinstance(item, str) for item in merged["junit"]
    ):
        raise ConfigError("junit must be a list of relative paths")
    for junit_path in merged["junit"]:
        _validate_relative_path(junit_path, "junit entry")

    if type(merged["max_artifact_bytes"]) is not int or merged["max_artifact_bytes"] <= 0:
        raise ConfigError("max_artifact_bytes must be a positive integer")

    return merged


def resolve_workspace(config_path: Path, config: dict[str, Any]) -> Path:
    base = _config_base_dir(config_path)
    workspace = Path(str(config["workspace"]))
    candidate = (base / workspace).resolve(strict=False)
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ConfigError("workspace must remain inside the configuration repository") from exc
    return candidate


def resolve_manifest_path(config_path: Path, config: dict[str, Any]) -> Path:
    root = resolve_workspace(config_path, config)
    relative = Path(str(config["manifest"]))
    candidate = root / relative

    if candidate.is_symlink():
        raise ConfigError(f"manifest output must not be a symlink: {candidate}")

    resolved = candidate.resolve(strict=False)
    try:
        rel = resolved.relative_to(root)
    except ValueError as exc:
        raise ConfigError("manifest output must remain inside the workspace") from exc

    if any(part.lower() in _PROTECTED_OUTPUT_PARTS for part in rel.parts):
        raise ConfigError("manifest output must not be inside protected repository metadata")
    return resolved
