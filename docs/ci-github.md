# GitHub Actions integration

EvidenceKit includes a composite action in `action/action.yml`.

A repository can run the evidence loop after tests/builds produce artifacts:

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Run tests
    run: pytest --junitxml=artifacts/pytest.xml
  - uses: ./action
    with:
      config: .evidencekit/config.yml
```

The action creates `evidence.json`, validates it, verifies referenced artifacts, creates `evidence-report.md`, and uploads both files as a workflow artifact.

For external consumers, use a released immutable tag after EvidenceKit becomes public.
