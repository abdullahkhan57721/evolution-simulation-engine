# Event Telemetry and Causal History

Population observations answer **what state did the simulation reach?** Event
telemetry answers the complementary question **what committed events caused that
state?**

The two systems deliberately remain separate. State observers receive immutable
summaries of authoritative `WorldState` values. Telemetry observers receive an
ordered causal history of materialized events that were successfully applied
inside a completed transaction.

## Commit semantics

A simulation step still runs against a transactional copy:

```text
SimulationEngine
    → SequentialStepCoordinator
        → StageCoordinator
            → propose
            → resolve
            → materialize
            → apply
                → capture event + structural effects
        → all stages succeed
        → increment completed step
        → commit SimulationState
        → emit StepTelemetry
```

If any stage raises, the working state and its telemetry are discarded together.
`TelemetryObserver` implementations therefore never receive events from failed
steps.

## Applied events

Each `AppliedEvent` records:

- the materialized domain event itself;
- its event step index;
- its zero-based lifecycle stage index;
- the fully qualified process and event types;
- structural world mutations caused by that event.

Keeping the materialized event preserves process-specific information without
making the telemetry package depend on concrete processes. For example,
`Movement.Event` can still expose displacement, target, purpose, and energetic
cost, while `Reproduction.Event` can still expose parents and parental
investment.

## Structural world effects

`WorldState` maintains a transaction-local mutation journal. Built-in mutation
records cover:

- organism addition and removal;
- organism movement;
- carcass addition and removal;
- resource quantity changes with before/after values.

The journal is cleared when a new transactional world copy is created. A stage
captures a journal checkpoint immediately before applying each event and then
associates only subsequent mutations with that event.

This avoids repeatedly comparing complete world snapshots after every event.

## Recording a run

`EventRecorder` is a built-in `TelemetryObserver`:

```python
from evo_engine.observation import EventRecorder
from evo_engine.engine import SimulationEngine

recorder = EventRecorder()

engine = SimulationEngine(
    step_coordinator=coordinator,
    stopping_condition=stopping_condition,
    telemetry_observers=(recorder,),
)

engine.run(simulation)

for step in recorder.steps:
    print(step.completed_step_index, len(step.events))

movement_events = recorder.events_for_process("Movement")
```

`EventRecorder.steps` preserves commit order, and each step preserves lifecycle
stage and resolver application order.

## Reference ecology

`build_reference_ecology()` attaches both measurement layers automatically:

```python
from evo_engine.presets import build_reference_ecology

ecology = build_reference_ecology()
ecology.engine.run(ecology.simulation)

population_history = ecology.recorder.observations
causal_history = ecology.event_recorder.steps
```

The population recorder answers questions such as how mean growth rate or
population size changed. The event recorder can then be used to investigate the
mechanisms behind those changes, such as mortality, reproduction, feeding,
growth, or movement events.

## Scope

This milestone records causal event history but does not yet infer biological
fitness, pedigree, allele frequencies, or statistical experimental outcomes.
Those analyses should consume committed observations and telemetry rather than
being embedded inside simulation processes.
