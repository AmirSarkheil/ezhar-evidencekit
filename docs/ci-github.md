# GitHub Actions integration

EvidenceKit includes a composite action in `action/action.yml`.

A repository can run the evidence loop after tests/builds produce artifacts:

```yaml
steps:
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4, pinned
  - name: Run tests
    run: pytest --junitxml=artifacts/pytest.xml
  - uses: ./action
    with:
      config: .evidencekit/config.yml
```

The action collects the configured manifest, validates it, verifies referenced artifacts against the configured workspace, creates a Markdown report, and uploads normalized copies of the manifest and report as a workflow artifact.

Custom manifest locations such as `reports/evidence.json` are supported. The upload names remain stable under `.evidencekit/action-output/`.

For external consumers, pin the EvidenceKit action itself to a reviewed **full commit SHA** after the repository becomes public. A release tag is useful as human-readable metadata but is not an immutable execution reference.
