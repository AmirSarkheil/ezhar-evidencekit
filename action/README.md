# EvidenceKit GitHub Action

The bundled composite action runs EvidenceKit in the calling repository and uploads the manifest and Markdown report as a workflow artifact.

Example:

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: ./action
    with:
      config: .evidencekit/config.yml
```

For external repositories, pin a released EvidenceKit tag once public releases exist. Do not point production workflows at a moving branch.
