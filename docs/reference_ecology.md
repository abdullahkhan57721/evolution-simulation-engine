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

The reference population begins homozygous for nine integer traits:

| Trait | Default | Role |
| --- | ---: | --- |
| `adult_body_mass` | 8 | Adult developmental body-mass target |
| `max_speed` | 1 | Maximum movement distance |
| `sensory_range` | 4 | Resource-detection radius |
| `energy_conservation_threshold` | 15 | Switch to conservation / food-seeking behavior |
| `energy_reserve` | 5 | Reserve protected from growth and reproduction |
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
    → detect nearest resource within sensory_range
    → move toward it

energy at/above threshold
    → exploration
    → untargeted Moore movement
```

The shared threshold is a reference-model choice, not an engine invariant.
Callers can compose different threshold models.

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
- power-law locomotion costs,
- same-cell predation by larger organisms,
- equal-share resource competition,
- fixed-rate growth with linear energy cost,
- maturity- and energy-gated sexual reproduction,
- meiotic segregation with single crossover,
- mutation of transmitted alleles,
- developmental energy reserves,
- starvation mortality, and
- developmental maximum-age mortality.

Predation is intentionally simple. Because the reference contains one generic
population, it currently represents opportunistic within-population predation:
larger organisms can prey on smaller organisms occupying the configured
predation neighborhood. Species, trophic roles, attack/defense traits, and prey
choice are future model layers rather than hidden assumptions in this preset.

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
        energy_conservation_threshold=18,
        energy_reserve=6,
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

- environmental resource consumption uses a fixed request amount rather than
  `max_intake_rate` or assimilation efficiency,
- resource sensing currently has perfect detection inside `sensory_range`,
- sensing has no energetic cost,
- predation uses body size rather than attack/defense traits,
- sexual reproduction has interchangeable parent roles and no sex trait,
- mate seeking does not yet drive movement,
- growth rate is fixed rather than heritable, and
- the preset provides no observer/analytics layer yet.

These are explicit limitations, not behavior hidden inside the reference
configuration. They make the preset useful as a roadmap: future capabilities can
be integrated here and immediately exercised against the full ecosystem.
