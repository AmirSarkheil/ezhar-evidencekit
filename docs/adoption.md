# Adoption plan

EvidenceKit should earn adoption through utility and reproducibility rather than promotional claims.

## Phase 1 — Private dogfooding

Use the tool on its own repository and at least one independent synthetic example. Preserve generated CI artifacts and failure cases as engineering evidence.

## Phase 2 — Public maintainer usability

After the release gate is satisfied:

- publish a five-minute quickstart;
- provide a minimal repository example and a pytest/JUnit example;
- document GitHub Actions integration with immutable pins;
- make issue templates and contribution rules easy to follow;
- answer early maintainer questions with reproducible examples.

## Phase 3 — Independent integrations

Prioritize integrations only when a real maintainer need exists. Candidate formats include additional test reports and CI metadata, but the core manifest should remain vendor-neutral.

## Signals to track

Useful adoption signals include:

- independent repositories producing valid manifests;
- repeat users across multiple releases;
- external issues or pull requests with reproducible cases;
- references to the schema or action by maintainers;
- successful verification of evidence generated on a different machine or runner.

Stars, impressions, and announcement reach may be observed, but they are not substitutes for independent use.
