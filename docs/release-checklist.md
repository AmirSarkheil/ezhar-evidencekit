# Release checklist

This checklist is the gate for the first public EvidenceKit release.

**Reviewed private candidate baseline:** `b45200f0f8c54e15e1392d55cf9d2eab25686c4e`

## Build and correctness

- [x] CI passes on Python 3.11, 3.12, and 3.13.
- [x] Ruff and mypy pass.
- [x] Tests pass with at least 80% measured package coverage.
- [x] Source distribution and wheel build successfully.
- [x] A clean wheel installs and the CLI starts.
- [x] collect -> validate -> verify -> report passes in self-dogfooding CI.
- [x] Composite GitHub Action passes with both default and custom manifest locations.
- [x] Tamper detection has positive and negative tests.

Latest private gate run: **68 tests passed** with **80.09% package coverage**, plus clean wheel installation and Windows/macOS smoke coverage.

## Security

- [x] Dependency audit passes.
- [x] Secret scan passes.
- [x] GitHub Actions dependencies are pinned to immutable full commit SHAs.
- [x] Path traversal, symlink escape, non-regular files, oversized inputs, malformed XML, and report injection are covered by tests or documented controls.
- [x] SECURITY.md has a private reporting route.
- [x] Threat-model claims distinguish consistency from authenticity.

## Contract and documentation

- [x] Evidence Manifest v1 schema matches the implementation.
- [x] Quickstart is reproducible from a clean environment.
- [x] Compatibility policy is documented.
- [x] README avoids certification, compliance, and production-readiness overclaims.
- [x] CHANGELOG and candidate release notes describe only implemented behavior.

## IP and governance

- [x] Open-source/private IP boundary reviewed.
- [x] No private EZHAR implementation, credentials, customer data, or internal-only material is present in the reviewed candidate.
- [x] LICENSE and NOTICE are present.
- [x] Governance, maintainers, contribution rules, and code of conduct are present.

## Public-release actions

These actions remain intentionally separate from the private engineering gate:

- [ ] Create the final reviewable release commit on `main` after this candidate-record update is merged.
- [ ] Record the immutable final release commit SHA.
- [ ] Create the signed/annotated release tag if signing is available.
- [ ] Publish release notes and distribution artifacts.
- [ ] Switch repository visibility only after explicit maintainer approval.

Passing this checklist does not itself publish, certify, or make the repository public.
