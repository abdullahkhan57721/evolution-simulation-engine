# Heritable Physiological Performance

The engine separates shared physical scaling laws from organism-specific
performance. This allows simulations to keep one ecological model while letting
individual coefficients evolve.

## Shared law versus heritable coefficient

A power-law cost model can now receive either a fixed numerical coefficient or an
organism-specific `CoefficientModel`:

```text
shared simulation law
    metabolic mass exponent
    locomotion mass exponent
    locomotion distance exponent
            ↓
organism-specific coefficient source
            ↓
current body mass / displacement
            ↓
energy cost
```

The built-in `GeneticPhenotypeCoefficient` reads an integer genetic phenotype
trait and divides it by a positive integer denominator. This preserves the
integer-locus genetics system while allowing fractional coefficients.

For example:

```python
from evo_engine.energetics import (
    GeneticPhenotypeCoefficient,
    PowerLawMetabolicCost,
)
from evo_engine.genetics import METABOLIC_COST_COEFFICIENT

cost_model = PowerLawMetabolicCost(
    coefficient=GeneticPhenotypeCoefficient(
        trait_name=METABOLIC_COST_COEFFICIENT,
        denominator=100,
    ),
    mass_exponent=0.75,
)
```

An expressed trait value of `30` therefore becomes coefficient `0.30`.

Fixed numerical coefficients remain fully supported. The coefficient abstraction
changes where a value may come from; it does not force genetics into generic
energetic models.

## Genetic growth rate

`GeneticPhenotypeGrowthRate` reads the canonical `growth_rate` trait and returns
that nonnegative integer as potential body-mass gain for the current growth
stage.

The `Growth` process retains responsibility for the later constraints:

```text
growth_rate trait
    ↓
potential body-mass gain
    ↓
cap at developmental adult_body_mass
    ↓
price capped gain with GrowthCostModel
    ↓
apply EnergyExpenditurePolicy
    ↓
realized mass gain + energy loss
```

This creates a meaningful life-history tradeoff without embedding it inside the
genetic model. A faster-growing organism can reach adult size sooner, but when
more mass is gained in one timestep the configured growth-cost model charges for
that larger increment immediately. If the organism cannot afford the full capped
gain under its expenditure policy, the current all-or-nothing growth semantics
still suppress the event.

A zero growth-rate trait is valid and means no potential growth for that organism.
This is useful both as a possible evolved boundary state and for experiments that
need to isolate other processes.

## Metabolic performance

`PowerLawMetabolicCost` now accepts a `CoefficientSource`. With the reference
trait-driven source its cost is:

```text
metabolic coefficient = metabolic_cost_coefficient / 100

raw metabolic cost
    = metabolic coefficient
      × current_body_mass ** metabolic_mass_exponent
```

The raw value is rounded with the existing nonnegative half-up cost semantics and
then subjected to the configured minimum cost.

The reference founder value is `30`, reproducing the previous fixed coefficient
of `0.30`.

## Locomotor performance

`PowerLawLocomotionCost` uses the same coefficient abstraction:

```text
locomotion coefficient = locomotion_cost_coefficient / 100

raw locomotion cost
    = locomotion coefficient
      × current_body_mass ** locomotion_mass_exponent
      × euclidean_distance ** locomotion_distance_exponent
```

The reference founder value is `20`, reproducing the previous fixed coefficient
of `0.20`.

Two organisms making the same displacement can therefore pay different energy
costs even when body mass and movement geometry are identical.

Coefficient traits may be zero. That produces a zero raw power-law coefficient;
any configured process/model minimum cost still applies afterward. In the
reference ecology, for example, basal metabolism retains a minimum cost of one
energy unit even when the genetic coefficient is zero.

## Reference ecology traits

The reference ecology now contains three additional physiological-performance
traits:

| Trait | Founder value | Domain | Interpretation |
| --- | ---: | ---: | --- |
| `growth_rate` | 1 | 0–4 | Potential body-mass units gained per growth timestep |
| `metabolic_cost_coefficient` | 30 | 0–200 | Hundredths of basal metabolic power-law coefficient |
| `locomotion_cost_coefficient` | 20 | 0–200 | Hundredths of locomotion power-law coefficient |

All are ordinary bounded integer loci on the reference chromosome. They therefore
participate in meiotic segregation, crossover, mutation, expression, and
inheritance exactly like the other reference traits.

The global mutation step remains one integer unit. For the energetic coefficients
that means one mutation step changes the effective coefficient by `0.01`. For
`growth_rate`, one mutation step changes potential growth by one body-mass unit
per growth timestep.

## What is and is not a tradeoff

The current model deliberately distinguishes heritable performance variation from
physiological allocation constraints.

`growth_rate` already creates an explicit timing/energy tradeoff because faster
realized growth consumes more growth energy sooner.

By contrast, lower metabolic and locomotion cost coefficients are currently
energetically advantageous without a built-in compensating disadvantage. They are
therefore evolvable performance traits, but not yet constrained efficiency
tradeoffs. The engine does not invent a penalty such as weaker attack, lower
speed, or reduced fertility merely to balance them.

A future physiology milestone can add explicit resource-allocation or performance
constraint models—for example, a tradeoff between locomotor efficiency and
maximum speed—while reusing the coefficient-source interfaces introduced here.

## Trait preflight

`GeneticPhenotypeCoefficient` and `GeneticPhenotypeGrowthRate` expose
`required_traits`. `PowerLawMetabolicCost`, `PowerLawLocomotionCost`, `Metabolism`,
`Movement`, and `Growth` aggregate those dependencies through the existing trait
requirement system.

Missing performance traits are therefore detected by engine preflight before the
simulation begins rather than failing only after a particular organism attempts
the relevant process.
