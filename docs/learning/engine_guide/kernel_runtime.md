# Kernel Runtime: One Complete Step Behind the Scenes

This chapter follows a simulation from `engine.run(simulation)` through one
committed step. The emphasis is on **state ownership, phase ordering, RNG
semantics, and what each component is allowed to observe or mutate**.

## The entire runtime in one diagram

```text
engine.run(simulation)
        |
        +--> observe initial committed state
        |
        +--> stopping_condition.should_stop(simulation.state)
        |
        v
SequentialStepCoordinator.coordinate(authoritative state)
        |
        +--> SimulationState.copy()
        |       |
        |       +--> copy domain_state
        |       +--> clone RNG state
        |       +--> share immutable context
        |
        v
working state
        |
        +--> StageCoordinator #0
        |       |
        |       +--> propose all
        |       +--> resolve
        |       +--> materialize all accepted
        |       +--> apply accepted + AppliedEvent telemetry
        |
        +--> StageCoordinator #1
        |       `-- same four phases
        |
        +--> ...
        |
        +--> increment working_state.step_index
        +--> attach StepTelemetry
        |
        v
return completed working state
        |
        v
simulation.state = returned state     <-- COMMIT
        |
        +--> telemetry observers
        +--> domain-state observers
        |
        v
next stop check
```

## Phase 0: construction has already frozen important choices

Before runtime begins, the configured object graph already determines:

```text
ordered stages
ordered processes inside each stage
resolver for each stage
stopping condition
observers
telemetry observers
immutable context
initial seed
```

`StageCoordinator.__init__()` also builds dispatch metadata and detects optional
materializers once rather than performing expensive structural inspection for
every applied event.

This distinction matters:

```text
construction time
    validate/cache stable wiring

runtime
    execute evolving decisions
```

## Phase 1: `SimulationEngine.run()` observes the initial state

The production run loop begins conceptually as:

```python
def run(self, simulation):
    self._observe(simulation.state)
    while not self.stopping_condition.should_stop(simulation.state):
        ...
```

The initial state is observable at `step_index == 0` before any transition is
executed.

This is useful for recorders that want a baseline.

### What observers receive

The ordinary observer API receives:

```text
domain_state
step_index
```

not the mutable `SimulationState` object itself.

That keeps the observer-facing contract focused on committed domain measurement.

## Phase 2: stopping condition reads authoritative state

The engine asks:

```python
self.stopping_condition.should_stop(simulation.state)
```

For `MaxSteps(max_steps=3)`:

```text
step_index 0 -> continue
step_index 1 -> continue
step_index 2 -> continue
step_index 3 -> stop
```

A stopping condition runs **before** starting the next transaction.

## Phase 3: the engine asks for one complete transaction

The key call is:

```python
simulation.state = self.step_coordinator.coordinate(
    simulation_state=simulation.state,
)
```

Do not read this as “mutate `simulation.state` in place.”

Read the right-hand side first:

```text
old authoritative state
        |
        v
coordinate(...)
        |
        v
completed new state
```

Only after `coordinate(...)` returns successfully does Python perform the
assignment on the left.

That makes this line the commit boundary.

## Phase 4: `SequentialStepCoordinator` copies the state

The real method begins:

```python
working_state = simulation_state.copy()
applied_events: list[AppliedEvent] = []
```

### Why the input is authoritative

The caller passed `simulation.state`, which is the current committed truth.

### Why `working_state` is safe to mutate

`SimulationState.copy()` creates a separate transaction envelope.

The implementation:

```python
copied_rng = random.Random.__new__(random.Random)
copied_rng.setstate(self.rng.getstate())
return SimulationState(
    domain_state=self.domain_state.copy(),
    context=self.context,
    step_index=self.step_index,
    rng=copied_rng,
    last_step_telemetry=None,
)
```

Architecturally:

```text
domain_state -> independently copied
rng          -> independently cloned at exact internal state
context      -> shared by reference because immutable
step_index   -> copied as value
telemetry    -> cleared until this transaction completes
```

## A failed step does not need an undo algorithm

Suppose stage 0 mutates `working_state`, consumes RNG, and stage 1 raises.

Control exits `coordinate(...)` before it returns.

Therefore this assignment never happens:

```text
simulation.state = working_state
```

The caller still owns the original object:

```text
authoritative state
    domain state: unchanged
    RNG state: unchanged
```

The dirty working copy becomes irrelevant.

This is rollback by **isolation**, not by reversal.

## Phase 5: stages run sequentially on the same working transaction

The coordinator loops:

```python
for stage_index, stage in enumerate(self.stages):
    stage_events = stage.coordinate(
        simulation_state=working_state,
        stage_index=stage_index,
    )
    applied_events.extend(stage_events)
```

Important consequence:

```text
stage 0 may mutate working_state
stage 1 sees stage 0's completed mutations
stage 2 sees stage 0 + stage 1 mutations
```

Stages are therefore an explicit way to model ordering when ordering is intended.

## Phase 6: one `StageCoordinator` proposes from its stage-start state

The stage calls:

```python
proposed_events = self._propose_events(simulation_state)
```

and `_propose_events` conceptually does:

```python
proposed_events = []
for process in self.processes:
    proposed_events.extend(process.propose_events(simulation_state))
