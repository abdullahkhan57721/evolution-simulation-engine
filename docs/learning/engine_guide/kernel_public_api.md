# Kernel Public API

This chapter is the use-oriented map of the public kernel surface. It answers:

> **What do I construct, what do I implement, and how are those pieces connected?**

The package `evo_engine.engine` re-exports the primary kernel-facing names. Start
there before reading internal helpers.

## Two kinds of API

The kernel exposes two conceptually different surfaces.

### Assembly/runtime objects

You construct these to assemble and run a simulation:

```text
Simulation
SimulationState          (usually created by Simulation)
SimulationEngine
StageCoordinator
SequentialStepCoordinator
MaxSteps / StoppingCondition implementation
SimulationSpec            (from evo_engine.configuration)
SimulationContext          (from evo_engine.context)
```

### Extension contracts

You implement these roles to plug behavior into the kernel:

```text
SimulationEvent
Process
EventMaterializer   (optional capability)
Resolver
StepCoordinator     (usually use SequentialStepCoordinator)
StoppingCondition
Observer
TelemetryObserver   (from evo_engine.telemetry)
```

Keeping those groups separate prevents a common confusion: `Process` is not an
engine object you “run” directly; it is a contract hosted by a `StageCoordinator`.

## The smallest runnable composition

A domain-neutral counter demonstrates the public shape with no biology.

```python
import attrs

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    SimulationState,
    StageCoordinator,
)
from evo_engine.resolvers import AcceptAll


@attrs.define(slots=True)
class CounterState:
    value: int = 0

    def copy(self) -> "CounterState":
        return CounterState(value=self.value)


@attrs.frozen(slots=True, kw_only=True)
class IncrementEvent:
    step_index: int
    amount: int = 1


@attrs.frozen(slots=True)
class IncrementProcess:
    @property
    def event_type(self) -> type[IncrementEvent]:
        return IncrementEvent

    def propose_events(self, simulation_state: SimulationState):
        return [
            IncrementEvent(
                step_index=simulation_state.step_index,
                amount=1,
            )
        ]

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: IncrementEvent,
        /,
    ) -> None:
        simulation_state.domain_state.value += event.amount


simulation = Simulation(
    initial_domain_state=CounterState(),
    seed=7,
)

stage = StageCoordinator(
    processes=(IncrementProcess(),),
    resolver=AcceptAll(),
)

engine = SimulationEngine(
    step_coordinator=SequentialStepCoordinator(stages=(stage,)),
    stopping_condition=MaxSteps(max_steps=3),
)

engine.run(simulation)

assert simulation.state.domain_state.value == 3
assert simulation.state.step_index == 3
```

The important object graph is:

```text
Simulation
    owns state

SimulationEngine
    owns run orchestration
      |
      +-- SequentialStepCoordinator
            |
            +-- StageCoordinator
                  |
                  +-- IncrementProcess
                  +-- AcceptAll resolver
```

## `SimulationEvent`

**[KERNEL contract]**

An event must expose:

```text
step_index: int
```

That is intentionally minimal. Event-specific fields belong to the process/domain.

A typical immutable event:

```python
@attrs.frozen(slots=True, kw_only=True)
class IncrementEvent:
    step_index: int
    amount: int
```

The process authors the event's `step_index`; committed telemetry validates it.
The kernel does not silently rewrite event time.

### Think “value describing a transition”

Events are best modeled as values rather than behavior-heavy objects. The process
owns the behavior.

## `Process[ProposedEvent, MaterializedEvent]`

**[KERNEL extension contract]**

A process owns one state-transition mechanism.

It promises:

```text
event_type
propose_events(simulation_state)
apply_event(simulation_state, event)
```

### `event_type`

```python
@property
def event_type(self) -> type[IncrementEvent]:
    return IncrementEvent
```

This declares the **proposal type** owned by the process.

