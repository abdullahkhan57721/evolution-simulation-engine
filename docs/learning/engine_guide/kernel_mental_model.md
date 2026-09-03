# The Kernel Mental Model

The kernel is the domain-neutral execution layer. It does not define evolution,
biology, organisms, genomes, energy, reproduction, or ecology. Its responsibility
is narrower and more foundational:

> **Coordinate state transitions reproducibly and transactionally while preserving
> explicit stage semantics.**

The authoritative concise contract is the
[Simulation Kernel Contract](../../kernel_contract.md).

## Where you are in the architecture

```text
[BIOLOGY]
modeled meaning
     ^
     |
[GENERAL EVOLUTION]
evolutionary semantics
     ^
     |
[KERNEL]  <-- YOU ARE HERE
transactional execution mechanics
```

## What the kernel knows

The kernel understands a deliberately small vocabulary:

```text
SimulationState
    transactional envelope

domain_state
    opaque mutable modeled payload

SimulationContext
    immutable shared configuration/services

Process
    owns a transition type and its application

Event
    proposed/resolved/materialized transition value

Resolver
    selects compatible proposals

Stage
    propose -> resolve -> materialize -> apply

Step
    ordered sequence of stages inside one transaction

RNG
    simulation-owned stochastic state

Telemetry
    committed applied-event description

Observer
    reads committed results
```

That is enough to run both a counter and a biological ecology.

## What the kernel explicitly does not know

The kernel does not define:

```text
organisms
birth / death
mating / reproduction
genomes / alleles
mutation / recombination
energy / metabolism
feeding / predation
resources
coordinates / neighborhoods
fitness / natural selection
biological lifecycle ordering
```

Those concepts can be implemented **using** kernel contracts without changing
what the contracts mean.

The easiest boundary test is:

> Could this code run a nonbiological `CounterState` or information network without
> importing the biological world?

The repository has focused architecture tests for exactly that reason.

## The five core runtime objects

A beginner reading the package can easily think every class is equally central.
They are not. Start with five objects.

### 1. `Simulation`

`Simulation` owns the **authoritative current `SimulationState`**.

```text
Simulation
    |
    +-- state -> SimulationState
```

This is the object whose `state` reference changes when a step commits.

### 2. `SimulationState`

`SimulationState` is one kernel-owned snapshot envelope:

```text
SimulationState
    |
    +-- domain_state
    +-- context
    +-- step_index
    +-- rng
    +-- last_step_telemetry
```

The domain owns the meaning of `domain_state`; the kernel owns the transaction
semantics around the envelope.

### 3. `SimulationEngine`

`SimulationEngine` orchestrates the run loop:

```text
observe initial state
while not stopped:
    coordinate one step
    commit returned state
    observe telemetry
    observe committed domain state
```

It does **not** contain the authoritative state.

### 4. `SequentialStepCoordinator`

This object establishes the transaction boundary and runs stages sequentially.

```text
committed state
    |
    v
copy
    |
    v
working state
    |
stage 0 -> stage 1 -> stage 2
    |
    v
step index + telemetry
    |
    v
return completed state
```

### 5. `StageCoordinator`

This object owns the semantic heart of one stage:

```text
propose all
    |
    v
resolve
    |
    v
materialize all accepted
    |
    v
apply accepted
```

If you understand those five objects, the rest of the kernel has a place to attach.

## Object ownership map

```text
Simulation
|
+-- state : SimulationState  <-----------------------------+
|       |                                                   |
|       +-- domain_state  -> domain owns meaning            |
|       +-- context       -> immutable shared services      |
|       +-- rng           -> simulation random stream       |
|       +-- step_index                                      |
|       +-- last_step_telemetry                             |
|                                                           |
+-----------------------------------------------------------+
                                                            |
SimulationEngine                                            |
|                                                           |
+-- step_coordinator : StepCoordinator ---------------------+
|       |
|       +-- SequentialStepCoordinator
|               |
|               +-- stages : tuple[StageCoordinator, ...]
|                       |
|                       +-- processes
|                       +-- resolver
|
+-- stopping_condition
+-- observers
+-- telemetry_observers
```

The line to remember is:

```text
Simulation owns state.
SimulationEngine coordinates state replacement.
```

## Responsibility versus authority

The kernel becomes much clearer if you avoid saying “the engine handles events”
and instead assign specific authority.

