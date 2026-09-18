# Pytest example

Produce JUnit XML, then collect it:

```bash
mkdir -p artifacts
pytest --junitxml=artifacts/pytest.xml
evidencekit collect --config .evidencekit/config.yml
evidencekit validate evidence.json
evidencekit verify evidence.json
```

The JUnit collector records a bounded pass/fail/skipped/unknown summary while the XML itself remains an integrity-checked artifact.