```

### Why every proposer sees the same state

No application occurs inside this loop.

So even though Python invokes processes sequentially, they all receive the same
mutational snapshot.

This is **semantic simultaneity implemented through phase separation**.

### Proposal ordering still exists

Proposals are collected in configured process order and each process's returned
sequence order. That ordering may be visible to a resolver.

The contract is not “unordered mathematics.” It is:

> All processes propose before any same-stage application.

## Phase 7: the resolver sees the complete proposal sequence

The stage calls:

```python
resolved_events = self.resolver.resolve_events(
    simulation_state=simulation_state,
    proposed_events=proposed_events,
)
```

The resolver gets:

```text
same stage-start SimulationState
+
complete proposed-event sequence
```

It returns the accepted sequence in the order events should later be prepared and
applied.

### Resolver must not become the mutator

The resolver can inspect state to decide conflicts, but domain mutation remains
owned by the process.

A resolver that mutates the domain would make proposal/materialization semantics
much harder to reason about and would mix policy with transition behavior.

## Phase 8: `StageCoordinator` maps accepted events back to process owners

During construction, the stage created a mapping:

```text
proposal event type -> process dispatch metadata
```

For each resolved event:

```python
event_type = type(resolved_event)
dispatch = self._dispatch_by_event_type.get(event_type)
```

If the resolver returns an event type no process owns, the kernel raises rather
than guessing.

This protects event ownership.

## Phase 9: all accepted events materialize

The stage builds a prepared-application list:

```python
prepared_applications = self._prepare_applications(
    simulation_state,
    resolved_events,
)
```

For every resolved event:

```text
find owning process
if it has materialize_event:
    call materializer using current stage state
else:
    use resolved event directly
store (process, materialized event, telemetry metadata)
```

Crucially, `_prepare_applications` completes the **entire accepted sequence** before
application begins.

## Why materialization sees pre-application state

Suppose accepted events A and B each choose a stochastic source based on current
resources.

The required sequence is:

```text
materialize A from state S
materialize B from state S
apply A -> state S1
apply B -> state S2
```

not:

```text
materialize A from S
apply A -> S1
materialize B from S1    <-- wrong same-stage observation
```

This is protected by focused tests.

## Materialization and RNG

A materializer receives the same `SimulationState`, including the transaction's
`rng`.

Therefore accepted-only stochastic choices consume the working RNG in resolver
order during materialization.

If the entire step later fails, those draws disappear with the working state.

If the step succeeds, the returned state's RNG contains the advanced stream and
becomes authoritative at commit.

This is the full chain:

```text
committed RNG(t)
      |
     clone
      |
working RNG(t)
      |
accepted materialization draws
      |
      v
working RNG(t+1 state)
      |
transaction success
      |
      v
committed RNG in new SimulationState
```

## Phase 10: apply prepared events in resolver order

Only after preparation is complete does the stage call the application helper.

Conceptually:

```python
for process, event in prepared_applications:
    process.apply_event(simulation_state, event)
```

This is where same-stage domain mutation begins.

Each process receives its own materialized event and the shared working
`SimulationState`.

## Optional effect capture happens around each application

The production helper supports an optional domain effect journal.

Before each application:

```text
read domain_state.effect_count if present
```

Then:

```text
process.apply_event(...)
```

Then, if effect journaling is active:

```text
domain_state.effects_since(checkpoint)
```

New effects are attached to that event's `AppliedEvent` telemetry.

### Why checkpoint immediately before each application

The checkpoint is per event rather than once for the whole stage, so effects can
be associated with the transition that caused them.

### Why effects are opaque

The kernel validates that the effect journal has the expected structural shape,
but it does not interpret effect content.

That preserves domain neutrality.

## Phase 11: create `AppliedEvent`

After a process successfully applies an event, the kernel records:

```text
event_step_index
authoritative stage_index
process type name
materialized event type name
materialized event object
captured opaque effects
```

`AppliedEvent` means:

> This materialized transition was successfully applied inside the working
> transaction.

At the step level, it still becomes authoritative only if the entire transaction
returns and is committed by `SimulationEngine`.

## Phase 12: finish all stages

`SequentialStepCoordinator` concatenates stage telemetry in stage/application
order.

After the final stage succeeds:

```python
working_state.step_index += 1
```

The step index therefore represents **completed steps**, not “currently executing
stage count.”

Then it creates:

```python
working_state.last_step_telemetry = StepTelemetry._from_kernel_values(
    completed_step_index=working_state.step_index,
    events=tuple(applied_events),
)
```

Now the working state contains a complete description of the step that produced
it.

## Phase 13: return the completed working state

The coordinator returns:

```python
return working_state
```

At this instant the caller has a candidate completed new snapshot.

The old authoritative state still exists until the caller performs assignment.

## Phase 14: `SimulationEngine` commits by replacing `simulation.state`

Returning to:

```python
simulation.state = self.step_coordinator.coordinate(...)
```

now the assignment occurs.

```text
before:
    simulation.state -> old State(t)

