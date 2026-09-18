from __future__ import annotations

from typing import Any, Final

EVIDENCE_MANIFEST_V1: Final[dict[str, Any]] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://ezhardynamics.com/schemas/evidence-manifest-v1.schema.json",
    "title": "EZHAR EvidenceKit Evidence Manifest v1",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "schema_version",
        "run",
        "environment",
        "checks",
        "artifacts",
        "manifest_sha256",
    ],
    "properties": {
        "schema_version": {"const": "1.0"},
        "run": {
            "type": "object",
            "additionalProperties": True,
            "required": ["id", "started_at"],
            "properties": {
                "id": {"type": "string", "minLength": 1},
                "started_at": {"type": "string", "format": "date-time"},
                "source_revision": {"type": ["string", "null"]},
            },
        },
        "environment": {
            "type": "object",
            "additionalProperties": True,
            "required": ["os", "runtime"],
            "properties": {
                "os": {"type": "string", "minLength": 1},
                "runtime": {"type": "string", "minLength": 1},
            },
        },
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["name", "status"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "status": {
                        "type": "string",
                        "enum": ["passed", "failed", "skipped", "unknown"],
                    },
                    "evidence_ref": {"type": "string"},
                    "summary": {"type": "string"},
                },
            },
        },
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["path", "sha256", "size"],
                "properties": {
                    "path": {"type": "string", "minLength": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "size": {"type": "integer", "minimum": 0},
                    "media_type": {"type": "string"},
                },
            },
        },
        "provenance": {"type": "object"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "manifest_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    },
}
