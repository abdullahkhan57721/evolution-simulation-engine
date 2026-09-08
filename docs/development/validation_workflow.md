# Validation Workflow

The repository uses layered validation so development stays fast without weakening
the final merge standard.

## Principle

Use the cheapest check that can answer the current question, then escalate as a
change becomes a merge candidate.

```text
coherent implementation batch
        ↓
safe Ruff autofix + focused tests
        ↓
fast checkpoint gate
        ↓
complete local quality gate
        ↓
non-draft protected CI
        ↓
relevant release / cinematic / scientific validation
        ↓
exact-head review and squash merge
```

The layers differ in **cadence**, not in final quality expectations.

## Inner loop

After a coherent Python implementation batch:

```bash
./scripts/fix
./scripts/test <focused test paths>
```

`scripts/fix` applies Ruff's safe lint fixes and canonical formatting to the same
default repository scope verified by `scripts/lint`. It does not enable Ruff unsafe
fixes.

Focused tests should cover the behavior currently being changed. Do not repeatedly
run full coverage merely to answer a local implementation question.

## Fast checkpoint

Before an ordinary development push or meaningful recovery checkpoint, run:

```bash
./scripts/check_all --fast --no-pause
```

The fast gate runs:

- Ruff lint and formatting verification;
- Pyright;
- Import Linter;
- focused frozen-kernel contracts;
- Complexipy.

It intentionally omits full pytest coverage and strict MkDocs. Those remain part of
the final gate.

A draft pull request is a recovery checkpoint. GitHub Actions runs the equivalent
fast gate in one shared environment rather than launching the full merge matrix on
every draft synchronization.

## Final candidate

Once the Issue acceptance criteria are functionally complete:

```bash
./scripts/fix
./scripts/check_all --no-pause
```

Then update the PR completion/recovery report and mark the PR ready for review.
Ready-for-review and subsequent non-draft head changes run the complete protected
quality matrix:

- Ruff;
- Pyright;
- Import Linter;
- kernel contracts;
- Complexipy;
- pytest with line + branch coverage at the repository threshold;
- strict MkDocs;
- reference/kernel/world-presentation performance profiling.

The protected aggregate status-check name remains stable. A changed final candidate
head must become green again before merge.

## Release and cinematic validation

Release Smoke and Cinematic Smoke are final/integration checks rather than lint
loops. They run for relevant non-draft pull requests (and Release Smoke also verifies
`main`) instead of consuming every draft synchronization.

Do not use this cadence change to weaken what the smoke tests verify.

## Frozen scientific validation

B3 and E3-E7 validation should answer a scientific regression question: **could this
change alter the frozen simulation/evidence result?**

Their pull-request path filters therefore conservatively include modeled/scientific
source changes while excluding downstream-only UI, Workbench, presentation, and
cinematic source changes. They also include their owning experiment scripts and
workflow files.

Orientation/navigation-only changes such as:

- `docs/development/current_state.md`;
- `docs/development/roadmap.md`;
- `mkdocs.yml`;

must not rerun frozen scientific matrices merely because prose/navigation changed.
Strict MkDocs remains responsible for documentation integrity.

Scientific workflows run on relevant non-draft candidate heads. Their existing
frozen discovery/confirmation protocols, seed sets, numerical criteria, artifacts,
and bounded scientific claims remain unchanged.

## When to run more than the default cadence

Escalate earlier when evidence warrants it. Examples include:

- a shared kernel/process/resolver/observation change that could affect many tests;
- a dependency-boundary refactor;
- a change near the 90% coverage threshold;
- a measured performance concern;
- a scientific-model change whose failure would be expensive to discover late;
- a renderer change requiring real visual/manual verification.

The layered workflow is not permission to postpone obvious risk. It is a way to
avoid paying unrelated final-gate costs after every small edit.
