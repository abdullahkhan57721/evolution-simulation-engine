# Evolution Simulation Engine

An extensible Python engine for evolutionary simulations with staged event
processing, spatial ecology, configurable genetics, and one- or two-parent
reproduction.

## Architecture

The engine separates simulation orchestration from ecological processes and
domain-specific policies:

```text
src/evo_engine/
├── engine/        simulation state, engine loop, stages, steps, lifecycle
├── world/         organisms, carcasses, and mutable world state
├── genetics/      alleles, loci, chromosomes, genomes, inheritance,
│                  recombination, expression, and genetic phenotype
├── development/   developmental variation and individual target profiles
├── life_history/  cross-process thresholds and lifespan strategies
├── growth/        policies that determine potential body-mass gain
├── behavior/      purposes, movement intent, sensing, targeting, selection
├── energetics/    energetic cost models for metabolism, movement, and growth
├── reproduction/ reproductive eligibility, parent selection, investment,
│                  and offspring placement
├── spatial/       neighborhoods, distances, boundaries, movement geometry
├── processes/     simulation processes that propose and apply events
├── resolvers/     conflict-resolution policies for proposed events
├── presets/       high-level composition roots for complete simulations
└── validation/    general and attrs-compatible runtime validators
```

A simulation step is transactional:

```text
SimulationEngine
    → SequentialStepCoordinator
        → StageCoordinator
            → Process.propose_events()
            → Resolver.resolve_events()
            → optional Process.materialize_event()
            → Process.apply_event()
```

Each step runs on a working copy of `SimulationState`. The completed state
replaces the authoritative state only after every stage succeeds.

## Genetics

Organisms separate inherited genetic state from developmental realization:

```text
Genome
    → GeneticArchitecture
        → GeneticPhenotype              genetic expectation
            → DevelopmentModel
                → DevelopmentalProfile  individual target values
                    → GrowthModel
                        → mutable organism body mass
```

The genetics subsystem supports configurable allele domains, mutation
policies, genotype-to-phenotype expression, clonal inheritance, sexual
inheritance, meiotic gamete formation, and crossover recombination.

## Reproduction

Reproduction supports exactly one or two parents. The process composes
independent policies for:

- reproductive eligibility
- parent selection
- parental energy investment
- genetic inheritance
- offspring placement

Conflict resolution remains separate from proposal logic. Developmental
variation for offspring is sampled only after a reproductive proposal has
been resolved, so rejected mating candidates consume no developmental RNG.

## Development

A `DevelopmentModel` may change trait values, but it must preserve the complete
ordered trait-name sequence from `GeneticPhenotype` into `DevelopmentalProfile`.
This invariant is checked whenever development is realized and whenever an
`Organism` is constructed.

## Growth

`Organism.body_mass` is mutable physical state, while the corresponding adult
body-mass value in `DevelopmentalProfile` remains an immutable individual
target. `Growth` composes a `GrowthModel` for potential mass gain with a
`GrowthCostModel` for energetic cost.

Potential growth is capped at the developmental target before energetic
pricing. The initial affordability rule is all-or-nothing: an organism grows
only when it can pay the full cost of the capped gain. Spending the final unit
of energy is allowed; mortality remains a separate process such as
`Starvation`, which therefore observes the organism's updated current mass.

## Behavior selection and directed movement

Behavioral processes may optionally expose a `behavioral_purpose` through the
runtime-checkable `BehavioralPurposeProvider` protocol. Fixed-purpose processes
use class-level declarations: growth is somatic investment, reproduction is
reproduction, and predation/resource consumption are energy acquisition.

Behavioral-purpose names are extensible strings rather than a closed enum. The
engine provides canonical names for common purposes while allowing simulations
to introduce custom purposes such as thermoregulation.

`BehaviorSelectionModel` answers a separate organism-level question: given the
organism's current state, should it attempt a behavior with a particular
purpose? `UnrestrictedBehavior` preserves the engine's historical behavior and
is the simulation default. `EnergyConservationBehavior` suppresses purposes
such as growth and reproduction below a fixed energy threshold while, by
default, still allowing energy-acquisition and survival behavior.

Selection happens before fixed-purpose processes perform their domain-specific
proposal work. The fixed-purpose integrations are `Growth`, `Reproduction`,
`Predation`, and `ResourceConsumption`. Selection is evaluated from current
state each time a process proposes, so an organism may acquire energy in an
earlier stage and leave conservation mode later in the same step.

