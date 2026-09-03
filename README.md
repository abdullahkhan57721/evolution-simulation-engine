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
├── energetics/    energetic coefficients, cost models, and expenditure policies
├── feeding/       intake-capacity and resource-assimilation physiology
├── reproduction/ reproductive eligibility, mate choice, parent selection,
│                  investment, movement adapters, and offspring placement
├── observation/   immutable population and evolutionary measurements
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

Two-parent mating can additionally compose search-range compatibility,
choosiness/signal compatibility, and pair preference. These policies are also
reusable by movement, so organisms may actively seek viable preferred mates
before entering the reproduction stage.

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

`GeneticPhenotypeGrowthRate` allows potential growth itself to be heritable.
Faster growth can reach adult size sooner but, under a mass-priced growth-cost
model, larger realized increments also consume more energy in that timestep.

## Heritable physiological performance

Power-law metabolic and locomotion models now accept a `CoefficientSource` rather
than only a fixed number. Existing fixed coefficients remain valid, while
`GeneticPhenotypeCoefficient` can derive an organism-specific fractional
coefficient from an integer genetic trait.

For example, an integer trait value of `30` with denominator `100` produces
coefficient `0.30`:

```python
from evo_engine.energetics import (
    GeneticPhenotypeCoefficient,
    PowerLawMetabolicCost,
)
from evo_engine.genetics import METABOLIC_COST_COEFFICIENT

metabolism = PowerLawMetabolicCost(
    coefficient=GeneticPhenotypeCoefficient(
        trait_name=METABOLIC_COST_COEFFICIENT,
    ),
    mass_exponent=0.75,
)
```

The reference ecology uses three heritable performance traits:

```text
growth_rate
metabolic_cost_coefficient
locomotion_cost_coefficient
```

The shared allometric exponents remain engine configuration. This separates the
common physical/ecological scaling law from the organism-specific performance
parameters that can mutate, recombine, and be inherited.

`growth_rate` has an explicit timing/energy tradeoff under the current growth
cost model. Lower metabolic and locomotion coefficients are currently directional
energetic advantages rather than forced tradeoffs; the engine does not invent a
compensating penalty without an explicit physiological allocation model.

## Evolution observability

`SimulationEngine` can accept structural `Observer` implementations. Observers are
offered only authoritative committed states: the run-start baseline and states
after successfully completed transactional steps. A failed working step is
discarded and never emitted as history.

The built-in `PopulationRecorder` stores immutable value records rather than live
organism references. It can summarize population size, carcasses, environmental
resources, age, energy, body mass, and selected integer genetic-phenotype traits.
Each trait record includes both numerical statistics and ordered value counts, so
population polymorphism is not hidden behind a mean.

```python
from evo_engine.observation import PopulationRecorder

recorder = PopulationRecorder(
    trait_names=("growth_rate", "metabolic_cost_coefficient"),
)

engine = SimulationEngine(
    step_coordinator=coordinator,
    stopping_condition=stopping_condition,
    observers=(recorder,),
)
```

Observer trait dependencies participate in genetic-architecture preflight. The
complete reference ecology attaches a recorder automatically and tracks all of its
integer founder traits each step.

## Feeding physiology

`ResourceConsumption` separates behavioral demand from physiological capacity
and digestive return. `requested_amount` is the amount an organism tries to
obtain, an optional `IntakeCapacityModel` limits how much may enter resource
competition, and an `AssimilationModel` converts the resolved food allocation
into usable energy.

Built-in models include fixed intake capacity, genetic `max_intake_rate`, full
one-to-one assimilation, fixed percentage assimilation, and genetic
`assimilation_efficiency`. Resource-allocation resolvers continue to operate on
food quantities only; assimilation occurs after allocation.

This keeps the pipeline explicit:

```text
behavioral food demand
    → intake-capacity ceiling
    → resource competition
    → consumed food
    → assimilation physiology
    → energy gain
```

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
such as growth and reproduction below a fixed or organism-specific energy
threshold while, by default, still allowing energy-acquisition and survival
behavior.

Selection happens before fixed-purpose processes perform their domain-specific
proposal work. The fixed-purpose integrations are `Growth`, `Reproduction`,
`Predation`, and `ResourceConsumption`. Selection is evaluated from current
state each time a process proposes, so an organism may acquire energy in an
earlier stage and leave conservation mode later in the same step.

