"""Chromosome representation for the genetics domain."""

from __future__ import annotations

import attrs

from evo_engine.genetics.allele import Allele
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class Chromosome:
    """Represent one chromosome copy and its phased alleles.

    Allele order is preserved so a genetic architecture can associate loci
    with ordered chromosome positions and future recombination logic can
    preserve haplotype phase.

    Attributes:
        name: Name identifying the homologous chromosome type.
        alleles: Alleles carried by this chromosome copy.
    """

    name: str
    alleles: tuple[Allele[object], ...] = ()

    def __attrs_post_init__(self) -> None:
        """Validate chromosome identity and allele membership."""
        validators.validate_str(self.name, name="name")

        if not self.name.strip():
            raise ValueError("name must not be empty or whitespace.")

        validators.validate_tuple(self.alleles, name="alleles")

        locus_names: set[str] = set()

        for index, allele in enumerate(self.alleles):
            if not isinstance(allele, Allele):
                raise TypeError(
                    f"alleles[{index}] must be an instance of Allele; "
                    f"received {allele!r}."
                )

            if allele.locus_name in locus_names:
                raise ValueError(
                    "a chromosome copy may contain at most one allele per "
                    f"locus; duplicate locus {allele.locus_name!r}."
                )

            locus_names.add(allele.locus_name)

    def allele_at(self, locus_name: str) -> Allele[object]:
        """Return the allele carried at a named locus.

        Args:
            locus_name: Name of the locus to retrieve.

        Returns:
            Allele carried at the locus.

        Raises:
            TypeError: If locus_name is not a string.
            ValueError: If locus_name is empty or whitespace.
            KeyError: If this chromosome copy has no allele at the locus.
        """
        validators.validate_str(locus_name, name="locus_name")

        if not locus_name.strip():
            raise ValueError("locus_name must not be empty or whitespace.")

        for allele in self.alleles:
            if allele.locus_name == locus_name:
                return allele

        raise KeyError(
            f"chromosome {self.name!r} has no allele at locus {locus_name!r}."
        )
