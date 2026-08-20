"""Genotype-to-phenotype expression models."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, Protocol, TypeVar

import attrs

from evo_engine.genetics.allele import Allele
from evo_engine.validation import validators

TraitValueT_co = TypeVar("TraitValueT_co", covariant=True)
AlleleValueT = TypeVar("AlleleValueT")

AllelesByLocus = Mapping[str, tuple[Allele[Any], ...]]


class ExpressionModel(Protocol[TraitValueT_co]):
    """Define how genetic information is expressed as a trait value."""

    def express(
        self,
        *,
        alleles_by_locus: AllelesByLocus,
    ) -> TraitValueT_co:
        """Express a phenotypic trait value from locus alleles.

        Args:
            alleles_by_locus: Alleles grouped by contributing locus name.

        Returns:
            Expressed trait value.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class MeanIntegerExpression:
    """Express the rounded arithmetic mean of integer allele values."""

    def express(
        self,
        *,
        alleles_by_locus: AllelesByLocus,
    ) -> int:
        """Return the rounded mean of all contributing integer alleles.

        Half-integer means are rounded away from zero using integer
        arithmetic.

        Args:
            alleles_by_locus: Alleles grouped by contributing locus name.

        Returns:
            Rounded arithmetic mean of the allele values.

        Raises:
            TypeError: If an allele value is not an integer.
            ValueError: If no alleles are supplied.
        """
        values: list[int] = []

        for alleles in alleles_by_locus.values():
            for allele in alleles:
                values.append(
                    validators.validate_int(
                        allele.value,
                        name="allele value",
                    )
                )

        if not values:
            raise ValueError("alleles_by_locus must contain at least one allele.")

        total = sum(values)
        count = len(values)

        magnitude, remainder = divmod(abs(total), count)

        if remainder * 2 >= count:
            magnitude += 1

        return magnitude if total >= 0 else -magnitude


@attrs.frozen(slots=True, kw_only=True)
class AdditiveIntegerExpression:
    """Express the sum of all contributing integer allele values."""

    def express(
        self,
        *,
        alleles_by_locus: AllelesByLocus,
    ) -> int:
        """Return the sum of all contributing integer allele values.

        Args:
            alleles_by_locus: Alleles grouped by contributing locus name.

        Returns:
            Sum of the allele values.

        Raises:
            TypeError: If an allele value is not an integer.
            ValueError: If no alleles are supplied.
        """
        values: list[int] = []

        for alleles in alleles_by_locus.values():
            for allele in alleles:
                values.append(
                    validators.validate_int(
                        allele.value,
                        name="allele value",
                    )
                )

        if not values:
            raise ValueError("alleles_by_locus must contain at least one allele.")

        return sum(values)


@attrs.frozen(slots=True, kw_only=True)
class CompleteDominanceExpression(Generic[AlleleValueT]):
    """Express the most dominant allele value at a single locus.

    Earlier entries in ``dominance_order`` are more dominant.

    Attributes:
        dominance_order: Allele values ordered from most to least dominant.
    """

    dominance_order: tuple[AlleleValueT, ...]

    def __attrs_post_init__(self) -> None:
        """Validate the dominance ordering."""
        validators.validate_tuple(
            self.dominance_order,
            name="dominance_order",
        )

        if not self.dominance_order:
            raise ValueError("dominance_order must contain at least one allele value.")

        for index, value in enumerate(self.dominance_order):
            if value in self.dominance_order[:index]:
                raise ValueError(
                    "dominance_order must not contain duplicate values; "
                    f"received {value!r}."
                )

    def express(
        self,
        *,
        alleles_by_locus: AllelesByLocus,
    ) -> AlleleValueT:
        """Return the most dominant allele value present.

        Args:
            alleles_by_locus: Alleles for exactly one contributing locus.

        Returns:
            Most dominant allele value present in the genotype.

        Raises:
            ValueError: If zero or multiple loci are supplied, no alleles are
                present, or an allele value is absent from dominance_order.
        """
        if len(alleles_by_locus) != 1:
            raise ValueError("CompleteDominanceExpression requires exactly one locus.")

        alleles = next(iter(alleles_by_locus.values()))

        if not alleles:
            raise ValueError("the contributing locus must contain at least one allele.")

        allele_values = tuple(allele.value for allele in alleles)

        for allele_value in allele_values:
            if allele_value not in self.dominance_order:
                raise ValueError(
                    f"allele value {allele_value!r} is not present in dominance_order."
                )

        for dominant_value in self.dominance_order:
            if dominant_value in allele_values:
                return dominant_value

        raise RuntimeError("failed to resolve complete dominance.")
