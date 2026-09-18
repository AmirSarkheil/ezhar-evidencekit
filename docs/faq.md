# FAQ

## Does EvidenceKit certify my release?

No. It records reproducibility and integrity evidence. Certification and compliance assessments require separate processes and evidence.

## Does it upload my artifacts?

The core CLI does not upload artifacts. The bundled GitHub Action uploads the generated manifest/report as a GitHub workflow artifact. Your own CI configuration controls what leaves the runner.

## Does it collect secrets automatically?

No content scanner can guarantee that. v0.1 uses explicit include patterns and warnings for suspicious filenames. Review your configuration and artifacts before publishing them.

## Can I use it without Git?

Yes. The source revision may be null when Git or CI revision metadata is unavailable.

## Is it tied to OpenAI, GitHub, or EZHAR private systems?

No. The core manifest, CLI, validation, and integrity model are vendor-neutral. Integrations are optional boundaries.

## What happens if an artifact changes?

`evidencekit verify` recomputes size and SHA-256 and reports the mismatch.
