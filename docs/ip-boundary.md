# Open-source IP boundary

EvidenceKit is intentionally designed as a standalone public utility.

## In scope

The open repository may contain:

- a vendor-neutral evidence manifest contract;
- generic collectors for public CI/test formats;
- integrity and reproducibility primitives;
- documentation, examples, tests, and integration glue;
- public governance and security processes.

## Out of scope

The repository must not contain or reconstruct:

- private AEGIS or AGR implementation code;
- proprietary policy engines, scoring logic, decision thresholds, or internal prompts;
- customer or partner data;
- private endpoints, credentials, tokens, or deployment secrets;
- internal codenames that reveal non-public architecture;
- code copied from private EZHAR repositories without an explicit release review.

## Review rule

A contribution that crosses the boundary is blocked even if it is technically useful. If a public feature needs concepts from a private system, contributors should define the smallest generic interface required by the open-source use case and implement it independently.

## Evidence rule

Examples and fixtures should be synthetic or derived from clearly redistributable public material. Claims in documentation should describe only behavior demonstrated by the public repository.
