"""Gamete-formation policies for sexual inheritance."""

from __future__ import annotations

import random
from collections import Counter
from typing import Protocol

import attrs

from evo_engine.genetics.chromosome import Chromosome
from evo_engine.genetics.gamete import Gamete
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.genome import Genome
from evo_engine.genetics.pairing import (
    ChromosomeAssociation,
    ChromosomePairing,
    SameNameBivalentPairing,
)
from evo_engine.genetics.recombination import (
    NoRecombination,
    RecombinationModel,
)
from evo_engine.genetics.segregation import (
    ChromosomeSegregation,
    MendelianSegregation,
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
    """Form a gamete through pairing, recombination, and segregation.

    Pairing first organizes parent chromosome copies into explicit transient
    associations. Recombination may exchange material only within each selected
    association and must preserve its chromosome-copy cardinality. Segregation
    then decides which and how many recombination products enter the gamete.

    Attributes:
        pairing: Policy organizing parent chromosome copies into associations.
        recombination: Model governing exchange within each association.
        segregation: Policy selecting chromosome copies transmitted to the gamete.
    """

    pairing: ChromosomePairing = attrs.field(factory=SameNameBivalentPairing)
    recombination: RecombinationModel = attrs.field(factory=NoRecombination)
    segregation: ChromosomeSegregation = attrs.field(factory=MendelianSegregation)

    def __attrs_post_init__(self) -> None:
        """Validate gamete-formation configuration."""
        self._require_callable(self.pairing, "pairing", "pair")
        self._require_callable(self.recombination, "recombination", "recombine")
        self._require_callable(self.segregation, "segregation", "segregate")

    @staticmethod
    def _require_callable(value: object, field_name: str, method_name: str) -> None:
        """Require a structural policy method on configured state."""
        try:
            method = getattr(value, method_name)
        except AttributeError as error:
            raise TypeError(
                f"{field_name} must provide a callable {method_name} method."
            ) from error

        if not callable(method):
            raise TypeError(
                f"{field_name} must provide a callable {method_name} method."
            )

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
            Gamete containing chromosome copies selected by segregation.

        Raises:
            TypeError: If inputs or policy outputs have invalid types.
            ValueError: If genome structure or a configured policy is invalid.
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

        associations = self.pairing.pair(
            genome,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )
        self._validate_pairing_result(genome, associations)

        recombined_associations = tuple(
            self._recombine_association(
                association,
                genetic_architecture=genetic_architecture,
                rng=rng,
            )
            for association in associations
        )

        transmitted_chromosomes = self.segregation.segregate(
            recombined_associations,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )
        self._validate_segregation_result(
            recombined_associations,
            transmitted_chromosomes,
        )

        return Gamete(chromosomes=transmitted_chromosomes)

    @staticmethod
    def _validate_pairing_result(
        genome: Genome,
        associations: object,
    ) -> None:
        """Require pairing to organize each parent chromosome exactly once."""
        if type(associations) is not tuple:
            raise TypeError("pairing must return a tuple of ChromosomeAssociation.")

        associated_chromosomes = []
        for index, association in enumerate(associations):
            if not isinstance(association, ChromosomeAssociation):
                raise TypeError(
                    f"pairing result[{index}] must be an instance of "
                    f"ChromosomeAssociation; received {association!r}."
                )
            associated_chromosomes.extend(association.chromosomes)

        parent_identity_counts = Counter(id(chromosome) for chromosome in genome.chromosomes)
        associated_identity_counts = Counter(
            id(chromosome) for chromosome in associated_chromosomes
        )
        if associated_identity_counts != parent_identity_counts:
            raise ValueError(
                "pairing must organize each parent chromosome copy exactly once "
                "without replacing chromosome objects."
            )

    def _recombine_association(
        self,
        association: ChromosomeAssociation,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> ChromosomeAssociation:
        """Recombine one association while enforcing copy-cardinality stability."""
        recombined = self.recombination.recombine(
            association,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )
        if not isinstance(recombined, ChromosomeAssociation):
            raise TypeError(
                "recombination must return an instance of ChromosomeAssociation."
            )
        if len(recombined.chromosomes) != len(association.chromosomes):
            raise ValueError(
                "recombination must preserve chromosome-association copy "
                "cardinality."
            )
        return recombined

    @staticmethod
    def _validate_segregation_result(
        associations: tuple[ChromosomeAssociation, ...],
        transmitted_chromosomes: object,
    ) -> None:
        """Require segregation to select only available recombination products."""
        if type(transmitted_chromosomes) is not tuple:
            raise TypeError("segregation must return a tuple of Chromosome.")

        available = Counter(
            id(chromosome)
            for association in associations
            for chromosome in association.chromosomes
        )
        transmitted: Counter[int] = Counter()

        for index, chromosome in enumerate(transmitted_chromosomes):
            if not isinstance(chromosome, Chromosome):
                raise TypeError(
                    f"segregation result[{index}] must be an instance of "
                    f"Chromosome; received {chromosome!r}."
                )
            transmitted[id(chromosome)] += 1

        if transmitted - available:
            raise ValueError(
                "segregation may transmit only chromosome copies supplied by "
                "recombination."
            )
