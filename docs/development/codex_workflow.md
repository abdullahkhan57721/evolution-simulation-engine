# Codex Ticket Workflow

This project uses ChatGPT Chat for consequential design/review and Codex for
scoped repository implementation. GitHub is the durable handoff between them.

The goal is not to make Codex less capable. The goal is to make implementation
recoverable, reviewable, and constrained by architecture that was decided before
coding began.

## Source of truth

Before coding, use this order:

1. current `main`, tests, and CI;
2. root `AGENTS.md`;
3. relevant architecture/subsystem docs and ADRs;
4. the active GitHub Issue for ticket scope;
5. the active PR for implementation/recovery state.

Do not rebuild project context from a long chat transcript when repository state
can answer the question directly.

## When a ticket is Codex-ready

An implementation Issue is ready for Codex when it states:

- the concrete goal and motivation;
- dependencies/blockers;
- expected or allowed files/packages/systems;
- areas that should not be touched;
- implementation requirements;
- non-goals;
- relevant architectural constraints and settled public contracts;
- verifiable acceptance criteria;
- targeted/quality-gate validation; and
- ticket-specific manual verification, or an explicit reason it is not
  applicable.

If a consequential shared contract is still unresolved, use an architecture or
design Issue first. Do not ask an implementation agent to decide a major public
architecture implicitly while coding.

## Scope discipline

Implement one Issue at a time.

Do not implement future-ticket features, refactor unrelated systems, or add a new
dependency merely because doing so would be convenient. The Issue's expected
areas are a scope boundary, not a trap: if the correct solution genuinely needs
to cross that boundary, keep the expansion minimal and record why in the Issue or
PR before or alongside the change.

When implementation uncovers a real problem outside the ticket scope, do not
silently fix it. Record it under **Risks / follow-ups** in the PR and create or
link a follow-up GitHub Issue when the finding merits future work.

## Reusable kickoff prompt

A normal implementation handoff can be short because the durable rules already
live in the repository:

```text
Implement GitHub Issue #NN only.

Before coding:
1. Read the root AGENTS.md.
2. Read Issue #NN completely.
3. Read the relevant architecture/subsystem docs, ADRs, and tests.
4. Verify the current branch/base and repository state rather than relying on
   prior-chat assumptions.

Respect the Issue's expected/allowed areas and do-not-touch boundaries. Do not
implement future-ticket features, perform unrelated refactors, or add unnecessary
dependencies. If the correct solution requires scope expansion, explain why in
the Issue or PR and keep it minimal.

Open a draft PR early enough to serve as a recovery checkpoint and keep its
Recovery checkpoint current. Use focused checks while developing. Before calling
the PR review-ready, apply safe fixes/formatting with ./scripts/fix, run
./scripts/check_all --no-pause when practical, and require the complete protected
GitHub Actions gate to be green.

Do not weaken tests, architecture checks, coverage, complexity, kernel contracts,
or performance guards merely to make CI pass.

Record out-of-scope findings as follow-ups rather than silently fixing them.
Bring the PR to a clean, green, review-ready state; leave final architectural
review and squash merge to the review workflow unless explicitly instructed
otherwise.
```

The exact prompt may be shorter once Codex reliably follows `AGENTS.md`; the Issue
and repository documents should carry the detailed context.

## PR completion report

The PR itself is the durable completion report. Before review, make sure it
contains:

- a concise summary of what changed;
- the architecture/public-contract impact, if any;
- commands/checks actually run and their results;
- ticket-specific manual verification and observed result, or an explicit
  `Not applicable` explanation;
- documentation updated or why no documentation change is needed;
- known risks and linked follow-up Issues; and
- a current recovery checkpoint with implemented work, remaining work, blocker,
  verified head, latest CI result, and next action.

Do not manually duplicate information Git already exposes reliably. The PR diff
is the authoritative file-change list; a separately maintained file inventory is
usually unnecessary.

## Manual verification

Automated tests and CI remain the primary correctness checks. Manual verification
is a small ticket-specific sanity check for behavior that is useful to observe as
a user/contributor rather than merely infer from a green build.

See [Manual Verification](manual_verification.md) for reusable guidance.

## Recovery after interruption

If a Codex or Chat session is interrupted, start from the repository rather than
reconstructing the old conversation. A useful recovery prompt is:

```text
Continue PR #NN. Read AGENTS.md, the linked Issue, relevant docs/ADRs, the PR
Recovery checkpoint, current diff, and latest CI before making changes. Verify
what remains and continue only the scoped milestone.
```

## Review and merge

The normal flow is:

```text
Chat / design review
        ↓
implementation-ready GitHub Issue
        ↓
Codex implementation
        ↓
draft PR + recovery checkpoint
        ↓
focused checks + protected CI
        ↓
independent Chat/reviewer architecture review
        ↓
exact green head
        ↓
squash merge
        ↓
verify main
```

For high-risk work, a separate reviewer may independently inspect the Issue,
architecture docs, PR diff, and tests without relying on the implementing agent's
private reasoning.

## Parallel Codex work

Parallelize implementation only after shared interfaces are settled. Good
parallel tasks have low shared-surface risk, such as independent tests,
documentation, benchmarks, or separate subsystems behind stable contracts.

Do not run multiple agents that simultaneously redesign the same public API or
foundational representation.

## Skills, hooks, and extra automation

Do not create a Codex skill, hook, or repository automation merely because it is
available. Add one after a repeated category of work demonstrates that a reusable
procedure would remove meaningful repetition without hiding important behavior.

## What we intentionally do not maintain

Several apparently useful documents are deliberately represented by GitHub and
existing versioned docs instead:

- **`Repo_Current_State.md`** — current `main`, active Issue/PR, commits, tests,
  and CI are more current and machine-verifiable than a manually refreshed state
  snapshot.
- **`Tickets.md`** — GitHub Issues are the ticket system and preserve status,
  links, discussion, dependencies, and PR closure.
- **`Known_Issues_And_Followups.md`** — follow-ups belong in GitHub Issues; the
  PR links discoveries to those Issues.
- **`Prompt_Context_Pack.md`** — the context pack is `AGENTS.md` + the active
  Issue + relevant docs/ADRs/tests + the current PR.
- **A separate design-update companion** — when a contract changes, update its
  authoritative architecture/subsystem documentation in the same PR.
- **One giant full-design document** — use the architecture index, focused
  subsystem docs, and ADRs so information can change at the correct lifetime.

This keeps durable rules, current architecture, historical rationale, dynamic
work state, and executable truth separate instead of allowing one large context
file to become stale.
