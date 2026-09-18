from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from evidencekit.models import CheckRecord


def collect_junit_checks(root: Path, paths: list[str]) -> list[CheckRecord]:
    checks: list[CheckRecord] = []
    for relative in paths:
        path = root / relative
        if not path.exists():
            checks.append(
                CheckRecord(
                    name=f"junit:{relative}",
                    status="unknown",
                    evidence_ref=relative,
                    summary="JUnit file not found",
                )
            )
            continue

        tree = ET.parse(path)
        root_node = tree.getroot()
        suites = [root_node] if root_node.tag == "testsuite" else list(root_node.findall("testsuite"))
        tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
        failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
        errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
        skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)

        if failures or errors:
            status = "failed"
        elif tests and skipped == tests:
            status = "skipped"
        else:
            status = "passed"

        checks.append(
            CheckRecord(
                name=f"junit:{relative}",
                status=status,
                evidence_ref=relative,
                summary=f"tests={tests}, failures={failures}, errors={errors}, skipped={skipped}",
            )
        )
    return checks
