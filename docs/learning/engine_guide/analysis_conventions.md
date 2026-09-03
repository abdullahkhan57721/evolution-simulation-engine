# Analysis Conventions

To keep complexity/performance notes consistent across the textbook, use these
conventions.

## Define variables locally

Never assume `N` always means population size. State it.

```text
P = processes
Q = proposals
R = accepted events
```

## Separate structural and delegated work

Prefer:

```text
O(P + Q + R) kernel overhead
+ resolver cost
+ process/materialization/application costs
```

instead of hiding arbitrary callbacks inside one Big-O.

## State memory lifetime

Prefer:

```text
O(Q) proposal references, stage-local
```

over merely:

```text
O(Q) memory
```

## Mark measured claims

Use words such as:

```text
measured hotspot
historical profile
synthetic kernel workload
reference end-to-end workload
```

Do not turn environment-specific milliseconds into permanent API facts.

## Distinguish optimization support from semantics

When reading production code, label:

```text
SEMANTIC
required for public behavior

SUPPORT
validation/diagnostics/type metadata

OPTIMIZATION
cache/layout/repeated-work reduction
```

An optimization may be removed or redesigned without changing semantics; a
semantic invariant may not.

## Treat complexity as a model

Asymptotic notation deliberately ignores many constants/runtime effects. Pair it
with profiling/benchmarking when practical performance matters.
