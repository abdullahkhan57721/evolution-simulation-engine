"""Genetic locus representation and allele mutation coordination."""

from __future__ import annotations

import random
from typing import Generic, TypeVar

import attrs

from evo_engine.genetics.allele import Allele
from evo_engine.genetics.domains import AlleleDomain
from evo_engine.genetics.mutation import MutationPolicy
from evo_engine.validation import validators

ValueT = TypeVar("ValueT")


@attrs.frozen(slots=True, kw_only=True)
class Locus(Generic[ValueT]):
    """Define a genetic locus and the rules governing its alleles.

    ``Locus`` is the biological specialization of a domain-neutral linkage
    component. ``chromosome_name`` and ``position`` remain the biological API;
    ``linkage_group`` and ``linkage_position`` expose the same structure to the
    general evolution layer.

    Attributes:
        name: Unique locus name within a genetic architecture.
        chromosome_name: Name of the chromosome containing the locus.
        position: Non-negative position of the locus on its chromosome.
        domain: Legal allele-value domain for the locus.
        mutation: Mutation policy applied to alleles at the locus.
    """

    name: str
    chromosome_name: str
    position: int
    domain: AlleleDomain[ValueT]
    mutation: MutationPolicy[ValueT]

    def __attrs_post_init__(self) -> None:
        """Validate locus identity and position."""
        validators.validate_str(self.name, name="name")
        validators.validate_str(self.chromosome_name, name="chromosome_name")
        validators.validate_int_ge(self.position, bound=0, name="position")

        if not self.name.strip():
            raise ValueError("name must not be empty or whitespace.")

        if not self.chromosome_name.strip():
            raise ValueError("chromosome_name must not be empty or whitespace.")

    @property
    def linkage_group(self) -> str:
        """Return the domain-neutral linkage group containing this locus."""
        return self.chromosome_name

    @property
    def linkage_position(self) -> int:
        """Return the domain-neutral coordinate of this locus."""
        return self.position

    def create_allele(self, value: ValueT) -> Allele[ValueT]:
        """Create a validated allele for this locus.

        Args:
            value: Allele value to create.

        Returns:
            Validated allele associated with this locus.

        Raises:
            TypeError: If the allele value has an invalid type.
            ValueError: If the allele value lies outside the locus domain.
        """
        self.domain.validate(value)

        return Allele(
            locus_name=self.name,
            value=value,
        )

    def validate_allele(self, allele: Allele[ValueT]) -> None:
        """Validate that an allele belongs to this locus and its domain.

        Args:
            allele: Allele to validate.

        Raises:
            TypeError: If the allele value has an invalid type.
            ValueError: If the allele belongs to another locus or its value is
                outside this locus's domain.
        """
        if allele.locus_name != self.name:
            raise ValueError(
                f"allele belongs to locus {allele.locus_name!r}, not {self.name!r}."
            )

        self.domain.validate(allele.value)

    def mutate(
        self,
        allele: Allele[ValueT],
        *,
        rng: random.Random,
    ) -> Allele[ValueT]:
        """Return a potentially mutated valid allele for this locus.

        The mutation policy proposes a candidate value. The allele domain then
        applies its boundary semantics and validates the final value.

        Args:
            allele: Existing allele at this locus.
            rng: Simulation random-number generator.

        Returns:
            Mutated or unchanged validated allele.

        Raises:
            TypeError: If an allele value or rng is invalid.
            ValueError: If the allele belongs to another locus or the resulting
                value cannot be made valid for this locus.
        """
        self.validate_allele(allele)

        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        candidate_value = self.mutation.mutate(
            allele.value,
            rng=rng,
        )
        constrained_value = self.domain.constrain(candidate_value)
        self.domain.validate(constrained_value)

        return Allele(
            locus_name=self.name,
            value=constrained_value,
        )
