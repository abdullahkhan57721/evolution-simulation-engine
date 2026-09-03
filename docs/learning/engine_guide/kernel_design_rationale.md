# Kernel Design Rationale and Invariants

The kernel is easier to understand when you see it as a sequence of answers to
failure modes in simpler designs.

This chapter asks repeatedly:

> **Why not just do the obvious simpler thing?**

It also turns the kernel into a short catalog of invariants you can use when
reading or reviewing code.

## Where you are in the architecture

```text
[KERNEL] semantic constitution  <-- YOU ARE HERE
    |
    +-- authoritative docs / ADRs
    +-- focused executable tests
    +-- production implementation
```

The most relevant rationale records are:

- [ADR 0001 — Domain-neutral kernel](../../decisions/0001-domain-neutral-kernel.md)
- [ADR 0002 — Stage simultaneity](../../decisions/0002-stage-simultaneity.md)
- [ADR 0003 — Transactional state and RNG](../../decisions/0003-transactional-state-and-rng.md)
- [ADR 0004 — Readability before micro-optimization](../../decisions/0004-readability-before-micro-optimization.md)

## Why not let every process directly update the world?

The naive design is attractive:

```python
for process in processes:
    process.update(world)
```

It is easy to read and may be correct for a toy model.

The problem is that process order becomes model causality:

```text
Process A sees S0
   |
 mutates
   v
Process B sees S1
   |
 mutates
   v
Process C sees S2
```

If A and B were conceptually simultaneous competitors, tuple order now determines
who got first access to state.

### Architectural answer

Separate candidate generation from application:

```text
all propose from common stage-start state
        |
        v
resolve competition explicitly
        |
        v
apply accepted events
```

This turns hidden order dependence into an explicit resolver policy.

## Why not let processes resolve their own conflicts?

Suppose `Feeding` internally prevents duplicate access to prey while `Reproduction`
implements a different ad-hoc partner lock and `Movement` invents another location
claim system.

Each process now needs:

```text
its domain behavior
+
knowledge of competing proposals
+
conflict bookkeeping
+
ordering policy
```

Competition logic becomes duplicated and difficult to compare.

### Architectural answer

A process describes its candidate transitions. A resolver owns the stage's
competition policy.

```text
Process -> what could happen / how to apply it
Resolver -> which candidates survive together
```

The resolver does not become a mutator. That keeps policy and transition behavior
separate.

## Why not materialize every proposal immediately?

Imagine a proposed reproductive event chooses random contributors during proposal.
Later the resolver rejects that candidate.

The candidate never occurs, but it has already consumed RNG.

Now adding an extra rejected candidate can change random outcomes for accepted
transitions later in the same run.

### Architectural answer

Defer accepted-only work:

```text
proposal
   |
resolve
   |
accepted? ---- no ----> no accepted-only RNG/work
   |
  yes
   |
materialize
```

This protects stochastic trajectories from rejected candidates.

## Why not materialize each event immediately before applying it?

A tempting loop is:

```python
for accepted_event in accepted:
    event = materialize(accepted_event)
    apply(event)
```

But then later materializers can see mutations from earlier applications.

```text
materialize A from S
apply A -> S1
materialize B from S1
```

That violates the intended same-stage snapshot semantics.

### Architectural answer

```text
materialize A from S
materialize B from S
materialize C from S
        |
        v
apply A
apply B
apply C
```

This is why **materialize-all-before-apply** is a public semantic contract rather
than a loop-organization preference.

The focused test
[`test_all_events_materialize_before_any_apply`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_stage_coordinator.py)
exists to protect this exact behavior.

## Why not mutate the authoritative state and undo on failure?

A manual rollback design needs to reverse every side effect correctly:

```text
entity mutations
container changes
RNG draws
effect journals
ID allocation
future new domain state
```

Every new domain feature becomes another rollback obligation.

### Architectural answer

Mutate an isolated copy:

```text
authoritative state
     |
    copy
     |
     v
working state
     |
  success? ------ no ------> discard
     |
    yes
     |
     v
replace authoritative reference
```

Rollback becomes a consequence of ownership/isolation rather than a giant undo
protocol.

