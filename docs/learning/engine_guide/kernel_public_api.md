# Kernel Public API

This chapter is the practical map of the frozen domain-neutral kernel API. Read it
after the [Kernel Mental Model](kernel_mental_model.md) so the names attach to
responsibilities rather than becoming a list to memorize.

> **[KERNEL]** The public engine package exposes orchestration contracts and
> runtime objects. Biology does not belong in these interfaces.

## Public `evo_engine.engine` surface

The engine package exports:

```text
SimulationEvent
Process
EventMaterializer
Resolver
StepCoordinator
StoppingCondition
Observer

SimulationState
Simulation
StageCoordinator
SequentialStepCoordinator
SimulationEngine
MaxSteps
```

Configuration and telemetry live in neighboring generic packages:

```text
SimulationContext / ContextKey
SimulationSpec / CompiledSimulation
AppliedEvent / StepTelemetry / TelemetryObserver
```

## Read the API in three groups

### Runtime state and ownership

```text
SimulationState
Simulation
SimulationContext
```

### Execution/orchestration

```text
Process
EventMaterializer
Resolver
StageCoordinator
StepCoordinator
SequentialStepCoordinator
StoppingCondition
MaxSteps
SimulationEngine
```

### Construction, observation, and records

```text
SimulationSpec
CompiledSimulation
Observer
TelemetryObserver
AppliedEvent
StepTelemetry
```

# `SimulationEvent`

Conceptually:

```python
class SimulationEvent(Protocol):
    @property
    def step_index(self) -> int: ...
```

The kernel deliberately requires very little. It needs an event-carried step index
for committed telemetry. Everything else belongs to the process/domain event type.

An event is best understood as a **candidate/selected/materialized transition
value**, not as an object that applies itself.

# `Process`

The central domain-extension contract is conceptually:

```python
class Process(Protocol):
    @property
    def event_type(self) -> type[SimulationEvent]: ...

    def propose_events(self, simulation_state: SimulationState): ...

    def apply_event(self, simulation_state: SimulationState, event, /) -> None: ...
```

A process owns one proposal event type within its stage.

## Responsibility

```text
propose_events(...)
    inspect current transactional state
    create candidate transitions

apply_event(...)
    mutate transactional domain state for a selected/materialized transition
```

The process owns **domain meaning and mutation**. It does not own cross-process
conflict resolution or the stage phase algorithm.

## Event-type ownership

Within one stage, proposal event types must be unique. That gives the stage an
unambiguous mapping:

```text
resolved proposal type -> owning process
```

A resolver therefore cannot inject an event type no configured process owns.

# `EventMaterializer`

Materialization is an optional capability:

```python
@runtime_checkable
class EventMaterializer(Protocol):
    def materialize_event(
        self,
        simulation_state: SimulationState,
        event,
        /,
    ): ...
```

Use it when an accepted event has details that should be determined **only after
resolution** but **before any same-stage application**.

Typical reasons include:

```text
accepted-only stochastic choice
inheritance/recombination outcome
deferred target/detail selection
expensive work that rejected proposals should not perform
```

Materialization must not become a hidden application phase. Domain mutation still
belongs to `apply_event()`.

# `Resolver`

Conceptually:

```python
class Resolver(Protocol):
    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events,
    ): ...
```

A resolver owns:

```text
which proposals survive
+
accepted-event order
```

A resolver does **not** own domain mutation.

Contrast:

| Resolver | Process |
| --- | --- |
| chooses/order candidates | defines/apply transition |
| conflict policy | domain mechanism |
| no domain mutation | mutation in `apply_event` |

`AcceptAll` is the simplest resolver: accept proposals in their existing order.
More complex domains may inject preference/capacity/conflict policies without
changing `StageCoordinator`.

# `StageCoordinator`

Construction:

```python
stage = StageCoordinator(
    processes=(process_a, process_b),
    resolver=resolver,
)
```

Semantic contract:

```text
PROPOSE ALL
    every process sees common stage-start state
        |
        v
RESOLVE
    resolver selects/order candidates
        |
        v
MATERIALIZE ALL ACCEPTED
    determine accepted deferred details
        |
        v
APPLY
    processes mutate in resolver order
```

