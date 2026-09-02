# 0006 — Add concise orientation and rolling roadmap documents

- **Status:** Accepted
- **Date:** 2026-09-02
- **Supersedes:** —
- **Superseded by:** —

## Context

ADR 0005 established the repository and GitHub workflow as durable collaboration
memory and deliberately rejected one giant project-context document. That
separation remains correct: executable state, architecture, rationale, ticket
scope, and recovery status change at different rates and should not be collapsed
into one authority.

After adopting that workflow, the #84/#85 nonbiological-evolution pilot exposed a
smaller problem. A fresh ChatGPT/Codex session could reconstruct the repository
correctly, but doing so still required reading several PRs, architecture pages,
and active Issues merely to answer basic orientation questions such as:

- what major architectural capabilities are already established;
- what the current development front is;
- which known friction is intentionally unresolved; and
- what milestone dependency direction is currently expected.

The missing artifact is therefore not a new source of truth. It is a concise
navigation layer over the existing sources of truth.

## Decision

Maintain two lightweight development-orientation documents:

- `docs/development/current_state.md` answers **where the project is now**;
- `docs/development/roadmap.md` answers **where the project is going** at the
  milestone/architecture level.

They are subordinate to current `main`, tests, CI, authoritative subsystem and
architecture documentation, ADRs, active GitHub Issues, and active PR recovery
checkpoints.

`current_state.md` may summarize established capabilities, the current
architectural front, known unresolved friction, recent significant milestones,
and the collaboration model. It must not mirror volatile SHAs, CI status,
detailed ticket progress, or full history.

`roadmap.md` may summarize milestone ordering, architectural dependency direction,
and implementation-mode guidance. It must not replace GitHub Issues as the task
and status system.

Fresh agent orientation should normally follow:

```text
AGENTS.md
    ↓
current_state.md
    ↓
roadmap.md
    ↓
relevant architecture / ADRs
    ↓
active Issue / PR / tests / CI
```

Milestone PRs update the orientation/roadmap documents only when they materially
change the information those documents summarize.

## Relationship to ADR 0005

This decision refines rather than supersedes ADR 0005.

ADR 0005 rejected a **giant mixed-lifetime project-context document** and retained
GitHub/repository-native sources as authoritative. This ADR preserves that rule.
The new files are deliberately small indexes/summaries with explicit staleness and
authority boundaries.

## Alternatives considered

- **Continue with no orientation snapshot.** Rejected after the #84/#85 pilot
  because correct context reconstruction remained more expensive than necessary
  for fresh sessions.
- **Create one giant `Repo_Current_State.md` / prompt context pack.** Rejected for
  the same reasons recorded in ADR 0005: mixed lifetimes, duplication, and drift.
- **Store roadmap/status only in ChatGPT Project memory.** Rejected because Codex,
  other contributors, and future tooling need context that travels with and is
  reviewed alongside the repository.
- **Mirror active Issues and PR status into the new documents.** Rejected because
  GitHub already represents that information more accurately and mechanically.

## Consequences

- Fresh sessions should reach useful architectural context faster.
- The repository gains a small amount of deliberate documentation maintenance.
- Milestone PR review should consider whether `current_state.md` or `roadmap.md`
  materially changed, but trivial PRs should leave them alone.
- Drift risk is controlled by keeping the documents concise, subordinate, and
  free of volatile data.
- ADR 0005 remains the broader collaboration-memory decision; this ADR documents
  the narrower orientation refinement.

## References

- ADR 0005 — repository collaboration memory
- Issue #87
- PR #88
- Issue #84 / PR #85 — nonbiological vertical-slice pilot
- `AGENTS.md`
- `docs/development/current_state.md`
- `docs/development/roadmap.md`