## Why not share the same RNG between the committed and working states?

If a failed transaction consumes random values from a shared generator, domain
state may roll back while stochastic state does not.

The next retry starts from a different random stream.

### Architectural answer

`SimulationState.copy()` clones the **complete generator state** into a distinct
`random.Random` object.

The focused test
[`test_simulation_state_copy_semantics.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_simulation_state_copy_semantics.py)
checks that the copy:

```text
is not the same RNG object
has the exact same initial RNG state
produces matching draws while advanced identically
can diverge independently afterward
```

The determinism test
[`test_kernel_determinism.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_kernel_determinism.py)
checks that equal seeds/configuration produce equal kernel outcomes.

## Why not give every process its own random generator?

That looks modular, but it creates a second hidden state graph:

```text
SimulationState RNG
Process A RNG
Process B RNG
Process C RNG
...
```

Exact checkpointing, rollback, and replay now require knowing how every process
owns/copies/seeds its private generator.

### Architectural answer

Simulation decisions consume `simulation_state.rng`.

A truly independent persisted random source could be modeled explicitly as domain
state, but invisible ad-hoc generators are not the normal path.

## Why not put `WorldState` directly in `SimulationState`?

The early engine was biology-shaped. That is convenient while there is only one
domain, but execution machinery then begins to acquire assumptions such as:

```text
organisms exist
resources exist
world dimensions exist
birth/death are generic lifecycle concepts
```

Those assumptions make the scheduler harder to reuse and distort future biology by
making today's domain model look universal.

### Architectural answer

Use:

```text
SimulationState.domain_state : opaque copyable payload
```

The kernel only knows how to transact it.

The architecture test
[`test_domain_neutral_kernel.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_domain_neutral_kernel.py)
checks that kernel-facing code avoids modeled-domain imports and vocabulary and
runs with a nonbiological counter state.

## Why not store all configuration directly on `SimulationState`?

If configuration and mutable state are mixed:

- it is unclear what must be copied;
- runtime components may mutate supposedly fixed model parameters;
- domain-specific names leak into generic state;
- adding a new configuration service expands the state API.

### Architectural answer

```text
SimulationState
    mutable transaction envelope

SimulationContext
    immutable shared configuration/services
```

Typed `ContextKey[T]` values let domain packages own the names/types of services
they define.

## Why not manufacture arbitrary dynamic context attributes?

Convenience syntax such as:

```python
Simulation(initial_domain_state=world, genetic_architecture=architecture)
```

could tempt an implementation to create:

```python
simulation.genetic_architecture
state.genetic_architecture
```

for every supplied name.

That would make the generic public API grow invisibly based on caller input.

### Architectural answer

Normalize named values into `SimulationContext`. The convenience is construction
sugar only.

Explicit lookup preserves a stable kernel object model.

## Why not let observers participate in updates?

An observer that mutates state or changes conflict decisions becomes part of model
causality.

Then enabling a recorder can change the simulation being recorded.

### Architectural answer

Observation is descriptive and occurs on committed state. Telemetry is descriptive
and records committed transitions.

Instrumentation should not change the model merely because it is enabled.

## Why not infer what happened only from final state?

Two different causal histories can lead to similar final state.

For example, a population could fall because of:

```text
mortality
migration/departure
predation
other removal
```

A snapshot alone may not distinguish those causes.

### Architectural answer

Committed `AppliedEvent` / `StepTelemetry` records preserve transition history and
optional opaque domain effects alongside state observation.

State answers **what is true now**. Telemetry helps answer **what committed to make
it so**.

## Why not make a universal `EvolutionaryEntity` base interface?

A huge general interface can easily encode today's biological assumptions:

```text
has heredity
has reproduction
has phenotype
has parents
...
```

But different evolutionary algorithms need different capabilities.

### Architectural answer

Treat “evolving entity” as a conceptual role and expose small contracts such as
`TransmissibleStateCarrier` where required.

This prevents taxonomy from becoming accidental coupling.

## Why not call all propagation “inheritance”?

Inheritance implies stronger biological/lineage semantics than the general layer
actually guarantees.

Horizontal replacement propagation between persistent information nodes is a
valid general-evolution mechanism but is not biological inheritance.

### Architectural answer

Use **propagation** generically and **inheritance** biologically.

That naming distinction reflects an actual semantic boundary, not cosmetic
terminology.

## Why not combine propagation and entity production?

If propagation always creates a new entity, horizontal transmission becomes
awkward.

If production always means inheritance, placement/identity/non-transmissible
newborn state become genetics concerns.

### Architectural answer

Keep:

```text
propagation -> determine transmissible state
production  -> construct entity
admission   -> insert into active domain
```

as separate responsibilities.

## Why not encode “fitness” as a required entity property?

A universal scalar risks turning an emergent outcome into an intrinsic property.

Biological contribution can depend on environment, competition, mate availability,
and many interacting processes.

### Architectural answer

Let selection emerge from differential persistence/propagation. Measure fitness or
lifetime reproductive success observationally where useful.

## Why prefer readability before micro-optimization?

Simulation engines can be performance-sensitive, but kernel code is also the place
where subtle semantic invariants live.

An optimization that obscures phase ordering can make correctness harder to audit.

### Architectural answer

- keep semantic flow readable;
- profile before optimizing;
- use domain-neutral synthetic kernel benchmarks for kernel claims;
- preserve tests for ordering/isolation/determinism;
- cache or specialize hot-path support only when evidence justifies it.

`StageCoordinator`'s cached dispatch metadata is an example: the semantic
`coordinate()` flow remains direct even though stable runtime inspection is moved
to construction.

# Invariant catalog

Use these invariants as a code-review checklist.

## Invariant 1 — kernel domain neutrality

**Promise**

The kernel does not assign biological/ecological meaning to `domain_state`.

**Why**

Execution mechanics should remain reusable and independent of the current domain.

**Implementation clues**

- opaque `SimulationState.domain_state`;
- no domain imports in kernel packages;
- generic process/event/resolver vocabulary.

**Executable companion**

[`tests/engine/test_domain_neutral_kernel.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_domain_neutral_kernel.py)

