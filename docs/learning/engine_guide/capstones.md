# Capstone Challenges

These capstones deliberately remove most scaffolding. They test whether the
textbook's ideas have become working design judgment rather than familiar
terminology.

Do not use the cheat sheet on the first attempt.

# Capstone 1 — Explain the engine without class names

Explain the simulation kernel without using any of these names:

```text
SimulationState
Simulation
SimulationEngine
StageCoordinator
SequentialStepCoordinator
Process
Resolver
EventMaterializer
SimulationSpec
AppliedEvent
StepTelemetry
```

Your explanation should still cover:

- authoritative versus working state;
- transactional rollback;
- RNG ownership;
- stage simultaneity;
- candidate transitions;
- conflict resolution;
- accepted-only deferred consequences;
- mutation ownership;
- commit;
- observation and causal telemetry.

### Why this works

Class names can hide shallow understanding. If you understand the architecture,
you can reconstruct the concepts independently of the current API vocabulary.

### Self-check

A strong answer should sound roughly like a design explanation rather than a list
of renamed classes:

```text
A run owns one committed snapshot. Each step begins by copying that snapshot,
including stochastic state. Domain mechanisms inspect one common stage-start
snapshot and propose candidate changes. A separate policy selects compatible
candidates. Deferred accepted-only stochastic details are determined before any
selected change mutates the working copy. Only a fully completed step replaces the
committed snapshot. Observers and telemetry consume committed outcomes rather than
participating in transition choice.
```

Do not memorize that wording; compare its concepts with yours.

# Capstone 2 — Derive a minimal kernel

Start only from this requirement:

> Build a reproducible simulation in which several modeled mechanisms may propose
> simultaneous, competing stochastic state transitions, and failed steps must not
> partially commit.

Derive the architecture yourself.

Questions to answer:

```text
What must own authoritative state?
How do you prevent partial mutation?
Where does RNG state live?
What does "simultaneous proposal" mean operationally?
How are conflicts separated from mutation?
When should rejected-only stochastic work be avoided?
What object/mechanism owns applying a selected transition?
What constitutes commit?
How can committed causal history be observed?
What should remain completely domain-neutral?
```

Then sketch a 100–150 line toy implementation.

Afterward compare it with:

- [Kernel Mental Model](kernel_mental_model.md)
- [Kernel Runtime](kernel_runtime.md)
- [Reading the Kernel Source](source_code_walkthrough.md)

For every production feature your mini-kernel lacks, ask:

> What real correctness, diagnostics, extensibility, performance, or observability
> problem does this extra mechanism solve?

# Capstone 3 — Review a deliberately flawed feature

A teammate proposes territorial reproduction with this design:

```text
1. Add current_territory_owner and pregnant_parent to SimulationState.
2. During Reproduction.propose_events(), immediately choose genetic contributors,
   consume recombination RNG, deduct energy, and create an offspring genome.
3. Let a TerritorialResolver choose which newborns get each cell and immediately
   insert winners into the world.
4. If two newborns conflict, observers remove the loser after the step.
5. To make it fast, cache whether the world has an effect journal when the
   StageCoordinator is constructed.
6. Store every full world snapshot and every event for every step for debugging.
```

Review the proposal across **all** of these lenses.

## Scientific/domain meaning

Which concepts are biological? Which are spatial? Which are generic execution
mechanics?

## Layer ownership

Which proposed `SimulationState` fields are domain leaks?

## Transactionality

Which mutations occur too early? What happens if a later stage raises?

## RNG semantics

Which rejected candidates consume randomness? Why does phase placement matter?

## Simultaneity

Do all same-stage proposals still observe the same stage-start modeled state?

## Resolver/process separation

Which component is applying mutation even though it should only choose candidates?

## Observation

Can observers repair invalid committed state? Why is that the wrong responsibility?

## Complexity

Define useful variables such as:

```text
N = organisms
Q = reproduction proposals
R = accepted births
T = steps
```

Which operations might be O(N), O(Q), O(R), or worse?

## Memory

What is the long-run consequence of retaining every full world snapshot?

If one snapshot is O(N) and population is roughly stable, what does storing `T`
snapshots imply?

## Performance

Which proposed optimization is semantics-sensitive rather than safely structural?

What should be profiled before changing it?

## Readability

How many responsibilities and phases have been collapsed together?

## Maintainability

What rules are now duplicated across process, resolver, observer, and kernel state?

## Extensibility

Would this design make future non-territorial or nonbiological simulations harder?

## Testability

Which focused tests would be difficult to write because responsibilities are no
longer isolated?

## Rewrite

Propose a cleaner design using existing boundaries wherever possible. Explicitly
state whether the frozen kernel needs any change.

# Capstone 4 — Performance without premature optimization

A profile of a large biological run shows:

```text
55% mate candidate search
18% developmental phenotype calculation
9% observation snapshot retention/serialization
5% generic kernel orchestration
13% everything else
```

A teammate proposes rewriting `StageCoordinator` into three specialized fast paths
and bypassing telemetry validation to "speed up the engine."

Analyze:

1. Is the proposal targeting the dominant cost?
2. What layer should be investigated first?
3. What complexity questions should be asked of mate candidate search?
4. What data structures might preserve scientific semantics while reducing search?
5. Which measurements should be separated into kernel-only and reference/end-to-end
   workloads?
6. When could a 5% kernel share still justify optimization?
7. What readability/maintenance cost would specialized stage algorithms create?
8. What evidence would be sufficient to accept a kernel optimization?

The desired habit is:

```text
reason about scaling early
        +
profile the correct layer
        +
optimize the measured structural problem
        +
preserve semantics/readability unless benefit justifies the cost
```

# Mastery rubric

Use the five levels from
[Reasoning About Proposed Changes](change_reasoning.md):

```text
1 recognition
2 explanation
3 prediction
4 diagnosis
5 design
```

A strong capstone performance is level 5: you can independently choose the
correct layer, preserve invariants, reason about scaling/memory, identify the
needed evidence, and design a coherent alternative.

# Delayed retrieval

Repeat one capstone several days later without rereading the chapter first.

If you can recognize the answer when reading it but cannot reconstruct the
reasoning yourself, return to the relevant chapter rather than merely rereading
the cheat sheet.
