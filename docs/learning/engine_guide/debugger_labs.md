# Debugger Labs

Reading architecture becomes much easier after you watch one transaction execute.
These labs turn the conceptual diagrams into observable runtime state.

The exact debugger UI does not matter. Use your editor's Python debugger or
`pdb`. The important part is **where you stop and what questions you ask**.

## Lab discipline: predict before stepping

Before every lab:

1. write down what you expect to happen;
2. identify which object should be authoritative versus working state;
3. predict whether RNG/state mutation should have occurred yet;
4. then use the debugger to test the prediction.

If you merely watch locals change, you will learn less.

# Lab 1 — Follow the smallest counter step

Use the domain-neutral counter fixtures in
[`tests/engine/helpers.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/helpers.py)
and the nonbiological kernel test as your mental model.

## Suggested breakpoints

Set breakpoints at:

```text
SimulationEngine.run
SequentialStepCoordinator.coordinate
SimulationState.copy
StageCoordinator.coordinate
StageCoordinator._propose_events
AcceptAll.resolve_events
IncrementProcess.propose_events
IncrementProcess.apply_event
```

## At `SimulationEngine.run`

Inspect:

```text
simulation.state
simulation.state.step_index
simulation.state.domain_state
id(simulation.state)
id(simulation.state.domain_state)
```

Write down the object identities.

Question:

> Is this the authoritative state?

Yes. `Simulation` owns this reference.

## Step into `SequentialStepCoordinator.coordinate`

Before `copy()`:

```text
simulation_state is simulation.state
```

After:

```python
working_state = simulation_state.copy()
```

compare:

```text
id(simulation_state)
id(working_state)

id(simulation_state.domain_state)
id(working_state.domain_state)

id(simulation_state.rng)
id(working_state.rng)
```

Predictions:

```text
SimulationState identities differ
domain_state identities differ
RNG identities differ
context identity is the same
step_index values are equal
```

## Enter the stage

At `_propose_events`, record:

```text
working_state.domain_state.value
working_state.step_index
```

Then enter `IncrementProcess.propose_events`.

Question:

> Has any domain mutation occurred in this stage yet?

No.

## Enter the resolver

At `AcceptAll.resolve_events`, inspect the proposal list.

Questions:

```text
Does the resolver receive the complete proposal sequence?
Has it changed domain_state?
What order does it return?
```

## Enter application

At `IncrementProcess.apply_event`, inspect:

```text
working_state.domain_state.value
simulation.state.domain_state.value
```

During the transaction, the working value should change while the simulation's
authoritative value remains unchanged.

This is the most important observation in the lab.

## Return to the engine

Stop immediately before and after:

```python
simulation.state = self.step_coordinator.coordinate(...)
```

Notice when the new state reference actually becomes authoritative.

### Mastery question

Can you point to the exact instant at which an applied working-state mutation
becomes committed simulation state?

# Lab 2 — Prove same-stage proposal simultaneity

Build or adapt a tiny test with two processes in the same stage.

Start:

```text
counter = 10
```

Process A proposes an event and would later change the counter.
Process B records the counter value it sees during proposal.

## Prediction

What should B see?

```text
10
```

not the result of A's application.

## Breakpoints

```text
StageCoordinator._propose_events
ProcessA.propose_events
ProcessB.propose_events
_apply_prepared_applications
```

Verify that the complete proposal loop finishes before application begins.

## Compare with a deliberately naive implementation

Temporarily sketch—not commit—this pseudocode:

```python
for process in processes:
    events = process.propose_events(state)
    for event in events:
        process.apply_event(state, event)
```

Predict what B would observe there.

The contrast explains why the phase boundary exists.

# Lab 3 — Prove materialize-all-before-apply

The focused test
[`test_all_events_materialize_before_any_apply`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_stage_coordinator.py)
is already a compact laboratory.

Initial state:

```text
counter = 10
```

Two accepted events each materialize by recording the current counter and later
apply by subtracting one.

## Prediction

Materialization observations should be:

```text
[10, 10]
```

Final state should be:

```text
8
```

## Breakpoints

```text
StageCoordinator._prepare_applications
MaterializingProcess.materialize_event
_apply_prepared_applications
MaterializingProcess.apply_event
```

Watch the prepared list grow while `domain_state.value` remains `10`.

Only after preparation is complete should application reduce it.

## Counterfactual

If the sequence were materialize-A/apply-A/materialize-B/apply-B, what would the
recorded observations be?

```text
[10, 9]
```

That counterfactual is the failure mode ADR 0002 protects against.

# Lab 4 — Watch accepted-only RNG

Use the nonbiological token example:

```bash
venv/bin/python examples/nonbiological_evolution.py
```

Set breakpoints in:

```text
TokenPropagationProcess.propose_events
TokenPropagationProcess.materialize_event
TokenVariation.vary
TokenPropagationProcess.apply_event
```

## During proposal

Inspect a `PropagationProposal`.

It contains:

```text
step_index
recipient_id
```

It does not contain source or propagated state.

Ask:

> Has source-selection RNG been consumed for this proposal yet?

No. That decision belongs to accepted materialization.

## During materialization

Watch:

```python
source = simulation_state.rng.choices(...)[0]
```

and then variation using the same `simulation_state.rng`.

Inspect the returned `PropagationEvent`.

Now the event contains the stochastic outcome as data.

## During application

Verify that application performs no source selection. It simply commits the
already-materialized replacement.

This is an important design goal: **make stochastic outcome data explicit before
mutation** when the semantics allow it.

# Lab 5 — Rejected proposals should not consume materialization RNG

Create a tiny resolver that accepts only the first of two proposals.

Create a materializer that:

```text
draws rng.randint(...)
appends the draw to a debug list
```

## Prediction

With two proposals but only one accepted:

```text
number of materializer RNG draws = 1
```

not 2.

Then add ten more proposals that the resolver always rejects.

Prediction:

> The accepted event's materialization trajectory should not change merely because
> rejected proposals exist, assuming proposal generation itself consumes no RNG.

This lab helps you distinguish **proposal-time randomness** from
**accepted-only randomness**.

# Lab 6 — Failed transaction preserves committed state and RNG

Create a two-stage step:

```text
Stage 0
    mutates working counter
    consumes RNG

Stage 1
    raises RuntimeError
```

Before running, record:

```python
old_state = simulation.state
old_domain_value = simulation.state.domain_state.value
old_rng_state = simulation.state.rng.getstate()
```

Run one coordination attempt inside `pytest.raises(...)` or a `try/except`.

## Prediction

After failure:

```text
simulation.state is old_state
simulation.state.domain_state.value == old_domain_value
simulation.state.rng.getstate() == old_rng_state
```

The mutated working copy may have existed, but it was never returned/assigned.

## What not to look for

Do not search for a giant rollback method. The architecture achieves rollback by
not mutating authoritative state in the first place.

# Lab 7 — Stage ordering is intentionally visible

Build two stages:

```text
Stage 0: +3
Stage 1: x4
```

Start at `2`.

Prediction:

```text
2 -> 5 -> 20
```

Reverse the stage tuple.

Prediction:

```text
2 -> 8 -> 11
```

This lab distinguishes:

```text
same-stage simultaneity
from
cross-stage sequential causality
```

The engine is not trying to erase ordering. It is making ordering explicit where
it belongs.

# Lab 8 — Observer versus telemetry observer

Use a recorder that implements both observer surfaces, like the nonbiological
`EvolutionRecorder`.

Breakpoints:

```text
SimulationEngine._observe_telemetry
SimulationEngine._observe
```

After commit, inspect:

```text
StepTelemetry.events
current domain_state composition
```

Ask:

```text
What happened?          -> telemetry
What is true now?       -> state observation
```

Then confirm both are operating on committed results.

# Lab 9 — Context identity across transactions

Create a simulation with a known `SimulationContext` or named context value.

Record:

```python
id(simulation.state.context)
```

Step into `SimulationState.copy()` and compare:

```python
id(working_state.context)
```

Prediction:

```text
same object identity
```

Then compare domain-state and RNG identities:

```text
different
```

This lab makes the mutable/immutable split concrete.

# Lab 10 — Read a production biological process by phase

After the kernel labs, choose `Aging` or another focused process.

Do **not** begin by trying to understand every biological helper it calls.

First find:

```text
event_type
propose_events
materialize_event?  (if present)
apply_event
```

Label each line by phase:

```text
read/propose
accepted-only preparation
mutation
```

Then trace the domain helpers.

This source-reading order prevents biological detail from obscuring the kernel
contract.

# A debugger worksheet

At every interesting breakpoint, fill out:

```text
Current function:
Current layer:
Current phase:
Authoritative or working state?
Current step_index:
Current stage_index:
Event semantic status:
    proposed / resolved / materialized / applied telemetry
Has domain mutation happened in this stage yet?
Has simulation RNG been consumed here?
If an exception occurs now, what remains authoritative?
What telemetry will exist if the transaction commits?
```

After a few labs, these questions should become automatic.

# You understand these labs if you can…

- visually distinguish authoritative and working object identities in a debugger;
- prove that same-stage proposal and materialization semantics match the contract;
- watch RNG advance only in the working transaction and explain rollback;
- identify the commit assignment without searching for a `commit()` method;
- separate state observation from committed transition telemetry; and
- debug a new process by locating its phase responsibilities before exploring its
  domain helpers.

Next: [Exercises](exercises.md).
