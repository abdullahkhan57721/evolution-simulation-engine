# Feeding Physiology

The feeding domain separates three questions that were previously collapsed into
one resource-consumption amount:

```text
behavioral demand
    → how much food does the organism try to obtain?

intake capacity
    → how much food can its physiology consume this timestep?

assimilation
    → how much usable energy does consumed food yield?
```

`ResourceConsumption.requested_amount` remains behavioral demand. An optional
`IntakeCapacityModel` caps that request before resource competition is resolved:

```text
effective request = min(requested_amount, intake capacity)
```

The resource-allocation resolver then decides how much of that request is actually
obtained. Only after resolution does the configured `AssimilationModel` convert
the consumed amount into organism energy.

This ordering is important. Competition should operate on food quantities, not on
how efficiently different organisms digest that food.

## Intake capacity

The built-in intake models are:

- `FixedIntakeCapacity`: one configured capacity for every organism,
- `GeneticPhenotypeIntakeCapacity`: reads the canonical `max_intake_rate` trait.

The genetic model declares its trait requirement, so engine preflight validation
fails before step zero if the configured genetic architecture does not define
`max_intake_rate`.

Example:

```python
from evo_engine.feeding import GeneticPhenotypeIntakeCapacity
from evo_engine.processes import ResourceConsumption

feeding = ResourceConsumption(
    requested_amount=10,
    intake_capacity_model=GeneticPhenotypeIntakeCapacity(),
)
```

An organism with `max_intake_rate == 4` requests at most four resource units even
though the configured behavioral demand is ten.

Keeping demand and capacity separate leaves room for later models in which hunger,
season, stomach fullness, learned behavior, or risk alter desired food intake
without changing the organism's physiological maximum.

## Assimilation

The built-in assimilation models are:

- `FullAssimilation`: one energy unit per consumed resource unit,
- `FixedAssimilationEfficiency`: fixed 0–100% conversion,
- `GeneticPhenotypeAssimilationEfficiency`: reads the canonical
  `assimilation_efficiency` trait.

Percentage models use deterministic half-up integer rounding. For example:

```text
3 resource units × 50% = 1.5 → 2 energy units
4 resource units × 75% = 3.0 → 3 energy units
```

The generic `AssimilationModel` is not restricted to percentages. A future model
could represent resource-specific energy density, digestive state, temperature,
microbiome effects, or other physiology and return more than one energy unit per
resource unit if the model's resource units are defined that way.

## Resource allocation remains separate

Suppose two organisms share six resource units:

```text
Organism A
    behavioral demand = 10
    max intake rate = 2
    assimilation = 50%

Organism B
    behavioral demand = 10
    max intake rate = 6
    assimilation = 100%
```

Their proposals entering an equal-share resolver are therefore 2 and 6 resource
units. The resolver allocates 2 and 4. Application then produces:

```text
A: consumes 2 → gains 1 energy
B: consumes 4 → gains 4 energy
```

Assimilation efficiency does not influence who receives food unless a simulation
explicitly chooses a resolver whose weighting policy reads that trait.

## Unassimilated material

The full allocated food amount is removed from the environmental resource pool.
Only the assimilated fraction becomes organism energy. The unassimilated fraction
is currently outside the modeled resource pool, representing losses such as
waste, indigestible material, or heat at this level of abstraction.

A future waste/excretion process can return some of that material to the ecosystem
without changing the current intake/assimilation interfaces.

## Reference ecology

The reference ecology uses both genetic feeding models:

```text
max_intake_rate = 4 resource units / timestep
assimilation_efficiency = 75%
behavioral request ceiling = 10 resource units / timestep
```

Both traits are bounded integer loci and can change through sexual inheritance,
recombination, and mutation. This makes resource competition and digestive
efficiency genuine heritable components of organism energy acquisition.
