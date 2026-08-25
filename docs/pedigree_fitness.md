# Pedigree and Lifetime Fitness

The engine can reconstruct direct pedigree relationships and individual lifetime
fitness from committed event telemetry without embedding ancestry bookkeeping in
`Organism` itself.

## Recorder

`PedigreeRecorder` implements both the state-observer and telemetry-observer
interfaces. Attach the same instance to both observer collections:

```python
from evo_engine.observation import PedigreeRecorder

pedigree = PedigreeRecorder()
engine = SimulationEngine(
    step_coordinator=coordinator,
    stopping_condition=stopping_condition,
    observers=(pedigree,),
    telemetry_observers=(pedigree,),
)
```

The baseline state registers founders. Later committed telemetry records births,
parentage, and biological deaths.

## Structural biological capabilities

Telemetry interpretation is capability-based rather than process-name-based.

`ParentageEvent` exposes `parent_ids`. A committed event that both exposes those
parents and adds an organism is interpreted as a biological birth.

`MortalityEvent` exposes `deceased_organism_ids`. A committed event is treated as
biological mortality only when it explicitly implements that capability and the
same applied event removes those organisms from the active world.

This distinction is important: removal from `WorldState` alone does **not** mean
death. Future migration, dormancy, or temporary-removal processes can therefore
remove organisms without corrupting mortality statistics.

Built-in starvation, maximum-age mortality, and predation events expose the
mortality capability. Reproduction events already expose their reproductive
parents structurally.

## Individual records

Each `IndividualLifeHistory` contains value-only historical information:

- permanent organism ID
- biological parent IDs
- founder status
- entry step and age
- inferred or observed birth step
- death step and cause
- direct offspring IDs
- realized reproductive success so far
- completed lifetime reproductive success after death
- lifespan when birth and death are both known

For a living organism, `lifetime_reproductive_success` is `None`, not its current
offspring count. The final lifetime outcome is right-censored until biological
death occurs. `realized_reproductive_success` remains available while the
organism is alive.

## Reference ecology

The complete reference preset attaches three complementary measurement systems:

```python
from evo_engine.presets import build_reference_ecology

ecology = build_reference_ecology()
ecology.engine.run(ecology.simulation)

population_history = ecology.recorder
event_history = ecology.event_recorder
pedigree = ecology.pedigree_recorder
```

Together they answer three different questions:

```text
PopulationRecorder
    -> what changed in the population?

EventRecorder
    -> which committed processes caused the changes?

PedigreeRecorder
    -> who descended from whom, who died, and how much direct fitness
       did each individual realize?
```

Pedigree remains observation-layer state. The simulation's biological entities
do not need parent pointers or lifetime counters merely to support analysis.
