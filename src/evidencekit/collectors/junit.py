from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from pathlib import Path

from defusedxml import ElementTree as DefusedET  # type: ignore[import-untyped]
from defusedxml.common import DefusedXmlException  # type: ignore[import-untyped]

from evidencekit.errors import SecurityError
from evidencekit.integrity import read_artifact_bytes
from evidencekit.models import CheckRecord


MAX_JUNIT_BYTES = 16_777_216
MAX_JUNIT_ELEMENTS = 200_000
MAX_JUNIT_DEPTH = 128


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _int_value(value: str | None) -> int:
    try:
        return max(0, int(value or "0"))
    except (TypeError, ValueError):
        return 0


def _parse_junit_summary(payload: bytes) -> tuple[int, int, int, int] | None:
    root_kind: str | None = None
    root_attributes: dict[str, str] = {}
    depth = 0
    element_count = 0
    suite_stack: list[bool] = []
    leaf_suite_count = 0
    suite_totals = [0, 0, 0, 0]
    testcase_totals = [0, 0, 0, 0]

    for event, element in DefusedET.iterparse(
        io.BytesIO(payload),
        events=("start", "end"),
    ):
        kind = _local_name(element.tag)

        if event == "start":
            depth += 1
            element_count += 1
            if element_count > MAX_JUNIT_ELEMENTS:
                raise ValueError(
                    f"JUnit XML exceeds element limit {MAX_JUNIT_ELEMENTS}"
                )
            if depth > MAX_JUNIT_DEPTH:
                raise ValueError(f"JUnit XML exceeds depth limit {MAX_JUNIT_DEPTH}")

            if root_kind is None:
                root_kind = kind
                root_attributes = dict(element.attrib)

            if kind == "testsuite":
                if suite_stack:
                    suite_stack[-1] = True
                suite_stack.append(False)
            continue

        if kind == "testcase":
            child_kinds = {_local_name(child.tag) for child in element}
            testcase_totals[0] += 1
            testcase_totals[1] += int("failure" in child_kinds)
            testcase_totals[2] += int("error" in child_kinds)
            testcase_totals[3] += int("skipped" in child_kinds)

        elif kind == "testsuite":
            has_child_suite = suite_stack.pop() if suite_stack else False
            if not has_child_suite:
                leaf_suite_count += 1
                suite_totals[0] += _int_value(element.attrib.get("tests"))
                suite_totals[1] += _int_value(element.attrib.get("failures"))
                suite_totals[2] += _int_value(element.attrib.get("errors"))
                suite_totals[3] += _int_value(element.attrib.get("skipped"))

        element.clear()
        depth -= 1

    if root_kind not in {"testsuite", "testsuites"}:
        return None
    if testcase_totals[0]:
        return tuple(testcase_totals)  # type: ignore[return-value]
    if leaf_suite_count:
        return tuple(suite_totals)  # type: ignore[return-value]
    return (
        _int_value(root_attributes.get("tests")),
        _int_value(root_attributes.get("failures")),
        _int_value(root_attributes.get("errors")),
        _int_value(root_attributes.get("skipped")),
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
    artifact_digests: dict[str, str],
) -> tuple[list[CheckRecord], list[str]]:
    checks: list[CheckRecord] = []
    warnings: list[str] = []
    parser_limit = min(max_artifact_bytes, MAX_JUNIT_BYTES)

    for relative in paths:
        expected_digest = artifact_digests.get(relative)
        if expected_digest is None:
            message = "JUnit evidence is not present in the artifact manifest"
            checks.append(_unknown(relative, message))
            warnings.append(f"{message}: {relative}")
            continue

        try:
            _path, payload, observed_digest = read_artifact_bytes(
                root,
                relative,
                max_bytes=parser_limit,
            )
        except (OSError, SecurityError) as exc:
            checks.append(_unknown(relative, str(exc)))
            warnings.append(str(exc))
            continue

        if observed_digest != expected_digest:
            message = "JUnit artifact changed after evidence hashing"
            checks.append(_unknown(relative, message))
            warnings.append(f"{message}: {relative}")
            continue

        try:
            totals = _parse_junit_summary(payload)
        except (ET.ParseError, DefusedXmlException, ValueError) as exc:
            message = f"unable to parse JUnit XML: {exc}"
            checks.append(_unknown(relative, message))
            warnings.append(f"{message}: {relative}")
            continue

        if totals is None:
            message = "unrecognized JUnit root element"
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
