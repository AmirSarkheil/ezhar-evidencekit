# GitHub Actions example

A minimal workflow pattern:

```yaml
name: evidence
on: [push, pull_request]

permissions:
  contents: read

jobs:
  evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest
      - run: mkdir -p artifacts && pytest --junitxml=artifacts/pytest.xml
      - uses: ./action
```

This in-repository example uses the local composite action. External consumers should pin a released version once releases exist.
