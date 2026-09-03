# What to Ignore on the First Source Pass

When learning the kernel, do not give every line equal attention.

First-pass priority:

```text
public contract
method-level control flow
state ownership
mutation points
phase ordering
commit point
focused tests
```

Defer until the semantic skeleton is clear:

```text
generic variance details
qualified type-name helpers
cached metadata representation
minor validation helpers
private telemetry construction details
performance-specific tuple/cache layout
```

Those details matter, but understanding them before the architecture often makes
the code feel more complicated than it is.
