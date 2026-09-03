"""Gamete-formation policies for sexual inheritance."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.genetics.chromosome_association import ChromosomeAssociation
from evo_engine.genetics.gamete import Gamete
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.genome import Genome
from evo_engine.genetics.pairing import (
    ChromosomePairingModel,
    SameNameBivalentPairing,
)
from evo_engine.genetics.recombination import (
    NoRecombination,
    RecombinationModel,
)
from evo_engine.genetics.segregation import (
    BivalentSegregation,
    ChromosomeSegregationModel,
)
from evo_engine.validation import validators


class GameteFormation(Protocol):
    """Define how one parent genome produces a gamete."""

    def form_gamete(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> Gamete:
        """Form a gamete from a parent genome."""
        ...


@attrs.frozen(slots=True, kw_only=True)
class MeioticGameteFormation:
    """Compose chromosome pairing, recombination, and segregation.

    Pairing determines temporary chromosome associations. Recombination may
    exchange material only within each selected association and must preserve its
    copy cardinality. Segregation then determines which and how many resulting
    chromosome copies enter the gamete.

    The default composition preserves current simple Mendelian behavior for
    singleton and diploid same-name chromosome groups without making that behavior
    universal architecture.
    """

    pairing: ChromosomePairingModel = attrs.field(factory=SameNameBivalentPairing)
    recombination: RecombinationModel = attrs.field(factory=NoRecombination)
    segregation: ChromosomeSegregationModel = attrs.field(factory=BivalentSegregation)

    def __attrs_post_init__(self) -> None:
        """Validate gamete-formation policy configuration."""
        self._require_callable(self.pairing, "pair", component_name="pairing")
        self._require_callable(
            self.recombination,
            "recombine",
            component_name="recombination",
        )
        self._require_callable(
            self.segregation,
            "segregate",
            component_name="segregation",
        )

    @staticmethod
    def _require_callable(component: object, method_name: str, *, component_name: str) -> None:
        """Require a configured policy to expose its public operation."""
        try:
            method = getattr(component, method_name)
        except AttributeError as error:
            raise TypeError(
                f"{component_name} must provide a callable {method_name} method."
            ) from error
        if not callable(method):
            raise TypeError(
                f"{component_name} must provide a callable {method_name} method."
            )

    def form_gamete(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> Gamete:
        """Form a gamete from one structurally valid parent genome.

        Args:
            genome: Parent genome.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Gamete containing the chromosome copies selected by segregation.

        Raises:
            TypeError: If inputs or policy outputs have invalid types.
            ValueError: If the genome or configured transmission policy is
                incompatible with the requested gamete formation.
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
        validators.validate_tuple(associations, name="pairing result")

        recombined: list[ChromosomeAssociation] = []
        for index, association in enumerate(associations):
            if not isinstance(association, ChromosomeAssociation):
                raise TypeError(
                    f"pairing result[{index}] must be a ChromosomeAssociation; "
                    f"received {association!r}."
                )

            recombined_association = self.recombination.recombine(
                association,
                genetic_architecture=genetic_architecture,
                rng=rng,
            )
            if not isinstance(recombined_association, ChromosomeAssociation):
                raise TypeError(
                    "recombination must return a ChromosomeAssociation; "
                    f"received {recombined_association!r}."
                )
            if len(recombined_association.chromosomes) != len(association.chromosomes):
                raise ValueError(
                    "recombination must preserve chromosome-association copy "
                    "cardinality."
                )
            recombined.append(recombined_association)

        chromosomes = self.segregation.segregate(
            tuple(recombined),
            genetic_architecture=genetic_architecture,
            rng=rng,
        )
        validators.validate_tuple(chromosomes, name="segregation result")
        return Gamete(chromosomes=chromosomes)