`StageCoordinator` uses it to map resolved events back to their owning process.
Within one stage, two processes may not claim the same proposal event type.

### `propose_events(...)`

```python
def propose_events(self, simulation_state: SimulationState):
    ...
```

This reads the supplied stage-start transactional state and returns zero or more
candidate events.

Architectural rule:

```text
proposal may describe candidate transitions
proposal does not own committed domain mutation
```

A process may use simulation RNG during proposal if the modeled semantics truly
require proposal-time randomness, but accepted-only stochastic work should be
postponed to materialization when possible.

### `apply_event(...)`

```python
def apply_event(
    self,
    simulation_state: SimulationState,
    event: IncrementEvent,
    /,
) -> None:
    simulation_state.domain_state.value += event.amount
```

This is the process's mutation phase.

The positional-only `/` means callers pass the event positionally. More
importantly for architecture, it lets structural implementations choose a natural
parameter name without the generic contract treating that name as semantic API.

## `EventMaterializer`

**[KERNEL optional extension contract]**

A process implements this capability when an accepted proposal needs deferred
work before application.

```python
def materialize_event(
    self,
    simulation_state: SimulationState,
    event: Proposal,
    /,
) -> MaterializedEvent:
    ...
```

Use materialization when information should be determined:

- only for accepted events;
- after resolution;
- while still observing the pre-application stage state.

Typical reasons include stochastic source selection, inheritance outcomes,
variation, or other deferred consequences.

### Proposal type may differ from materialized type

```text
PropagationProposal
        |
 materialize_event
        v
PropagationEvent
```

The proposal can stay small and conflict-oriented while the materialized event
contains the details required for application and telemetry.

## `Resolver`

**[KERNEL extension contract]**

A resolver implements:

```python
def resolve_events(
    self,
    simulation_state: SimulationState,
    proposed_events: Sequence[SimulationEvent],
) -> Sequence[SimulationEvent]:
    ...
```

Its responsibilities are:

```text
inspect complete proposal set
select compatible proposals
choose accepted-event order
```

Its responsibility is **not**:

```text
mutate domain_state
perform the winning process behavior
```

The simplest concrete resolver is:

```python
AcceptAll()
```

which returns all proposals in their original order.

## `StageCoordinator`

**[KERNEL runtime object]**

Construction:

```python
stage = StageCoordinator(
    processes=(process_a, process_b),
    resolver=resolver,
)
```

A stage owns this semantic sequence:

```text
1. collect all process proposals
2. resolve complete proposal sequence
3. materialize every accepted event
4. apply prepared events in resolver order
5. return AppliedEvent telemetry
```

The same `SimulationState` working snapshot is passed through the stage.

### Constructor work

The constructor also:

- freezes the process sequence into a tuple;
- rejects duplicate proposal event types;
- builds event-type dispatch metadata;
- detects/caches optional materializers;
- caches type names used for telemetry.

Those are important implementation details, but they do not change the four-phase
stage semantics.

## `SequentialStepCoordinator`

**[KERNEL runtime object]**

Construction:

```python
coordinator = SequentialStepCoordinator(
    stages=(stage_0, stage_1, stage_2),
)
```

It implements the `StepCoordinator` contract:

```python
coordinate(simulation_state) -> SimulationState
```

Its responsibilities:

```text
copy authoritative input
run stages sequentially on working state
collect applied-event telemetry
increment step_index
attach StepTelemetry
return completed working state
```

It does not itself know what any stage means biologically.

## `StepCoordinator`

**[KERNEL extension contract]**

The interface is intentionally small:

```text
coordinate(current SimulationState) -> completed SimulationState
```

Most simulations should use `SequentialStepCoordinator`. The Protocol exists so
another generic step-coordination strategy could be substituted if a genuine
future need requires different semantics.

Do not implement a custom coordinator merely because one domain wants a
convenience ordering. The frozen kernel's existing stage semantics should normally
host domain behavior above it.

## `SimulationState`

