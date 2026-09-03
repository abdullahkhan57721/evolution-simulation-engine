# Evolution Simulation Engine — Agent Instructions

This file is the durable entry point for AI coding agents and other contributors.
Read it before making architectural or code changes. Keep it concise: detailed
technical knowledge belongs in the linked versioned documentation, not here.

## Mission

Build an extensible Python engine for evolutionary simulations with a fully
domain-neutral simulation kernel and layered domain semantics above it. The
kernel coordinates reproducible transactional state transitions; biological,
genetic, ecological, spatial, and other modeled meanings belong outside the
kernel.

The project should remain capable of growing toward richer genetics and sexual
reproduction rather than optimizing abstractions only for the simplest current
use cases.

## Source-of-truth hierarchy

When information disagrees, do not trust a long chat transcript over the
repository.

1. Inspect current `main`, tests, and CI for executable reality.
2. Use this `AGENTS.md` for durable collaboration and development rules.
3. Use `docs/architecture/` and current subsystem documentation for architecture.
4. Use `docs/decisions/` for the rationale behind settled major decisions.
5. Use the active GitHub Issue and PR for dynamic milestone status, scope, and
   recovery state.
6. Use `docs/development/current_state.md` and
   `docs/development/roadmap.md` as concise orientation/planning aids subordinate
   to the sources above.
7. Treat conversation summaries and old PR descriptions as secondary context.

If documentation appears stale relative to code, fix the documentation in the
same change rather than silently working around it.

## Fresh-session orientation

A fresh ChatGPT/Codex session should normally orient in this order:

1. read this `AGENTS.md`;
2. read `docs/development/current_state.md` for a concise snapshot of where the
   project is now;
3. read `docs/development/roadmap.md` for milestone-level direction;
4. read the relevant architecture/subsystem docs and ADRs;
5. read the active GitHub Issue and PR/recovery checkpoint;
6. verify any live fact that matters against current `main`, tests, CI, Issues,
   and PRs rather than trusting the snapshots blindly.

The orientation documents deliberately avoid volatile SHAs, CI state, detailed
ticket progress, and full history. They are navigation aids, not a replacement
for live repository truth.

## Architectural layers

The intended dependency direction is broadly:

```text
validation / context / generic foundations
                    |
                    v
             simulation kernel
                    |
                    v
         general evolution abstractions
                    |
                    v
      biological/domain specializations
                    |
                    v
        processes and resolvers
                    |
                    v
       presets / experiments / interfaces
```

The exact enforceable dependency boundaries live in `pyproject.toml`,
`.github/ARCHITECTURE_GUARDRAILS.md`, and focused architecture tests.

### Frozen simulation kernel

The kernel is complete for the current architecture and is in maintenance mode.
Its canonical contract is `docs/kernel_contract.md`.

Key vocabulary:

- `SimulationState`: kernel-owned transactional envelope.
- `domain_state`: opaque mutable modeled-domain payload.
- `SimulationContext`: immutable shared configuration/services.
- `event`: proposed/resolved/materialized transition.
- `effect`: opaque committed consequence optionally captured in telemetry.

A `StageCoordinator` preserves this semantic order:

```text
propose all
→ resolve
→ materialize all accepted events
→ apply accepted events
```

All processes in a stage propose from the same stage-start state. Do not change
this simultaneity contract as a convenience for one domain.

A kernel change needs evidence of a generic correctness, expressiveness,
diagnostics, isolation/determinism, or structural-performance need. Domain
convenience alone is not sufficient.

## Non-negotiable design rules

- Keep the simulation kernel domain-neutral.
- Do not leak organisms, genomes, reproduction, energy, spatial worlds, or other
  modeled-domain semantics into generic kernel APIs.
- Once `simulation_state.domain_state` is explicitly unwrapped by domain code,
  domain-native vocabulary such as `world` and `WorldState` is appropriate.
- Keep proposal, conflict resolution, event materialization, and application as
  distinct responsibilities.
- Preserve transactional state and RNG semantics. Simulation randomness comes
  from `SimulationState.rng`; do not introduce hidden independent generators for
  simulation decisions.
