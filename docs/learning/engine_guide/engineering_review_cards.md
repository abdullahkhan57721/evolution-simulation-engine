# Engineering Review Cards

This page is a compact companion to the source walkthrough. It is intentionally
redundant with deeper chapters so you can keep one page open while reading code.

For complete explanations, use
[Computational Complexity and Performance Thinking](computational_complexity.md)
and [Engineering Anatomy of the Kernel](kernel_engineering_anatomy.md).

## Review legend

```text
C_domain_copy(N)  cost of copying opaque modeled state
M_domain_copy(N)  extra memory of that copy
P                 processes in a stage
Q                 proposals in a stage
R                 accepted/resolved events in a stage
E                 committed events in a step
S                 stages in a step
T                 completed steps
K                 context services
```

## `SimulationState.copy()`

```text
Role:
    transaction snapshot

Time:
    C_domain_copy(N) + fixed kernel overhead

Memory:
    M_domain_copy(N) + fixed envelope/RNG state

Frequency:
    once per step

Readability strength:
    copy contract is centralized

Maintenance strength:
    one validated construction path

Main optimization warning:
    never trade away domain/RNG rollback for copy avoidance without
    strong generic evidence
```

## `SequentialStepCoordinator.coordinate()`

```text
Role:
    one complete transactional step

Time:
    C_domain_copy(N) + sum(stage costs) + O(E)

Memory:
    M_domain_copy(N) + O(E) + stage temporaries

Frequency:
    once per step

Readability strength:
    linear procedural control flow mirrors semantics

Maintenance strength:
    one success path, no special-case algorithms

Main optimization warning:
    "O(S)" hides the real stage/domain work
```

## `StageCoordinator.coordinate()`

```text
Role:
    propose -> resolve -> materialize-all -> apply

Structural time:
    O(P + Q + R) + resolver cost
    + delegated proposal/materialization/application costs

Structural memory:
    O(Q + R) + telemetry/effects

Frequency:
    once per stage; several operations per event

Readability strength:
    semantic phases visible in top-level method

Maintenance strength:
    cached metadata surrounds one semantic algorithm

Main optimization warning:
    preserve simultaneity and accepted-only materialization
```

## Resolver

```text
Role:
    choose candidate transitions and ordering

Complexity:
    policy-specific

Mutation:
    none

Extensibility:
    high; conflict policy changes independently

Smell:
    resolver begins applying domain state changes
```

## `AppliedEvent` / `StepTelemetry`

```text
Role:
    committed causal telemetry

Time:
    O(1) record work per applied event; O(R/E) aggregate

Memory:
    O(1) fixed fields per record; O(E) aggregate references/records

Frequency:
    once per committed event

Performance lesson:
    constant-time work can be a measured hotspot at high frequency

Optimization warning:
    telemetry expressiveness is not disposable benchmark overhead
```

## `SimulationContext.require()`

```text
Role:
    explicit immutable service/config lookup

First uncached typed lookup:
    O(K)

Cached typed lookup:
    average O(1)

Cache memory:
    O(number of typed keys cached)

Tradeoff:
    small stable memory cache for repeated lookup work
```

## `SimulationSpec.compile()`

```text
Role:
    static generic preflight + runtime construction

Frequency:
    once before run

Complexity:
    configuration-graph dependent; conceptually traversal-like

Performance lesson:
    startup work and hot runtime work need different budgets

Maintenance strength:
    static checks stay out of repeated runtime loops
```

## `SimulationEngine.run()`

```text
Role:
    repeat committed steps, then observe committed results

Time:
    sum over T steps of stopping + step + observation costs

Memory:
    engine itself small; observer retention can dominate long-run memory

Frequency:
    one loop iteration per completed step

Semantic landmark:
    simulation.state = completed_working_state is the commit point
```

## Multi-lens review prompt

For any file, answer these without the guide:

```text
What does it own?
What may it mutate?
What invariant does it protect?
What are its scale variables?
What is its structural complexity?
What delegated costs remain unknown?
What does it allocate and for how long?
How frequently does it run?
Is it measured hot?
Can I see the algorithm clearly?
What would make future changes risky?
What can vary behind existing contracts?
Which tests prove the important behavior?
```