Movement is intentionally different because the process itself has no single
purpose. A `MovementIntentModel` determines why each organism is attempting to
move before target selection or displacement RNG is consumed.
`FixedMovementIntent` assigns one configured purpose and
`EnergyThresholdMovementIntent` provides a simple two-state energy rule.
`PrioritizedMovementIntent` generalizes this into ordered
`MovementIntentRule` objects: the first matching `MovementIntentCondition`
selects the movement purpose and a fallback purpose applies when no condition
matches.

Movement may then select an ecological target.
`PurposeMovementTargetRouter` dispatches different behavioral purposes to
independent target models. `NearestResourceTarget` handles food-seeking
movement; the reproduction domain's `PreferredMateTarget` can handle
reproduction-purpose movement while reusing the same eligibility,
compatibility, and preference policies used by actual mating.

`NearestResourceTarget` composes a sensory-range model and a sensory-accuracy
model. The reference ecology uses genetic `sensory_range` and
`sensory_accuracy`: range limits which resource deposits can be considered,
while accuracy determines whether each in-range deposit is detected. Perfect
accuracy consumes no RNG; intermediate accuracy performs independent detection
checks.

If no relevant target is selected, the organism falls back to its configured
ordinary `MovementPattern`, representing search or exploration rather than
omniscient navigation. A selected target is approached with
`StraightLineTowardTarget`, which respects the organism's Euclidean `max_speed`
limit. The selected target is recorded on `Movement.Event` together with
movement purpose and destination.

The movement decision pipeline is therefore:

```text
MovementIntentModel
    → why is this organism moving?
BehaviorSelectionModel
    → should it attempt that purpose now?
MovementTargetModel
    → is there a relevant target it can detect or select?
        ├─ target found → TargetedMovementModel
        └─ no target    → MovementPattern search/fallback
BoundaryCondition
    → where does the displacement resolve?
LocomotionCostModel
    → what does the movement cost?
EnergyExpenditurePolicy
    → may the organism pay that cost?
Movement.Event
    → record purpose, target, destination, and cost
```

The reference ecology uses this priority:

```text
low energy          → seek food
reproduction-ready  → seek a preferred viable mate
otherwise           → explore
```

Food seeking therefore outranks mate seeking during energy conservation.
`mate_search_range` is the detection/targeting horizon for compatible mates,
while `mating_radius` is the close-range distance required for actual
reproduction.

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

Example simple state-dependent resource-seeking movement configuration:

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
pattern is used. Richer simulations can replace the two-state intent with
`PrioritizedMovementIntent` and route additional purposes such as reproduction.

## Complete reference ecology

`evo_engine.presets` provides a complete ecological/evolutionary composition
that wires the current major capabilities together under the standard lifecycle.
It includes heritable metabolic and locomotion performance, metabolism,
starvation checkpoints, resource generation and decomposition, prioritized
food-seeking/mate-seeking/exploratory movement, probabilistic resource sensing,
trait-driven predation, genetic intake capacity, resource competition, genetic
assimilation efficiency, heritable growth rate, sexual mate choice, close-range
sexual reproduction, recombination, mutation, aging, developmental maximum-age
mortality, and per-step evolutionary population observation.

```python
from evo_engine.presets import build_reference_ecology

ecology = build_reference_ecology()
ecology.engine.run(ecology.simulation)

latest = ecology.recorder.latest
```

The preset is an integration baseline and starting point, not a scientifically
calibrated model. Simulation-wide assumptions are explicit in
`ReferenceEcologyConfig`; founder organism traits are explicit in
`ReferenceTraitValues`.

## Portfolio dashboard

The optional Streamlit/Plotly dashboard turns the reference ecology into an
end-to-end portfolio experience without making UI frameworks part of the core
runtime. Its dependency direction is intentionally one-way:

```text
simulation/domain layers
        ↓
committed observations and experiment results
        ↓
evo_engine.ui presentation transforms
        ↓
Streamlit + Plotly
```

The dashboard exposes a curated validated configuration, runs the existing
reference ecology, animates immutable committed spatial snapshots, and presents
population/ecological summaries, heritable-trait trajectories, raw allele and
genotype frequencies, committed event activity, mortality and reproductive
outcomes, multi-seed replicate comparisons, and the existing JSON/CSV experiment
exports.

Install the project and UI dependencies into the project virtual environment:

```bash
python -m pip install -e ".[dev]"
python -m pip install -r requirements-ui.txt
```

Launch the dashboard:

```bash
venv/bin/python -m streamlit run src/evo_engine/ui/app.py
```

`requirements-ui.txt` is deliberately optional: ordinary engine users and core
runtime environments do not need Streamlit or Plotly. The quality workflow also
installs these dependencies so the UI package and headless Streamlit interactions
are linted, type-checked, and tested in CI.

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
