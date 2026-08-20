"""Shared test helpers for current engine-domain tests."""

from __future__ import annotations

import random
from collections.abc import Mapping

from evo_engine.engine import SimulationState
from evo_engine.genetics import (
    Chromosome,
    GeneticArchitecture,
    GeneticPhenotype,
    Genome,
    IntegerAlleleDomain,
    Locus,
    MeanIntegerExpression,
    NoMutation,
    Trait,
)
from evo_engine.world import Organism, WorldState


def make_empty_architecture() -> GeneticArchitecture:
    """Return a genetic architecture with no modeled loci or traits."""
    return GeneticArchitecture(
        loci=(),
        traits=(),
    )


def make_empty_genome() -> Genome:
    """Return a genome with no modeled chromosomes."""
    return Genome(
        chromosomes=(),
    )


def make_integer_architecture(
    *trait_names: str,
) -> GeneticArchitecture:
    """Return one-locus integer traits on a single modeled chromosome."""
    loci = tuple(
        Locus(
            name=trait_name,
            chromosome_name="1",
            position=index * 100,
            domain=IntegerAlleleDomain(),
            mutation=NoMutation(),
        )
        for index, trait_name in enumerate(
            trait_names,
            start=1,
        )
    )
    traits = tuple(
        Trait(
            name=trait_name,
            locus_names=(trait_name,),
            expression=MeanIntegerExpression(),
        )
        for trait_name in trait_names
    )

    return GeneticArchitecture(
        loci=loci,
        traits=traits,
    )


def make_diploid_genome(
    genetic_architecture: GeneticArchitecture,
    trait_values: Mapping[str, int],
) -> Genome:
    """Return a diploid genome with homozygous values for modeled loci."""
    alleles = tuple(
        genetic_architecture.locus(locus_name).create_allele(value)
        for locus_name, value in trait_values.items()
    )

    return Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=alleles,
            ),
            Chromosome(
                name="1",
                alleles=alleles,
            ),
        )
    )


def make_organism(
    *,
    genetic_architecture: GeneticArchitecture | None = None,
    trait_values: Mapping[str, int] | None = None,
    age: int = 0,
    energy: int = 100,
    body_mass: int | None = None,
    x: int = 0,
    y: int = 0,
) -> Organism:
    """Return an organism configured for a test."""
    if genetic_architecture is None:
        genetic_architecture = make_empty_architecture()

    if trait_values is None:
        genome = make_empty_genome()
    else:
        genome = make_diploid_genome(
            genetic_architecture,
            trait_values,
        )

    return Organism.from_genome(
        genetic_architecture=genetic_architecture,
        genome=genome,
        age=age,
        energy=energy,
        body_mass=body_mass,
        x=x,
        y=y,
    )


def make_state(
    *,
    width: int = 10,
    height: int = 10,
    genetic_architecture: GeneticArchitecture | None = None,
    seed: int = 1,
) -> SimulationState:
    """Return an empty simulation state for a test."""
    if genetic_architecture is None:
        genetic_architecture = make_empty_architecture()

    return SimulationState(
        world=WorldState(
            width=width,
            height=height,
        ),
        genetic_architecture=genetic_architecture,
        rng=random.Random(seed),
    )


def add_organism(
    state: SimulationState,
    *,
    trait_values: Mapping[str, int] | None = None,
    age: int = 0,
    energy: int = 100,
    body_mass: int | None = None,
    x: int = 0,
    y: int = 0,
) -> Organism:
    """Create, add, and return an organism using the state's architecture."""
    organism = make_organism(
        genetic_architecture=state.genetic_architecture,
        trait_values=trait_values,
        age=age,
        energy=energy,
        body_mass=body_mass,
        x=x,
        y=y,
    )
    state.world.add_organism(organism)
    return organism


def genetic_phenotype(**trait_values: int) -> GeneticPhenotype:
    """Return a simple integer genetic phenotype."""
    return GeneticPhenotype(
        trait_values=tuple(trait_values.items()),
    )
