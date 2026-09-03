"""Temporary chromosome associations formed during gamete production."""

from __future__ import annotations

import attrs

from evo_engine.genetics.chromosome import Chromosome
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class ChromosomeAssociation:
    """Represent chromosome copies selected to interact during gamete formation.

    An association is temporary meiotic organization, not persistent chromosome
    identity. Pairing policies decide which chromosome copies belong together;
    recombination policies operate only within the association they receive.

    Attributes:
        chromosomes: Nonempty chromosome copies in the association.
    """

    chromosomes: tuple[Chromosome, ...]

    def __attrs_post_init__(self) -> None:
        """Validate the association contents."""
        validators.validate_tuple(self.chromosomes, name="chromosomes")
        if not self.chromosomes:
            raise ValueError("chromosome association must not be empty.")

        for index, chromosome in enumerate(self.chromosomes):
            if not isinstance(chromosome, Chromosome):
                raise TypeError(
                    f"chromosomes[{index}] must be a Chromosome; "
                    f"received {chromosome!r}."
                )
