"""Heritable trait definitions for the genetics domain."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Generic, TypeVar

import attrs

from evo_engine.genetics.allele import Allele
from evo_engine.genetics.expression import ExpressionModel
from evo_engine.genetics.genome import Genome
from evo_engine.validation import validators

TraitValueT = TypeVar("TraitValueT")


@attrs.frozen(slots=True, kw_only=True)
class Trait(Generic[TraitValueT]):
    """Define an expressed trait and its genetic contributors.

    Attributes:
        name: Unique trait name within a genetic architecture.
        locus_names: Loci contributing genetic information to the trait.
        expression: Model mapping those loci to an expressed trait value.
    """

    name: str
    locus_names: tuple[str, ...]
    expression: ExpressionModel[TraitValueT]

    def __attrs_post_init__(self) -> None:
        """Validate trait identity and locus references."""
        validators.validate_str(self.name, name="name")
        validators.validate_tuple(
            self.locus_names,
            name="locus_names",
        )

        if not self.name.strip():
            raise ValueError("name must not be empty or whitespace.")

        if not self.locus_names:
            raise ValueError("locus_names must contain at least one locus name.")

        seen_locus_names: set[str] = set()

        for index, locus_name in enumerate(self.locus_names):
            validators.validate_str(
                locus_name,
                name=f"locus_names[{index}]",
            )

            if not locus_name.strip():
                raise ValueError(
                    f"locus_names[{index}] must not be empty or whitespace."
                )

            if locus_name in seen_locus_names:
                raise ValueError(
                    f"locus_names must not contain duplicates; received {locus_name!r}."
                )

            seen_locus_names.add(locus_name)

        try:
            express = self.expression.express
        except AttributeError as error:
            raise TypeError(
                "expression must provide a callable express method."
            ) from error

        if not callable(express):
            raise TypeError("expression must provide a callable express method.")

    def express(self, genome: Genome) -> TraitValueT:
        """Express this trait from an organism genome.

        Args:
            genome: Genome containing the contributing loci.

        Returns:
            Expressed trait value.
        """
        if not isinstance(genome, Genome):
            raise TypeError("genome must be an instance of Genome.")

        alleles_by_locus: dict[
            str,
            tuple[Allele[Any], ...],
        ] = {
            locus_name: genome.alleles_at(locus_name) for locus_name in self.locus_names
        }

        return self.expression.express(
            alleles_by_locus=MappingProxyType(alleles_by_locus)
        )
