"""Chromosome pairing policies for biological gamete formation."""

from __future__ import annotations

import random
from typing import Protocol

from evo_engine.genetics.chromosome_association import ChromosomeAssociation
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.genome import Genome


class ChromosomePairingModel(Protocol):
    """Organize parent chromosome copies into temporary meiotic associations."""

    def pair(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[ChromosomeAssociation, ...]:
        """Return chromosome associations for one parent genome."""
        ...


class SameNameBivalentPairing:
    """Pair current simple chromosome groups as singletons or bivalents.

    Chromosome-name equality is a convention of this concrete policy rather than
    a universal definition of homology. The policy supports one or two copies of
    each same-name chromosome group and explicitly rejects larger groups.
    """

    def pair(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[ChromosomeAssociation, ...]:
        """Return singleton or bivalent associations in genome order."""
        if not isinstance(genome, Genome):
            raise TypeError(
                "genome must be an instance of Genome; "
                f"received {genome!r}."
            )
        if not isinstance(genetic_architecture, GeneticArchitecture):
            raise TypeError(
                "genetic_architecture must be a GeneticArchitecture; "
                f"received {genetic_architecture!r}."
            )
        if not isinstance(rng, random.Random):
            raise TypeError(
                "rng must be an instance of random.Random; "
                f"received {rng!r}."
            )

        chromosome_names = tuple(
            dict.fromkeys(chromosome.name for chromosome in genome.chromosomes)
        )
        associations: list[ChromosomeAssociation] = []

        for chromosome_name in chromosome_names:
            chromosomes = genome.chromosomes_named(chromosome_name)
            if len(chromosomes) > 2:
                raise ValueError(
                    "SameNameBivalentPairing supports at most two copies per "
                    f"chromosome name; {chromosome_name!r} has {len(chromosomes)}."
                )
            associations.append(ChromosomeAssociation(chromosomes=chromosomes))

        return tuple(associations)
