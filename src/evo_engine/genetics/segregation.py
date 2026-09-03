"""Chromosome segregation policies for biological gamete formation."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.genetics.chromosome import Chromosome
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.pairing import ChromosomeAssociation
from evo_engine.validation import validators


class ChromosomeSegregation(Protocol):
    """Define which recombination products enter a gamete."""

    def segregate(
        self,
        associations: tuple[ChromosomeAssociation, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[Chromosome, ...]:
        """Select chromosome copies transmitted to one gamete.

        Args:
            associations: Recombined chromosome associations.
            genetic_architecture: Shared biological genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Ordered chromosome copies transmitted to the gamete.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class MendelianSegregation:
    """Transmit one chromosome from each singleton or bivalent association.

    Associations segregate independently. A singleton is therefore transmitted
    intact, a bivalent contributes one uniformly selected copy, and multiple
    bivalents can contribute multiple copies of the same chromosome type when a
    pairing policy has explicitly organized a higher-copy genome that way.
    """

    def segregate(
        self,
        associations: tuple[ChromosomeAssociation, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[Chromosome, ...]:
        """Select one chromosome copy from each supported association.

        Args:
            associations: Recombined singleton or bivalent associations.
            genetic_architecture: Shared biological genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Ordered transmitted chromosome copies.

        Raises:
            TypeError: If an input has an invalid type.
            ValueError: If an association contains more than two chromosomes.
        """
        validators.validate_tuple(associations, name="associations")
        if not isinstance(genetic_architecture, GeneticArchitecture):
            raise TypeError(
                "genetic_architecture must be an instance of GeneticArchitecture."
            )
        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        transmitted = []
        for index, association in enumerate(associations):
            if not isinstance(association, ChromosomeAssociation):
                raise TypeError(
                    f"associations[{index}] must be an instance of "
                    f"ChromosomeAssociation; received {association!r}."
                )
            if len(association.chromosomes) > 2:
                raise ValueError(
                    "MendelianSegregation supports singleton or bivalent "
                    f"associations; associations[{index}] contains "
                    f"{len(association.chromosomes)} chromosomes."
                )
            transmitted.append(rng.choice(association.chromosomes))

        return tuple(transmitted)
