# EZHAR EvidenceKit

> **Status:** pre-release MVP development (v0.1.0 candidate). This repository is being built and reviewed privately before any public launch.

EZHAR EvidenceKit is a vendor-neutral open-source toolkit for creating, validating, verifying, and reporting reproducible evidence packages from software and AI engineering workflows.

It turns files produced by tests/builds into a versioned, machine-readable Evidence Manifest with SHA-256 integrity metadata and a human-readable report.

## Why

"Tests passed" is often not enough for a reviewer. EvidenceKit answers a narrower question:

**What ran, against which source revision and environment, and which exact artifacts can be independently checked later?**

EvidenceKit does not implement proprietary policy engines, scoring logic, or private product workflows. It records verifiable engineering facts.

## MVP commands

~~~bash
python -m pip install -e .
evidencekit init
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

## Evidence Manifest v1

A manifest records:

- schema version
- run identity and UTC timestamp
- immutable source revision when available
- OS and Python runtime
- checks and evidence references
- artifact paths, sizes, media types, and SHA-256 digests
- a digest of the manifest itself

See [docs/schema.md](docs/schema.md).

## Security model

Collectors are explicit and default-deny: EvidenceKit only includes files matched by configured include patterns. Artifact paths are normalized and restricted to the workspace root, symlink escapes are rejected, size limits are enforced, and sensitive-name heuristics produce warnings.

See [SECURITY.md](SECURITY.md) and [docs/threat-model.md](docs/threat-model.md).

## What EvidenceKit does not claim

EvidenceKit is not a certification product, formal-verification system, SBOM replacement, or compliance guarantee. It complements tools such as CI systems, provenance frameworks, signing systems, and SBOM generators.

## Development

~~~bash
python -m pip install -e ".[dev]"
ruff check .
mypy src/evidencekit
pytest -q
python -m build
~~~

## Project governance

- License: Apache-2.0
- Maintainer model: primary maintainer with transparent contribution/review rules
- Security reports: see [SECURITY.md](SECURITY.md)
- Contributing: see [CONTRIBUTING.md](CONTRIBUTING.md)
- Roadmap: see [ROADMAP.md](ROADMAP.md)

## IP boundary

This repository is intentionally standalone. No private EZHAR DYNAMICS product repository is imported or required at runtime. Examples and fixtures are synthetic and generic.

Copyright 2026 EZHAR DYNAMICS contributors.
