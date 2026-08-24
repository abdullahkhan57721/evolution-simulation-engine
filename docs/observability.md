# Evolution Observability

The engine separates simulation dynamics from measurement. Processes and
resolvers determine what happens; observers inspect only committed states after
transactional execution succeeds.

## Observer boundary

`SimulationEngine` accepts zero or more structural `Observer` implementations.
An observer receives only:

```text
committed WorldState
completed step_index
```

rather than the full mutable orchestration state. This keeps measurement code
independent of stage coordination, stopping rules, random-number-generator state,
and simulation-control internals.

The engine offers observers the state at run start and after every successfully
committed step:

```text
preflight trait requirements
        ↓
observe authoritative step 0 if requested
        ↓
transactional step working copy
        ├─ failure → discard working copy; no post-step observation
        └─ success → commit new SimulationState
                         ↓
                    observe committed state if requested
```

Custom observers are responsible for treating `WorldState` as read-only. The
built-in recorder stores immutable value records and never retains mutable entity
references.

## PopulationRecorder

`PopulationRecorder` records an evolutionary time series at a configurable step
interval. It can include the step-zero founder baseline and can summarize selected
integer genetic-phenotype traits.

```python
from evo_engine.engine import SimulationEngine
from evo_engine.observation import PopulationRecorder

recorder = PopulationRecorder(
    trait_names=("growth_rate", "metabolic_cost_coefficient"),
    every_n_steps=1,
)

engine = SimulationEngine(
    step_coordinator=coordinator,
    stopping_condition=stopping_condition,
    observers=(recorder,),
)

engine.run(simulation)

for observation in recorder.observations:
    print(
        observation.step_index,
        observation.population_size,
        observation.trait("growth_rate").summary.mean,
    )
```

The recorder exposes its configured trait names through `required_traits`, so the
normal engine preflight rejects undefined traits before step zero rather than
failing midway through a run.

## PopulationObservation

Each immutable `PopulationObservation` contains:

- completed `step_index`
- active `population_size`
- `carcass_count`
- total environmental resource units
- age summary
- energy summary
- current body-mass summary
- configured integer genetic-trait summaries

Age, energy, body mass, and integer traits use `IntegerSummary`:

```text
count
total
mean
minimum
maximum
```

An extinct population has a valid empty summary with count and total equal to
zero and mean/minimum/maximum equal to `None`.

## Trait distributions

Each `IntegerTraitSummary` additionally stores deterministic ordered
`(value, count)` pairs. This is important because a mean alone can hide
population structure.

For example, these populations have the same mean trait value:

```text
population A: 2, 2, 2, 2
population B: 1, 1, 3, 3
```

but their distributions differ:

```text
A → ((2, 4),)
B → ((1, 2), (3, 2))
```

Tracking the distribution therefore makes mutation, inheritance, selection, and
population polymorphism visible without forcing one downstream analysis format.

## Observation scheduling

Scheduling belongs to the observer rather than `SimulationEngine`.
`PopulationRecorder(every_n_steps=5)` records every fifth committed step.
`include_step_zero=False` suppresses the founder baseline.

This makes different observers independently schedulable. A lightweight
population recorder may run every step while a future expensive spatial snapshot
observer runs less frequently.

Repeated calls to `SimulationEngine.run()` do not duplicate a recorder's most
recent step because `PopulationRecorder.should_observe()` suppresses an already
recorded `step_index`.

## Reference ecology

`build_reference_ecology()` now creates and attaches a `PopulationRecorder`
automatically:

```python
from evo_engine.presets import build_reference_ecology

ecology = build_reference_ecology()
ecology.engine.run(ecology.simulation)

baseline = ecology.recorder.observations[0]
latest = ecology.recorder.latest
```

The reference recorder tracks every integer trait in `ReferenceTraitValues`, so
its time series can directly expose changes in growth rate, metabolic and
locomotion coefficients, sensory traits, feeding physiology, predation traits,
mate-choice traits, life-history thresholds, and lifespan.

The reference preset remains a modeling baseline rather than a calibrated
biological claim. Observation makes its dynamics inspectable; it does not make
the numerical assumptions empirically validated.

## Deliberately separate future layers

This milestone records state, not causal event history. Several related but
distinct capabilities remain separate:

- event telemetry: births, deaths, predation, feeding, movement, and costs by step
- pedigree and lifetime fitness accounting
- allele/genotype frequencies distinct from expressed phenotype distributions
- experiment replication across multiple seeds
- CSV/JSON/DataFrame export
- plotting and animation
- checkpoint/save-and-resume persistence

Keeping these separate avoids turning one observer into a monolithic analytics,
logging, storage, and visualization subsystem.
