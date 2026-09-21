# EZHAR EvidenceKit v0.1.0

Released: **2026-09-18**

EZHAR EvidenceKit v0.1.0 is the first public baseline of a vendor-neutral toolkit for producing reproducible engineering evidence packages.

## Core workflow

```text
collect -> validate -> verify -> report
```

EvidenceKit can collect configured artifacts, record byte sizes and SHA-256 digests, ingest bounded JUnit XML results, validate Evidence Manifest v1, detect later artifact or manifest changes, and render machine-readable JSON or a human-readable Markdown report.

## CLI

v0.1.0 includes:

- `evidencekit init`
- `evidencekit collect`
- `evidencekit validate`
- `evidencekit verify`
- `evidencekit report`

## Evidence Manifest v1

The manifest records:

- schema version;
- run identity and UTC timestamp;
- source revision when available;
- runtime environment;
- checks and evidence references;
- artifact paths, sizes, media types, and SHA-256 digests;
- warnings;
- a deterministic manifest self-digest.

The self-digest is a consistency mechanism. It is **not** a digital signature and does not establish author authenticity.

## GitHub Actions integration

The bundled composite action supports:

- the default `.evidencekit/config.yml` path;
- custom EvidenceKit configuration and manifest locations;
- configurable workflow artifact names;
- validation and verification before artifact upload;
- normalized manifest and Markdown report outputs.

Repository GitHub Actions dependencies are pinned to immutable commit SHAs.

## Verified release baseline

Before publication, the reviewed baseline demonstrated:

- Python 3.11, 3.12, and 3.13 CI;
- Ruff and strict mypy checks;
- 68 passing tests with 80.09% measured package coverage;
- source distribution and wheel builds;
- clean wheel installation and CLI startup;
- clean-environment quickstart reproduction;
- Linux self-dogfooding of `collect -> validate -> verify -> report`;
- Windows and macOS smoke testing;
- default and custom-manifest composite-action smoke tests;
- dependency auditing and secret scanning;
- parity between the runtime schema and checked-in JSON Schema.

## Security-focused behavior

v0.1.0 includes controls and regression tests for:

- path traversal;
- symlink escape;
- protected repository metadata;
- non-regular files;
- bounded configuration, manifest, artifact, and JUnit inputs;
- malformed XML;
- JUnit parser element/depth limits;
- Markdown report injection;
- atomic output handling where supported.

See `SECURITY.md` and `docs/threat-model.md` for the precise trust boundary and limitations.

## Release artifacts

The GitHub Release automation publishes:

- the Python wheel;
- the source distribution;
- `SHA256SUMS.txt`;
- `release-evidence.json`;
- `release-evidence-report.md`.

The release evidence package is produced by EvidenceKit itself against the built distribution files.

## Scope and non-goals

EvidenceKit does not provide certification, compliance attestation, formal verification, SBOM replacement, complete secret detection, or proof of real-world outcomes.

The open-source repository is intentionally separated from private EZHAR product implementations and confidential R&D assets. See `docs/ip-boundary.md`.
