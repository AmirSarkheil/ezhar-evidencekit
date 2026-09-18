# Roadmap

Roadmap items are plans, not implemented claims.

## v0.1.0 — Core evidence loop
- Versioned Evidence Manifest v1.
- collect -> validate -> verify -> report workflow.
- Artifact hashing and tamper detection.
- JUnit check ingestion.
- Python 3.11-3.13 CI.
- Security/dependency checks.
- GitHub Action MVP.
- Minimal examples and documentation.

## v0.2.x — Maintainer ergonomics
- `doctor` environment diagnostics.
- More polished GitHub Action inputs/outputs.
- Additional CI adapters and examples.
- Better validation diagnostics.

## v0.3.x — Evidence comparison
- `diff` between two manifests.
- Explicit evidence deltas.
- Optional signature/provenance extensions after a separate design review.

The project will not add provider-specific complexity to the core unless a real integration need justifies it.