`coordinate(...)` returns committed-within-the-working-step `AppliedEvent`
telemetry for the stage. It does not create a new step-level state transaction;
that is the step coordinator's job.

# `SimulationState`

`SimulationState` is the transaction envelope:

```text
domain_state
context
step_index
rng
last_step_telemetry
```

## `domain_state`

The kernel requires only a callable `copy()` capability. It otherwise treats the
payload as opaque.

That is the kernel/domain boundary.

## `context`

Immutable `SimulationContext` shared by reference across transactional copies.

## `rng`

The simulation-owned `random.Random` whose exact internal state is cloned during
`SimulationState.copy()`.

## `copy()`

Architectural meaning:

```text
new transaction envelope
+ independent domain copy
+ independent RNG object with identical RNG state
+ shared immutable context
+ no new-step telemetry yet
```

Do not assume the method is O(1); its domain copy cost is supplied by the domain.
See [Computational Complexity and Performance Thinking](computational_complexity.md).

# `SimulationContext` and `ContextKey[T]`

`SimulationContext` is immutable configuration/service state shared across
transactions.

Use:

```python
service = simulation_state.context.require(SOME_KEY)
```

or optional lookup via `get(...)`.

A typed `ContextKey[T]` combines:

```text
stable service name
runtime expected type
static return type T
```

Named keyword values accepted while constructing `Simulation` or
`SimulationState` are convenience/normalization sugar: they become context
entries. They are not dynamic attributes on state.

# `Simulation`

Construction:

```python
simulation = Simulation(
    initial_domain_state=domain_state,
    seed=42,
    context=context,
)
```

`Simulation` owns the authoritative state reference:

```text
simulation.state
```

The constructor copies the caller-provided initial domain state, creates the
simulation RNG, and constructs the initial `SimulationState`.

This ownership fact is fundamental:

> **`SimulationEngine` runs the loop, but `Simulation` owns authoritative state.**

# `StepCoordinator`

Conceptually:

```python
class StepCoordinator(Protocol):
    def coordinate(
        self,
        simulation_state: SimulationState,
    ) -> SimulationState: ...
```

Its contract is deliberately narrow: given the current authoritative snapshot,
produce a completed candidate snapshot for the next step.

# `SequentialStepCoordinator`

Construction:

```python
coordinator = SequentialStepCoordinator(
    stages=(stage_0, stage_1),
)
```

Runtime responsibility:

```text
copy authoritative state
    -> run stages sequentially on one working copy
    -> collect applied-event telemetry
    -> advance step index
    -> attach StepTelemetry
    -> return completed state
```

Later stages intentionally see mutations from earlier stages. Same-stage proposal
simultaneity and cross-stage sequential visibility are different semantics.

# `StoppingCondition` and `MaxSteps`

Contract:

```python
class StoppingCondition(Protocol):
    def should_stop(self, simulation_state: SimulationState) -> bool: ...
```

`MaxSteps` is the basic provided implementation. Stopping policy is injected into
the engine rather than hard-coded into the run loop.

# `Observer`

Conceptually:

```python
@runtime_checkable
class Observer(Protocol):
    def should_observe(self, domain_state, /, *, step_index: int) -> bool: ...

    def observe(self, domain_state, /, *, step_index: int) -> None: ...
```

Observers receive **committed domain state**, not the `SimulationState`
transaction envelope.

Their role is descriptive. They must not become a backdoor for modifying the
causal simulation trajectory.

The engine observes the initial committed state, then observes again after each
successful step commit when the observer policy says to do so.

# Telemetry observers

Telemetry observers consume `StepTelemetry` after a completed state is committed.
They answer a different question from state observers:

```text
Observer
    What does committed state look like?

TelemetryObserver
    What committed transitions produced it?
```

# `AppliedEvent`

One immutable committed event record contains:

```text
event_step_index
stage_index
process_type
event_type
event
effects
```

The event object remains domain-specific; telemetry stores it without forcing the
kernel to understand its fields.

