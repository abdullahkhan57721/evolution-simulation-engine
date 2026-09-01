# 0005 — Use the repository as durable collaboration memory

- **Status:** Accepted
- **Date:** 2026-09-01
- **Supersedes:** —
- **Superseded by:** —

## Context

Development increasingly involves ChatGPT Chat, GitHub-connected agents, and
Codex. Long conversational transcripts have finite context windows, may be
interrupted, and are poor authoritative records for architecture and dynamic
implementation status. Reconstructing state from chat history wastes time and
creates opportunities for stale assumptions.

## Decision

The repository and GitHub workflow are the durable collaboration memory.
Information is separated by lifetime and purpose:

- `AGENTS.md` stores concise durable working rules for agents/contributors.
- `docs/architecture/` and subsystem docs describe current architecture.
- `docs/decisions/` preserves rationale for major settled choices.
- GitHub Issues define current milestone scope, non-goals, acceptance criteria,
  and dependencies.
- Pull requests are live implementation/recovery checkpoints.
- Tests, architecture contracts, and CI encode executable invariants.

Long-running implementation should open a PR early and keep a recovery checkpoint
current so another agent can continue from repository state without requiring the
originating chat transcript.

When repository state and conversation memory disagree, inspect current `main`,
its tests/CI, and current authoritative documentation rather than assuming the
conversation is newer or correct.

## Alternatives considered

- **Maintain one giant project-context document.** Rejected because mixed durable
  rules, architectural facts, and dynamic task status become stale at different
  rates and are difficult to review.
- **Use a separate GitHub Wiki as the main memory.** Rejected as the primary
  source because wiki content is easier to let drift independently of code and
  PR review. A wiki may still be used for external/user-facing material, but
  versioned repository docs are authoritative for engineering.
- **Rely on ChatGPT Project memory.** Rejected as the sole source because coding
  agents and other contributors need context that travels with the repository
  and changes atomically with code.

## Consequences

- Fresh chats and agents should need substantially less historical transcript.
- Issue and PR descriptions become more important and should be kept accurate.
- Architectural decisions and workflow changes must update their authoritative
  repository documents in the same PR.
- Some lightweight documentation maintenance is required, but duplicated context
  should decrease.
- Chat remains useful for architecture and discussion; Codex can consume the same
  repository-level rules for implementation.

## References

- `AGENTS.md`
- `docs/architecture/index.md`
- `.github/ISSUE_TEMPLATE/`
- `.github/pull_request_template.md`
- Issue #77
