from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any, NoReturn

from jsonschema import Draft202012Validator, FormatChecker

from evidencekit.canonical import manifest_digest
from evidencekit.errors import ValidationFailure
from evidencekit.schema import EVIDENCE_MANIFEST_V1


MAX_MANIFEST_BYTES = 4_194_304
MAX_JSON_DEPTH = 64


def _reject_nonfinite(value: str) -> NoReturn:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _check_json_depth(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False

    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ValidationFailure(
                    f"manifest JSON nesting exceeds maximum depth {MAX_JSON_DEPTH}"
                )
        elif char in "]}":
            depth -= 1
            if depth < 0:
                return


def _read_manifest_text(path: Path) -> str:
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK

    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValidationFailure(f"unable to open manifest: {exc}") from exc

    try:
        with os.fdopen(descriptor, "rb") as handle:
            mode = os.fstat(handle.fileno()).st_mode
            if not stat.S_ISREG(mode):
                raise ValidationFailure("manifest must be a regular file")
            payload = handle.read(MAX_MANIFEST_BYTES + 1)
            if len(payload) > MAX_MANIFEST_BYTES:
                raise ValidationFailure(
                    f"manifest exceeds maximum size of {MAX_MANIFEST_BYTES} bytes"
                )
    except ValidationFailure:
        raise
    except OSError as exc:
        raise ValidationFailure(f"unable to read manifest: {exc}") from exc

    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise ValidationFailure(f"manifest is not valid UTF-8: {exc}") from exc

    _check_json_depth(text)
    return text


def validate_manifest_data(manifest: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(EVIDENCE_MANIFEST_V1, format_checker=FormatChecker())
    errors = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(manifest), key=lambda item: list(item.absolute_path))
    ]

    expected = manifest.get("manifest_sha256")
    if isinstance(expected, str):
        try:
            actual = manifest_digest(manifest)
        except (TypeError, ValueError, UnicodeError) as exc:
            errors.append(f"manifest_sha256: unable to canonicalize manifest: {exc}")
        else:
            if expected != actual:
                errors.append("manifest_sha256: digest mismatch")
    return errors


def load_and_validate(path: Path) -> dict[str, Any]:
    text = _read_manifest_text(path)
    try:
        manifest = json.loads(text, parse_constant=_reject_nonfinite)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValidationFailure(f"unable to parse manifest JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValidationFailure("manifest root must be a JSON object")

    errors = validate_manifest_data(manifest)
    if errors:
        raise ValidationFailure("; ".join(errors))
    return manifest