**Failure symptom**

Kernel code starts accessing `.organisms`, `.genome`, `.energy`, or another domain
concept.

## Invariant 2 — authoritative state is not mutated during a step transaction

**Promise**

A step operates on a copy; authoritative state changes only by replacement after
success.

**Why**

Partial failure must not leave committed model state half-mutated.

**Implementation clues**

```text
SequentialStepCoordinator.coordinate()
    -> simulation_state.copy()

SimulationEngine.run()
    -> simulation.state = returned_state
```

**Failure symptom**

An exception halfway through a step changes `simulation.state.domain_state`.

## Invariant 3 — RNG is transactional with modeled state

**Promise**

A state copy contains an independent RNG object at the exact same generator state.

**Why**

Failed/discarded work must not advance committed randomness.

**Executable companions**

- [`test_simulation_state_copy_semantics.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_simulation_state_copy_semantics.py)
- [`test_kernel_determinism.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_kernel_determinism.py)

**Failure symptom**

Retrying an unchanged committed state after a failed transaction produces a shifted
random trajectory.

## Invariant 4 — all same-stage processes propose before application

**Promise**

All process proposals in one stage observe the common stage-start state.

**Why**

Configured process iteration order should not silently become same-stage causal
priority.

**Implementation clue**

`StageCoordinator._propose_events()` completes before resolver/materialization/
application.

**Executable companion**

[`tests/engine/test_stage_coordinator.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_stage_coordinator.py)

**Failure symptom**

A later proposer changes its candidate because an earlier process already applied.

## Invariant 5 — resolver selects, process mutates

**Promise**

Resolver chooses accepted events/order. The event-owning process applies domain
mutation.

**Why**

Competition policy and transition meaning should remain independently replaceable.

**Implementation clue**

```text
resolver.resolve_events(...)
        -> resolved event values

process.apply_event(...)
        -> mutation
```

**Failure symptom**

A resolver directly changes `domain_state` as part of deciding winners.

## Invariant 6 — every accepted event materializes before any same-stage application

**Promise**

All accepted deferred consequences observe the same pre-application stage state.

**Why**

Later materialization must not depend on earlier accepted-event mutation.

**Executable companion**

`test_all_events_materialize_before_any_apply()` in
[`tests/engine/test_stage_coordinator.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_stage_coordinator.py)

