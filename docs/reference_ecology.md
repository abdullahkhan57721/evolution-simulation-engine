# Reference Ecology

The reference ecology is a complete, runnable composition of the engine's current
major ecological and evolutionary capabilities. It is intended to serve three
purposes:

1. a working example for users learning the engine,
2. an integration baseline that exposes cross-process semantic defects, and
3. a starting point for experiments that can be customized without rewriting
   orchestration.

It is **not** a calibrated biological model. Its default numbers are deliberately
simple and transparent.

## Public API

```python
from evo_engine.presets import build_reference_ecology

ecology = build_reference_ecology()
ecology.engine.run(ecology.simulation)
```

The returned `ReferenceEcology` bundles:

- `config`: the resolved `ReferenceEcologyConfig`,
- `simulation`: world state, genetics, RNG, and behavior selection, and
- `engine`: processes, resolvers, lifecycle, and stopping condition.

For finer control, the preset also exposes builders for the genetic architecture,
founder genome, world, simulation, and engine.

## Founder genetic architecture

The reference population begins homozygous for twenty integer traits:

| Trait | Default | Role |
| --- | ---: | --- |
| `adult_body_mass` | 8 | Adult developmental body-mass target |
| `growth_rate` | 1 | Potential body-mass gain per growth timestep |
| `max_speed` | 1 | Maximum movement distance |
| `locomotion_cost_coefficient` | 20 | Hundredths of locomotion power-law coefficient |
| `sensory_range` | 4 | Resource-detection radius |
| `sensory_accuracy` | 90 | Percent chance to detect each in-range resource deposit |
| `max_intake_rate` | 4 | Maximum environmental resource intake per timestep |
| `assimilation_efficiency` | 75 | Percent of consumed resources converted to usable energy |
| `metabolic_cost_coefficient` | 30 | Hundredths of basal metabolic power-law coefficient |
| `energy_conservation_threshold` | 15 | Switch to conservation / food-seeking behavior |
| `energy_reserve` | 5 | Reserve protected from growth and reproduction |
| `attack_strength` | 8 | Predator performance opposed by prey defense |
| `defense` | 5 | Prey resistance to predator attack |
| `mate_search_range` | 3 | Distance within which both parents can discover one another |
| `choosiness` | 5 | Minimum partner mating signal accepted |
| `mating_signal` | 8 | Signal presented to potential mates |
| `maturity_age` | 4 | Reproductive maturity |
| `reproduction_energy_threshold` | 20 | Minimum energy for reproductive eligibility |
| `offspring_energy` | 4 | Energy invested by each reproductive parent |
| `maximum_age` | 30 | Hard lifespan in completed timesteps |

Each trait is represented by one bounded integer locus. The loci share one
chromosome. Sexual reproduction therefore exercises chromosome segregation,
single-crossover recombination, mutation, genetic expression, and developmental
realization.

The default mutation probability is 10,000 parts per million (1%) per transmitted
allele, with a maximum integer change of one. Allele domains clamp mutations at
valid boundaries.

The two energetic coefficient traits use integer hundredths. Founder values 30 and
20 therefore reproduce the previous fixed coefficients `0.30` and `0.20`, while a
one-unit mutation changes the effective coefficient by `0.01`.

## Founder population

The default world is 12 × 12 with 20 founders. Founders occupy distinct cells in
row-major order instead of consuming random draws during initialization. This
makes initial state construction transparent and ensures nearby mating partners
exist.

Founders begin at their realized adult body mass. Newborns, in contrast, begin at
one quarter of their adult target and can therefore exercise the Growth process.

## Behavioral strategy

The simulation uses `EnergyConservationBehavior` driven by each organism's
developmental `energy_conservation_threshold`.

At or above the threshold, all currently modeled behavioral purposes are allowed.
Below the threshold, energy acquisition and survival remain allowed while somatic
investment and reproduction are suppressed.

Movement uses `PrioritizedMovementIntent`:

```text
1. energy below conservation threshold
       → energy_acquisition
       → consider resources within sensory_range
       → detect each in-range resource using sensory_accuracy
       → move toward the nearest detected resource

2. otherwise, individually reproduction-ready
       → reproduction
       → consider currently viable mates within mutual mate_search_range
       → prefer the highest mating preference score
       → move toward the selected mate

3. otherwise
       → exploration
       → untargeted Moore movement
```

The order is biologically meaningful. Low-energy food acquisition outranks mate
seeking. Reproduction becomes a movement motivation only when the organism passes
the same maturity and reproductive-energy eligibility policy used later by the
Reproduction process.

`PurposeMovementTargetRouter` dispatches energy-acquisition movement to resource
targeting and reproduction-purpose movement to `PreferredMateTarget`. Exploration
has no target and therefore falls back to the ordinary movement pattern.

