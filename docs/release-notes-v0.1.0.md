# EZHAR EvidenceKit v0.1.0 — Candidate Release Notes

> **Pre-public candidate.** These notes describe the reviewed private candidate and are not a public release announcement.

## What v0.1.0 provides

EvidenceKit v0.1.0 introduces a compact, vendor-neutral evidence loop for software and AI engineering workflows:

```text
collect -> validate -> verify -> report
```

The candidate can collect configured artifacts, record their byte sizes and SHA-256 digests, ingest bounded JUnit XML results, validate a versioned Evidence Manifest v1, detect later artifact or manifest changes, and render machine-readable JSON or a human-readable Markdown report.

## CLI

The candidate includes:

- `evidencekit init`
- `evidencekit collect`
- `evidencekit validate`
- `evidencekit verify`
- `evidencekit report`

## Evidence Manifest v1

The manifest records the schema version, run identity and timestamp, source revision when available, runtime environment, checks, artifact paths and integrity metadata, warnings, and a deterministic manifest self-digest.

The self-digest detects inconsistent modification when the recorded digest is not recomputed. It is **not** a digital signature and does not establish author authenticity.

## GitHub Actions integration

The bundled composite action can use the default configuration path or a custom EvidenceKit configuration and manifest location. It validates and verifies the generated manifest, renders a Markdown report, and uploads normalized manifest/report copies as a workflow artifact. The artifact name is configurable for workflows that invoke EvidenceKit more than once.

GitHub Actions dependencies in the repository are pinned to immutable commit SHAs.

## Verified candidate gates

The private candidate has demonstrated:

- Python 3.11, 3.12, and 3.13 CI;
- Ruff and strict mypy checks;
- 68 passing tests with an enforced 80% coverage floor;
- source distribution and wheel builds;
- clean wheel installation and CLI startup;
- clean-environment quickstart reproduction;
- Linux self-dogfooding of collect -> validate -> verify -> report;
- Windows and macOS smoke testing;
- default and custom-manifest composite-action smoke tests;
- dependency auditing and secret scanning;
- schema parity between the runtime contract and checked-in JSON Schema.

## Security-focused behavior

The v0.1.0 candidate includes controls and regression tests for path traversal, symlink escape, protected repository metadata, non-regular files, bounded configuration/manifest/artifact inputs, malformed XML, JUnit parser resource limits, Markdown report injection, and atomic output handling where supported.

See `SECURITY.md` and `docs/threat-model.md` for the precise trust boundary and limitations.

## Scope and non-goals

EvidenceKit does not provide certification, compliance attestation, formal verification, SBOM replacement, complete secret detection, or proof of real-world outcomes. It records reproducible engineering evidence and integrity metadata.

The open-source repository is intentionally separated from private EZHAR DYNAMICS product implementation and proprietary policy/scoring logic. See `docs/ip-boundary.md`.

## Publication status

No public publication is implied by this document. Repository visibility, release tagging, and distribution publication remain separate maintainer-controlled actions.
