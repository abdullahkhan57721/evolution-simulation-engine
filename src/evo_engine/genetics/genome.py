"""Genome representation for the genetics domain."""

from __future__ import annotations

import attrs

from evo_engine.genetics.allele import Allele
from evo_engine.genetics.chromosome import Chromosome
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class Genome:
    """Represent an organism's inherited chromosome state.

    Multiple chromosomes may share the same name, representing homologous
    chromosome copies. Keeping each copy separate preserves phase for future
    segregation and recombination models.

    Attributes:
        chromosomes: Ordered chromosome copies comprising the genome. May
            be empty for simulations with no modeled loci.
    """

    chromosomes: tuple[Chromosome, ...]

    def __attrs_post_init__(self) -> None:
        """Validate genome chromosome state."""
        validators.validate_tuple(self.chromosomes, name="chromosomes")

        for index, chromosome in enumerate(self.chromosomes):
            if not isinstance(chromosome, Chromosome):
                raise TypeError(
                    f"chromosomes[{index}] must be an instance of Chromosome; "
                    f"received {chromosome!r}."
                )

    def chromosomes_named(self, name: str) -> tuple[Chromosome, ...]:
        """Return all chromosome copies with a given name.

        Args:
            name: Homologous chromosome name to retrieve.

        Returns:
            Matching chromosome copies in genome order.

        Raises:
            TypeError: If name is not a string.
            ValueError: If name is empty or whitespace.
            KeyError: If the genome contains no chromosome with the name.
        """
        validators.validate_str(name, name="name")

        if not name.strip():
            raise ValueError("name must not be empty or whitespace.")

        chromosomes = tuple(
            chromosome for chromosome in self.chromosomes if chromosome.name == name
        )

        if not chromosomes:
            raise KeyError(f"genome has no chromosome named {name!r}.")

        return chromosomes

    def alleles_at(self, locus_name: str) -> tuple[Allele[object], ...]:
        """Return every allele carried at a named locus.

        The returned tuple follows genome chromosome order, preserving which
        allele copy belongs to which chromosome copy through the genome's
        chromosome representation.

        Args:
            locus_name: Name of the locus to retrieve.

        Returns:
            Alleles carried at the locus.

        Raises:
            TypeError: If locus_name is not a string.
            ValueError: If locus_name is empty or whitespace.
            KeyError: If the genome carries no allele at the locus.
        """
        validators.validate_str(locus_name, name="locus_name")

        if not locus_name.strip():
            raise ValueError("locus_name must not be empty or whitespace.")

        alleles = tuple(
            allele
            for chromosome in self.chromosomes
            for allele in chromosome.alleles
            if allele.locus_name == locus_name
        )

        if not alleles:
            raise KeyError(f"genome has no allele at locus {locus_name!r}.")

        return alleles
