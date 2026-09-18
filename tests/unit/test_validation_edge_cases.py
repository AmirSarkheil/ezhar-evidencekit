from __future__ import annotations

from evidencekit.canonical import manifest_digest
from evidencekit.validate import validate_manifest_data


def _base_manifest() -> dict:
    manifest = {
        "schema_version": "1.0",
        "run": {
            "id": "run",
            "started_at": "2026-09-18T00:00:00Z",
            "source_revision": None,
        },
        "environment": {"os": "linux", "runtime": "python-3.12"},
        "checks": [],
        "artifacts": [],
    }
    manifest["manifest_sha256"] = manifest_digest(manifest)
    return manifest


def test_unpaired_surrogate_can_be_canonicalized() -> None:
    manifest = _base_manifest()
    manifest["run"]["id"] = "\ud800"
    manifest["manifest_sha256"] = manifest_digest(manifest)
    assert validate_manifest_data(manifest) == []


def test_non_finite_number_is_validation_error_not_exception() -> None:
    manifest = _base_manifest()
    manifest["extra"] = float("nan")
    errors = validate_manifest_data(manifest)
    assert any("canonicalize" in error for error in errors)
