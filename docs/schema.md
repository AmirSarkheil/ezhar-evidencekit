# Evidence Manifest v1

The authoritative JSON Schema is `schemas/evidence-manifest-v1.schema.json`.

Required top-level groups:

| Field | Purpose |
|---|---|
| `schema_version` | Versioned public contract |
| `run` | Run identity, UTC timestamp, source revision |
| `environment` | Minimum OS and runtime metadata |
| `checks` | Bounded status records and evidence references |
| `artifacts` | Path, SHA-256, size, optional media type |
| `manifest_sha256` | Digest over canonical manifest content |

Optional groups include `provenance` and `warnings`.

v1 accepts unknown fields so additive metadata can travel through older validators without being discarded. Breaking contract changes require a new major schema version.
