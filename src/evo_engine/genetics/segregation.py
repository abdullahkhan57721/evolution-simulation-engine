"""Chromosome segregation policies for biological gamete formation."""

from __future__ import annotations

import random
from typing import Protocol

from evo_engine.genetics.chromosome import Chromosome
from evo_engine.genetics.chromosome_association import ChromosomeAssociation
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.validation import validators


class ChromosomeSegregationModel(Protocol):
    """Select chromosome copies transmitted from meiotic associations."""

    def segregate(
        self,
        associations: tuple[ChromosomeAssociation, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[Chromosome, ...]:
        """Return chromosome copies entering one gamete."""
        ...


class BivalentSegregation:
    """Transmit a singleton or one chromosome from each bivalent association."""

    def segregate(
        self,
        associations: tuple[ChromosomeAssociation, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[Chromosome, ...]:
        """Select one transmitted chromosome from every supplied association."""
        validators.validate_tuple(associations, name="associations")
        if not isinstance(genetic_architecture, GeneticArchitecture):
            raise TypeError(
                "genetic_architecture must be a GeneticArchitecture; "
                f"received {genetic_architecture!r}."
            )
        if not isinstance(rng, random.Random):
            raise TypeError(
                f"rng must be an instance of random.Random; received {rng!r}."
            )

        transmitted: list[Chromosome] = []
        for index, association in enumerate(associations):
            if not isinstance(association, ChromosomeAssociation):
                raise TypeError(
                    f"associations[{index}] must be a ChromosomeAssociation; "
                    f"received {association!r}."
                )

            copy_count = len(association.chromosomes)
            if copy_count == 1:
                transmitted.append(association.chromosomes[0])
            elif copy_count == 2:
                transmitted.append(rng.choice(association.chromosomes))
            else:
                raise ValueError(
                    "BivalentSegregation supports singleton and bivalent "
                    f"associations; association {index} has {copy_count} copies."
                )

        return tuple(transmitted)