Optional `effects` are opaque domain consequences captured around application
when the domain exposes the effect-journal capability.

# `StepTelemetry`

Groups all `AppliedEvent` values from one completed step:

```text
completed_step_index
events
```

Event ordering follows stage order and resolver/application order.

Telemetry is descriptive, not authoritative modeled state.

# `SimulationSpec`

`SimulationSpec` is the domain-neutral pre-runtime assembly and preflight boundary.

Conceptually:

```python
spec = SimulationSpec(
    initial_domain_state=domain_state,
    step_coordinator=coordinator,
    stopping_condition=MaxSteps(max_steps=100),
    seed=42,
    context=context,
    observers=(observer,),
    telemetry_observers=(telemetry_observer,),
)

compiled = spec.compile()
```

Compilation:

```text
validate structural contracts
collect/validate generic dependencies
    |
    v
construct Simulation
construct SimulationEngine
    |
    v
CompiledSimulation
```

Static generic dependency/configuration failures should happen here rather than
inside hot runtime loops.

Domain-specific compilers may build on this boundary and add domain validation.
The generic spec itself does not learn biological rules.

# `CompiledSimulation`

A small validated bundle:

```text
simulation
engine
dependency_report
```

Typical use:

```python
compiled = spec.compile()
compiled.engine.run(compiled.simulation)
```

# Direct construction versus compilation

For focused examples/tests, direct runtime construction can be clear:

```text
Simulation(...)
SimulationEngine(...)
```

For a complete configured model, prefer `SimulationSpec.compile()` so generic
preflight occurs before mutable runtime starts.

The distinction is:

```text
direct construction
    teach/test/runtime objects directly

SimulationSpec
    describe complete setup + validate + construct runtime
```

# Minimal complete kernel composition

A nonbiological minimal setup conceptually looks like:

```python
stage = StageCoordinator(
    processes=(increment_process,),
    resolver=AcceptAll(),
)

coordinator = SequentialStepCoordinator(stages=(stage,))

spec = SimulationSpec(
    initial_domain_state=counter_state,
    step_coordinator=coordinator,
    stopping_condition=MaxSteps(max_steps=10),
    seed=42,
)

compiled = spec.compile()
compiled.engine.run(compiled.simulation)
```

The kernel does not care whether `counter_state` represents a counter, ecology,
information network, or another copyable domain.

# Extension decision guide

When adding behavior, ask:

```text
new modeled state transition?
    -> Process/event

competing candidates?
    -> Resolver policy

accepted-only deferred details?
    -> EventMaterializer capability

new immutable service/configuration?
    -> SimulationContext / typed ContextKey

new committed-state measurement?
    -> Observer

new causal-event consumer?
    -> TelemetryObserver

new stop rule?
    -> StoppingCondition
```

Do not modify the kernel because a biological feature is complicated. First ask
whether existing contracts can already express it.

# Concept-to-code quick map

| Concept | API |
| --- | --- |
| authoritative state owner | `Simulation` |
| transactional envelope | `SimulationState` |
| immutable services | `SimulationContext` |
| candidate/application mechanism | `Process` |
| optional accepted-only preparation | `EventMaterializer` |
| conflict policy | `Resolver` |
| stage phases | `StageCoordinator` |
| whole-step transaction | `SequentialStepCoordinator` |
| run/stop/observe loop | `SimulationEngine` |
| complete preflight assembly | `SimulationSpec` |
| committed transition record | `AppliedEvent` / `StepTelemetry` |

# You understand this chapter if you can...

- assemble a minimal simulation from the public API;
- explain who owns authoritative state;
- distinguish a process from a resolver and materializer;
- explain what a stage and a step coordinator each own;
- identify when context, observer, telemetry observer, or stopping policy is the
  correct extension point;
- explain `SimulationSpec.compile()` as preflight plus runtime construction; and
- look at a proposed biological feature and avoid changing the kernel when an
  existing public contract already expresses it.

## Next

Read [Kernel Runtime Walkthrough](kernel_runtime.md) to see exactly how these
objects call one another.