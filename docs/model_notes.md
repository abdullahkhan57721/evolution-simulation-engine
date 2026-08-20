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
