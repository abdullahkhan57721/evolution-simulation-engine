# Example: Complexity Versus Measurement

Imagine two versions of per-event telemetry creation.

```text
Version A: O(1) per event, 20 Python operations
Version B: O(1) per event, 12 Python operations
```

Across `R` events both are O(R).

A profiler/benchmark may still show B materially faster because the constant work
per event fell.

Now imagine a startup validator:

```text
O(V + E) configuration traversal
```

that runs once and consumes 2 ms.

It can have a more complex asymptotic expression while being irrelevant to a
multi-minute simulation.

The lesson:

```text
complexity class
+ scale
+ frequency
+ constant cost
+ allocation
+ measurement
```

all contribute to practical performance reasoning.
