# Cost Model Example

Complexity statements depend on what operations you treat as unit cost.

Consider:

```python
for entity in entities:
    score(entity)
```

It is tempting to say O(N). That is only the loop overhead if `score(entity)` is
constant with respect to the variables you care about.

If `score()` scans `L` loci:

```text
O(NL)
```

If it compares every pair of loci:

```text
O(NL^2)
```

The same principle applies to the kernel:

```python
stage.coordinate(state)
```

is one method call syntactically, but its computational cost contains proposal,
resolver, materialization, application, and telemetry work.

Always make the hidden cost model explicit when it matters.
