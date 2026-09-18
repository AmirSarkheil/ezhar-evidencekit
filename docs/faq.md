# FAQ

## Does EvidenceKit certify my release?

No. It records reproducibility and integrity evidence. Certification and compliance assessments require separate processes and evidence.

## Does it upload my artifacts?

The core CLI does not upload anything. The bundled GitHub Action uploads a normalized copy of the generated manifest and Markdown report as a GitHub workflow artifact. It does **not** upload every collected source artifact. Your CI configuration controls any additional uploads.

Custom manifest locations are supported by the action; the uploaded copies use stable names under `.evidencekit/action-output/`.

## Does the manifest SHA-256 prove authenticity?

No. It is a deterministic consistency check. Someone who can modify a manifest can also recompute that self-digest. If authenticity matters, anchor the digest in a separately trusted system or use a signing/provenance mechanism.

## Does it collect secrets automatically?

No content scanner can guarantee that. v0.1 uses explicit include patterns, protects repository metadata directories, and warns on suspicious filenames. Review your configuration and artifacts before publishing them.

## Can I use it without Git?

Yes. The source revision may be null when Git or CI revision metadata is unavailable.

## Is it tied to OpenAI, GitHub, or EZHAR private systems?

No. The core manifest, CLI, validation, and integrity model are vendor-neutral. Integrations are optional boundaries.

## What happens if an artifact changes?

`evidencekit verify` recomputes size and SHA-256 and reports the mismatch.
