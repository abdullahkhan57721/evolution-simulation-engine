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
built-in recorders store immutable value records and never retain mutable entity
references.

## PopulationRecorder

`PopulationRecorder` records an evolutionary time series at a configurable step
interval. It always records mating-type composition and can additionally
summarize selected integer genetic-phenotype traits.

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
        observation.mating_type_counts.value_counts,
        observation.trait("growth_rate").summary.mean,
    )
```

The recorder exposes its configured trait names through `required_traits`, so the
normal engine preflight rejects undefined traits before step zero rather than
failing midway through a run. Mating type is organism state rather than a genetic
trait, so recording it creates no genetic-architecture dependency.

## PopulationObservation

Each immutable `PopulationObservation` contains:

- completed `step_index`
- active `population_size`
- `carcass_count`
- total environmental resource units
- age summary
- energy summary
- current body-mass summary
- mating-type counts
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

## Mating-type composition

`CategoryCounts` stores deterministic lexicographically ordered
`(category, count)` pairs for string-valued population categories. The population
recorder uses it for `Organism.mating_type`.

For example:

```text
(("type_a", 12), ("type_b", 9))
```

`count_for()` returns an absolute count and `frequency_for()` returns the fraction
of the categorized population represented by one label. Frequencies are `None`
for an empty population because a category fraction is undefined when the total
count is zero.

`PopulationObservation` requires mating-type counts to sum exactly to
`population_size`. This makes sex-ratio or mating-type-ratio histories complete
rather than a best-effort side measurement.

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

## SpatialRecorder

`SpatialRecorder` captures immutable committed world frames for downstream
visualization and animation without retaining live `WorldState`, organism,
carcass, genome, or mapping references.

Each `SpatialObservation` contains:

- completed `step_index`;
- world width and height;
- organisms ordered by permanent ID, with ID, position, age, energy, body mass,
  and mating type;
- resource deposits ordered by coordinate, with position and amount; and
- carcasses ordered by permanent ID, with position and remaining resource units.

The spatial recorder deliberately does **not** duplicate per-organism genomes,
trait distributions, event causality, or pedigree state. Those concerns already
have dedicated observers. A visualization can therefore compose the spatial
frames with population, genetic, event, and pedigree records rather than treating
a spatial snapshot as a universal analysis object.

Spatial observation is opt-in because frame histories can be much larger than
summary histories. The complete reference ecology accepts additional observers
without attaching a `SpatialRecorder` by default:

```python
from evo_engine.observation import SpatialRecorder
from evo_engine.presets import build_reference_ecology

spatial = SpatialRecorder(every_n_steps=1)
ecology = build_reference_ecology(
    additional_observers=(spatial,),
)
ecology.engine.run(ecology.simulation)

for frame in spatial.observations:
    print(frame.step_index, len(frame.organisms), len(frame.resources))
```

Downstream Plotly, Streamlit, notebook, video, or other presentation code should
consume these immutable records rather than reach back into historical mutable
simulation internals.

## Observation scheduling

Scheduling belongs to the observer rather than `SimulationEngine`.
`PopulationRecorder(every_n_steps=5)` records every fifth committed step.
`include_step_zero=False` suppresses the founder baseline.

This makes different observers independently schedulable. A lightweight
population recorder may run every step while a larger spatial snapshot recorder
runs less frequently.

Repeated calls to `SimulationEngine.run()` do not duplicate a recorder's most
recent step because built-in state recorders suppress an already recorded
`step_index`.

## Reference ecology

`build_reference_ecology()` creates and attaches the standard population,
genetic-composition, event, and pedigree recorders automatically:

```python
from evo_engine.presets import build_reference_ecology

ecology = build_reference_ecology()
ecology.engine.run(ecology.simulation)

baseline = ecology.recorder.observations[0]
latest = ecology.recorder.latest
```

The reference population recorder tracks every integer trait in
`ReferenceTraitValues` plus the active population's mating-type composition. Its
time series can therefore expose changes in growth rate, metabolic and locomotion
coefficients, sensory traits, feeding physiology, predation traits, mate-choice
traits, life-history thresholds, lifespan, and reproductive type ratios.

The reference preset remains a modeling baseline rather than a calibrated
biological claim. Observation makes its dynamics inspectable; it does not make
the numerical assumptions empirically validated.

## Separate observation layers

Population snapshots intentionally remain separate from other measurement
concerns. The current stack includes:

```text
PopulationRecorder
    → population/ecosystem summaries
    → phenotype distributions
    → mating-type composition

SpatialRecorder
    → immutable spatial world frames
    → organism/resource/carcass positions and selected scalar state

GeneticCompositionRecorder
    → allele frequencies
    → genotype frequencies

EventRecorder
    → committed causal event history

PedigreeRecorder
    → parentage
    → mortality causes
    → lifetime reproductive success
```

The experiment layer composes the non-spatial analysis records across seeds and
exports them without moving analytics responsibilities back into simulation
processes. Plotting, animation, and higher-level statistical analysis remain
downstream consumers of immutable records; callers opt into spatial history only
when a presentation or analysis requires it.
