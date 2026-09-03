# Review Workflows

This page turns the textbook into a practical workflow for code reading and PR
review.

## Reading an unfamiliar file

Use this order:

```text
1. Identify architectural layer.
2. Read the public contract or docstring.
3. Find the focused tests.
4. State the invariant in your own words.
5. Read the top-level control flow.
6. Separate essential semantics from support/optimization plumbing.
7. Mark inputs, outputs, mutation, and authority.
8. Define scaling variables.
9. Estimate structural time + memory lifetime.
10. Only then inspect low-level helpers and optimization details.
```

This usually works better than reading from line 1 to EOF.

## Reviewing a PR

Before approving, answer:

```text
What problem is being solved?
Which layer owns it?
What public contract changes?
What invariant could regress?
What tests prove the new behavior?
Does RNG/state visibility change?
What is the algorithmic cost at realistic scales?
What allocations/retention change?
Is measured performance evidence needed?
Does the implementation preserve readable control flow?
Does it create duplicate semantic paths?
Could the same goal fit behind an existing contract?
Are authoritative docs/ADRs updated when needed?
```

## Performance review workflow

```text
Observe a problem
    -> reproduce workload
    -> identify correct layer
    -> profile
    -> inspect algorithm/data structures first
    -> inspect repeated work/allocation second
    -> propose smallest clear change
    -> verify focused semantics tests
    -> benchmark comparable before/after
    -> reject if readability/maintenance cost outweighs value
```

## Architecture review workflow

```text
new behavior
    -> state scientific/domain meaning
    -> identify owning layer
    -> try existing contracts
    -> identify exact expressiveness/correctness gap
    -> create non-domain-specific statement of deficiency
    -> change lower contract only if gap remains real
```

## Debugging workflow

Before stepping:

```text
predict current state object
predict step/stage index
predict event phase
predict whether RNG should have advanced
predict whether mutation should have happened
```

At the breakpoint compare reality with the prediction. The mismatch is often more
informative than merely watching variables change.

## Maintenance review workflow

For a proposed refactor:

```text
Which concepts disappear?
Which concepts are added?
How many semantic paths exist before/after?
How wide is the change radius?
Are tests easier to localize?
Are dependencies more explicit?
Does the top-level algorithm become easier to see?
```

A refactor that reduces line count but increases hidden invariants may be a net
loss.
