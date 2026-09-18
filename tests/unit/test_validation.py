from __future__ import annotations

from evidencekit.canonical import manifest_digest
from evidencekit.validate import validate_manifest_data


def _manifest() -> dict:
    data = {
        "schema_version": "1.0",
        "run": {"id": "run-1", "started_at": "2026-09-18T00:00:00Z", "source_revision": None},
        "environment": {"os": "linux", "runtime": "python-3.12"},
        "checks": [],
        "artifacts": [],
        "warnings": [],
    }
    data["manifest_sha256"] = manifest_digest(data)
    return data


def test_valid_manifest() -> None:
    assert validate_manifest_data(_manifest()) == []


def test_invalid_status_is_rejected() -> None:
    manifest = _manifest()
    manifest["checks"] = [{"name": "pytest", "status": "maybe"}]
    manifest["manifest_sha256"] = manifest_digest(manifest)
    errors = validate_manifest_data(manifest)
    assert any("status" in error for error in errors)
