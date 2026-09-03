# Performance Evidence Hierarchy

Use progressively stronger evidence for progressively more consequential changes.

```text
1. Complexity reasoning
   identifies potential scaling hazards

2. Profile
   identifies measured runtime paths in a representative workload

3. Focused benchmark
   compares a specific implementation choice

4. Allocation measurement
   supports memory/object-creation claims

5. End-to-end validation
   confirms the change matters in realistic integration
```

Architecture-changing optimizations should also include strong semantic tests and
independent rationale. A microbenchmark alone is not sufficient evidence to change
a public execution contract.
