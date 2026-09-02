# Codex Ticket Workflow

This project uses ChatGPT Chat for consequential design/review and for
architecture-heavy or tightly scoped implementation. Codex is used selectively
for execution-heavy repository work behind sufficiently settled contracts.
GitHub is the durable handoff between them.

The goal is not to make Codex less capable. The goal is to choose the
implementation mode that minimizes total cycle time and user attention while
keeping work recoverable, reviewable, and constrained by settled architecture.

## Source of truth and orientation

Before coding, use this order:

1. current `main`, tests, and CI for executable reality;
2. root `AGENTS.md` for durable working rules;
3. `docs/development/current_state.md` for concise orientation;
4. `docs/development/roadmap.md` for milestone-level direction;
5. relevant architecture/subsystem docs and ADRs;
6. the active GitHub Issue for exact ticket scope;
7. the active PR for implementation/recovery state.

The orientation and roadmap files are navigation aids, not higher-trust copies of
GitHub state. Verify live scope/status/CI directly rather than assuming a snapshot
is current.

Do not rebuild project context from a long chat transcript when repository state
can answer the question directly.

## Choosing ChatGPT versus Codex

Use ChatGPT Chat primarily when work is:

- architecture-heavy or design-sensitive;
- a consequential shared/public-contract decision;
- tightly scoped and sequential;
- likely to benefit strongly from the current design conversation;
- a small refactor or implementation where direct interactive iteration is
  faster;
- independent architectural review or merge judgment.

Use Codex selectively when work is:

- execution-heavy behind settled interfaces;
- broad, repetitive, or migration-oriented;
- a large test/fixture/documentation matrix after the architecture is fixed;
- validation/debug-cycle intensive;
- independently parallelizable with low shared-surface risk;
- valuable to run unattended while other design work continues.

Do not hand a consequential unresolved API question to Codex and ask it to settle
the architecture implicitly while coding. Do not delegate merely because a
change is substantial. Optimize for total time to a correct merged change, not
for agent wall-clock coding time in isolation.

A useful hybrid is to settle and implement the canonical/representative path in
Chat, then delegate a broad mechanical migration or analogous test expansion to
Codex.

## When a ticket is Codex-ready

An implementation Issue is ready for Codex when it states:

- the concrete goal and motivation;
- dependencies/blockers;
- expected or allowed files/packages/systems;
- areas that should not be touched;
- implementation requirements;
- non-goals;
- relevant architectural constraints and settled public contracts;
- important ownership/mutability semantics for reused contracts when they are not
  obvious;
- likely wrong interpretations or traps when a locally plausible implementation
  could violate architecture;
- verifiable acceptance criteria;
- targeted/quality-gate validation; and
- ticket-specific manual verification, or an explicit reason it is not
  applicable.

Before implementing against an existing public Protocol/model, inspect its actual
declaration, docstring, and focused tests. Do not infer argument ownership,
mutability, or semantics from parameter names alone.

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

## Reusable Codex kickoff prompt

A normal implementation handoff can be short because the durable rules already
live in the repository:

```text
Implement GitHub Issue #NN only.

Before coding:
1. Read the root AGENTS.md.
2. Read docs/development/current_state.md and docs/development/roadmap.md.
3. Read Issue #NN completely.
4. Read the relevant architecture/subsystem docs, ADRs, public contract
   declarations, focused tests, and nearby examples.
5. Verify the current branch/base and repository state rather than relying on
   prior-chat assumptions.

Respect the Issue's expected/allowed areas and do-not-touch boundaries. Do not
implement future-ticket features, perform unrelated refactors, or add unnecessary
dependencies. If the correct solution requires scope expansion, explain why in
the Issue or PR and keep it minimal.

Do not infer public-contract ownership or mutability semantics from parameter
names alone; inspect the actual declarations/docs/tests before using them.

Open a draft PR early enough to serve as a recovery checkpoint and keep its
Recovery checkpoint current. Use focused checks while developing. Before calling
the PR review-ready, apply safe fixes/formatting with ./scripts/fix, run
./scripts/check_all --no-pause when practical, and require the complete protected
GitHub Actions gate to be green.

Do not weaken tests, architecture checks, coverage, complexity, kernel contracts,
or performance guards merely to make CI pass.

Record out-of-scope findings as follow-ups rather than silently fixing them.
Before stopping, update the PR with the checks actually run, manual-verification
result, documentation impact, risks/follow-ups, and current recovery checkpoint.
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

If the milestone materially changes project orientation or roadmap direction,
update `current_state.md` and/or `roadmap.md` in the same PR. Do not update them
for trivial maintenance or copy volatile SHAs/CI state into them.

## Manual verification

Automated tests and CI remain the primary correctness checks. Manual verification
is a small ticket-specific sanity check for behavior that is useful to observe as
a user/contributor rather than merely infer from a green build.

See [Manual Verification](manual_verification.md) for reusable guidance.

## Recovery after interruption

If a Codex or Chat session is interrupted, start from the repository rather than
reconstructing the old conversation. A useful recovery prompt is:

```text
Continue PR #NN. Read AGENTS.md, current_state.md, roadmap.md, the linked Issue,
relevant docs/ADRs, the PR Recovery checkpoint, current diff, and latest CI
before making changes. Verify what remains and continue only the scoped
milestone.
```

## Review and merge

Two normal flows are valid.

Architecture-heavy / tightly scoped work:

```text
Chat design
    ↓
Issue + branch
    ↓
Chat implementation
    ↓
PR + focused checks + protected CI
    ↓
independent review
    ↓
exact green head
    ↓
squash merge
    ↓
verify main
```

Execution-heavy delegated work:

```text
Chat settles architecture
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

## What we intentionally do and do not maintain

We intentionally maintain two concise navigation aids:

- **`current_state.md`** — a few-minute orientation snapshot of established
  capabilities, current architectural front, known friction, and recent
  milestones;
- **`roadmap.md`** — milestone-level architectural direction and dependency
  ordering.

They are deliberately subordinate to live repository/GitHub truth and must not
become giant mixed-lifetime context packs.

Several apparently useful documents remain deliberately represented by GitHub
and existing versioned docs instead:

- **`Tickets.md`** — GitHub Issues are the ticket system and preserve status,
  links, discussion, dependencies, and PR closure.
- **`Known_Issues_And_Followups.md`** — follow-ups belong in GitHub Issues; the
  PR links discoveries to those Issues.
- **`Prompt_Context_Pack.md`** — there is no giant prompt pack; orientation is
  `AGENTS.md` + `current_state.md` + `roadmap.md`, followed by the active Issue,
  relevant docs/ADRs/tests, and current PR.
- **A separate design-update companion** — when a contract changes, update its
  authoritative architecture/subsystem documentation in the same PR.
- **One giant full-design document** — use the architecture index, focused
  subsystem docs, ADRs, and the concise orientation/roadmap aids so information
  can change at the correct lifetime.

This keeps durable rules, current architecture, historical rationale, rolling
orientation, roadmap direction, dynamic work state, and executable truth
separate while reducing fresh-session reconstruction cost.
