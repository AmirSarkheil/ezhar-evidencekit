# EZHAR EvidenceKit

[![CI](https://github.com/AmirSarkheil/ezhar-evidencekit/actions/workflows/ci.yml/badge.svg)](https://github.com/AmirSarkheil/ezhar-evidencekit/actions/workflows/ci.yml)
[![Security](https://github.com/AmirSarkheil/ezhar-evidencekit/actions/workflows/security.yml/badge.svg)](https://github.com/AmirSarkheil/ezhar-evidencekit/actions/workflows/security.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11--3.13-blue.svg)](pyproject.toml)

> **Version:** v0.1.0 — first public release baseline.

EZHAR EvidenceKit is a vendor-neutral open-source toolkit for creating, validating, verifying, and reporting reproducible evidence packages from software and AI engineering workflows.

It turns files produced by tests and builds into a versioned, machine-readable Evidence Manifest with SHA-256 integrity metadata and a human-readable report.

## Why

"Tests passed" is often not enough for a reviewer. EvidenceKit answers a narrower question:

**What ran, against which source revision and environment, and which exact artifacts can be independently checked later?**

EvidenceKit does not implement proprietary policy engines, scoring logic, or private product workflows. It records verifiable engineering facts.

## Install

For the v0.1.0 source release:

~~~bash
git clone https://github.com/AmirSarkheil/ezhar-evidencekit.git
cd ezhar-evidencekit
git checkout v0.1.0
python -m pip install .
~~~

For development:

~~~bash
python -m pip install -e ".[dev]"
~~~

## Quickstart

~~~bash
evidencekit init
mkdir -p artifacts
printf "example evidence\n" > artifacts/example.txt
evidencekit collect --config .evidencekit/config.yml
evidencekit validate evidence.json
evidencekit verify evidence.json
evidencekit report evidence.json --format markdown --output evidence-report.md
~~~

The v0.1 CLI includes:

- `evidencekit init`
- `evidencekit collect`
- `evidencekit validate`
- `evidencekit verify`
- `evidencekit report`

See [docs/quickstart.md](docs/quickstart.md) for the complete walkthrough.

## Evidence Manifest v1

A manifest records:

- schema version;
- run identity and UTC timestamp;
- source revision when available;
- OS and Python runtime;
- checks and evidence references;
- artifact paths, sizes, media types, and SHA-256 digests;
- a deterministic digest of the manifest itself.

See [docs/schema.md](docs/schema.md).

## Security model

Collectors are explicit and default-deny: EvidenceKit only includes files matched by configured include patterns. Artifact paths are constrained to the configured workspace, symlink escapes and non-regular files are rejected, bounded input limits are enforced, and suspicious artifact names produce warnings.

The manifest self-digest is a consistency mechanism, not a digital signature or authenticity proof.

See [SECURITY.md](SECURITY.md) and [docs/threat-model.md](docs/threat-model.md).

## What EvidenceKit does not claim

EvidenceKit is not a certification product, formal-verification system, SBOM replacement, complete secret scanner, compliance guarantee, or proof of real-world outcomes. It complements CI systems, provenance frameworks, signing systems, and SBOM generators.

## Verified v0.1.0 baseline

Before public release, the reviewed baseline demonstrated:

- Python 3.11, 3.12, and 3.13 CI;
- Ruff and strict mypy checks;
- 68 passing tests with 80.09% measured package coverage;
- source distribution and wheel builds;
- clean wheel installation and CLI smoke testing;
- clean-environment quickstart reproduction;
- Windows and macOS smoke tests;
- self-dogfooding of `collect -> validate -> verify -> report`;
- default and custom-manifest composite GitHub Action smoke tests;
- dependency auditing and secret scanning;
- runtime-schema and checked-in JSON Schema parity.

These are engineering test results for the reviewed release baseline, not certification claims.

## Development

~~~bash
python -m pip install -e ".[dev]"
ruff check .
mypy src/evidencekit
pytest --cov=evidencekit --cov-report=term-missing --cov-fail-under=80
python -m build
~~~

## Project governance

- License: Apache-2.0
- Maintainer model: primary maintainer with transparent contribution and review rules
- Security reports: see [SECURITY.md](SECURITY.md)
- Contributing: see [CONTRIBUTING.md](CONTRIBUTING.md)
- Roadmap: see [ROADMAP.md](ROADMAP.md)
- Release verification: see [docs/release-checklist.md](docs/release-checklist.md)
- Adoption plan: see [docs/adoption.md](docs/adoption.md)
- v0.1.0 release notes: see [docs/release-notes-v0.1.0.md](docs/release-notes-v0.1.0.md)

## IP boundary

This repository is intentionally standalone. No private EZHAR DYNAMICS product repository is imported or required at runtime. Examples and fixtures are synthetic and generic. See [docs/ip-boundary.md](docs/ip-boundary.md) for the explicit carve-out rules.

Copyright 2026 EZHAR DYNAMICS contributors.
