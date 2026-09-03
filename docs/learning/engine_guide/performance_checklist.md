# Performance Review Checklist

```text
[ ] Is there a real performance problem at target scale?
[ ] Workload reproducible/comparable?
[ ] Correct layer profiled?
[ ] Scale variables and complexity understood?
[ ] Dominant path identified empirically?
[ ] Algorithm/data structure considered before interpreter tricks?
[ ] Repeated stable work/allocation identified?
[ ] RNG/order/state-visibility semantics preserved?
[ ] Readability/maintenance cost evaluated?
[ ] Focused tests protect behavior?
[ ] Comparable before/after benchmark exists?
[ ] Improvement is large enough to justify the change?
[ ] Stop rule considered after hotspot removal?
```
