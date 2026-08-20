"""Gamete representation for the genetics domain."""

from __future__ import annotations

import attrs

from evo_engine.genetics.chromosome import Chromosome
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class Gamete:
    """Represent transmitted chromosome material from one parent.

    A gamete stores chromosome copies separately so haplotype phase is
    preserved through segregation and future recombination models.

    Attributes:
        chromosomes: Ordered chromosome copies carried by the gamete. May
            be empty when the genetic architecture contains no loci.
    """

    chromosomes: tuple[Chromosome, ...]

    def __attrs_post_init__(self) -> None:
        """Validate gamete chromosome state."""
        validators.validate_tuple(self.chromosomes, name="chromosomes")

        for index, chromosome in enumerate(self.chromosomes):
            if not isinstance(chromosome, Chromosome):
                raise TypeError(
                    f"chromosomes[{index}] must be an instance of "
                    f"Chromosome; received {chromosome!r}."
                )

    def chromosomes_named(self, name: str) -> tuple[Chromosome, ...]:
        """Return chromosome copies with a given homologous name.

        Args:
            name: Chromosome name to retrieve.

        Returns:
            Matching chromosome copies in gamete order.

        Raises:
            TypeError: If name is not a string.
            ValueError: If name is empty or whitespace.
            KeyError: If the gamete contains no chromosome with the name.
        """
        validators.validate_str(name, name="name")

        if not name.strip():
            raise ValueError("name must not be empty or whitespace.")

        chromosomes = tuple(
            chromosome for chromosome in self.chromosomes if chromosome.name == name
        )

        if not chromosomes:
            raise KeyError(f"gamete has no chromosome named {name!r}.")

        return chromosomes
