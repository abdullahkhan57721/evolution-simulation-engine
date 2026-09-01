# Architecture Decision Records

Architecture Decision Records (ADRs) preserve the rationale for major decisions
that future contributors are likely to reconsider. They complement current
architecture documentation: docs describe what the system is now; ADRs explain
why consequential choices were made.

## When to write an ADR

Write an ADR when a decision:

- changes a public architectural contract or durable dependency direction;
- chooses among multiple plausible designs with meaningful tradeoffs;
- is likely to be reopened later unless the original rationale is recorded; or
- establishes a project-wide engineering policy with architectural consequences.

Do not create ADRs for routine refactors, naming changes, isolated bug fixes, or
implementation details that can be understood directly from code/tests.

## Lifecycle

Use these statuses:

- **Proposed** — under active design discussion.
- **Accepted** — current decision.
- **Superseded** — replaced by a newer ADR.
- **Rejected** — considered and deliberately not adopted.

Accepted ADRs are historical records. If the decision changes, create a new ADR
and mark the old one as superseded rather than rewriting the old rationale.

## Format

Copy `_template.md` to the next numbered filename:

```text
NNNN-short-decision-title.md
```

Keep an ADR concise. Link to detailed architecture docs, issues, PRs, tests, and
benchmarks rather than duplicating them.

## Current decisions

- [0001 — Keep the simulation kernel domain-neutral](0001-domain-neutral-kernel.md)
- [0002 — Preserve stage simultaneity with materialize-before-apply](0002-stage-simultaneity.md)
- [0003 — Own transactional state and randomness in SimulationState](0003-transactional-state-and-rng.md)
- [0004 — Prefer readability before micro-optimization](0004-readability-before-micro-optimization.md)
- [0005 — Use the repository as durable collaboration memory](0005-repository-collaboration-memory.md)
