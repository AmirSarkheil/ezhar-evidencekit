# Release checklist

This document records the engineering and publication gate for EZHAR EvidenceKit v0.1.0.

## Reviewed baseline

The private engineering baseline was verified before publication. The public-release commit is the merge commit that introduces the v0.1.0 publication marker and final release-facing documentation.

## Build and correctness

- [x] CI passes on Python 3.11, 3.12, and 3.13.
- [x] Ruff and strict mypy pass.
- [x] Tests pass with at least 80% measured package coverage.
- [x] Source distribution and wheel build successfully.
- [x] A clean wheel installs and the CLI starts.
- [x] A clean-environment quickstart reproduces successfully.
- [x] collect -> validate -> verify -> report passes in self-dogfooding CI.
- [x] Composite GitHub Action passes with default and custom manifest locations.
- [x] Tamper detection has positive and negative tests.
- [x] Windows and macOS smoke tests pass.
- [x] Runtime schema matches the checked-in JSON Schema.

Latest measured release-gate baseline: **68 tests passed** with **80.09% package coverage**.

## Security

- [x] Dependency audit passes.
- [x] Secret scan passes.
- [x] GitHub Actions dependencies are pinned to immutable full commit SHAs.
- [x] Path traversal, symlink escape, non-regular files, oversized inputs, malformed XML, JUnit parser limits, and report injection are covered by tests or documented controls.
- [x] SECURITY.md provides a private reporting route.
- [x] Threat-model claims distinguish consistency from authenticity.

## Contract and documentation

- [x] Evidence Manifest v1 schema matches the implementation.
- [x] Quickstart is reproducible from a clean environment.
- [x] Compatibility policy is documented.
- [x] README avoids certification, compliance, and production-readiness overclaims.
- [x] CHANGELOG and release notes describe only implemented behavior.
- [x] Citation metadata identifies v0.1.0 and its release date.

## IP and governance

- [x] Open-source/private IP boundary reviewed.
- [x] No private EZHAR implementation, credentials, customer data, or internal-only material is present in the reviewed release baseline.
- [x] LICENSE and NOTICE are present.
- [x] Governance, maintainers, contribution rules, and code of conduct are present.

## Publication authorization

- [x] Maintainer explicitly approved the v0.1.0 public launch on 2026-09-18.
- [x] Repository automation is configured to create the annotated `v0.1.0` tag and GitHub Release from the authorized merge commit.
- [x] Release automation rebuilds the wheel and source distribution, creates SHA-256 checksums, and generates a release EvidenceKit manifest/report before publication.
- [ ] Repository visibility is changed to **Public** in GitHub repository administration.

The final visibility toggle is a GitHub repository-administration action and is intentionally separate from source-code verification.
