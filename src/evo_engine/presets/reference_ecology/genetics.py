"""Genetic architecture and founder-world builders for the reference ecology."""

from __future__ import annotations

from evo_engine.genetics import (
    Chromosome,
    ChromosomeStructure,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    MeanIntegerExpression,
    Trait,
    UniformIntegerMutation,
)
from evo_engine.presets.reference_ecology.config import (
    REFERENCE_CHROMOSOME,
    REFERENCE_TRAIT_DOMAINS,
    ReferenceEcologyConfig,
    resolve_reference_config,
)
from evo_engine.presets.reference_ecology.mating_types import (
    reference_founder_mating_type,
)
from evo_engine.world import Organism, WorldState


def build_reference_genetic_architecture(
    config: ReferenceEcologyConfig | None = None,
) -> GeneticArchitecture:
    """Build the genetic architecture used by the reference ecology.

    Each modeled trait has one bounded integer locus. All loci share one
    explicitly diploid chromosome so sexual reproduction exercises segregation
    and crossover.

    Args:
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Genetic architecture containing every trait required by the preset.
    """
    config = resolve_reference_config(config)
    mutation = UniformIntegerMutation(
        probability_ppm=config.mutation_probability_ppm,
        max_change=config.mutation_max_change,
    )

    loci = tuple(
        Locus(
            name=trait_name,
            chromosome_name=REFERENCE_CHROMOSOME,
            position=index * 100,
            domain=IntegerAlleleDomain(
                minimum=minimum,
                maximum=maximum,
            ),
            mutation=mutation,
        )
        for index, (trait_name, (minimum, maximum)) in enumerate(
            REFERENCE_TRAIT_DOMAINS.items(),
            start=1,
        )
    )
    traits = tuple(
        Trait(
            name=trait_name,
            locus_names=(trait_name,),
            expression=MeanIntegerExpression(),
        )
        for trait_name in REFERENCE_TRAIT_DOMAINS
    )

    return GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(
                    name=REFERENCE_CHROMOSOME,
                    allowed_copy_counts=(2,),
                ),
            )
        ),
        loci=loci,
        traits=traits,
    )


def build_reference_founder_genome(
    genetic_architecture: GeneticArchitecture,
    config: ReferenceEcologyConfig | None = None,
) -> Genome:
    """Build the homozygous founder genome used by the reference ecology.

    Args:
        genetic_architecture: Architecture used to create and validate alleles.
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Diploid homozygous founder genome.
    """
    config = resolve_reference_config(config)
    alleles = tuple(
        genetic_architecture.locus(trait_name).create_allele(value)
        for trait_name, value in config.traits.as_mapping().items()
    )

    return Genome(
        chromosomes=(
            Chromosome(
                name=REFERENCE_CHROMOSOME,
                alleles=alleles,
            ),
            Chromosome(
                name=REFERENCE_CHROMOSOME,
                alleles=alleles,
            ),
        )
    )


def build_reference_world(
    genetic_architecture: GeneticArchitecture,
    config: ReferenceEcologyConfig | None = None,
) -> WorldState:
    """Build the reference world and compact founder population.

    Founders occupy distinct cells in row-major order. Compact placement keeps
    early mating and interaction opportunities possible without hidden random
    initialization draws. Mating types cycle deterministically through the
    reference type set, yielding a balanced founder population without consuming
    simulation RNG.

    Args:
        genetic_architecture: Architecture shared by all organisms.
        config: Optional reference configuration. Defaults to standard values.

    Returns:
        Initialized world containing the founder population.
    """
    config = resolve_reference_config(config)
    founder_genome = build_reference_founder_genome(
        genetic_architecture,
        config,
    )
    world = WorldState(
        width=config.width,
        height=config.height,
    )

    for index in range(config.initial_population):
        world.add_organism(
            Organism.from_genome(
                genetic_architecture=genetic_architecture,
                genome=founder_genome,
                age=0,
                energy=config.initial_energy,
                mating_type=reference_founder_mating_type(index),
                x=index % config.width,
                y=index // config.width,
            )
        )

    return world
