# Evolution Simulation Engine

An extensible Python engine for evolutionary simulations with staged event
processing, spatial ecology, configurable genetics, and one- or two-parent
reproduction.

## Architecture

The engine separates simulation orchestration from ecological processes and
domain-specific policies:

```text
src/evo_engine/
├── engine/        simulation state, engine loop, stages, steps, protocols
├── world/         organisms, carcasses, and mutable world state
├── genetics/      alleles, loci, chromosomes, genomes, inheritance,
│                  recombination, expression, and genetic phenotype
├── development/   developmental variation and individual target profiles
├── growth/        policies that determine potential body-mass gain
├── energetics/    energetic cost models for metabolism, movement, and growth
├── reproduction/ reproductive eligibility, parent selection, investment,
│                  and offspring placement
├── spatial/       neighborhoods, distances, boundaries, movement patterns
├── processes/     simulation processes that propose and apply events
├── resolvers/     conflict-resolution policies for proposed events
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

Run the basic example:

```bash
python examples/basic_aging_simulation.py
```

Double-click `open_project_terminal.command` on macOS to open a shell at the
project root with the local virtual environment activated.

Double-click `make_review_zip.command` to create a clean review ZIP in
`~/Downloads`.
