from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from evidencekit.canonical import manifest_digest
from evidencekit.errors import ValidationFailure
from evidencekit.schema import EVIDENCE_MANIFEST_V1


def validate_manifest_data(manifest: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(EVIDENCE_MANIFEST_V1, format_checker=FormatChecker())
    errors = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(manifest), key=lambda item: list(item.absolute_path))
    ]
    expected = manifest.get("manifest_sha256")
    if isinstance(expected, str):
        actual = manifest_digest(manifest)
        if expected != actual:
            errors.append("manifest_sha256: digest mismatch")
    return errors


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"unable to read manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValidationFailure("manifest root must be a JSON object")
    errors = validate_manifest_data(manifest)
    if errors:
        raise ValidationFailure("; ".join(errors))
    return manifest
