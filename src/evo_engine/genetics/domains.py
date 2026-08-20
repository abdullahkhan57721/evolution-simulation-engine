"""Allele value domains for genetic loci."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

import attrs

from evo_engine.validation import validators

ValueT = TypeVar("ValueT")


class AlleleDomain(Protocol[ValueT]):
    """Define the legal values for alleles at a locus."""

    def validate(self, value: object) -> None:
        """Validate an allele value.

        Args:
            value: Candidate allele value.

        Raises:
            TypeError: If the value has an invalid type.
            ValueError: If the value lies outside the domain.
        """
        ...

    def constrain(self, value: ValueT) -> ValueT:
        """Return the domain-constrained form of an allele value.

        Args:
            value: Candidate allele value.

        Returns:
            Legal allele value.

        Raises:
            TypeError: If the value has an invalid type.
            ValueError: If the domain cannot constrain the value.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class IntegerAlleleDomain:
    """Define an optionally bounded integer allele domain.

    Out-of-range integer candidates are clamped to the nearest configured
    boundary by :meth:`constrain`.

    Attributes:
        minimum: Optional inclusive minimum allele value.
        maximum: Optional inclusive maximum allele value.
    """

    minimum: int | None = None
    maximum: int | None = None

    def __attrs_post_init__(self) -> None:
        """Validate domain bounds."""
        if self.minimum is not None:
            validators.validate_int(self.minimum, name="minimum")

        if self.maximum is not None:
            validators.validate_int(self.maximum, name="maximum")

        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError(
                "minimum must be less than or equal to maximum; "
                f"received minimum={self.minimum} and maximum={self.maximum}."
            )

    def validate(self, value: object) -> None:
        """Validate an integer allele value.

        Args:
            value: Candidate allele value.

        Raises:
            TypeError: If value is not an integer.
            ValueError: If value lies outside the configured bounds.
        """
        validated_value = validators.validate_int(value, name="allele value")

        if self.minimum is not None and validated_value < self.minimum:
            raise ValueError(
                f"allele value must be at least {self.minimum}; "
                f"received {validated_value}."
            )

        if self.maximum is not None and validated_value > self.maximum:
            raise ValueError(
                f"allele value must be at most {self.maximum}; "
                f"received {validated_value}."
            )

    def constrain(self, value: int) -> int:
        """Clamp an integer allele value to the configured bounds.

        Args:
            value: Candidate integer allele value.

        Returns:
            Constrained allele value.

        Raises:
            TypeError: If value is not an integer.
        """
        constrained_value = validators.validate_int(value, name="allele value")

        if self.minimum is not None:
            constrained_value = max(constrained_value, self.minimum)

        if self.maximum is not None:
            constrained_value = min(constrained_value, self.maximum)

        return constrained_value


@attrs.frozen(slots=True, kw_only=True)
class ChoiceAlleleDomain(Generic[ValueT]):
    """Define a finite set of legal allele values.

    Unlike an integer range, an invalid categorical value has no natural
    boundary to clamp to, so :meth:`constrain` validates and returns the value
    unchanged.

    Attributes:
        values: Legal allele values for the locus.
    """

    values: tuple[ValueT, ...]

    def __attrs_post_init__(self) -> None:
        """Validate the configured choices."""
        if not self.values:
            raise ValueError("values must contain at least one allele value.")

        for index, value in enumerate(self.values):
            if value in self.values[:index]:
                raise ValueError(
                    f"values must not contain duplicates; received {value!r}."
                )

    def validate(self, value: object) -> None:
        """Validate that a value belongs to the configured choices.

        Args:
            value: Candidate allele value.

        Raises:
            ValueError: If value is not one of the configured choices.
        """
        if value not in self.values:
            raise ValueError(
                f"allele value must be one of {self.values!r}; received {value!r}."
            )

    def constrain(self, value: ValueT) -> ValueT:
        """Validate and return a categorical allele value unchanged.

        Args:
            value: Candidate allele value.

        Returns:
            The validated allele value.

        Raises:
            ValueError: If value is not one of the configured choices.
        """
        self.validate(value)
        return value
