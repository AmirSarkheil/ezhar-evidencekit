from __future__ import annotations

from pathlib import Path

from evidencekit.collectors.junit import collect_junit_checks
from evidencekit.integrity import sha256_file


def _digest_map(path: Path, relative: str) -> dict[str, str]:
    return {relative: sha256_file(path)}


def test_junit_derives_failure_from_testcases(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    report = artifact_dir / "pytest.xml"
    relative = "artifacts/pytest.xml"
    report.write_text(
        "<testsuite><testcase name='x'><failure>boom</failure></testcase></testsuite>",
        encoding="utf-8",
    )

    checks, warnings = collect_junit_checks(
        tmp_path,
        [relative],
        1_000_000,
        _digest_map(report, relative),
    )
    assert warnings == []
    assert checks[0].status == "failed"
    assert "tests=1" in (checks[0].summary or "")
    assert "failures=1" in (checks[0].summary or "")


def test_non_junit_xml_is_unknown(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    relative = "report.xml"
    report.write_text("<not-junit/>", encoding="utf-8")
    checks, warnings = collect_junit_checks(
        tmp_path,
        [relative],
        1_000_000,
        _digest_map(report, relative),
    )
    assert checks[0].status == "unknown"
    assert warnings


def test_malformed_xml_is_unknown(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    relative = "report.xml"
    report.write_text("<testsuite>", encoding="utf-8")
    checks, warnings = collect_junit_checks(
        tmp_path,
        [relative],
        1_000_000,
        _digest_map(report, relative),
    )
    assert checks[0].status == "unknown"
    assert warnings


def test_oversized_junit_is_not_parsed(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    relative = "report.xml"
    report.write_text("<testsuite/>", encoding="utf-8")
    checks, warnings = collect_junit_checks(
        tmp_path,
        [relative],
        1,
        _digest_map(report, relative),
    )
    assert checks[0].status == "unknown"
    assert "maximum size" in (checks[0].summary or "")
    assert warnings


def test_junit_parent_traversal_is_rejected(tmp_path: Path) -> None:
    relative = "../outside.xml"
    checks, warnings = collect_junit_checks(
        tmp_path,
        [relative],
        1_000_000,
        {relative: "0" * 64},
    )
    assert checks[0].status == "unknown"
    assert warnings


def test_junit_must_be_in_artifact_manifest(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    report.write_text("<testsuite tests='1'/>", encoding="utf-8")
    checks, warnings = collect_junit_checks(
        tmp_path,
        ["report.xml"],
        1_000_000,
        {},
    )
    assert checks[0].status == "unknown"
    assert "not present in the artifact manifest" in (checks[0].summary or "")
    assert warnings


def test_junit_digest_change_is_reported_unknown(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    relative = "report.xml"
    report.write_text("<testsuite tests='1'/>", encoding="utf-8")
    original = sha256_file(report)
    report.write_text("<testsuite tests='2'/>", encoding="utf-8")

    checks, warnings = collect_junit_checks(
        tmp_path,
        [relative],
        1_000_000,
        {relative: original},
    )
    assert checks[0].status == "unknown"
    assert "changed after evidence hashing" in (checks[0].summary or "")
    assert warnings
