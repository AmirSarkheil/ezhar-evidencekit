from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from defusedxml import ElementTree as DefusedET  # type: ignore[import-untyped]
from defusedxml.common import DefusedXmlException  # type: ignore[import-untyped]

from evidencekit.errors import SecurityError
from evidencekit.integrity import safe_artifact_path
from evidencekit.models import CheckRecord


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _int_attr(node: ET.Element, name: str) -> int:
    try:
        return max(0, int(node.attrib.get(name, "0")))
    except (TypeError, ValueError):
        return 0


def _derive_totals(root_node: ET.Element) -> tuple[int, int, int, int] | None:
    root_kind = _local_name(root_node.tag)
    if root_kind not in {"testsuite", "testsuites"}:
        return None

    testcases = [
        element for element in root_node.iter() if _local_name(element.tag) == "testcase"
    ]
    if testcases:
        failures = 0
        errors = 0
        skipped = 0
        for testcase in testcases:
            child_kinds = {_local_name(child.tag) for child in testcase}
            failures += int("failure" in child_kinds)
            errors += int("error" in child_kinds)
            skipped += int("skipped" in child_kinds)
        return len(testcases), failures, errors, skipped

    if "tests" in root_node.attrib:
        return (
            _int_attr(root_node, "tests"),
            _int_attr(root_node, "failures"),
            _int_attr(root_node, "errors"),
            _int_attr(root_node, "skipped"),
        )

    suites = [
        element for element in root_node.iter() if _local_name(element.tag) == "testsuite"
    ]
    if not suites:
        return (0, 0, 0, 0)

    leaf_suites = [
        suite
        for suite in suites
        if not any(_local_name(child.tag) == "testsuite" for child in suite)
    ]
    source = leaf_suites or suites
    return (
        sum(_int_attr(suite, "tests") for suite in source),
        sum(_int_attr(suite, "failures") for suite in source),
        sum(_int_attr(suite, "errors") for suite in source),
        sum(_int_attr(suite, "skipped") for suite in source),
    )


def _unknown(relative: str, summary: str) -> CheckRecord:
    return CheckRecord(
        name=f"junit:{relative}",
        status="unknown",
        evidence_ref=relative,
        summary=summary,
    )


def collect_junit_checks(
    root: Path,
    paths: list[str],
    max_artifact_bytes: int,
) -> tuple[list[CheckRecord], list[str]]:
    checks: list[CheckRecord] = []
    warnings: list[str] = []

    for relative in paths:
        try:
            candidate = safe_artifact_path(root, relative, require_exists=False)
            if not candidate.exists():
                checks.append(_unknown(relative, "JUnit file not found"))
                continue
            path = safe_artifact_path(root, relative)
            if not path.is_file():
                message = "JUnit path is not a regular file"
                checks.append(_unknown(relative, message))
                warnings.append(f"{message}: {relative}")
                continue
            size = path.stat().st_size
            if size > max_artifact_bytes:
                message = (
                    f"JUnit file exceeds max_artifact_bytes "
                    f"({size} > {max_artifact_bytes} bytes)"
                )
                checks.append(_unknown(relative, message))
                warnings.append(f"{message}: {relative}")
                continue
        except (OSError, SecurityError) as exc:
            checks.append(_unknown(relative, str(exc)))
            warnings.append(str(exc))
            continue

        try:
            tree = DefusedET.parse(path)
            root_node = tree.getroot()
        except (OSError, ET.ParseError, DefusedXmlException) as exc:
            message = f"unable to parse JUnit XML: {exc}"
            checks.append(_unknown(relative, message))
            warnings.append(f"{message}: {relative}")
            continue

        totals = _derive_totals(root_node)
        if totals is None:
            message = f"unrecognized JUnit root element: {_local_name(root_node.tag)}"
            checks.append(_unknown(relative, message))
            warnings.append(f"{message}: {relative}")
            continue

        tests, failures, errors, skipped = totals
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

    return checks, warnings