| Component | Responsibility / authority |
| --- | --- |
| `Simulation` | owns authoritative current state |
| `SimulationState` | packages domain state, context, RNG, step/telemetry state |
| `SimulationEngine` | owns run/stop/observe orchestration |
| `SequentialStepCoordinator` | owns one-step transaction and ordered stage execution |
| `StageCoordinator` | owns stage-phase ordering |
| `Process` | owns proposal type, domain transition meaning, and mutation |
| `Resolver` | owns acceptance/order among competing proposals |
| `EventMaterializer` | owns accepted-only deferred event detail for a process |
| `Observer` | reads committed domain state |
| telemetry observer | reads committed step telemetry |

This prevents a common mistake: moving mutation into a resolver simply because the
resolver “decides the winner.” Decision authority is not mutation ownership.

## `domain_state` is intentionally opaque

A kernel method may do this:

```python
domain_state = simulation_state.domain_state
```

But generic kernel code should not then assume:

```python
domain_state.organisms
domain_state.resources
domain_state.width
```

The only mandatory capability is a callable `copy()` method for transactional
isolation.

This boundary allows:

```text
SimulationState(domain_state=CounterState(...))
SimulationState(domain_state=InformationNetwork(...))
SimulationState(domain_state=WorldState(...))
```

with the same kernel mechanics.

## `SimulationContext` is not another mutable state bag

`SimulationContext` holds immutable services/configuration shared across snapshots.

Conceptually:

```text
             immutable context
              /     |      \
             /      |       \
        State 0   State 1   State 2
```

Because the context cannot change through normal public mutation, copies can share
it safely by reference.

This is different from `domain_state`, which must be copied because it is expected
to mutate.

## `SimulationState.copy()` is the transaction primitive

The real copy method does three architecturally important things:

```text
1. independently copy domain_state
2. clone the complete RNG state
3. share immutable context by reference
```

and it clears `last_step_telemetry` on the new working snapshot until the new step
has completed.

A useful mental expansion is:

```python
working_state = SimulationState(
    domain_state=committed.domain_state.copy(),
    context=committed.context,
    step_index=committed.step_index,
    rng=clone_rng(committed.rng),
    last_step_telemetry=None,
)
```

That one operation explains most rollback behavior.

## The transaction commit line

Inside `SimulationEngine.run()`, the decisive assignment is conceptually:

```python
simulation.state = self.step_coordinator.coordinate(
    simulation_state=simulation.state,
)
```

Read it from right to left:

```text
old authoritative state
        |
        v
coordinate complete transaction
        |
        v
completed working state
        |
        v
replace simulation.state
```

If `coordinate(...)` raises, the assignment never occurs.

That is the commit boundary.

## Stages are sequential; processes within a stage share proposal state

Suppose a step has stages `A`, `B`, and `C`.

```text
working state at step start
        |
        v
stage A
        |
        v
state after A
        |
        v
stage B
        |
        v
state after B
        |
        v
stage C
```

Stage B is allowed to observe mutations committed within the working transaction
by stage A.

But inside a single stage:

```text
stage-start state
  |       |       |
  v       v       v
Proc A  Proc B  Proc C
propose propose propose
```

No proposal sees a prior process's application because application has not started.

## Why each process owns one proposal event type per stage

After resolution, the coordinator must map each returned event back to the process
that knows how to materialize/apply it.

The stage therefore requires unique process proposal event types:

```text
EventTypeA -> ProcessA
EventTypeB -> ProcessB
EventTypeC -> ProcessC
```

If two processes in the same stage claimed the same event type, dispatch would be
ambiguous.

The constructor rejects that configuration early.

## Materialization is optional capability, not a mandatory base method

Many events need no deferred work:

```text
proposal event == event that can be applied
```

Other processes satisfy `EventMaterializer`:

```text
resolved proposal
        |
        v
materialize_event(...)
        |
        v
richer materialized event
```

`StageCoordinator` detects that optional capability once during construction and
caches the bound callable for runtime dispatch.

Architecturally, remember the optional phase first. The caching is an
implementation/performance detail.

## The minimum semantic kernel

Strip away validation, telemetry, type-name caching, and effect capture, and one
stage is conceptually:

```python
def coordinate_stage(state):
    proposals = []
    for process in processes:
        proposals.extend(process.propose_events(state))

    accepted = resolver.resolve_events(state, proposals)

    prepared = []
    for event in accepted:
        process = owner_of(type(event))
        if process_has_materializer(process):
            event = process.materialize_event(state, event)
        prepared.append((process, event))

    for process, event in prepared:
        process.apply_event(state, event)
```

