# Model Notes

## Current Modeling Architecture

The engine distinguishes inherited genetic state, deterministic genetic
expression, individual developmental realization, mutable organism state,
ecological processes, and event-resolution policy.

### Active world state

`WorldState` contains only organisms and other entities that currently matter
to continuation of the simulation. Dead organisms are removed. Ecologically
relevant remains may persist as `Carcass` entities.

### Genetics and genetic phenotype

An organism carries a `Genome` and an expressed `GeneticPhenotype`.

Shared `GeneticArchitecture` configuration defines:

- loci and allele domains
- locus-specific mutation policies
- traits and genotype-to-phenotype expression

The genetic representation preserves separate chromosome copies so linked
alleles retain phase for segregation and recombination.

### Development

`GeneticPhenotype` stores values expressed deterministically from the genome. A
`DevelopmentModel` then realizes an organism-specific `DevelopmentalProfile`.
This keeps genetic inheritance separate from nonheritable developmental or
environmental variation.

For example, a genome may express `adult_body_mass = 20`, while
`GaussianIntegerDevelopment` can realize an individual adult target of 18,
20, or 23. The genome and genetic phenotype remain unchanged. Current mutable
`Organism.body_mass` can later grow toward that realized target.

`IndependentDevelopment` allows different traits to use different
developmental models while unconfigured traits pass through deterministically.
Every `DevelopmentModel` must preserve the complete ordered trait-name sequence
from `GeneticPhenotype` into `DevelopmentalProfile`; development may change values
but cannot add, remove, or reorder traits.

### Growth

Growth operates on mutable current `Organism.body_mass` while treating the
corresponding `DevelopmentalProfile` value as an immutable individual target.
This preserves the separation between inherited expectation, developmental
realization, and lifetime physical state:

```text
Genome
    → GeneticArchitecture
        → GeneticPhenotype
            → DevelopmentModel
                → DevelopmentalProfile
                    → GrowthModel
                        → current body_mass
```

`GrowthModel` determines potential mass gain. The `Growth` process caps that
gain at the developmental target before asking a `GrowthCostModel` to price the
actual gain. The initial affordability policy is all-or-nothing: if the full
capped gain is unaffordable, no Growth event is proposed.

Growth is an energetic process but not a mortality process. An organism may
spend its final energy on growth and reach `energy == 0`; a later `Starvation`
stage is responsible for removing it. Because starvation derives carcass
resource units from current body mass, any successfully grown mass is preserved
in the resulting carcass.

Energy-consuming processes placed in the same stage all propose from the same
pre-stage energy state. Growth therefore rechecks affordability when applying a
resolved event. If another same-stage event has already spent the required
energy, Growth raises instead of adding unpaid tissue. Under
`SequentialStepCoordinator`, that failure occurs on the transactional working
copy, leaving the authoritative state unchanged.

### Behavioral purpose and behavior selection

Behavioral purpose is modeled as an optional component capability rather than a
requirement of every simulation process. Components that expose a
`behavioral_purpose` satisfy the runtime-checkable `BehavioralPurposeProvider`
protocol. Fixed-purpose processes use class-level declarations.

Behavioral purposes are extensible nonblank strings. Canonical engine purposes
currently include energy acquisition, survival, somatic investment,
reproduction, and exploration. Growth declares somatic investment;
Reproduction declares reproduction; Predation and ResourceConsumption declare
energy acquisition.

`BehaviorSelectionModel` is separate from process ordering and from
process-specific eligibility. It answers whether a particular organism should
attempt a behavioral purpose from its current state. The configured selector is
shared simulation configuration stored on `SimulationState` and is re-used by
transactional state copies.

`UnrestrictedBehavior` always allows behavior and is the default, preserving
existing simulation semantics. `EnergyConservationBehavior` activates when
`organism.energy < energy_threshold`. At or above the threshold every purpose is
allowed. Below the threshold, only configured low-energy purposes are allowed;
by default these are energy acquisition and survival.

The fixed-purpose integrations are:

- `Growth` — somatic investment
- `Reproduction` — reproduction
- `Predation` — energy acquisition
- `ResourceConsumption` — energy acquisition

Selection occurs before those processes perform their normal proposal logic.
A suppressed organism therefore does not proceed into growth models,
reproductive eligibility/parent selection, predator-prey proposal generation,
or resource-consumption proposals.

### Movement intent, sensing, and ecological targets

Movement uses action-level purpose rather than a process-level declaration.
`Movement` itself intentionally has no `behavioral_purpose`, because movement
may represent foraging, escape, mate search, exploration, migration, or another
context-dependent action.

A `MovementIntentModel` determines the purpose of each organism's movement
attempt from current state. `FixedMovementIntent` defaults to exploration and
may instead assign energy acquisition, survival, reproduction, or another valid
purpose. Custom intent models may determine purpose dynamically and
independently for each organism.

Behavior selection runs immediately after intent. Suppressed movement stops at
that point: target selection, sensing, movement-pattern RNG, boundary handling,
and locomotion pricing are not evaluated.

Allowed movement may then use a `MovementTargetModel`. `NoMovementTarget` is the
default and preserves untargeted movement semantics. `NearestResourceTarget`
provides the first ecological targeting policy. It is active for energy
acquisition by default and selects the nearest resource deposit within the
organism's sensory radius.

