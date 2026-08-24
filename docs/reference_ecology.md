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

The reference population begins homozygous for seventeen integer traits:

| Trait | Default | Role |
| --- | ---: | --- |
| `adult_body_mass` | 8 | Adult developmental body-mass target |
| `max_speed` | 1 | Maximum movement distance |
| `sensory_range` | 4 | Resource-detection radius |
| `sensory_accuracy` | 90 | Percent chance to detect each in-range resource deposit |
| `max_intake_rate` | 4 | Maximum environmental resource intake per timestep |
| `assimilation_efficiency` | 75 | Percent of consumed resources converted to usable energy |
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

Movement uses `EnergyThresholdMovementIntent` with the same developmental
threshold:

```text
energy below threshold
    → energy_acquisition
    → consider resources within sensory_range
    → detect each in-range resource using sensory_accuracy
    → move toward the nearest detected resource

energy at/above threshold
    → exploration
    → untargeted Moore movement
```

The shared threshold is a reference-model choice, not an engine invariant.
Callers can compose different threshold models.

The reference ecology uses genetic sensory range and genetic sensory accuracy.
Accuracy 0 always misses an in-range deposit and accuracy 100 always detects it;
intermediate values use the simulation RNG independently for each in-range
deposit considered during targeting.

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

## Mate choice and sexual selection

Reference mating now separates individual eligibility, encounter range,
acceptance, and preference:

```text
maturity + reproduction energy eligibility
        ↓
hard mating neighborhood
        ↓
both parents within each other's mate_search_range
        ↓
each parent's mating_signal >= the other's choosiness
        ↓
mutual signal-surplus preference score
        ↓
PreferenceOrder conflict resolution
        ↓
sexual inheritance and birth
```

The hard `mating_radius` defaults to 20 and acts as a broad geometry cap. The
organism-specific founder `mate_search_range` is three and therefore supplies the
meaningful local encounter limit in the default 12 × 12 world.

`MutualSignalCompatibility` requires two-way acceptance. A candidate pair forms
only when each partner's expressed signal meets the other's expressed choosiness.
`MutualSignalMarginPreference` then scores the total amount by which both signals
exceed those thresholds. The reproduction resolver selects the highest-scoring
non-conflicting proposals first, so mate-search range, choosiness, and mating
signal can all alter realized reproductive success.

The current sexual-selection model is role-symmetric because reproductive parents
are interchangeable. It does not yet represent sexes, mating types, or asymmetric
courtship roles. Those can be added through different parent-selection policies
without changing sexual inheritance.

## Energy priorities

The preset deliberately uses different expenditure policies for different kinds
of activity:

```text
mandatory metabolism
    → may deplete energy to zero

movement / food seeking
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

- power-law basal metabolism,
- random resource generation,
- carcass decomposition,
- state-dependent resource-seeking/exploratory movement,
- genetic sensory range and probabilistic sensory accuracy,
- power-law locomotion costs,
- size- and attack/defense-gated same-neighborhood predation,
- attack-advantage predation preference,
- genetic intake-capacity limits,
- equal-share resource competition,
- genetic resource-to-energy assimilation efficiency,
- fixed-rate growth with linear energy cost,
- maturity- and energy-gated sexual reproduction,
- genetic mutual mate-search range,
- genetic choosiness and mating signal,
- mutual signal-surplus mating preference,
- meiotic segregation with single crossover,
- mutation of transmitted alleles,
- developmental energy reserves,
- starvation mortality, and
- developmental maximum-age mortality.

## Customization

All numerical baseline values live in `ReferenceEcologyConfig` and
`ReferenceTraitValues`.

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
    traits=ReferenceTraitValues(
        adult_body_mass=10,
        max_speed=2,
        sensory_range=6,
        sensory_accuracy=85,
        max_intake_rate=8,
        assimilation_efficiency=70,
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
- mate search affects reproduction-stage encounter but does not yet drive
  movement toward potential mates,
- growth rate is fixed rather than heritable, and
- the preset provides no observer/analytics layer yet.

These are explicit limitations, not behavior hidden inside the reference
configuration. They make the preset useful as a roadmap: future capabilities can
be integrated here and immediately exercised against the full ecosystem.
