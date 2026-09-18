# Security Policy

## Supported versions

The current v0.1.x line is supported for security fixes. When a newer supported line is released, this policy will be updated explicitly.

## Reporting a vulnerability

Please do **not** open a public issue for a vulnerability, secret exposure, or exploit details.

Preferred channel: GitHub Private Vulnerability Reporting when enabled for this repository. If that is unavailable, contact the maintainer privately at **a.sarkheil@ezhardynamics.com** with the subject `EvidenceKit Security`.

Include the affected version or commit, reproduction steps, expected impact, and whether public disclosure has already occurred. Do not include third-party secrets or personal data.

## Scope

Security-sensitive areas include path confinement, symlink handling, manifest integrity, untrusted artifact parsing, GitHub Actions permissions, release provenance, dependency integrity, and report rendering.

EvidenceKit does not claim certification, formal verification, or complete prevention of secret leakage. Users remain responsible for deciding which artifacts are safe to collect and publish.
