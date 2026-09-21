# Changelog

All notable user-visible changes to EvidenceKit are documented here.

## [Unreleased]

### Documentation
- Simplified the public roadmap and community-adoption guidance to avoid publishing unnecessary internal planning detail.
- Generalized the public/private IP-boundary language and public contribution/release wording.
- Clarified the copyright notice to identify the current author and project contributors without implying a separate legal entity ownership record.

## [0.1.0] - 2026-09-18

### Added
- Evidence Manifest v1 contract with deterministic manifest self-digest.
- CLI commands: `init`, `collect`, `validate`, `verify`, and `report`.
- SHA-256 artifact integrity verification and tamper detection.
- Bounded JUnit XML evidence ingestion with malformed-input and resource-limit handling.
- Markdown and JSON reporting.
- GitHub Actions CI, dependency auditing, secret scanning, and a composite EvidenceKit action.
- Default and custom manifest-path action flows.
- Configurable GitHub Actions artifact naming.
- Clean-environment quickstart verification.
- Python 3.11, 3.12, and 3.13 CI plus Windows and macOS smoke coverage.
- Runtime-schema and checked-in JSON Schema parity enforcement.
- Governance, contribution, security, compatibility, release-gate, adoption, and IP-boundary documentation.

### Security and scope
- Path traversal, symlink escape, protected repository metadata, non-regular files, oversized inputs, malformed XML, JUnit parser limits, and report-injection cases are explicitly handled or tested.
- GitHub Actions dependencies are pinned to immutable commit SHAs.
- Manifest self-digest is a consistency mechanism, not a signature or authenticity proof.
- EvidenceKit does not claim certification, compliance attestation, formal verification, complete secret detection, or proof of real-world outcomes.
