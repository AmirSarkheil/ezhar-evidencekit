# Threat Model

EvidenceKit processes files and metadata that may originate from CI jobs or untrusted pull requests. Its core threat boundary is the configured workspace.

| Threat | v0.1 control |
|---|---|
| Path traversal | Reject absolute paths and parent traversal; on supported POSIX runners, open each path component through directory descriptors with no-follow semantics |
| Symlink escape | Reject symlink artifacts, config targets, and manifest outputs; artifact reads use no-follow opens where the platform supports them |
| Manifest corruption | Deterministic canonical serialization plus a SHA-256 self-digest detects accidental/inconsistent modification when the recorded digest is not recomputed |
| Manifest authenticity | **Not provided in v0.1.** An attacker able to edit the manifest can recompute its self-digest; use a separately trusted digest/signature when authenticity is required |
| Artifact drift | Recompute byte size and SHA-256 from the same opened file descriptor during verify and compare with the recorded manifest |
| Special-file blocking | Hash only regular files; reject FIFOs, devices, directories, and symlinks |
| Oversized artifacts | Configurable byte limit is enforced while reading opened artifact descriptors; a hard upper bound also limits configured artifact size |
| XML parser abuse | JUnit XML is parsed from already bounded, no-follow-opened bytes with a hardened parser, and only when its digest matches the artifact manifest |
| Secret leakage | Explicit include patterns, protected metadata directories, suspicious-name warnings, documentation, and review |
| Untrusted action input | Composite-action config input is passed through environment variables rather than interpolated into shell syntax |
| Untrusted PR execution | Repository workflows use read-only permissions unless a narrowly scoped read permission is required |
| Dependency compromise | Dependency audit, automated dependency updates, and GitHub Actions pinned to immutable commit SHAs |
| Report injection | Manifest-derived Markdown values are HTML-escaped and Markdown metacharacters are escaped before rendering |

## Trust boundary

The manifest self-digest is a consistency mechanism, not a signature. EvidenceKit can show that current artifacts differ from the recorded hashes, but v0.1 does not prove who created the manifest or prevent an attacker with write access from replacing both an artifact and its recorded digest.

For stronger authenticity, retain the manifest digest in a separately trusted system or add signing/provenance tooling outside the v0.1 core.

## Non-goals

EvidenceKit does not inspect arbitrary artifact contents for every class of secret, does not sandbox programs that produced artifacts, and does not provide certification or formal verification. CI operators remain responsible for untrusted code execution boundaries.
