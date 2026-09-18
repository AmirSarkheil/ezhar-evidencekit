from __future__ import annotations

import json

from evidencekit.models import CheckRecord
from evidencekit.report import render_json


def test_check_record_omits_none_fields() -> None:
    record = CheckRecord(name="pytest", status="passed")
    assert record.to_dict() == {"name": "pytest", "status": "passed"}


def test_render_json_is_machine_readable() -> None:
    manifest = {
        "schema_version": "1.0",
        "run": {"id": "run", "started_at": "2026-09-18T00:00:00Z"},
        "environment": {"os": "linux", "runtime": "python-3.12"},
        "checks": [],
        "artifacts": [],
        "manifest_sha256": "0" * 64,
    }
    rendered = render_json(manifest)
    assert rendered.endswith("\n")
    assert json.loads(rendered)["schema_version"] == "1.0"
