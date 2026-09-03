# Performance Case Studies from This Repository

This chapter uses a few stable lessons from the repository's performance work to
show how performance engineering differs from theoretical complexity analysis.
Exact historical wall-clock numbers are examples, not contracts.

> Authoritative performance policy and current measurement commands live in
> [Performance Measurement](../../performance.md).

## Case study 1 — Move stable repeated work out of a hot path

A recurring kernel optimization theme has been:

```text
stable discovery performed repeatedly per event
        ↓
measure that repeated work
        ↓
move discovery to construction/setup
        ↓
cache stable metadata
        ↓
keep one readable semantic path
```

Examples include caching event dispatch/materializer metadata and qualified type
names in `StageCoordinator` rather than rediscovering them for each accepted event.

### Complexity lesson

The asymptotic stage class can remain linear before and after while constant
per-event work drops.

### Maintainability lesson

The optimization is attractive because it does not create a parallel stage
algorithm. The semantic flow stays:

```text
propose -> resolve -> materialize-all -> apply
```

## Case study 2 — Do not optimize a tiny measured cost just because you can

`SimulationState.copy()` still constructs a normal validated state envelope after
copying the domain and cloning RNG state. Profiling found that constructor
validation itself was a small part of the fixed kernel workload.

A second trusted constructor could reduce that work.

The repository chose not to add it.

### Why?

```text
benefit:
    tiny measured saving

cost:
    second construction path
    another invariant boundary
    more maintenance burden
    more cognitive load
```

### Lesson

Performance engineering is not the search for every removable instruction. It is
the search for changes whose measured value justifies their total engineering
cost.

## Case study 3 — Allocation can remain a hotspot after structural cleanup

After repeated validation/dispatch overhead is reduced, real committed telemetry
still requires object allocation and field assignment.

`AppliedEvent` construction remains O(1) per event and O(R) across `R` committed
events.

That can still be a significant profile contributor because the operation happens
for every committed event.

### Lesson

```text
same Big-O
!=
same runtime
```

An O(1) per-event operation can be a hotspot at high frequency.

## Case study 4 — Dynamic semantics can limit caching

The optional domain effect journal is intentionally dynamic. The kernel reads the
current `effect_count` before each application.

A tempting optimization is:

> Check once whether the domain has a journal and cache the absence for the whole
> stage.

That could reduce repeated work, but it can violate the dynamic contract if journal
capability changes.

### Lesson

Before caching ask:

```text
Is the value genuinely stable for the cache lifetime?
Is stability guaranteed by the public contract?
Or does it merely happen to be stable in today's common domain?
```

Performance assumptions must not silently strengthen architecture contracts.

## Case study 5 — Avoid special-case algorithm multiplication

Another tempting optimization is separate stage algorithms for common cases:

```text
no materializers
with materializers
no effects
with effects
```

The repository explicitly resists this without strong evidence.

### Why?

Every additional path must preserve:

```text
proposal simultaneity
resolver semantics
accepted-only materialization
application order
telemetry correctness
effect behavior
error behavior
```

A tiny constant-factor speedup can create a large semantic maintenance surface.

### Lesson

Prefer one readable algorithm plus small measured optimizations until profiling
shows a structural reason to split paths.

## Case study 6 — Measure the correct layer

Reference-ecology profiles contain:

```text
kernel orchestration
+ biology
+ ecology
+ spatial work
+ observation (in observed scenario)
```

Therefore they cannot by themselves prove a kernel hotspot.

The repository maintains domain-neutral synthetic kernel scenarios specifically to
isolate generic orchestration costs.

### Lesson

A profiler tells you where **that workload** spent time. Correct attribution still
requires architectural reasoning.

## Case study 7 — Observability is computational work

The repository distinguishes reference scenarios with and without the complete
observation/telemetry stack.

Observation can add:

```text
runtime
allocations
historical retention
serialization/storage
```

But observation also adds scientific and diagnostic value.

### Lesson

The right question is not "can we remove observation to make it faster?"

Ask:

```text
Which observations are scientifically required?
Which histories must be retained?
Can data be aggregated or streamed?
What does the profile say the observation layer costs?
```

## Case study 8 — Reproducibility protects benchmark interpretation

Stochastic simulations can do different amounts of work if their outcomes differ.
Meaningful benchmark comparison therefore requires comparable configuration,
randomness, and outcome dimensions.

### Lesson

A faster result is not evidence of faster code when it processed a smaller or
different simulation.

Performance experiments need the same discipline as scientific experiments.

## A reusable performance-review template

```text
Claimed problem:
____________________________________

Workload/scenario:
____________________________________

Correct architectural layer:
____________________________________

Scaling variables:
____________________________________

Profile evidence:
____________________________________

Algorithmic issue or constant-factor issue?
____________________________________

Allocation/memory evidence:
____________________________________

Proposed change:
____________________________________

Semantic risks:
____________________________________

Readability/maintenance cost:
____________________________________

Before/after measurement:
____________________________________

Would I accept the tradeoff?
____________________________________
```

## Central performance principle

```text
reason about scaling early
profile before implementation tuning
improve algorithms/repeated work first
measure comparable workloads
preserve semantic contracts
keep readability and maintainability as constraints
stop when the remaining opportunity is not worth the complexity
```
