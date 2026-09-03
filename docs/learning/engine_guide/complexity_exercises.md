# Complexity and Performance Exercises

Do these after the conceptual complexity chapter and before the final capstones.
Try each without running code first.

## 1. Proposal aggregation

A stage has `P` processes. Together they emit `Q` events. The coordinator stores
all proposals in one Python list.

Questions:

1. What is the kernel-side aggregation time, excluding proposal-generation work?
2. What extra list memory is retained?
3. Why is `O(P + Q)` more informative than `O(Q)`?

## 2. Opaque domain copy

A student writes:

> `SimulationState.copy()` is O(1) because it only calls a few methods.

Explain the error. Write the compositional time and memory expressions using
`C_domain_copy(N)` and `M_domain_copy(N)`.

## 3. Dispatch data structure

Suppose accepted event type → process dispatch is implemented by scanning all `P`
processes for every one of `R` accepted events.

1. What is the dispatch cost?
2. What is it with an average-O(1) dictionary lookup?
3. What stable memory/setup cost does the dictionary add?
4. Is this a reasonable time-space tradeoff?

## 4. Resolver algorithms

Compare:

```text
Resolver A: return proposals in their current order.
Resolver B: sort all proposals by score.
```

For `Q` proposals, give the likely complexity classes. Explain why
`StageCoordinator` itself should not claim one universal resolver complexity.

## 5. Materialization timing

There are 100,000 proposals, 500 accepted events, and each materialization costs
approximately the same amount.

Compare materialization work if it happens:

```text
A. before resolution for every proposal
B. after resolution only for accepted events
```

Then explain why the decision is primarily semantic even though the performance
difference may be large.

## 6. Constant-time hotspot

`AppliedEvent` construction is O(1) per event.

Explain how it can still be a measurable hotspot. What information besides Big-O
do you need?

## 7. Memory lifetime

Classify each structure by approximate lifetime:

```text
SimulationContext
working domain copy
proposal list
prepared applications
last StepTelemetry
recorder storing every full population snapshot
```

Which can create long-run memory growth?

## 8. Observer retention

A population has approximately `N = 50,000` entities for `T = 10,000` steps.
An observer stores a full O(N) snapshot every step.

What is the asymptotic historical memory growth? Why might aggregate summaries or
streaming be considered?

## 9. Wrong-layer optimization

An end-to-end profile says:

```text
60% spatial neighbor search
20% genetics/development
8% observation
5% kernel
7% other
```

Someone proposes hand-optimizing `SimulationContext.require()` first because its
uncached lookup is O(K).

Review the proposal.

## 10. Scaling thought experiment

A mate-search algorithm compares every eligible organism with every other eligible
organism.

If eligible population grows from 1,000 to 10,000, approximately how does pair
work scale? What kinds of domain-preserving algorithm/data-structure improvements
would you investigate before touching the kernel?

## 11. Benchmark validity

Two benchmark runs use different random seeds. Run B finishes 20% faster but also
commits 35% fewer events.

Can you conclude the implementation is faster? What would a stronger comparison
control?

## 12. Readability tradeoff

A refactor reduces stage runtime by 0.7% in a controlled microbenchmark but creates
three specialized stage loops.

List the semantic/maintenance questions that must be answered before accepting it.
What repository policy is relevant?

## 13. Context cache

There are `K` context values and `C` typed keys used repeatedly.

Explain the likely time-space behavior of:

```text
first uncached typed lookup
later cached typed lookup
cache storage
```

Why might the current tuple+cache design still be reasonable even if a dictionary
could make every initial lookup average O(1)?

## 14. Change radius

Which likely has the larger maintenance impact?

```text
A. rename a private local helper
B. change Process.apply_event() public semantics
```

List the surfaces you would inspect for B.

## 15. Multi-lens review

Pick one kernel function and fill out:

```text
Responsibility:
Semantic invariant:
Scale variables:
Structural time:
Delegated costs:
Memory size + lifetime:
Frequency:
Measured-hot evidence:
Readability:
Maintainability:
Extensibility:
Testability:
Optimization boundary:
```

Do not choose `StageCoordinator` the first time; use `Simulation`,
`SimulationEngine`, or `SimulationContext` so you practice transferring the method.