The reference ecology uses genetic sensory range and genetic sensory accuracy.
Accuracy 0 always misses an in-range resource deposit and accuracy 100 always
detects it; intermediate values use the simulation RNG independently for each
in-range deposit considered during targeting.

## Feeding physiology

Environmental resource feeding separates behavioral demand, physiological intake
capacity, ecological allocation, and energy assimilation:

```text
behavioral resource request = 10
        ↓
max_intake_rate trait
        ↓
effective resource request
        ↓
EqualShare resource allocation
        ↓
actual consumed resource amount
        ↓
assimilation_efficiency trait
        ↓
usable energy gain
```

The default founder `max_intake_rate` is four resource units per timestep, so the
fixed behavioral request ceiling of ten does not itself constrain founder intake.
Mutation can therefore make intake capacity evolutionarily meaningful. The
default `assimilation_efficiency` is 75% and percentage conversion uses
deterministic half-up integer rounding.

The allocation resolver operates only on resource quantities. Assimilation occurs
after resource allocation, so digestive efficiency does not automatically give an
organism priority in competition for food.

The full allocated amount leaves the environmental resource pool. Any
unassimilated fraction is currently outside the modeled pool rather than being
returned as waste. A future excretion/decomposition layer can model that material
without changing the intake or assimilation interfaces.

## Heritable physiological performance

Growth speed and the coefficients controlling basal metabolism and locomotion are
now organism traits rather than fixed reference-wide parameters.

The shared mathematical forms remain engine configuration:

```text
metabolic cost
    = (metabolic_cost_coefficient / 100)
      × current_body_mass ** metabolic_mass_exponent

locomotion cost
    = (locomotion_cost_coefficient / 100)
      × current_body_mass ** locomotion_mass_exponent
      × distance ** locomotion_distance_exponent

growth potential
    = growth_rate body-mass units per growth timestep
```

The reference exponents remain `0.75` for metabolism, `0.50` for locomotion mass,
and `1.0` for locomotion distance. They describe the common scaling environment in
which organism-specific coefficients act.

`growth_rate` creates an explicit timing/energy tradeoff. Faster-growing juveniles
can approach adult body mass sooner, but the Growth process prices the larger
capped mass increment in the same timestep. With the default linear growth cost,
each realized body-mass unit costs two energy units, subject to the organism's
energy reserve policy.

The two cost coefficients create heritable performance variation: equal-mass
organisms can pay different maintenance costs, and organisms making the same
displacement can pay different locomotion costs. Lower coefficients currently have
no built-in compensating penalty, so they are directional efficiency advantages
rather than forced physiological tradeoffs. The engine leaves any future
allocation constraint explicit rather than inventing an unrelated disadvantage.

## Predation performance

Reference predation separates spatial opportunity, biological feasibility, and
preference:

```text
predation neighborhood
        ↓
current predator body mass > current prey body mass
        ↓
predator attack_strength > prey defense
        ↓
preference score = attack_strength - defense
        ↓
PreferenceOrder conflict resolution
```

Size and combat performance are independent. A predator must currently be larger
than its prey and also have sufficient expressed attack strength. Among feasible
pairings, larger attack-defense advantages are considered first. Because each
organism may participate in at most one resolved predation event in a stage,
these scores influence prey choice and interaction conflicts.

The reference contains one generic population, so this remains opportunistic
within-population predation rather than a species or trophic-role system.

## Mate choice, movement, and sexual selection

Reference mating separates individual readiness, discovery, mate choice, movement,
physical proximity, and reproduction:

```text
maturity + reproduction energy eligibility
        ↓
reproduction-purpose movement
        ↓
mutual mate_search_range
        ↓
mutual signal / choosiness compatibility
        ↓
highest mutual signal-surplus preference
        ↓
targeted movement toward preferred mate
        ↓
within mating_radius = 1
        ↓
reproduction proposal + PreferenceOrder resolution
        ↓
sexual inheritance and birth
```

`mate_search_range` and `mating_radius` deliberately model different spatial
scales. Founder `mate_search_range=3` determines how far away a compatible mate
can be discovered and targeted. `mating_radius=1` is the close-range condition
required for actual reproduction.

`PreferredMateTarget` and `PairwiseMating` share the same reproductive eligibility,
mating compatibility, and mating preference objects. A mate that movement regards
as viable is therefore evaluated with the same maturity, energy, search-range,
choosiness, signal, and preference semantics used by reproduction.

`MutualSignalCompatibility` requires two-way acceptance. A candidate pair exists
only when each partner's expressed signal meets the other's expressed choosiness.
`MutualSignalMarginPreference` scores the total amount by which both signals exceed
those thresholds. During mate seeking, higher preference beats shorter distance;
distance and organism ID are deterministic tie-breakers.

