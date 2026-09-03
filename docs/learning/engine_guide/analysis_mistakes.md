# Common Analysis Mistakes

```text
Calling the whole engine O(n) without defining n.
Treating arbitrary callbacks as constant-time because they are one method call.
Ignoring allocation/lifetime when discussing space.
Calling code hot because it is inside a loop without profiling/frequency data.
Using end-to-end biology profiles to claim kernel-only cost.
Optimizing startup work while per-event/domain work dominates.
Assuming caching is safe without a stability guarantee.
Equating fewer lines with better readability.
Equating more abstraction with better maintainability.
Using observers to repair invalid state after commit.
Changing stage/RNG semantics for a microbenchmark win.
Treating historical timing numbers as permanent properties.
```

Use the review worksheets to catch these systematically.
