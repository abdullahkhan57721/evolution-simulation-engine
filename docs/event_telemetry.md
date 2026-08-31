# Event Telemetry and Causal History

State observations answer **what state did the simulation reach?** Event
telemetry answers the complementary question **what committed events caused that
state?**

The two systems deliberately remain separate. State observers receive the
committed domain state. Telemetry observers receive an ordered causal history of
materialized events that were successfully applied inside a completed
transaction.

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
                → capture event + domain effects
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
- opaque domain effects caused by that event, in occurrence order.

The telemetry envelope deliberately does not prescribe effect types. A biological
world may attach organism, carcass, resource, or environmental mutations; a
nonbiological simulation may attach entirely different effect objects. Consumers
interpret only the effect types belonging to their domain.

Keeping the materialized event likewise preserves process-specific information
without making the telemetry package depend on concrete processes. For example,
`Movement.Event` can expose displacement and energetic cost while a different
domain can expose unrelated event data through the same envelope.

## Biological world effects

`WorldState` maintains a transaction-local mutation journal. Its world-domain
mutation records include:

- `OrganismAdded`, `OrganismRemoved`, and `OrganismMoved`;
- `CarcassAdded` and `CarcassRemoved`;
- `ResourcesChanged`;
- `EnvironmentalValueChanged`.

These records live in `evo_engine.world`, not in the generic telemetry package.
`StageCoordinator` treats values returned by the optional world journal as opaque
objects and attaches them to `AppliedEvent.effects`.

The journal is cleared when a new transactional world copy is created. A stage
captures a journal checkpoint immediately before applying each event and then
associates only subsequent mutations with that event. This avoids repeatedly
comparing complete world snapshots after every event.

Biological observers perform biological interpretation. For example,
`PedigreeRecorder` filters committed effects for `OrganismAdded` and
`OrganismRemoved` while separately using parentage and mortality event semantics.
The generic telemetry envelope itself does not expose organism-specific
convenience properties.

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

## Architectural boundary

The dependency direction is intentional:

```text
telemetry
    → generic AppliedEvent / StepTelemetry envelopes

world
    → biological/ecological mutation records

observation
    → domain-specific interpretation of event + effect objects
```

This lets the same commit/rollback and causal-history machinery support domains
that do not contain organisms, carcasses, spatial resources, or biological
mortality.
