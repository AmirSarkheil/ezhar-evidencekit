# Threat Model

EvidenceKit processes files and metadata that may originate from CI jobs or untrusted pull requests. Its core threat boundary is the configured workspace.

| Threat | v0.1 control |
|---|---|
| Path traversal | Reject absolute paths and parent traversal; confine resolved paths to workspace |
| Symlink escape | Reject symlink artifacts |
| Manifest tampering | Deterministic canonical serialization and SHA-256 manifest digest |
| Artifact tampering | Recompute size and SHA-256 on verify |
| Oversized artifacts | Configurable byte limit |
| Secret leakage | Explicit include patterns, suspicious-name warning, documentation and review |
| Untrusted PR execution | Read-only workflow permissions by default |
| Dependency compromise | Dependency audit and automated dependency updates |
| Report injection | Markdown output contains values as text; future renderers must escape target formats |

## Non-goals

EvidenceKit does not inspect arbitrary artifact contents for all classes of secrets and does not sandbox the programs that produced artifacts. CI operators remain responsible for untrusted code execution boundaries.
