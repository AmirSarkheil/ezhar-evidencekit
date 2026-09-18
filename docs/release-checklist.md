# Release checklist

This checklist is the gate for the first public EvidenceKit release.

## Build and correctness

- [ ] CI passes on Python 3.11, 3.12, and 3.13.
- [ ] Ruff and mypy pass.
- [ ] Tests pass with at least 80% measured package coverage.
- [ ] Source distribution and wheel build successfully.
- [ ] A clean wheel installs and the CLI starts.
- [ ] collect -> validate -> verify -> report passes in self-dogfooding CI.
- [ ] Composite GitHub Action passes with both default and custom manifest locations.
- [ ] Tamper detection has positive and negative tests.

## Security

- [ ] Dependency audit passes.
- [ ] Secret scan passes.
- [ ] GitHub Actions dependencies are pinned to immutable full commit SHAs.
- [ ] Path traversal, symlink escape, non-regular files, oversized inputs, malformed XML, and report injection are covered by tests or documented controls.
- [ ] SECURITY.md has a private reporting route.
- [ ] Threat-model claims distinguish consistency from authenticity.

## Contract and documentation

- [ ] Evidence Manifest v1 schema matches the implementation.
- [ ] Quickstart is reproducible from a clean environment.
- [ ] Compatibility policy is documented.
- [ ] README avoids certification, compliance, and production-readiness overclaims.
- [ ] CHANGELOG and release notes describe only shipped behavior.

## IP and governance

- [ ] Open-source/private IP boundary reviewed.
- [ ] No private EZHAR implementation, credentials, customer data, or internal-only material is present.
- [ ] LICENSE and NOTICE are present.
- [ ] Governance, maintainers, contribution rules, and code of conduct are present.

## Public-release actions

Only after all gates above are satisfied:

1. squash or otherwise create a reviewable release commit on `main`;
2. record the immutable commit SHA;
3. create the signed/annotated release tag if signing is available;
4. publish release notes and distribution artifacts;
5. switch repository visibility only when the maintainer explicitly approves public launch.
