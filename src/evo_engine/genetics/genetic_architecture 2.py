"""Shared genetic architecture for genome validation and expression."""

from __future__ import annotations

from typing import Any

import attrs

from evo_engine.genetics.genetic_phenotype import GeneticPhenotype
from evo_engine.genetics.genome import Genome
from evo_engine.genetics.locus import Locus
from evo_engine.genetics.requirements import validate_required_traits
from evo_engine.genetics.trait import Trait


@attrs.frozen(slots=True, kw_only=True)
class GeneticArchitecture:
    """Define loci, traits, and genotype-to-genetic phenotype relationships.

    A genetic architecture is shared simulation configuration. Organisms carry
    genomes; the architecture validates those genomes and expresses them as
    genetic phenotypes.

    Attributes:
        loci: Genetic loci available in the architecture. May be empty.
        traits: Expressed traits defined from those loci.
    """

    loci: tuple[Locus[Any], ...]
    traits: tuple[Trait[Any], ...]

    def __attrs_post_init__(self) -> None:
        """Validate architecture identities and references."""
        if type(self.loci) is not tuple:
            raise TypeError("loci must be a tuple.")

        if type(self.traits) is not tuple:
            raise TypeError("traits must be a tuple.")

        locus_names = self._validate_loci()
        self._validate_traits(locus_names)

    def _validate_loci(self) -> set[str]:
        """Validate locus identity and chromosome-position uniqueness."""
        locus_names: set[str] = set()
        locus_positions: set[tuple[str, int]] = set()

        for index, locus in enumerate(self.loci):
            if not isinstance(locus, Locus):
                raise TypeError(
                    f"loci[{index}] must be an instance of Locus; received {locus!r}."
                )

            if locus.name in locus_names:
                raise ValueError(
                    f"loci must have unique names; duplicate {locus.name!r}."
                )

            position_key = (
                locus.chromosome_name,
                locus.position,
            )
            if position_key in locus_positions:
                raise ValueError(
                    "loci on the same chromosome must have unique "
                    f"positions; duplicate {position_key!r}."
                )

            locus_names.add(locus.name)
            locus_positions.add(position_key)

        return locus_names

    def _validate_traits(self, locus_names: set[str]) -> None:
        """Validate trait identity and locus references."""
        trait_names: set[str] = set()

        for index, trait in enumerate(self.traits):
            if not isinstance(trait, Trait):
                raise TypeError(
                    f"traits[{index}] must be an instance of Trait; received {trait!r}."
                )

            if trait.name in trait_names:
                raise ValueError(
                    f"traits must have unique names; duplicate {trait.name!r}."
                )

            unknown_loci = tuple(
                locus_name
                for locus_name in trait.locus_names
                if locus_name not in locus_names
            )
            if unknown_loci:
                raise ValueError(
                    f"trait {trait.name!r} references unknown loci {unknown_loci!r}."
                )

            trait_names.add(trait.name)

    @property
    def trait_names(self) -> frozenset[str]:
        """Return all genetic phenotype trait names defined by the architecture."""
        return frozenset(trait.name for trait in self.traits)

    def require_traits(
        self,
        required_traits: frozenset[str],
        *,
        context: str = "simulation configuration",
    ) -> None:
        """Require genetic phenotype traits before a simulation begins.

        Args:
            required_traits: GeneticPhenotype trait names required by configured
                engine components.
            context: Description used in configuration error messages.

        Raises:
            ValueError: If one or more required traits are undefined.
        """
        validated_requirements = validate_required_traits(required_traits)
        missing_traits = validated_requirements - self.trait_names

        if not missing_traits:
            return

        missing_list = ", ".join(repr(name) for name in sorted(missing_traits))
        raise ValueError(
            f"{context} requires undefined genetic phenotype trait(s): {missing_list}."
        )

    def locus(self, name: str) -> Locus[Any]:
        """Return a locus by name.

        Args:
            name: Locus name.

        Returns:
            Matching locus.

        Raises:
            KeyError: If no locus has the name.
        """
        for locus in self.loci:
            if locus.name == name:
                return locus

        raise KeyError(f"genetic architecture has no locus named {name!r}.")

    def trait(self, name: str) -> Trait[Any]:
        """Return a trait by name.

        Args:
            name: Trait name.

        Returns:
            Matching trait.

        Raises:
            KeyError: If no trait has the name.
        """
        for trait in self.traits:
            if trait.name == name:
                return trait

        raise KeyError(f"genetic architecture has no trait named {name!r}.")

    def validate_genome(self, genome: Genome) -> None:
        """Validate a genome against this architecture.

        Every allele must belong to a known locus, appear on the chromosome
        configured for that locus, and satisfy the locus's allele domain.
        Every locus required by an expressed trait must be represented at
        least once in the genome.

        Args:
            genome: Genome to validate.

        Raises:
            TypeError: If genome or one of its components has an invalid type.
            ValueError: If genetic structure conflicts with the architecture.
        """
        if not isinstance(genome, Genome):
            raise TypeError("genome must be an instance of Genome.")

        chromosome_names = {locus.chromosome_name for locus in self.loci}

        for chromosome in genome.chromosomes:
            self._validate_chromosome(
                chromosome,
                chromosome_names=chromosome_names,
            )

        for locus_name in self._required_locus_names():
            try:
                genome.alleles_at(locus_name)
            except KeyError as error:
                raise ValueError(
                    f"genome is missing locus {locus_name!r}, "
                    "which is required for genetic phenotype expression."
                ) from error

    def _validate_chromosome(
        self,
        chromosome: Any,
        *,
        chromosome_names: set[str],
    ) -> None:
        """Validate one chromosome and all alleles carried on it."""
        if chromosome.name not in chromosome_names:
            raise ValueError(f"genome contains unknown chromosome {chromosome.name!r}.")

        for allele in chromosome.alleles:
            try:
                locus = self.locus(allele.locus_name)
            except KeyError as error:
                raise ValueError(
                    f"genome contains allele for unknown locus {allele.locus_name!r}."
                ) from error

            if locus.chromosome_name != chromosome.name:
                raise ValueError(
                    f"locus {locus.name!r} belongs to chromosome "
                    f"{locus.chromosome_name!r}, not {chromosome.name!r}."
                )

            locus.validate_allele(allele)

    def _required_locus_names(self) -> set[str]:
        """Return loci needed to express all configured traits."""
        return {locus_name for trait in self.traits for locus_name in trait.locus_names}

    def express(self, genome: Genome) -> GeneticPhenotype:
        """Express a validated genome as a genetic phenotype.

        Args:
            genome: Genome to validate and express.

        Returns:
            GeneticPhenotype containing all configured trait values.
        """
        self.validate_genome(genome)

        # Preserve configured trait order so genetic phenotype serialization and
        # deterministic comparisons remain stable.
        return GeneticPhenotype(
            trait_values=tuple(
                (
                    trait.name,
                    trait.express(genome),
                )
                for trait in self.traits
            )
        )