after:
    simulation.state -> completed State(t+1)
```

This is the exact moment the new state becomes authoritative from the simulation
object's perspective.

## Phase 15: telemetry observers run

The engine reads:

```python
telemetry = simulation_state.last_step_telemetry
```

and supplies it to configured telemetry observers whose
`should_observe_telemetry(...)` returns true.

These observers see committed transition history.

## Phase 16: domain-state observers run

Then the engine unwraps:

```python
domain_state = simulation_state.domain_state
```

and calls ordinary observers that choose to observe the current step.

These observers see committed modeled state.

The order is therefore:

```text
commit
  |
  +--> telemetry observers
  |
  +--> domain-state observers
```

## Phase 17: repeat stop check

The loop returns to:

```text
stopping_condition.should_stop(simulation.state)
```

using the newly committed state.

## The state timeline

A useful notation is:

```text
S0 committed
  |
  | copy
  v
W0
  |
  | stages mutate W0
  v
W1 completed
  |
  | commit assignment
  v
S1 committed
  |
  | copy
  v
W1'
  |
  ...
```

`W0` and `S0` may have equal values initially, but they are different mutable
domain objects and different RNG objects.

## The event timeline

Do not use the word “event” without asking which semantic stage you mean.

```text
PROPOSED EVENT
candidate transition produced by process
        |
        v
RESOLVED EVENT
proposal selected by resolver
        |
        v
MATERIALIZED EVENT
accepted transition with deferred details determined
        |
        v
PROCESS APPLICATION
working domain state is mutated
        |
        v
AppliedEvent
immutable telemetry record describing successful application
```

A proposal object and materialized event object may be the same Python type for a
simple process, but their **semantic role in the pipeline is still different**.

## Example: the nonbiological token process

The repository's token propagation example makes materialization especially clear.

### Proposal

```python
PropagationProposal(
    step_index=simulation_state.step_index,
    recipient_id=node_id,
)
```

The proposal says only:

> This recipient has a replacement opportunity.

It does not yet choose a source or variation result.

### Materialization

After acceptance, `materialize_event(...)`:

1. reads all source nodes;
2. computes weights from expressed broadcast characteristics;
3. uses `simulation_state.rng.choices(...)` to select a source;
4. propagates and possibly varies the selected token using the same simulation RNG;
5. returns a richer `PropagationEvent` with source and propagated state recorded.

### Application

`apply_event(...)` does one simple mutation:

```python
network.nodes[event.recipient_id].token = event.propagated_state
```

This is an excellent demonstration of the phases:

```text
proposal: who may receive?
resolution: which opportunities survive?
materialization: source + variation outcome?
application: perform replacement
```

## Why observers do not see rejected proposals

Ordinary observers receive only committed domain state.
Telemetry observers receive only committed `AppliedEvent` records.

Rejected candidate proposals are therefore not part of committed causal history by
default.

If a domain needs proposal diagnostics, that is a separate diagnostic concern and
should not be confused with authoritative applied-event telemetry.

## Determinism depends on component ordering too

A fixed seed is necessary but not always sufficient for identical trajectories.
The kernel contract assumes equal:

```text
initial state
configuration/context
seed
component ordering
```

If two materializers consume RNG in a different accepted-event order, they may
receive different draws even with the same seed.

That is not a defect: accepted-event ordering is part of the configured execution
semantics.

## Runtime debugging questions

At any breakpoint, ask:

```text
Is this simulation.state or a working copy?
What is step_index?
Has this stage started applying yet?
Is this event only proposed, resolved, or materialized?
Has RNG been consumed in this transaction?
Would a failure here leave authoritative state unchanged?
What telemetry will exist if the transaction commits?
```

Those questions are more useful than simply inspecting every local variable.

## Misconception checks

### “When `AppliedEvent` is created, the step is already committed.”

Not necessarily. It records successful application inside the working transaction.
The entire step must still return and replace `simulation.state`.

### “All same-stage events are applied simultaneously.”

No. They are applied in resolver order. Proposal and materialization share the
pre-application state.

### “The process must avoid mutating `SimulationState` entirely.”

No. `apply_event` is specifically where process-owned mutation of the working
state belongs.

### “The old state disappears when `copy()` is called.”

No. The old authoritative object remains untouched and referenced by `Simulation`
until a successful result replaces it.

### “A rejected event has a materialized stochastic outcome hidden somewhere.”

Not when the stochastic work is correctly deferred to materialization. Rejected
proposals never reach that phase.

## You understand this chapter if you can…

- trace one call from `SimulationEngine.run()` to `SimulationState.copy()` and
  back to the commit assignment;
- identify exactly when stages can see previous-stage mutation and when same-stage
  processes cannot;
- explain the state seen by proposal, resolver, materializer, and application;
- explain how RNG draws survive or disappear with transaction success/failure;
- distinguish proposed/resolved/materialized event values from `AppliedEvent`
  telemetry;
- explain how per-application domain effects are captured without the kernel
  understanding them; and
- place observers and telemetry observers after the commit boundary.

Next: [Kernel Design Rationale and Invariants](kernel_design_rationale.md).