The current sexual-selection model is role-symmetric because reproductive parents
are interchangeable. It does not yet represent sexes, mating types, or asymmetric
courtship roles. Those can be added through different movement and parent-selection
policies without changing sexual inheritance.

## Energy priorities

The preset deliberately uses different expenditure policies for different kinds
of activity:

```text
mandatory metabolism
    → may deplete energy to zero

movement / food seeking / mate seeking
    → SpendToZero
    → may risk the final available energy

growth
    → KeepEnergyReserve

reproduction
    → KeepEnergyReserve
```

This creates the intended priority:

```text
maintenance
→ survival / food acquisition
→ movement toward other goals
→ growth
→ reproduction
```

Growth and reproduction read each organism's developmental `energy_reserve`, so
risk tolerance can evolve independently of the conservation threshold.

## Standard lifecycle wiring

The engine uses `build_standard_lifecycle` with these stages:

```text
1.  Starvation
2.  MaximumAgeMortality
3.  Metabolism
4.  Starvation
5.  ResourceGeneration + Decomposition
6.  Movement
7.  Predation
8.  ResourceConsumption
9.  Growth
10. Aging
11. MaximumAgeMortality
12. Reproduction
13. Starvation
```

Repeated mortality stages are checkpoints, not duplicated biological models.
Aging occurs before the end-of-step age-mortality boundary, and reproduction
occurs afterward, so newborns remain age zero on their birth step.

## Process configuration

The defaults compose:

- power-law basal metabolism with a genetic organism-specific coefficient,
- random resource generation,
- carcass decomposition,
- prioritized food-seeking, mate-seeking, and exploratory movement,
- purpose-routed movement targets,
- genetic sensory range and probabilistic sensory accuracy,
- power-law locomotion costs with a genetic organism-specific coefficient,
- size- and attack/defense-gated same-neighborhood predation,
- attack-advantage predation preference,
- genetic intake-capacity limits,
- equal-share resource competition,
- genetic resource-to-energy assimilation efficiency,
- genetic growth rate with linear energy cost,
- maturity- and energy-gated sexual reproduction,
- genetic mutual mate-search range,
- genetic choosiness and mating signal,
- mutual signal-surplus mating preference,
- close-range mating after active mate seeking,
- meiotic segregation with single crossover,
- mutation of transmitted alleles,
- developmental energy reserves,
- starvation mortality, and
- developmental maximum-age mortality.

## Customization

Simulation-wide numerical assumptions live in `ReferenceEcologyConfig`, while
founder organism traits live in `ReferenceTraitValues`.

For example:

```python
from evo_engine.presets import (
    ReferenceEcologyConfig,
    ReferenceTraitValues,
    build_reference_ecology,
)

config = ReferenceEcologyConfig(
    width=20,
    height=20,
    initial_population=40,
    max_steps=200,
    seed=123,
    mating_radius=1,
    metabolic_mass_exponent=0.75,
    locomotion_mass_exponent=0.50,
    locomotion_distance_exponent=1.0,
    traits=ReferenceTraitValues(
        adult_body_mass=10,
        growth_rate=2,
        max_speed=2,
        locomotion_cost_coefficient=25,
        sensory_range=6,
        sensory_accuracy=85,
        max_intake_rate=8,
        assimilation_efficiency=70,
        metabolic_cost_coefficient=35,
        energy_conservation_threshold=18,
        energy_reserve=6,
        attack_strength=10,
        defense=7,
        mate_search_range=5,
        choosiness=6,
        mating_signal=10,
        maturity_age=5,
        reproduction_energy_threshold=24,
        offspring_energy=5,
        maximum_age=40,
    ),
)

ecology = build_reference_ecology(config)
ecology.engine.run(ecology.simulation)
```

For changes that alter process choice rather than numeric configuration, use the
lower-level builders or assemble stages directly. The preset is deliberately not
a replacement for the engine's compositional API.

## Runnable example

Run:

```bash
venv/bin/python examples/reference_ecology_simulation.py
```

The example prints the completed step count plus final population, carcass, and
environmental-resource summaries.

## Known simplifications

The reference ecology intentionally exposes several areas for future model work:

- unassimilated food is not yet returned to the environment as waste,
- sensing has no energetic cost,
- predation success is deterministic once size and attack/defense eligibility
  are satisfied,
- sexual reproduction has interchangeable parent roles and no sex trait,
- mate detection is perfect inside mutual mate-search range,
- signaling and courtship have no energetic cost separate from locomotion,
- metabolic and locomotion efficiency have no explicit compensating performance
  tradeoff, and
- the preset provides no observer/analytics layer yet.

These are explicit limitations, not behavior hidden inside the reference
configuration. They make the preset useful as a roadmap: future capabilities can
be integrated here and immediately exercised against the full ecosystem.
