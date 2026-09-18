from __future__ import annotations

from pathlib import Path

from evidencekit.collectors.junit import collect_junit_checks


def test_junit_derives_failure_from_testcases(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    report = artifact_dir / "pytest.xml"
    report.write_text(
        "<testsuite><testcase name='x'><failure>boom</failure></testcase></testsuite>",
        encoding="utf-8",
    )

    checks, warnings = collect_junit_checks(tmp_path, ["artifacts/pytest.xml"], 1_000_000)
    assert warnings == []
    assert checks[0].status == "failed"
    assert "tests=1" in (checks[0].summary or "")
    assert "failures=1" in (checks[0].summary or "")


def test_non_junit_xml_is_unknown(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    report.write_text("<not-junit/>", encoding="utf-8")
    checks, warnings = collect_junit_checks(tmp_path, ["report.xml"], 1_000_000)
    assert checks[0].status == "unknown"
    assert warnings


def test_malformed_xml_is_unknown(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    report.write_text("<testsuite>", encoding="utf-8")
    checks, warnings = collect_junit_checks(tmp_path, ["report.xml"], 1_000_000)
    assert checks[0].status == "unknown"
    assert warnings


def test_oversized_junit_is_not_parsed(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    report.write_text("<testsuite/>", encoding="utf-8")
    checks, warnings = collect_junit_checks(tmp_path, ["report.xml"], 1)
    assert checks[0].status == "unknown"
    assert "exceeds" in (checks[0].summary or "")
    assert warnings


def test_junit_parent_traversal_is_rejected(tmp_path: Path) -> None:
    checks, warnings = collect_junit_checks(tmp_path, ["../outside.xml"], 1_000_000)
    assert checks[0].status == "unknown"
    assert warnings
