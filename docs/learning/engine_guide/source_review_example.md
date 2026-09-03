# Worked Source Review Example

This page demonstrates the complete multi-lens review method on a small kernel
method without reproducing the entire implementation.

## Target: `SequentialStepCoordinator.coordinate()`

### 1. Responsibility

Coordinate one complete transactional simulation step through ordered stages.

### 2. Semantic skeleton

```text
copy authoritative state
run stages against working copy
gather applied-event telemetry
advance step index
attach step telemetry
return completed working state
```

### 3. Ownership / authority

```text
input SimulationState:
    authoritative snapshot supplied by caller

working state:
    mutable transaction candidate

stage/processes:
    may mutate working domain state according to contracts

coordinator:
    orchestrates; does not define domain meaning

SimulationEngine:
    later commits by assigning returned state to simulation.state
```

### 4. Invariant

A failed stage must not alter the caller's authoritative domain state or RNG.

### 5. Complexity

Let `S` be stages and `E` committed events.

```text
time:
    C_domain_copy(N)
    + sum(stage_cost_i)
    + O(E) telemetry aggregation

memory:
    M_domain_copy(N)
    + O(E) applied-event references/StepTelemetry
    + stage-local temporaries
```

Do **not** summarize this as only O(S); the delegated stage work dominates the
meaningful expression.

### 6. Frequency

Once per completed simulation step attempt.

### 7. Memory lifetime

The working copy lasts through the step and becomes the next committed state on
success. Stage-local event lists are shorter-lived. The completed step telemetry is
attached to the returned state.

### 8. Readability

Strengths:

```text
linear procedural flow
meaningful working_state name
stage loop follows simulation semantics
telemetry constructed after successful stage completion
```

### 9. Maintainability

One transaction path means future changes to rollback/telemetry semantics do not
need to be synchronized across several fast paths.

### 10. Extensibility

New ordered stages can be composed without changing the coordinator.

### 11. Testability

Focused tests can inject a stage that raises after consuming RNG/mutating the
working copy and prove the original state remains unchanged.

### 12. Optimization boundary

A tempting optimization is direct mutation of the input state to avoid copying.
That is not a local speed tweak; it destroys the transaction contract.

### 13. One-paragraph professional summary

> `SequentialStepCoordinator.coordinate()` establishes the per-step transaction,
> executes domain-defined stages sequentially against that working snapshot,
> aggregates committed-event telemetry, and returns the completed next-state
> candidate. Its total cost is dominated by the domain copy and delegated stage
> algorithms rather than its short stage loop. The design intentionally pays copy
> time/memory for strong rollback and RNG isolation while keeping control flow
> highly readable and stage composition extensible.

Now use the same method on `SimulationContext.require()` or
`SimulationEngine.run()` without looking at the Engineering Review Cards first.