**[KERNEL runtime state]**

Important public fields:

```text
domain_state
context
step_index
rng
last_step_telemetry
```

### `domain_state`

Opaque domain-defined mutable payload. It must provide callable `copy()`.

### `context`

Immutable `SimulationContext`, shared by reference across transactional copies.

### `step_index`

Current committed simulation step index.

### `rng`

The simulation-owned `random.Random` instance. Stochastic model decisions should
consume this generator unless an explicitly modeled independent random source is
itself part of domain state.

### `last_step_telemetry`

`StepTelemetry | None` describing the most recently completed step in this state
snapshot.

### `copy()`

Creates an independent transactional envelope by:

```text
copying domain_state
cloning complete RNG state
sharing immutable context
preserving step_index
clearing last_step_telemetry
```

## `SimulationContext` and `ContextKey[T]`

**[KERNEL/generic foundation]**

`SimulationContext` stores immutable named services/configuration.

The typed lookup path is:

```python
value = simulation_state.context.require(MY_CONTEXT_KEY)
```

A `ContextKey[T]` carries:

```text
name
runtime value_type
static generic return type T
```

This gives explicit access without manufacturing arbitrary dynamic attributes on
`SimulationState`.

### Named construction sugar

You may also construct:

```python
Simulation(
    initial_domain_state=world,
    genetic_architecture=architecture,
)
```

Those keyword values are normalized into a `SimulationContext`. They do not become
new simulation attributes.

## `Simulation`

**[KERNEL runtime object]**

Construction:

```python
simulation = Simulation(
    initial_domain_state=my_state,
    seed=42,
    context=context,
)
```

or with named context-value sugar when no complete `context` is supplied.

The constructor:

1. requires the initial domain state to be copyable;
2. copies the initial domain state so the runtime does not reuse the caller's
   mutable object directly;
3. creates the seeded simulation RNG;
4. constructs the initial `SimulationState`;
5. stores it as `simulation.state`.

`simulation.context` is a convenience property returning
`simulation.state.context`.

## `StoppingCondition` and `MaxSteps`

**[KERNEL contract + concrete implementation]**

A stopping condition answers:

```text
should_stop(simulation_state) -> bool
```

`MaxSteps` is the standard simple implementation:

```python
MaxSteps(max_steps=10)
```

It stops when:

```text
simulation_state.step_index >= max_steps
```

A domain-specific stopping condition can inspect `domain_state` if the modeled
termination criterion genuinely belongs to that domain.

## `Observer`

**[KERNEL extension contract]**

An observer receives committed `domain_state`, not the whole mutable kernel state:

```python
should_observe(domain_state, *, step_index) -> bool
observe(domain_state, *, step_index) -> None
```

The API reinforces the responsibility:

> Observe the committed modeled domain without participating in updates.

Observers are called once before the run loop begins and after each committed
step when `should_observe(...)` returns true.

## `AppliedEvent` and `StepTelemetry`

**[KERNEL telemetry values]**

`AppliedEvent` records one successfully applied materialized event:

```text
event_step_index
stage_index
process_type
event_type
event
effects
```

`StepTelemetry` groups applied events for one completed step:

```text
completed_step_index
events: tuple[AppliedEvent, ...]
```

These are immutable descriptive records.

## `TelemetryObserver`

**[KERNEL telemetry extension contract]**

A telemetry observer consumes committed `StepTelemetry` independently of domain
state observers.

Use it when the question is about causal transition history rather than only the
resulting state snapshot.

## `SimulationSpec`

**[GENERIC CONFIGURATION / composition boundary]**

For nontrivial construction, prefer describing a complete simulation before
runtime:

```python
compiled = SimulationSpec(
    initial_domain_state=state,
    step_coordinator=coordinator,
    stopping_condition=MaxSteps(max_steps=6),
    seed=84,
    context=context,
    observers=(observer,),
    telemetry_observers=(telemetry_observer,),
).compile()
```

