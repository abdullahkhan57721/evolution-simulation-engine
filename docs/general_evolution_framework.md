# General Evolution Framework

The engine separates a domain-neutral evolutionary kernel from biological
semantics. Biology remains a first-class supported domain, but `Genome`,
`Chromosome`, `Locus`, and `Allele` are treated as one concrete realization of
more general evolutionary ideas rather than assumptions built into every
layer.

## Core evolutionary semantics

The `evo_engine.evolution` package defines the reusable concepts underneath the
biological genetics layer:

| General concept | Meaning | Biological specialization |
| --- | --- | --- |
| evolving entity | entity carrying transmissible state | `Organism` |
| heritable state | information that can pass to descendants | `Genome` |
| expression | mapping from heritable state to operative characteristics | `GeneticArchitecture.express` |
| variation | transformation that may alter transmitted information | mutation |
| transmission | construction of descendant heritable state from contributors | inheritance |
| linkage component | addressable transmissible component | `Locus` |
| linkage group | components that may remain associated during transmission | chromosome |
| linkage position | coordinate controlling proximity within a linkage group | locus position |

Selection is deliberately **not** represented as a required stored scalar.
Differential persistence and replication can emerge from configured processes,
resource competition, predation, mating success, mortality, and reproduction.

The runtime event architecture is already largely domain-neutral:

```text
state
  -> propose transitions
  -> resolve incompatible transitions
  -> materialize accepted stochastic consequences
  -> apply transitions
  -> commit timestep
  -> observe
```

A future nonbiological evolutionary domain can reuse those transaction and
conflict semantics while supplying different entity and heritable-state types.

## Biological genetics as an adapter layer

The genetics package maps biological vocabulary onto the general contracts
without removing the biology-oriented API:

- `Locus.chromosome_name` is also exposed as `Locus.linkage_group`.
- `Locus.position` is also exposed as `Locus.linkage_position`.
- mutation policies implement the general `VariationOperator` semantics through
  `vary(...)` while retaining `mutate(...)`.
- inheritance models implement the general `TransmissionModel` semantics
  through `transmit(...)` while retaining `inherit(...)`.
- `GeneticArchitecture.express(...)` already has the shape of a general
  heritable-state expression mapping.

The result is an adapter, not a parallel implementation: biological callers may
keep using the familiar API while generic evolutionary tooling can target the
upstream contracts.

## Linkage, proximity, and "stickiness"

The standard genetics term for nearby genes tending to be inherited together is
**genetic linkage**. Recombination can separate linked loci, and the probability
of separation generally increases with distance between them.

The engine now models two independent pieces:

1. **geometry** — positions of transmissible components within a linkage group;
2. **local breakpoint intensity** — how permissive each region is to breaking
   that linkage.

`SingleCrossoverRecombination` already used physical locus coordinates. A
larger coordinate gap therefore had more possible crossover locations than a
small gap. The explicit linkage-map API generalizes that behavior.

### Uniform linkage map

`UniformLinkageMap` preserves the previous behavior: every possible breakpoint
coordinate has equal weight.

```python
from evo_engine.genetics import SingleCrossoverRecombination, UniformLinkageMap

recombination = SingleCrossoverRecombination(
    probability_ppm=500_000,
    linkage_map=UniformLinkageMap(),
)
```

### Sticky regions and hotspots

`PiecewiseLinkageMap` changes local breakpoint intensity.

```python
from evo_engine.genetics import (
    PiecewiseLinkageMap,
    RecombinationInterval,
    SingleCrossoverRecombination,
)

linkage_map = PiecewiseLinkageMap(
    default_rate=1.0,
    intervals=(
        RecombinationInterval(
            linkage_group="chromosome_1",
            start=100,
            end=300,
            relative_rate=0.1,
        ),
        RecombinationInterval(
            linkage_group="chromosome_1",
            start=700,
            end=720,
            relative_rate=8.0,
        ),
    ),
)

recombination = SingleCrossoverRecombination(
    probability_ppm=500_000,
    linkage_map=linkage_map,
)
```

The first interval is relatively **sticky**: breakpoints are ten times less
likely per coordinate than the default background. The second interval is a
recombination **hotspot**. A rate of zero prevents a crossover breakpoint in an
interval entirely.

This design intentionally lives in `evo_engine.evolution`, not genetics, so a
nonbiological system may reuse ordered linkage and local transmission
association without pretending its components are genes.

## Categorical heritable state

Heritable information need not be numeric. `UniformChoiceMutation` supports
mutation among arbitrary configured categorical values.

```python
from evo_engine.genetics import (
    ChoiceAlleleDomain,
    Locus,
    UniformChoiceMutation,
)

color_locus = Locus(
    name="eye_color",
    chromosome_name="chromosome_2",
    position=150,
    domain=ChoiceAlleleDomain(values=("brown", "green", "blue")),
    mutation=UniformChoiceMutation(
        probability_ppm=1_000,
        choices=("brown", "green", "blue"),
    ),
)
```

If no process depends on `eye_color`, this adds heritable mutable variation
without modifying movement, metabolism, feeding, growth, predation,
reproduction, or engine orchestration.

## Architectural boundary

`evo_engine.evolution` is an upstream foundation. It may depend on validation
utilities, but it must not import biological domains, world state, concrete
processes, resolvers, presets, or engine orchestration. Import Linter enforces
that dependency direction.

The intended layering is:

```text
validation
    |
    v
general evolution abstractions
    |
    v
biological genetics and other domain models
    |
    v
processes / resolvers / engine composition
    |
    v
presets / experiments / user interfaces
```

This lets the project become more general without turning biological code into
vague abstractions or forcing nonbiological domains to depend on biological
terminology.