One step is conceptually:

```python
def coordinate_step(committed_state):
    working_state = committed_state.copy()
    for stage in stages:
        stage.coordinate(working_state)
    working_state.step_index += 1
    return working_state
```

And the run loop is conceptually:

```python
while not stopping_condition.should_stop(simulation.state):
    simulation.state = step_coordinator.coordinate(simulation.state)
```

Everything else in the kernel supports, validates, observes, or optimizes those
semantics.

## Essential semantics versus implementation support

This distinction is critical when reading `StageCoordinator`.

### Essential semantics

```text
proposal collection
resolver call
materialize all accepted events
apply accepted events in resolver order
capture committed telemetry
```

### Implementation support

```text
_dispatch_by_event_type
_ProcessDispatch
cached materialize_event bound method
qualified type-name cache
_PreparedApplication tuple representation
effect-journal validation helpers
```

Do not confuse the second list with the conceptual architecture.

## Telemetry belongs to committed application

For each applied event, the kernel records `AppliedEvent` metadata. At the end of a
step, `SequentialStepCoordinator` creates `StepTelemetry` containing all applied
events in stage/application order.

This gives a causal trace of what actually committed.

A proposal that was rejected is not an `AppliedEvent`.

A materialized event that somehow never applies because the transaction raises is
not part of authoritative committed telemetry because the whole working state is
discarded.

## Optional domain effects stay opaque

A domain state may expose:

```text
effect_count
effects_since(checkpoint)
```

Before each application, the kernel can checkpoint the journal; after application,
it can attach newly produced effects to `AppliedEvent`.

The kernel validates the journal shape but does not interpret effect values.

This is a good example of a narrow capability boundary:

```text
kernel responsibility:
    capture effects associated with this application

domain responsibility:
    define what an effect means
```

## `SimulationSpec` sits before mutable runtime

A `SimulationSpec` describes a complete generic simulation configuration before
runtime objects are created.

Conceptually:

```text
initial domain state
step coordinator
stopping condition
context
seed
observers
telemetry observers
dependency declarations
        |
        v
     preflight
        |
        v
CompiledSimulation
   |            |
   v            v
Simulation    SimulationEngine
```

This prevents static wiring/capability errors from being discovered deep inside a
run when they can be found before mutable runtime exists.

## Public API versus internal implementation

The package `evo_engine.engine` intentionally re-exports the main kernel-facing
objects. When learning the public surface, start there rather than treating every
module helper as equally public.

The public kernel vocabulary includes:

```text
Simulation
SimulationState
SimulationEngine
StageCoordinator
SequentialStepCoordinator
SimulationEvent
Process
EventMaterializer
Resolver
StepCoordinator
StoppingCondition
Observer
MaxSteps
```

The next chapter explains those contracts in use-oriented detail.

## Misconception checks

### “`SimulationEngine` owns the state.”

No. `Simulation` owns `state`. The engine orchestrates replacement of that
reference after a successful coordinated step.

### “`domain_state` is a generic world object.”

No. It is an opaque copyable payload. `WorldState` is one biological domain
implementation.

### “Context is copied transactionally.”

No. Immutable context is shared by reference. Mutable domain state and RNG state
are independently copied.

### “The process event type and materialized event type must always be the same.”

No. A materializer may turn a proposal type into a richer event type. Dispatch
ownership is established from the process's proposal event type.

### “StageCoordinator's dispatch cache is part of stage semantics.”

No. It supports efficient implementation of the semantics. The public semantic
contract is phase ordering and ownership.

## You understand this chapter if you can…

- draw the ownership graph from `Simulation` through `SimulationState` and the
  coordinators;
- point to the conceptual transaction commit assignment;
- explain why `domain_state` is opaque and only required to be copyable;
- explain what is copied versus shared in `SimulationState.copy()`;
- distinguish sequential stage ordering from same-stage proposal/materialization
  simultaneity;
- explain why process proposal event types must be unique within a stage;
- separate `StageCoordinator`'s semantic core from dispatch/performance plumbing;
- explain how telemetry differs from proposals; and
- reduce the production kernel to the minimum semantic pseudocode without losing
  the contract.

Next: [Kernel Public API](kernel_public_api.md).
