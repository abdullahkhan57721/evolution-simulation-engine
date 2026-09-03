# When to Optimize

Use this short rule set when performance pressure appears.

```text
1. Notice obvious scaling hazards during design.
2. Build/identify a reproducible representative workload.
3. Profile the layer that owns the measured cost.
4. Prefer algorithm/data-structure improvements and removal of repeated work.
5. Measure allocations when memory/object creation is the suspected cost.
6. Preserve semantic tests before and after.
7. Benchmark comparable workloads.
8. Evaluate readability/maintenance cost.
9. Reject tiny gains that create disproportionate conceptual debt.
10. Stop when meaningful structural hotspots are gone.
```

Do not confuse "think about complexity early" with "micro-optimize early."
