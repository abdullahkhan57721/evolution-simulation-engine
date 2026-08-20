"""Gamete-formation policies for sexual inheritance."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.genetics.gamete import Gamete
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.genome import Genome
from evo_engine.genetics.recombination import (
    NoRecombination,
    RecombinationModel,
)


class GameteFormation(Protocol):
    """Define how one parent genome produces a gamete."""

    def form_gamete(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> Gamete:
        """Form a gamete from a parent genome.

        Args:
            genome: Parent genome.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Formed gamete.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class MeioticGameteFormation:
    """Form a gamete through recombination and chromosome segregation.

    For each homologous chromosome group, the configured recombination model
    first produces chromosome copies available for segregation. One resulting
    copy is then selected uniformly at random. Chromosome groups assort
    independently.

    Attributes:
        recombination: Model governing exchange between homologous chromosomes.
    """

    recombination: RecombinationModel = attrs.field(
        factory=NoRecombination,
    )

    def __attrs_post_init__(self) -> None:
        """Validate gamete-formation configuration."""
        try:
            recombine = self.recombination.recombine
        except AttributeError as error:
            raise TypeError(
                "recombination must provide a callable recombine method."
            ) from error

        if not callable(recombine):
            raise TypeError("recombination must provide a callable recombine method.")

    def form_gamete(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> Gamete:
        """Form a gamete from a parent genome.

        Args:
            genome: Parent genome.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Gamete containing one segregated chromosome copy of each type.

        Raises:
            TypeError: If genome, genetic_architecture, or rng is invalid.
            ValueError: If genetic or recombination structure is invalid.
        """
        if not isinstance(genome, Genome):
            raise TypeError("genome must be an instance of Genome.")

        if not isinstance(
            genetic_architecture,
            GeneticArchitecture,
        ):
            raise TypeError(
                "genetic_architecture must be an instance of GeneticArchitecture."
            )

        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        genetic_architecture.validate_genome(genome)

        # dict.fromkeys preserves first-seen chromosome order while
        # collapsing homologous copies into one segregation group.
        chromosome_names = tuple(
            dict.fromkeys(chromosome.name for chromosome in genome.chromosomes)
        )

        selected_chromosomes = []

        for chromosome_name in chromosome_names:
            homologs = genome.chromosomes_named(chromosome_name)

            # Recombination acts within one homologous chromosome group.
            # Segregation then transmits exactly one candidate copy.
            segregation_candidates = self.recombination.recombine(
                homologs,
                genetic_architecture=genetic_architecture,
                rng=rng,
            )

            if not segregation_candidates:
                raise ValueError(
                    "recombination must return at least one chromosome candidate."
                )

            selected_chromosomes.append(rng.choice(segregation_candidates))

        return Gamete(
            chromosomes=tuple(selected_chromosomes),
        )
