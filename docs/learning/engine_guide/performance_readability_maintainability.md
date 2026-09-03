# Performance, Readability, and Maintainability Together

This page exists to prevent a common analytical mistake: evaluating a change along
only one dimension.

## A change can improve one axis and damage another

```text
faster but less readable
simpler locally but more coupled globally
more extensible but over-abstracted
more validated but slower in a hot path
more memory-efficient but harder to debug
```

Professional design is the search for a good **tradeoff**, not the maximum score on
one dimension.

## The repository's default priority

For the frozen kernel:

```text
semantic correctness
    > readability / maintainability
        > speculative micro-optimization
```

Performance still matters. The rule is that performance changes require evidence
and should target meaningful structural work without obscuring the orchestration
contract.

## When performance and readability align

Good examples include:

```text
remove repeated stable work
cache small immutable metadata
choose a direct dictionary lookup over repeated scanning
avoid unnecessary conversion/allocation
move static validation to preflight
```

These can make code both faster and conceptually cleaner.

## When they conflict

Suppose a benchmark suggests a 1% improvement from duplicating the stage algorithm
into four specialized loops.

Evaluate the total cost:

```text
runtime benefit:
    1%

maintenance cost:
    four paths must preserve simultaneity
    four paths must preserve RNG timing
    four paths must preserve telemetry/effects
    fixes/tests become duplicated
    source reading becomes harder
```

The performance gain may be real and still not be worth adopting.

## Maintainability is not free either

A maximally abstract, perfectly factored design can add call layers, objects,
registries, or indirection that have both cognitive and runtime cost.

Ask whether the abstraction represents a real variation point.

```text
real resolver policy variation -> useful abstraction
hypothetical universal LifecycleStrategyRegistryFactory -> probably not yet
```

## A review matrix

For a consequential change, write:

| Dimension | Before | After | Evidence |
| --- | --- | --- | --- |
| correctness |  |  | tests/invariant |
| semantics |  |  | contract/ADR |
| time complexity |  |  | analysis |
| memory |  |  | analysis/tracemalloc |
| measured runtime |  |  | profile/benchmark |
| readability |  |  | control-flow/naming review |
| maintainability |  |  | path/change-radius review |
| extensibility |  |  | demonstrated variation |
| testability |  |  | focused-test impact |

Do not invent quantitative scores for subjective dimensions. The table forces the
tradeoffs to be explicit.

## A stopping rule for optimization

Stop when:

```text
measured structural hotspots are gone
remaining gains are tiny/noisy
proposed changes add disproportionate complexity
or the dominant cost has moved to another layer
```

That is not complacency. It is optimization discipline.

## Transferable lesson

The mature question is not:

> Can I make this code faster?

It is:

> What problem is dominant at the scale we care about, and what is the smallest
> evidence-backed change that improves it while preserving correctness and keeping
> future change understandable?
