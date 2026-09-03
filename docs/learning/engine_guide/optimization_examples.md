# Optimization Examples: Classify the Risk

Classify each proposed optimization before deciding whether to implement it.

## A. Cache event-type dispatch metadata at stage construction

```text
Classification: structurally safer
Why: stable configuration moved out of repeated per-event path
Semantic risk: low if metadata truly cannot change
Evidence needed: profile shows repeated discovery matters
```

## B. Materialize proposals before resolution

```text
Classification: semantics-sensitive
Why: rejected candidates perform deferred work and may consume RNG
Semantic risk: high
Decision: reject unless stage contract itself is deliberately redesigned
```

## C. Skip transactional domain copy and mutate authoritative state directly

```text
Classification: architecture-changing / semantic
Why: rollback and RNG/state atomicity disappear
Decision: not a performance refactor; would require a new transaction architecture
```

## D. Add a second no-validation `SimulationState` constructor

```text
Classification: maintenance-sensitive constant-factor optimization
Potential benefit: less setup work per copy
Cost: second invariant/construction path
Current repository lesson: measured constructor-validation cost was too small to justify it
```

## E. Store resolver membership in a set rather than repeatedly searching a list

```text
Classification: potentially structurally safe data-structure change
Questions: does order matter? are elements hashable? does memory increase matter?
Evidence: analyze frequency/scale and benchmark if relevant
```

## F. Cache an evolving biological characteristic for an entire run

```text
Classification: semantics-sensitive
Risk: cached value may depend on mutable state/environment/history
Decision: only safe if contract proves stability for cache lifetime
```

## G. Stream observation records instead of retaining all raw records in memory

```text
Classification: observation/experiment design change
Benefit: lower retained memory
Questions: are later analyses dependent on in-memory raw history? can export preserve required data?
Kernel impact: none unless a genuine generic observation deficiency exists
```
