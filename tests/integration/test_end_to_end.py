from __future__ import annotations

import json
from pathlib import Path

from evidencekit.canonical import manifest_digest
from evidencekit.cli import main
from evidencekit.verify import verify_manifest


def test_cli_end_to_end_and_tamper_detection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["init"]) == 0
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    sample = artifacts / "result.txt"
    sample.write_text("passed\n", encoding="utf-8")

    assert main(["collect", "--config", ".evidencekit/config.yml"]) == 0
    assert main(["validate", "evidence.json"]) == 0
    assert main(["verify", "evidence.json"]) == 0
    assert main(["report", "evidence.json", "--output", "evidence-report.md"]) == 0
    assert (tmp_path / "evidence-report.md").exists()

    sample.write_text("tampered\n", encoding="utf-8")
    _, problems = verify_manifest(tmp_path / "evidence.json")
    assert any("mismatch" in problem for problem in problems)


def test_manifest_digest_detects_manifest_tamper(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "x.txt").write_text("x", encoding="utf-8")
    assert main(["collect", "--config", ".evidencekit/config.yml"]) == 0

    path = tmp_path / "evidence.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    original = manifest["manifest_sha256"]
    manifest["environment"]["os"] = "tampered"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert manifest_digest(manifest) != original
    assert main(["validate", "evidence.json"]) == 2