- Keep generic configuration/preflight generic. Domain validation belongs in the
  domain compiler/configuration layer.
- Prefer explicit composition and small contracts over magical synthetic
  attributes or implicit service lookup.
- Prefer readability and maintainability over micro-optimization. Optimize only
  after measurement, and use synthetic kernel benchmarks for kernel claims.
- Reference-ecology timings mix domain costs with kernel costs and are not a
  substitute for a domain-neutral kernel benchmark.
- Encode stable architectural invariants in tests or Import Linter whenever they
  can be checked mechanically.

## Python and code conventions

- Python: 3.12+; CI targets Python 3.12.
- Virtual environment directory: `venv`, never `.venv`.
- Formatting/linting: Ruff, line length 88.
- Static typing: Pyright.
- Cognitive complexity: Complexipy, maximum allowed complexity 15.
- Runtime model classes commonly use `attrs`; follow nearby established style.
- Public Python APIs should have present-tense Google-style docstrings.
- Favor readable procedural flow where it makes orchestration easier to follow.
- Keep validation close to the object/contract that owns the invariant.
- Add or update tests for architectural and behavioral changes.
- Avoid compatibility aliases during deliberate pre-1.0 atomic API migrations
  unless compatibility is an explicit milestone requirement.

## Repository navigation

Start with:

- `README.md` — user-facing overview.
- `docs/development/current_state.md` — concise current orientation.
- `docs/development/roadmap.md` — rolling milestone-level architectural direction.
- `docs/architecture/index.md` — architecture map and reading order.
- `docs/kernel_contract.md` — frozen kernel semantics.
- `docs/general_evolution_framework.md` — domain-neutral evolution layer.
- `docs/development/codex_workflow.md` — selective Codex handoff, scope, and
  recovery flow.
- `docs/development/manual_verification.md` — practical ticket-level verification.
- `.github/ARCHITECTURE_GUARDRAILS.md` — enforced dependency direction.
- `docs/decisions/` — major architectural decisions and rationale.
- `src/evo_engine/` — implementation.
- `tests/` — executable behavior and architecture contracts.
- `scripts/` — canonical development commands.

Generated architecture artifacts live under `docs/architecture/generated/`.
Do not hand-edit generated files when a generator owns them.

## Canonical development commands

Install development dependencies from the repository root:

```bash
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e ".[dev,docs]"
venv/bin/python -m pip install -r requirements-performance.txt
```

Apply safe automatic formatting/fixes before final verification:

```bash
./scripts/fix
```

Run the routine local quality gate non-interactively:

```bash
./scripts/check_all --no-pause
```

Useful focused commands:

```bash
./scripts/lint
./scripts/typecheck
./scripts/architecture
./scripts/kernel_contracts
./scripts/complexity
./scripts/coverage
./scripts/docs
```

GitHub Actions additionally runs the performance/profile regression checks and
uploads their artifacts. Do not weaken performance guards merely to merge a
change; investigate whether a regression is real first.

## Issue → branch → PR → merge workflow

Substantial work should be recoverable without the originating chat.

1. Create or identify a GitHub Issue before substantial implementation.
2. The Issue should state goal, why, dependencies, expected/allowed areas,
   do-not-touch boundaries, requirements, non-goals, architectural constraints,
   acceptance criteria, automated validation, and manual verification.
3. Create a focused branch from current `main`.
4. Make coherent commits and open a PR early rather than waiting until 90% of the
   work is complete.
5. Keep the PR's **Recovery checkpoint** current during long-running work.
6. Run targeted tests while developing.
7. Run the routine quality gate locally when practical.
8. Require the complete protected GitHub Actions quality gate to be green.
9. Squash-merge the exact reviewed/green head SHA.
10. Re-fetch and verify `main` after merge.
11. If the merged milestone materially changed architectural capability, the
    current development front, known friction, collaboration policy, or roadmap
    direction, update `docs/development/current_state.md` and/or
    `docs/development/roadmap.md` in that milestone rather than leaving them
    stale.

