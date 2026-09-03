# Performance Misconception Checks

**"O(1) means cheap."**

No. It means cost does not asymptotically grow with the chosen input size. The
constant can be large, and the operation may execute extremely often.

**"If Big-O did not change, the optimization did nothing important."**

No. Constant work and allocation can materially affect hot paths while asymptotic
class remains unchanged.

**"The profiler tells me what architecture to change."**

No. It tells you where a workload spent time. Architectural attribution and design
still require reasoning.

**"The longest function is probably slowest."**

No. Runtime contribution depends on frequency and per-call cost.

**"Caching is always a safe optimization."**

No. Cached values must be semantically stable for the cache lifetime.

**"Observers are outside the simulation, so they are free."**

No. Observation can consume CPU, allocate objects, serialize data, and retain
history.

**"A startup O(n log n) operation is worse than a per-event O(n) operation."**

Not necessarily. Frequency and real scale matter.

**"A faster benchmark means better design."**

No. The workload must be comparable and the change must preserve correctness,
readability, and maintainability at an acceptable tradeoff.