Sensory ability is modeled separately from target selection through
`SensoryRangeModel`. The initial implementations are:

- `FixedSensoryRange` — experiment-level configuration with no trait requirement
- `GeneticPhenotypeSensoryRange` — reads an integer genetic phenotype trait,
  defaulting to the built-in `sensory_range` trait

`NearestResourceTarget` composes `GeneticPhenotypeSensoryRange` by default.
Consequently, sensory range is not a universal requirement of Movement. Nested
trait requirements behave as follows:

```text
ordinary untargeted Movement
    → max_speed

Movement + NearestResourceTarget()
    → max_speed
    → sensory_range

Movement + NearestResourceTarget(FixedSensoryRange(...))
    → max_speed
```

This matters biologically and architecturally. Simulations can make sensing an
evolvable trait when desired without forcing sensory genetics into every
movement experiment.

The engine already reserves the built-in trait name `sensory_accuracy`, but the
initial resource-seeking model intentionally does not use it. Detection is
currently perfect inside sensory range and absent outside it. Accuracy can later
represent missed detections, localization noise, or directional error without
changing the range abstraction.

`NearestResourceTarget` currently measures direct squared Euclidean distance.
A resource outside the sensory radius is not considered and therefore cannot
influence movement. Among equally near deposits, more resource units are
preferred; remaining ties are resolved deterministically by coordinate. A
resource on the organism's current cell is detectable even when sensory range
is zero.

When a target is selected, `StraightLineTowardTarget` chooses an integer-grid
displacement in the target's direction while respecting Euclidean `max_speed`.
Targets within one timestep's movement capability are reached exactly. More
distant targets are approached without exceeding the speed disk. If no target
is selected, Movement falls back to its ordinary `MovementPattern`. For a hungry
organism this fallback can represent undirected search rather than freezing or
omniscient navigation.

The resulting proposal sequence is:

```text
MovementIntentModel
    → why is this organism moving?
BehaviorSelectionModel
    → should it attempt that purpose now?
MovementTargetModel
    → is there a relevant target it can detect?
        ├─ target found → TargetedMovementModel
        └─ no target    → MovementPattern
BoundaryCondition
    → resolve destination
LocomotionCostModel
    → price movement
Movement.Event
    → record purpose, selected target, destination, and cost
```

Movement target coordinates are recorded on `Movement.Event` when a target is
selected. They are proposal metadata rather than application instructions: the
event's resolved destination remains the only position applied to the organism.
This keeps application mechanical while preserving why and toward what the
movement was proposed for later observation or analysis.

The current resource-seeking implementation is intentionally not toroidal-aware
at the perception/navigation layer. It uses direct Euclidean target distance and
direct straight-line approach. Toroidal shortest-path sensing and navigation can
be added as separate policies rather than hidden inside the first model.

Movement intent, sensing, targeting, and geometry remain distinct:

```text
MovementIntentModel
    → why move?
SensoryRangeModel
    → how far can targets be detected?
MovementTargetModel
    → which detectable target matters?
TargetedMovementModel / MovementPattern
    → how is displacement chosen?
```

Behavior selection is derived rather than stored on the organism. Every process
consults the selector from current state when it proposes. Consequently, a
low-energy organism may acquire energy in an earlier stage and automatically
leave conservation mode before a later Growth, Reproduction, or exploratory
Movement stage in the same timestep.

This distinction is intentional:

```text
Timestep/stage order
    → when a process gets an opportunity
MovementIntentModel / fixed process purpose
    → why this organism is attempting the behavior
BehaviorSelectionModel
    → whether this organism attempts that behavioral purpose
Perception and targeting policies
    → what relevant environmental information can guide the attempt
Process eligibility and domain rules
    → whether the attempted behavior is biologically feasible
Energetic affordability/reserve policy
    → whether the resulting expenditure may be paid
```

The final energetic-reserve layer is not yet generalized; current processes
retain their existing affordability rules.

### Inheritance

The genetics subsystem currently supports:

- `ClonalInheritance` for one-parent reproduction
- `SexualInheritance` for two-parent reproduction
- `MeioticGameteFormation`
- no-recombination and single-crossover recombination policies

Mutation acts on transmitted alleles according to each locus's mutation
policy.

### Reproduction

The `Reproduction` process composes independent policies for individual
eligibility, parent selection, parental investment, inheritance, and
offspring placement, developmental realization, and newborn body-mass policy.

Exactly one- or two-parent reproduction is supported.

### Event processing

Each simulation stage follows:

1. processes propose events from the same pre-application state
2. a resolver reconciles the proposals
3. all resolved events are materialized from that same pre-application state
4. materialized events are applied in resolver order

Materialization is optional. Processes whose resolved events already contain every
decision needed for application require no materialization hook. Processes such as
`Reproduction` use `materialize_event()` for post-resolution stochastic work such
as inheritance, mutation, recombination, phenotype expression, and offspring
placement.

The coordinator materializes every resolved event before applying any event. This
preserves stage simultaneity: no materializer observes mutations produced by an
earlier event in the same stage. Application is therefore reserved for
mechanical state mutation.

A `SequentialStepCoordinator` runs ordered stages on a transactional copy of
`SimulationState`.
