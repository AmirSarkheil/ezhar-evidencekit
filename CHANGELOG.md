# Changelog

All notable user-visible changes to EvidenceKit are documented here.

## [Unreleased]

No additional user-visible changes are currently queued beyond the reviewed v0.1.0 candidate.

## [0.1.0] - TBD

Private candidate contents verified before public release:

### Added
- Evidence Manifest v1 contract with deterministic manifest self-digest.
- CLI commands: `init`, `collect`, `validate`, `verify`, and `report`.
- SHA-256 artifact integrity verification and tamper detection.
- Bounded JUnit XML evidence ingestion with malformed-input handling.
- Markdown and JSON reporting.
- GitHub Actions CI, dependency auditing, secret scanning, and a composite EvidenceKit action.
- Default and custom manifest-path action flows.
- Clean-environment quickstart verification.
- Python 3.11, 3.12, and 3.13 CI plus Windows and macOS smoke coverage.
- Governance, contribution, security, compatibility, release-gate, adoption, and IP-boundary documentation.

### Security and scope
- Path traversal, symlink escape, protected repository metadata, non-regular files, oversized inputs, and report-injection cases are explicitly handled or tested.
- Manifest self-digest is a consistency mechanism, not a signature or authenticity proof.
- EvidenceKit does not claim certification, compliance attestation, formal verification, or proof of real-world outcomes.

The release date remains unset until the maintainer explicitly approves public publication.