The protected GitHub status-check name is intentionally stable. When refactoring
CI, preserve branch-protection compatibility unless the repository rules are
updated deliberately in the same operational change.

## Ticket scope discipline

Implement one Issue at a time. Do not implement future-ticket features, refactor
unrelated systems, or add dependencies merely because doing so would be
convenient.

Treat the Issue's expected/allowed areas and do-not-touch list as explicit scope
guardrails. They are not permission to produce an incorrect solution: if the
correct implementation genuinely must cross a boundary, keep the expansion
minimal and record why in the Issue or PR before or alongside the change.

When work uncovers a real problem outside the ticket scope, do not silently fix
it. Record it in the PR's **Risks / follow-ups** section and create or link a
follow-up GitHub Issue when it merits future work.

Detailed Codex handoff guidance lives in `docs/development/codex_workflow.md`.

## ChatGPT and Codex allocation

ChatGPT Chat is the default place for consequential design and for implementation
when the hard part is architecture, the change is tightly scoped/sequential, or
the design conversation itself provides important context. Chat may implement
and carry such milestones through PR, CI, squash merge, and `main` verification.

Use Codex selectively when the work is primarily execution-heavy behind settled
interfaces: broad or repetitive migrations, large test matrices, validation and
debug cycles, independent parallel tasks, or work that benefits from unattended
repository iteration.

Do not delegate to Codex merely because a ticket is substantial. Optimize for
total cycle time, user attention, architectural correctness, and recoverability.
Shared public-contract decisions should be settled before handing mechanical
implementation to Codex.

## Recovery checkpoint protocol

For work that may span sessions, the PR description is the durable handoff.
Maintain these fields:

```text
Implemented:
Remaining:
Current blocker:
Last verified head:
Last CI result:
Next action:
```

A new agent should be able to continue from the Issue + PR + repository without
asking the user to reconstruct prior chat history.

## PR completion report

Before calling a PR review-ready, make the PR itself the completion report. It
should record:

- what changed and any architecture/public-contract impact;
- commands/checks actually run and their results;
- ticket-specific manual verification and observed result, or why it is not
  applicable;
- documentation updated or why none is needed;
- known risks and linked follow-up Issues; and
- the current recovery checkpoint.

Do not duplicate information Git already exposes reliably. The PR diff is the
authoritative list of changed files.

## Architecture decisions

Create an ADR only for a decision future contributors are likely to reconsider
and where the rationale matters. Do not create ADRs for routine implementation
choices.

Use `docs/decisions/_template.md`. Accepted ADRs are historical records: if a
major decision changes, add a new ADR that supersedes the old one rather than
rewriting history.

## Task decomposition and parallel work

Prefer small milestones with one coherent architectural purpose. Design shared
contracts before parallelizing dependent implementation.

Good parallel work has low shared-surface risk: independent tests, documentation,
benchmarks, or subsystems behind already-settled interfaces. Avoid running
multiple agents that simultaneously redesign the same public contract.

For high-risk architecture, an independent review agent may review the Issue,
ADR/docs, diff, and tests without relying on the implementing agent's private
reasoning.

## Documentation rule

Whenever a public contract, architectural boundary, development command, or
workflow changes, update its authoritative documentation in the same PR. Avoid
copying the same detailed rule into multiple files; link to the authoritative
source instead.

After a milestone materially changes a stable architecture, simulation,
evolution, biology, performance, or code-reading concept taught in
`docs/learning/engine_guide/`, update the relevant textbook chapter in the same
milestone/PR and keep it consistent with
`docs/learning/engine_guide/guide_spec.md`. Do not churn the textbook for
implementation details or refactors that do not change what a learner needs to
understand.

When a milestone materially changes current orientation or roadmap direction,
update the corresponding development snapshot in the same PR. Do not churn those
files for trivial maintenance or copy volatile GitHub state into them.

## Completion rule

Do not call a milestone complete merely because code was written. Completion
means the Issue's acceptance criteria are satisfied, relevant docs/tests are
updated, required manual verification is completed or explicitly not applicable,
the full protected quality gate is green, the PR is merged, and `main` is
verified at the resulting merge SHA.
