"""Chromosome-copy association policies for biological gamete formation."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.genetics.chromosome import Chromosome
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.genome import Genome
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class ChromosomeAssociation:
    """Represent chromosome copies selected to interact during gamete formation.

    An association is transient meiotic organization, not persistent chromosome
    identity. It intentionally does not require chromosome-name equality so
    future pairing policies can represent biological relationships stronger than
    today's simple same-name rule. Each physical chromosome-copy object may occur
    at most once in an association; distinct copies may still carry equal state.

    Attributes:
        chromosomes: Ordered chromosome copies participating in the association.
    """

    chromosomes: tuple[Chromosome, ...]

    def __attrs_post_init__(self) -> None:
        """Validate associated chromosome copies."""
        validators.validate_tuple(self.chromosomes, name="chromosomes")
        if not self.chromosomes:
            raise ValueError("chromosomes must contain at least one chromosome.")

        chromosome_identities: set[int] = set()
        for index, chromosome in enumerate(self.chromosomes):
            if not isinstance(chromosome, Chromosome):
                raise TypeError(
                    f"chromosomes[{index}] must be an instance of Chromosome; "
                    f"received {chromosome!r}."
                )
            chromosome_identity = id(chromosome)
            if chromosome_identity in chromosome_identities:
                raise ValueError(
                    "chromosomes must contain unique chromosome-copy objects; "
                    f"chromosomes[{index}] repeats an earlier copy."
                )
            chromosome_identities.add(chromosome_identity)


class ChromosomePairing(Protocol):
    """Define how a parent genome is organized into chromosome associations."""

    def pair(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[ChromosomeAssociation, ...]:
        """Organize parent chromosome copies for recombination and segregation.

        Args:
            genome: Structurally valid parent genome.
            genetic_architecture: Shared biological genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Ordered chromosome associations covering the parent genome.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class SameNameBivalentPairing:
    """Pair same-name chromosome copies as singletons or bivalents.

    This policy preserves the current simple biological rule: one same-name copy
    forms a singleton association and two same-name copies form one bivalent.
    Higher-copy groups are structurally allowed when the genetic architecture
    permits them, but are unsupported by this particular pairing policy.
    """

    def pair(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[ChromosomeAssociation, ...]:
        """Return same-name singleton or bivalent chromosome associations.

        Args:
            genome: Structurally valid parent genome.
            genetic_architecture: Shared biological genetic architecture.
            rng: Simulation random-number generator. This deterministic policy
                does not consume it.

        Returns:
            Associations in first-seen chromosome-name order.

        Raises:
            TypeError: If an input has an invalid type.
            ValueError: If a same-name group contains more than two copies.
        """
        if not isinstance(genome, Genome):
            raise TypeError("genome must be an instance of Genome.")
        if not isinstance(genetic_architecture, GeneticArchitecture):
            raise TypeError(
                "genetic_architecture must be an instance of GeneticArchitecture."
            )
        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        genetic_architecture.validate_genome(genome)

        chromosome_names = tuple(
            dict.fromkeys(chromosome.name for chromosome in genome.chromosomes)
        )
        associations = []
        for chromosome_name in chromosome_names:
            chromosomes = genome.chromosomes_named(chromosome_name)
            if len(chromosomes) > 2:
                raise ValueError(
                    "SameNameBivalentPairing supports at most two copies per "
                    f"chromosome name; {chromosome_name!r} has {len(chromosomes)}."
                )
            associations.append(ChromosomeAssociation(chromosomes=chromosomes))

        return tuple(associations)
