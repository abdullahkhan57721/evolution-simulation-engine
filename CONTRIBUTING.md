# Contributing

The Evolution Simulation Engine uses a recoverable, issue-driven development
workflow. The goal is that another contributor or agent can understand and
continue substantial work from GitHub without needing the chat or terminal
session that started it.

Read `AGENTS.md` first for the durable architecture and development rules.

## Before implementation

For substantial work, create or identify a GitHub Issue. Prefer the repository's
Issue forms so the brief includes:

- goal and motivation;
- dependencies/blockers;
- expected or allowed files/packages/systems;
- explicit do-not-touch boundaries;
- implementation requirements;
- non-goals;
- architectural constraints;
- proposed public contracts when relevant;
- acceptance criteria;
- required automated tests/documentation/performance evidence; and
- ticket-specific manual verification, or an explicit reason it is not
  applicable.

Resolve shared public contracts before parallelizing dependent implementation.

For Codex-specific handoff guidance and the reusable kickoff prompt, see
`docs/development/codex_workflow.md`.

## Scope and follow-ups

Implement one Issue at a time. Do not silently implement future-ticket features,
perform unrelated refactors, or add unnecessary dependencies.

If a correct implementation genuinely must leave the Issue's expected/allowed
areas, keep the expansion minimal and explain it in the Issue or PR. If you find
a worthwhile problem that is outside the current scope, record it in the PR's
**Risks / follow-ups** section and create or link a follow-up GitHub Issue rather
than folding the work into the current milestone.

GitHub Issues are also the canonical known-issues/ticket system; do not maintain a
parallel static backlog file that can drift from GitHub.

## Branch and pull request

Create a focused branch from current `main` and open a pull request early once a
coherent implementation direction exists. The PR is a live recovery checkpoint,
not only a final review artifact.

Keep the PR template's recovery fields current during long work:

```text
Implemented:
Remaining:
Current blocker:
Last verified head:
Last CI result:
Next action:
```

If a session is interrupted, the next contributor should inspect the Issue, PR,
latest commit, and latest CI run before asking for historical reconstruction.

Before review, the PR should also record the commands/checks actually run,
manual-verification result, documentation impact, and known risks/follow-ups.
The Git diff remains the authoritative changed-file inventory.

## Local environment

The repository uses Python 3.12+ and a project-root virtual environment named
`venv`.

```bash
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e ".[dev,docs]"
venv/bin/python -m pip install -r requirements-performance.txt
```

Apply safe automatic fixes/formatting with:

```bash
./scripts/fix
```

Run the routine local quality gate with:

```bash
./scripts/check_all --no-pause
```

The routine gate includes Ruff, Pyright, Import Linter, focused Kernel Contracts,
Complexipy, pytest with coverage, and strict MkDocs. GitHub Actions additionally
runs the repository's performance/profile regression checks and uploads their
artifacts.

## Focused commands

```bash
./scripts/lint
./scripts/typecheck
./scripts/architecture
./scripts/kernel_contracts
./scripts/complexity
./scripts/coverage
./scripts/docs
```

Use focused tests while developing; use the complete gate before merge.

## Manual verification

A green build is necessary but does not always demonstrate that the intended
public workflow is usable. Each implementation Issue therefore includes a short
manual-verification plan, or explicitly states why no meaningful manual check
exists.

The PR records what was actually observed. Keep manual checks small and
reproducible; important deterministic behavior should still be protected by
automated tests. See `docs/development/manual_verification.md`.

## Architecture changes

Before changing a public contract or durable dependency direction:

1. read `docs/architecture/index.md`;
2. inspect relevant ADRs under `docs/decisions/`;
3. inspect the executable architecture tests/contracts that protect the current
   boundary;
4. decide whether the new choice warrants an ADR;
5. update code, tests, and authoritative documentation in the same PR.

The simulation kernel is currently frozen/maintenance-mode architecture. Read
`docs/kernel_contract.md` before changing generic orchestration.

## Performance changes

Do not trade readability for speculative speed. Profile first. Use synthetic
kernel measurements for kernel claims and reference-scenario profiles for
integration/domain performance. Do not weaken an existing performance guard
merely to make CI pass.

## Merge

A milestone is complete only when:

- its acceptance criteria are satisfied;
- relevant tests and docs are updated;
- required manual verification is completed or explicitly not applicable;
- known out-of-scope findings are recorded as follow-ups rather than hidden scope
  expansion;
- the protected GitHub Actions quality gate is green on the exact PR head;
- the PR is squash-merged; and
- `main` is verified at the resulting merge SHA.

Keep the protected status-check name compatible when reorganizing CI unless the
repository rule is deliberately updated as part of the same operational change.
