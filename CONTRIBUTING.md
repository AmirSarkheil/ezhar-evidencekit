# Contributing

Thank you for improving EvidenceKit.

## Before opening a PR

For substantial features, open an issue first so the public contract and IP/security impact can be discussed. Keep pull requests small and focused.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy src/evidencekit
pytest -q
python -m build
```

A change is expected to include tests for new behavior, documentation when user-visible behavior changes, and a changelog entry when appropriate.

## Review rules

- CI must pass.
- Schema-impacting changes require explicit compatibility review.
- Security-sensitive changes require threat-model review.
- Do not copy code, datasets, prompts, internal codenames, endpoints, credentials, or implementation details from private EZHAR repositories.
- Contributions are submitted under Apache-2.0 unless explicitly stated otherwise.

By participating, contributors agree to follow the Code of Conduct.
