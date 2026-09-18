# Compatibility

## Python

The v0.1 target matrix is Python 3.11, 3.12, and 3.13.

## Manifest schema

Evidence Manifest v1 follows this policy:

- breaking changes require a new major schema;
- optional additive metadata may appear in minor tool releases;
- unknown fields are accepted by v1;
- supported schema fixtures should remain testable for at least two minor tool releases after a successor is introduced.

## CLI

Existing command names and exit-code meaning should not change in patch releases. Breaking CLI changes require explicit migration notes.
