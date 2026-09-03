# The Performance Lens in One Page

For any runtime path:

```text
1. Define scale variables.
2. State structural complexity.
3. Keep delegated costs explicit.
4. Record memory growth + lifetime.
5. Record invocation frequency.
6. Distinguish theoretical hazard from measured hotspot.
7. Profile the correct architectural layer.
8. Prefer algorithm/data-structure/repeated-work improvements.
9. Benchmark comparable before/after workloads.
10. Reject gains that damage semantics/readability/maintainability disproportionately.
```

For any memory path:

```text
persistent state?
transaction copy?
stage temporary?
cache?
historical retention?
```

For any optimization:

```text
structurally safe?
semantics-sensitive?
architecture-changing?
```

That is the performance framework used throughout the textbook.
