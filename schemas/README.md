# Evidence Manifest schemas

`evidence-manifest-v1.schema.json` is the public contract for EvidenceKit v0.1.

Compatibility policy:

- Breaking contract changes require a new major schema version.
- Optional additive fields may be introduced in minor tool releases.
- Unknown fields are accepted by the v1 validator to support forward-compatible metadata.
- Golden fixtures should be retained for every supported schema generation.

The manifest contains evidence facts and integrity metadata only. It does not encode proprietary decision logic.
