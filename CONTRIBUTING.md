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
- non-goals;
- architectural constraints;
- proposed public contracts when relevant;
- acceptance criteria;
- required tests/documentation;
- performance considerations;
- dependencies/blockers.

Resolve shared public contracts before parallelizing dependent implementation.

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
- the protected GitHub Actions quality gate is green on the exact PR head;
- the PR is squash-merged; and
- `main` is verified at the resulting merge SHA.

Keep the protected status-check name compatible when reorganizing CI unless the
repository rule is deliberately updated as part of the same operational change.