Compilation:

```text
validate structural contracts
collect generic dependency requirements
reject missing dependencies
create Simulation
create SimulationEngine
return CompiledSimulation
```

`CompiledSimulation` bundles:

```text
simulation
engine
dependency_report
```

Domain-specific compilers may build on `SimulationSpec` and add domain validation,
but the generic preflight layer must stay domain-neutral.

## Dependency declarations

Configured components may declare required generic `Dependency` values.

Conceptually:

```text
component graph requires:
    capability A
    capability B

configuration provides:
    capability A

compile
    -> missing B diagnostic
```

The report preserves provenance when available, so diagnostics can identify which
configured component required the missing capability.

This is static wiring validation, not evolving simulation state.

## Concept -> public API map

| Concept | Public API |
| --- | --- |
| authoritative simulation | `Simulation` |
| transactional snapshot | `SimulationState` |
| immutable services/config | `SimulationContext`, `ContextKey` |
| run loop | `SimulationEngine` |
| complete step transaction | `SequentialStepCoordinator` |
| one update phase | `StageCoordinator` |
| candidate transition value | `SimulationEvent` |
| modeled transition behavior | `Process` |
| accepted-only deferred detail | `EventMaterializer` |
| conflict/competition policy | `Resolver` |
| run termination policy | `StoppingCondition`, `MaxSteps` |
| committed state measurement | `Observer` |
| committed causal history | `AppliedEvent`, `StepTelemetry`, `TelemetryObserver` |
| pre-runtime specification | `SimulationSpec` |

## Code -> concept map

When you see:

```text
Simulation(...)
    think: authoritative state owner + seeded initial transaction envelope

state.copy()
    think: transaction boundary

StageCoordinator(...)
    think: same-stage transition semantics

process.propose_events(...)
    think: candidates from stage-start snapshot

resolver.resolve_events(...)
    think: acceptance/order, not mutation

process.materialize_event(...)
    think: accepted-only deferred consequence

process.apply_event(...)
    think: process-owned domain mutation

simulation.state = coordinator.coordinate(...)
    think: commit

observer.observe(...)
    think: committed state description

telemetry.events
    think: transitions that actually applied in committed step
```

## What normally belongs outside the kernel API

If your new concept contains words such as:

```text
genome
organism
mating
energy
predator
resource
phenotype
chromosome
```

that is a strong signal it belongs above the kernel.

The kernel API should change only if the domain cannot represent required behavior
correctly through the existing generic contracts, or a genuine generic
correctness/determinism/diagnostics/performance problem exists.

## Misconception checks

### “I should instantiate `SimulationState` directly for every run.”

Usually `Simulation` or `SimulationSpec.compile()` should create the initial state.
Direct construction is useful in focused tests and low-level integration.

### “A `Process` returns the new state.”

No. A process proposes event values and later mutates the supplied working
`SimulationState` during application.

### “`EventMaterializer` is required for every process.”

No. It is an optional capability.

### “`SimulationSpec` replaces domain compilers.”

No. It is the generic preflight/compilation boundary. Domain compilers can layer
stronger domain validation above it.

### “Context values passed as keywords become object attributes.”

No. That syntax is construction sugar for immutable context storage.

## You understand this chapter if you can…

- assemble the counter example from `Simulation`, a process, `StageCoordinator`,
  `SequentialStepCoordinator`, a resolver, `SimulationEngine`, and `MaxSteps`;
- explain which API objects you construct versus which Protocols you implement;
- explain the difference between a proposal event type and a materialized event
  type;
- identify which component owns domain mutation and which owns conflict selection;
- explain how context lookup differs from dynamic attributes;
- explain when to use a domain-state observer versus a telemetry observer; and
- explain why `SimulationSpec` exists even though you could manually instantiate
  `Simulation` and `SimulationEngine`.

Next: [Kernel Runtime](kernel_runtime.md).
