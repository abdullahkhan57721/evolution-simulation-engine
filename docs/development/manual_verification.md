# Manual Verification

Automated tests, static analysis, architecture checks, and CI are the primary
correctness mechanisms for this project. Manual verification is a small,
ticket-specific sanity check that confirms useful observable behavior rather than
merely trusting that a build passed.

Every implementation Issue should state a manual verification plan. When there is
no meaningful manual check beyond the automated suite, write `Not applicable`
and explain why.

## What a useful manual check contains

Keep the verification short and reproducible:

1. **Scenario** — the user/contributor behavior being exercised.
2. **Command or action** — the exact command, example, or inspection step.
3. **Expected result** — what should be observable if the ticket works.
4. **Observed result** — record the actual outcome in the PR.

Do not turn manual verification into a second full QA suite. If a behavior is
important and deterministic enough to protect automatically, add a test instead.

## Common verification patterns

### Public API or configuration changes

Exercise the new public path with the smallest realistic example or existing
example script. Confirm the documented inputs work and invalid inputs fail in the
intended way.

Prefer a regression test for detailed edge cases; the manual check should answer
whether the feature is usable through its intended public surface.

### Deterministic simulation behavior

Run a small fixed-seed scenario that exercises the ticket. Confirm the relevant
observable invariant, event sequence, or summary outcome. Do not encode a large
snapshot merely because it is easy to compare; protect only behavior that is
actually contractual.

### Checkpoint, export, or persistence behavior

Perform a small round trip:

```text
create/run
→ save/export
→ load/import/resume
→ inspect the restored or emitted result
```

Confirm that the artifact can be consumed through the intended public workflow
and that the meaningful state is preserved.

### Examples or command-line workflows

Run the affected example/command from the repository root using the documented
environment. Confirm it exits successfully and produces the intended visible
result without unexpected tracebacks or warnings.

### Documentation changes

Run `./scripts/docs` and, when the change is presentation-sensitive, inspect the
rendered page/navigation. Strict MkDocs proves the site builds; visual inspection
can catch confusing layout, broken reading order, or an unintentionally buried
page.

### Packaging or installation changes

Use a clean temporary virtual environment when the ticket changes packaging,
dependency declarations, or installation instructions. Install the project using
the documented command and verify the intended import/entry point.

### Performance changes

Use the benchmark/profile appropriate to the claimed layer. Compare against the
relevant baseline and record the evidence in the PR. A faster result is not by
itself sufficient if the change makes the architecture harder to understand; the
repository's readability-first rule still applies.

For generic kernel claims, use the domain-neutral synthetic kernel benchmarks.
Reference-ecology timings are integration signals and include domain costs.

## Manual verification in Issues

A useful ticket section looks like:

```text
Manual verification:
1. Run examples/<relevant_example>.py with the fixed seed from the ticket.
2. Confirm the new public behavior is observable.
3. Confirm the prior neighboring behavior still works.
4. Record the observed result in the PR.
```

If there is no meaningful manual scenario:

```text
Manual verification:
Not applicable — this is an internal refactor with no intended observable
behavior change, and the affected contract is fully covered by the targeted
regression tests and quality gate.
```

## Manual verification in PRs

The PR should record what was actually done, not merely repeat the Issue plan.
For example:

```text
Manual verification:
- Ran: venv/bin/python examples/example.py
- Expected: fixed-seed run completes and emits the new summary field.
- Observed: completed successfully; summary field present with the expected type
  and no new warnings.
```

If the plan changed during implementation, explain why.

## Relationship to the quality gate

Manual verification does not replace any required automated check. Before merge,
the relevant focused tests and the complete protected GitHub Actions gate must
still pass on the exact reviewed head.
