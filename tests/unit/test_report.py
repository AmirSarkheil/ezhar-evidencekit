from __future__ import annotations

from evidencekit.report import render_markdown


def test_markdown_report_escapes_manifest_values() -> None:
    manifest = {
        "schema_version": "1.0",
        "run": {
            "id": "<script>|[x](https://example.invalid)",
            "started_at": "2026-09-18T00:00:00Z",
            "source_revision": None,
        },
        "environment": {"os": "linux", "runtime": "python-3.12"},
        "checks": [
            {
                "name": "check|name",
                "status": "passed",
                "evidence_ref": "[click](javascript:alert(1))",
            }
        ],
        "artifacts": [],
        "warnings": ["<b>warning</b>"],
        "manifest_sha256": "0" * 64,
    }

    rendered = render_markdown(manifest)
    assert "<script>" not in rendered
    assert "<b>" not in rendered
    assert "check\\|name" in rendered
    assert "\\[click\\]\\(javascript:alert\\(1\\)\\)" in rendered


def test_markdown_report_replaces_unpaired_surrogates() -> None:
    manifest = {
        "schema_version": "1.0",
        "run": {
            "id": "\ud800",
            "started_at": "2026-09-18T00:00:00Z",
            "source_revision": None,
        },
        "environment": {"os": "linux", "runtime": "python-3.12"},
        "checks": [],
        "artifacts": [],
        "warnings": [],
        "manifest_sha256": "0" * 64,
    }

    rendered = render_markdown(manifest)
    rendered.encode("utf-8")
    assert "ud800" in rendered
