"""One-locus genetics and deterministic founders for controlled locomotion."""

from __future__ import annotations

from evo_engine.genetics import (
    MAX_SPEED,
    Chromosome,
    ChromosomeStructure,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    MeanIntegerExpression,
    NoMutation,
    Trait,
)
from evo_engine.presets.controlled_locomotion.config import (
    CONTROLLED_MAX_SPEED_MAXIMUM,
    ControlledLocomotionConfig,
)
from evo_engine.validation import validators
from evo_engine.world import Organism, WorldState

CONTROLLED_LOCOMOTION_CHROMOSOME = "locomotion"


def build_controlled_locomotion_genetic_architecture() -> GeneticArchitecture:
    """Build the one-locus haploid genetic architecture used by E2.

    Returns:
        Genetic architecture containing only inherited ``max_speed`` with no
        mutation. Haploidy is an experimental composition choice; it does not
        alter the engine's general support for richer ploidy or sexual genetics.
    """
    return GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(
                    name=CONTROLLED_LOCOMOTION_CHROMOSOME,
                    allowed_copy_counts=(1,),
                ),
            )
        ),
        loci=(
            Locus(
                name=MAX_SPEED,
                chromosome_name=CONTROLLED_LOCOMOTION_CHROMOSOME,
                position=0,
                domain=IntegerAlleleDomain(
                    minimum=0,
                    maximum=CONTROLLED_MAX_SPEED_MAXIMUM,
                ),
                mutation=NoMutation(),
            ),
        ),
        traits=(
            Trait(
                name=MAX_SPEED,
                locus_names=(MAX_SPEED,),
                expression=MeanIntegerExpression(),
            ),
        ),
    )


def build_controlled_locomotion_founder_genome(
    genetic_architecture: GeneticArchitecture,
    *,
    max_speed: int,
) -> Genome:
    """Build one validated founder genome with the requested locomotor capacity.

    Args:
        genetic_architecture: Controlled one-locus architecture.
        max_speed: Inherited maximum movement capacity.

    Returns:
        Haploid founder genome containing the focal ``max_speed`` allele.
    """
    if not isinstance(genetic_architecture, GeneticArchitecture):
        raise TypeError("genetic_architecture must be a GeneticArchitecture.")
    validators.validate_int_in_range(
        max_speed,
        lower=0,
        upper=CONTROLLED_MAX_SPEED_MAXIMUM,
        name="max_speed",
    )
    genome = Genome(
        chromosomes=(
            Chromosome(
                name=CONTROLLED_LOCOMOTION_CHROMOSOME,
                alleles=(
                    genetic_architecture.locus(MAX_SPEED).create_allele(max_speed),
                ),
            ),
        )
    )
    genetic_architecture.validate_genome(genome)
    return genome


def build_controlled_locomotion_world(
    genetic_architecture: GeneticArchitecture,
    config: ControlledLocomotionConfig,
) -> WorldState:
    """Build the deterministic founder world for a controlled locomotion assay.

    Args:
        genetic_architecture: Controlled one-locus architecture.
        config: Deterministic founder, resource, and fixed-biology configuration.

    Returns:
        Initialized world with caller-ordered founders and resource deposits.
    """
    if not isinstance(genetic_architecture, GeneticArchitecture):
        raise TypeError("genetic_architecture must be a GeneticArchitecture.")
    if not isinstance(config, ControlledLocomotionConfig):
        raise TypeError("config must be a ControlledLocomotionConfig.")

    world = WorldState(width=config.width, height=config.height)
    for deposit in config.resource_deposits:
        world.add_resources(x=deposit.x, y=deposit.y, amount=deposit.amount)

    for founder in config.founders:
        genome = build_controlled_locomotion_founder_genome(
            genetic_architecture,
            max_speed=founder.max_speed,
        )
        world.add_organism(
            Organism.from_genome(
                genetic_architecture=genetic_architecture,
                genome=genome,
                energy=config.initial_energy,
                body_mass=config.body_mass,
                mating_type="clonal",
                x=founder.x,
                y=founder.y,
            )
        )

    return world
