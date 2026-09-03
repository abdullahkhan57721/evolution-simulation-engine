# Reading Tests as Architecture

Focused tests are executable explanations of invariants.

## Recommended order

```text
1. Read the test name.
2. Identify setup that matters semantically.
3. Ignore fixture boilerplate on first pass.
4. Read the action under test.
5. Translate assertions into a plain-language promise.
6. Find production code enforcing that promise.
```

## Example style

A test that verifies two materializers both observe the pre-application state is
not merely checking values. It encodes:

```text
all accepted events materialize
before
any accepted event applies
```

That is architecture.

## Add an engineering lens

After extracting the invariant ask:

```text
What simpler implementation would fail this test?
What optimization could accidentally break it?
Does the test constrain ordering/RNG/state visibility?
Would a public-contract change require changing this test deliberately?
```

Tests are therefore both correctness evidence and a map of which optimizations or
refactors are semantically safe.
