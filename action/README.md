# EvidenceKit GitHub Action

The bundled composite action runs EvidenceKit in the calling repository, validates and verifies the configured manifest, then uploads a normalized copy of the manifest and its Markdown report as a workflow artifact.

The action supports a custom `manifest` path in `.evidencekit/config.yml`; the uploaded artifact still uses stable names under `.evidencekit/action-output/`.

Example inside this repository:

```yaml
steps:
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
  - uses: ./action
    with:
      config: .evidencekit/config.yml
```

For external repositories, pin EvidenceKit to the **full commit SHA** of a reviewed release commit:

```yaml
- uses: AmirSarkheil/ezhar-evidencekit/action@<FULL_COMMIT_SHA>
```

A release tag can be kept in a comment for readability, but production workflows should not rely on a mutable tag or moving branch as the trust anchor.
