"""Inheritance models for producing offspring genomes."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.evolution import TransmissionModel
from evo_engine.genetics.chromosome import Chromosome
from evo_engine.genetics.gamete import Gamete
from evo_engine.genetics.gamete_formation import (
    GameteFormation,
    MeioticGameteFormation,
)
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.genome import Genome


class InheritanceModel(
    TransmissionModel[Genome, GeneticArchitecture],
    Protocol,
):
    """Define biological inheritance as general heritable-state transmission."""

    @property
    def parent_count(self) -> int:
        """Return the required number of biological parents."""
        ...

    def inherit(
        self,
        parent_genomes: tuple[Genome, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> Genome:
        """Produce an offspring genome from parent genomes.

        Args:
            parent_genomes: Genomes contributing to the offspring.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Offspring genome.
        """
        ...


def _validate_inheritance_inputs(
    parent_genomes: tuple[Genome, ...],
    *,
    genetic_architecture: GeneticArchitecture,
    rng: random.Random,
) -> None:
    """Validate inputs shared by inheritance implementations."""
    if type(parent_genomes) is not tuple:
        raise TypeError("parent_genomes must be a tuple.")

    for index, genome in enumerate(parent_genomes):
        if not isinstance(genome, Genome):
            raise TypeError(
                f"parent_genomes[{index}] must be an instance of Genome; "
                f"received {genome!r}."
            )

    if not isinstance(
        genetic_architecture,
        GeneticArchitecture,
    ):
        raise TypeError(
            "genetic_architecture must be an instance of GeneticArchitecture."
        )

    if not isinstance(rng, random.Random):
        raise TypeError("rng must be an instance of random.Random.")

    for genome in parent_genomes:
        genetic_architecture.validate_genome(genome)


def _mutate_chromosome(
    chromosome: Chromosome,
    *,
    genetic_architecture: GeneticArchitecture,
    rng: random.Random,
) -> Chromosome:
    """Return a chromosome whose alleles passed through locus mutation."""
    return Chromosome(
        name=chromosome.name,
        alleles=tuple(
            genetic_architecture.locus(allele.locus_name).mutate(
                allele,
                rng=rng,
            )
            for allele in chromosome.alleles
        ),
    )


def _mutate_gamete(
    gamete: Gamete,
    *,
    genetic_architecture: GeneticArchitecture,
    rng: random.Random,
) -> Gamete:
    """Return a gamete with independently mutated transmitted alleles."""
    return Gamete(
        chromosomes=tuple(
            _mutate_chromosome(
                chromosome,
                genetic_architecture=genetic_architecture,
                rng=rng,
            )
            for chromosome in gamete.chromosomes
        )
    )


@attrs.frozen(slots=True, kw_only=True)
class ClonalInheritance:
    """Produce an offspring genome by copying one parent genome.

    Every copied allele passes through the mutation policy configured for its
    locus. Chromosome structure and phase are otherwise preserved.
    """

    @property
    def parent_count(self) -> int:
        """Return one required biological parent."""
        return 1

    @property
    def contributor_count(self) -> int:
        """Return one contributing heritable state through the general API."""
        return self.parent_count

    def inherit(
        self,
        parent_genomes: tuple[Genome, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> Genome:
        """Produce a clonally inherited offspring genome.

        Args:
            parent_genomes: Tuple containing exactly one parent genome.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Mutated clonal copy of the parent genome.

        Raises:
            TypeError: If an input has an invalid type.
            ValueError: If parent count or genetic state is invalid.
        """
        _validate_inheritance_inputs(
            parent_genomes,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )

        if len(parent_genomes) != 1:
            raise ValueError("ClonalInheritance requires exactly one parent genome.")

        parent_genome = parent_genomes[0]
        offspring_genome = Genome(
            chromosomes=tuple(
                _mutate_chromosome(
                    chromosome,
                    genetic_architecture=genetic_architecture,
                    rng=rng,
                )
                for chromosome in parent_genome.chromosomes
            )
        )

        genetic_architecture.validate_genome(offspring_genome)

        return offspring_genome

    def transmit(
        self,
        parent_states: tuple[Genome, ...],
        *,
        context: GeneticArchitecture,
        rng: random.Random,
    ) -> Genome:
        """Transmit genomes through the domain-neutral evolution contract."""
        return self.inherit(
            parent_states,
            genetic_architecture=context,
            rng=rng,
        )


@attrs.frozen(slots=True, kw_only=True)
class SexualInheritance:
    """Produce an offspring genome from gametes formed by two parents.

    Attributes:
        gamete_formation: Policy used independently for each parent genome.
    """

    gamete_formation: GameteFormation = attrs.field(
        factory=MeioticGameteFormation,
    )

    @property
    def parent_count(self) -> int:
        """Return two required biological parents."""
        return 2

    @property
    def contributor_count(self) -> int:
        """Return two contributing heritable states through the general API."""
        return self.parent_count

    def __attrs_post_init__(self) -> None:
        """Validate sexual-inheritance configuration."""
        try:
            form_gamete = self.gamete_formation.form_gamete
        except AttributeError as error:
            raise TypeError(
                "gamete_formation must provide a callable form_gamete method."
            ) from error

        if not callable(form_gamete):
            raise TypeError(
                "gamete_formation must provide a callable form_gamete method."
            )

    def inherit(
        self,
        parent_genomes: tuple[Genome, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> Genome:
        """Produce a sexually inherited offspring genome.

        Each parent independently forms one gamete. Transmitted alleles then
        pass through their locus mutation policies, and the two gametes are
        combined into the offspring genome.

        Args:
            parent_genomes: Tuple containing exactly two parent genomes.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Offspring genome assembled from the two parental gametes.

        Raises:
            TypeError: If an input has an invalid type.
            ValueError: If parent count or genetic state is invalid.
        """
        _validate_inheritance_inputs(
            parent_genomes,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )

        if len(parent_genomes) != 2:
            raise ValueError("SexualInheritance requires exactly two parent genomes.")

        gametes = tuple(
            _mutate_gamete(
                self.gamete_formation.form_gamete(
                    parent_genome,
                    genetic_architecture=genetic_architecture,
                    rng=rng,
                ),
                genetic_architecture=genetic_architecture,
                rng=rng,
            )
            for parent_genome in parent_genomes
        )

        offspring_genome = Genome(
            chromosomes=tuple(
                chromosome for gamete in gametes for chromosome in gamete.chromosomes
            )
        )

        genetic_architecture.validate_genome(offspring_genome)

        return offspring_genome

    def transmit(
        self,
        parent_states: tuple[Genome, ...],
        *,
        context: GeneticArchitecture,
        rng: random.Random,
    ) -> Genome:
        """Transmit genomes through the domain-neutral evolution contract."""
        return self.inherit(
            parent_states,
            genetic_architecture=context,
            rng=rng,
        )
