# Open-source IP boundary

EvidenceKit is intentionally designed as a standalone public utility.

## In scope

This repository may contain:

- the public Evidence Manifest contract;
- generic interoperability with public engineering formats;
- integrity and reproducibility primitives;
- documentation, examples, tests, and integration glue;
- public governance and security processes.

## Out of scope

This repository must not contain or reconstruct:

- private EZHAR product implementations;
- proprietary decision, governance, or evaluation logic;
- confidential research and development assets;
- customer, partner, or other non-public data;
- private endpoints, credentials, tokens, or deployment secrets;
- code or documentation copied from private repositories without explicit release review.

## Review rule

A contribution that crosses this boundary is blocked even if it is technically useful.

When a public feature needs a concept that also exists in private work, the public implementation must be independently defined around the smallest generic interface required by the open-source use case.

## Evidence rule

Examples and fixtures should be synthetic or derived from clearly redistributable public material. Public claims should describe only behavior demonstrated by this repository.
