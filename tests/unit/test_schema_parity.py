from __future__ import annotations

import json
from pathlib import Path

from evidencekit.schema import EVIDENCE_MANIFEST_V1


def test_checked_in_schema_matches_runtime_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    checked_in = json.loads(
        (root / "schemas" / "evidence-manifest-v1.schema.json").read_text(encoding="utf-8")
    )
    assert checked_in == EVIDENCE_MANIFEST_V1
