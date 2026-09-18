# Concepts

## Evidence package

An evidence package is a versioned manifest plus the artifacts it references. The manifest records reproducibility and integrity facts without interpreting proprietary business or policy decisions.

## Integrity

Each artifact receives a SHA-256 digest and byte size. The manifest receives its own SHA-256 digest over deterministic JSON serialization with the self-digest field omitted.

## Reproducibility

EvidenceKit captures a source revision when available, UTC run time, runtime environment, checks, and artifact references. These facts help another reviewer reconstruct what was examined.

## Provenance

Provenance is broader than hashing. EvidenceKit v0.1 provides a place for generic provenance metadata but does not claim signed supply-chain provenance. Signature support is a later design item.

## Validation vs verification

- **validate** checks the manifest contract and manifest digest.
- **verify** additionally re-hashes referenced artifacts and reports missing or changed files.

## Evidence is not certification

A valid EvidenceKit package is not proof of safety, compliance, certification, or operational fitness. It is an integrity and reproducibility record.