Movement is intentionally different because the process itself has no single
purpose. A `MovementIntentModel` determines why each organism is attempting to
move before target selection or displacement RNG is consumed.
`FixedMovementIntent` assigns one configured purpose. `EnergyThresholdMovementIntent`
derives purpose from current energy: below its threshold it defaults to energy
acquisition, while at or above the threshold it defaults to exploration. Both
purposes are configurable. The movement-intent threshold and
`EnergyConservationBehavior` threshold are independent configuration because
intent answers what the organism is trying to do, while behavior selection
answers whether that purpose is attempted.

Movement may then select an ecological target. `NearestResourceTarget` targets
the nearest detectable resource deposit for energy-acquisition movement. By
default it composes `GeneticPhenotypeSensoryRange`, which reads the built-in
`sensory_range` genetic phenotype trait. That requirement is nested: ordinary
untargeted movement still requires only `max_speed`, while trait-driven resource
seeking additionally requires `sensory_range`. `FixedSensoryRange` is available
for experiments where sensing should be configuration rather than heritable
biology.

The initial resource-targeting rule uses direct Euclidean sensory distance. A
resource outside the sensing radius has no effect on movement. If no resource
is detected, the organism falls back to its configured ordinary
`MovementPattern`, representing search behavior rather than omniscient
navigation. A detected target is approached with `StraightLineTowardTarget`,
which respects the organism's Euclidean `max_speed` limit. The selected target
is recorded on `Movement.Event` together with movement purpose and destination.

The engine also defines a built-in `sensory_accuracy` trait name for future
noisy or imperfect perception, but resource seeking currently uses sensory
range only.

The movement decision pipeline is therefore:

```text
MovementIntentModel
    → why is this organism moving?
BehaviorSelectionModel
    → should it attempt that purpose now?
MovementTargetModel
    → is there a relevant target it can detect?
        ├─ target found → TargetedMovementModel
        └─ no target    → MovementPattern search/fallback
BoundaryCondition
    → where does the displacement resolve?
LocomotionCostModel
    → what does the movement cost?
Movement.Event
    → record purpose, target, destination, and cost
```

Example conservation configuration:

```python
from evo_engine.behavior import EnergyConservationBehavior
from evo_engine.engine import Simulation

simulation = Simulation(
    initial_world_state=world,
    genetic_architecture=architecture,
    behavior_selection_model=EnergyConservationBehavior(
        energy_threshold=10,
    ),
)
```

Example state-dependent resource-seeking movement configuration:

```python
from evo_engine.behavior import (
    EnergyThresholdMovementIntent,
    NearestResourceTarget,
)
from evo_engine.processes import Movement

movement = Movement(
    movement_pattern=movement_pattern,
    boundary_condition=boundary_condition,
    locomotion_cost_model=locomotion_cost_model,
    movement_intent_model=EnergyThresholdMovementIntent(
        energy_threshold=10,
    ),
    movement_target_model=NearestResourceTarget(),
)
```

With that configuration, organisms below 10 energy attempt energy-acquisition
movement and can target detectable resources. At or above 10 energy they attempt
exploration, so `NearestResourceTarget` is inactive and the ordinary movement
pattern is used. The simulation's genetic architecture must define both
`max_speed` and `sensory_range`.

## Complete reference ecology

`evo_engine.presets` provides a complete ecological/evolutionary composition
that wires the current major capabilities together under the standard lifecycle.
It includes metabolism, starvation checkpoints, resource generation and
decomposition, state-dependent resource-seeking movement, predation, resource
competition, growth, sexual reproduction, recombination, mutation, aging, and
developmental maximum-age mortality.

```python
from evo_engine.presets import build_reference_ecology

ecology = build_reference_ecology()
ecology.engine.run(ecology.simulation)
```

The preset is an integration baseline and starting point, not a scientifically
calibrated model. All numerical assumptions are explicit in
`ReferenceEcologyConfig` and `ReferenceTraitValues`.

Install the project and development tools into the project virtual
environment:

```bash
python -m pip install -e ".[dev,docs]"
```

Run the active tests:

```bash
python -m pytest
```

Apply safe Ruff fixes and formatting when desired:

```bash
./scripts/fix
```

Run the complete quality gate (Ruff lint/format verification, Pyright, Import
Linter when configured, Complexipy cognitive complexity, pytest with line and
branch coverage, and MkDocs):

```bash
./scripts/check_all
```

On macOS, double-click `check_project.command` to run the same gate and keep
the Terminal window open for the final summary.

Run the examples:

```bash
venv/bin/python examples/basic_aging_simulation.py
venv/bin/python examples/reference_ecology_simulation.py
```

Double-click `open_project_terminal.command` on macOS to open a shell at the
project root with the local virtual environment activated.

Double-click `make_review_zip.command` to create a clean review ZIP in
`~/Downloads`.