**Failure symptom**

Materialized event B sees state produced by application of accepted event A in the
same stage.

## Invariant 7 — rejected candidates do not consume accepted-only materialization work

**Promise**

Only resolver-selected events enter `materialize_event(...)`.

**Why**

Rejected candidates should not perturb accepted stochastic outcomes when the
random decision semantically belongs only to accepted transitions.

**Implementation clue**

```text
propose
 -> resolve
 -> _prepare_applications(resolved_events only)
```

**Failure symptom**

Adding a candidate that is always rejected shifts later materialization RNG.

## Invariant 8 — one proposal event type has one process owner within a stage

**Promise**

Stage dispatch from resolved event type to process is unambiguous.

**Why**

The coordinator must know which process can materialize/apply a returned event.

**Implementation clue**

`StageCoordinator.__init__()` rejects duplicate process `event_type` values.

**Executable companion**

`test_stage_rejects_duplicate_proposed_event_types()` in the stage-coordinator
tests.

**Failure symptom**

The kernel must guess which process owns a resolved event.

## Invariant 9 — resolvers cannot inject unknown event ownership

**Promise**

A resolved event must map back to a registered process proposal type.

**Why**

Resolver selection should not manufacture transitions whose mutation semantics are
unknown to the stage.

**Executable companion**

`test_resolved_unknown_event_type_raises()` in the stage-coordinator tests.

## Invariant 10 — immutable context is shared, not transactionally mutated

**Promise**

State copies share `SimulationContext` by reference.

**Why**

Stable configuration/services should not become hidden evolving state.

**Implementation clue**

`SimulationState.copy()` passes `context=self.context`.

**Failure symptom**

A runtime transition modifies model configuration through shared context.

## Invariant 11 — committed telemetry describes applied transitions

**Promise**

`AppliedEvent` is created after process application succeeds; `StepTelemetry`
groups the completed step's applied events.

**Why**

Telemetry should represent authoritative causal history, not merely intentions.

**Failure symptom**

Rejected proposals appear indistinguishably as committed events.

## Invariant 12 — observers are descriptive

**Promise**

Observation does not participate in conflict resolution or mutate committed state
as an observation side effect.

**Why**

Turning instrumentation on or off should not alter modeled dynamics.

**Executable companion**

[`tests/engine/test_observation.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_observation.py)

## Invariant 13 — static dependency problems fail before runtime

**Promise**

`SimulationSpec` generic preflight aggregates declared dependencies and rejects
missing capabilities before constructing/running mutable simulation state.

**Why**

Static wiring errors should not emerge unpredictably in later steps.

**Failure symptom**

A missing configured service is discovered only after a long simulation has
started when it could have been validated from the component graph.

## How to use invariants while reading code

Instead of asking:

> What do these 150 lines do?

ask:

```text
Which invariants must this file preserve?
Which lines are semantic?
Which lines validate the invariant?
Which lines only optimize/diagnose the same invariant?
```

For `StageCoordinator`, that immediately narrows the important questions to:

```text
common proposal snapshot
explicit resolver call
materialize-all-before-apply
unambiguous event ownership
process-owned mutation
per-application telemetry/effects
```

The dispatch cache becomes much easier to understand once you know what it is
supporting.

## You understand this chapter if you can…

- derive the current phase separation from failure modes in direct mutation;
- explain why proposal-time and accepted-only randomness are different semantic
  categories;
- explain rollback as isolation rather than undo;
- defend domain neutrality without claiming every layer should use generic
  vocabulary;
- choose at least five invariants and point to the production/test area that
  protects them;
- distinguish a semantic invariant from a performance implementation detail; and
- review a proposed kernel change by asking what generic deficiency or invariant
  it addresses rather than whether it is convenient for one biological feature.

Next: [Worked Examples Across the Layers](worked_examples.md).
