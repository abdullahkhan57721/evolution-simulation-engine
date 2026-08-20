"""Mutation policies for genetic allele values."""

from __future__ import annotations

import math
import random
from typing import Generic, Protocol, TypeVar

import attrs

from evo_engine.validation import validators

ValueT = TypeVar("ValueT")

PROBABILITY_SCALE = 1_000_000


class MutationPolicy(Protocol[ValueT]):
    """Define how an allele value may mutate."""

    def mutate(
        self,
        value: ValueT,
        *,
        rng: random.Random,
    ) -> ValueT:
        """Return a potentially mutated allele value.

        Args:
            value: Current allele value.
            rng: Simulation random-number generator.

        Returns:
            Mutated or unchanged allele value.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class NoMutation(Generic[ValueT]):
    """Leave an allele value unchanged."""

    def mutate(
        self,
        value: ValueT,
        *,
        rng: random.Random,
    ) -> ValueT:
        """Return the allele value unchanged.

        Args:
            value: Current allele value.
            rng: Simulation random-number generator.

        Returns:
            Unchanged allele value.
        """
        return value


@attrs.frozen(slots=True, kw_only=True)
class UniformIntegerMutation:
    """Mutate an integer allele by a bounded uniform step.

    Attributes:
        probability_ppm: Mutation probability in parts per million.
        max_change: Maximum absolute nonzero change when mutation occurs.
    """

    probability_ppm: int
    max_change: int

    def __attrs_post_init__(self) -> None:
        """Validate mutation configuration."""
        validators.validate_int_in_range(
            self.probability_ppm,
            lower=0,
            upper=PROBABILITY_SCALE,
            name="probability_ppm",
        )
        validators.validate_int_ge(
            self.max_change,
            bound=0,
            name="max_change",
        )

    def mutate(
        self,
        value: int,
        *,
        rng: random.Random,
    ) -> int:
        """Return a potentially mutated integer allele value.

        Args:
            value: Current integer allele value.
            rng: Simulation random-number generator.

        Returns:
            Mutated or unchanged integer allele value.

        Raises:
            TypeError: If value is not an integer or rng is invalid.
        """
        validated_value = validators.validate_int(value, name="value")

        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        if self.max_change == 0:
            return validated_value

        mutation_roll = rng.randrange(PROBABILITY_SCALE)

        if mutation_roll >= self.probability_ppm:
            return validated_value

        magnitude = rng.randint(1, self.max_change)
        direction = -1 if rng.randrange(2) == 0 else 1

        return validated_value + direction * magnitude


@attrs.frozen(slots=True, kw_only=True)
class GaussianIntegerMutation:
    """Mutate an integer allele by a Gaussian-distributed step.

    Attributes:
        probability_ppm: Mutation probability in parts per million.
        standard_deviation: Standard deviation of the Gaussian mutation step.
    """

    probability_ppm: int
    standard_deviation: int | float

    def __attrs_post_init__(self) -> None:
        """Validate mutation configuration."""
        validators.validate_int_in_range(
            self.probability_ppm,
            lower=0,
            upper=PROBABILITY_SCALE,
            name="probability_ppm",
        )

        standard_deviation = validators.validate_number(
            self.standard_deviation,
            name="standard_deviation",
        )

        if not math.isfinite(standard_deviation):
            raise ValueError("standard_deviation must be finite.")

        if standard_deviation < 0:
            raise ValueError("standard_deviation must be non-negative.")

    def mutate(
        self,
        value: int,
        *,
        rng: random.Random,
    ) -> int:
        """Return a potentially Gaussian-mutated integer allele value.

        Args:
            value: Current integer allele value.
            rng: Simulation random-number generator.

        Returns:
            Mutated or unchanged integer allele value.

        Raises:
            TypeError: If value is not an integer or rng is invalid.
        """
        validated_value = validators.validate_int(value, name="value")

        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        if self.standard_deviation == 0:
            return validated_value

        mutation_roll = rng.randrange(PROBABILITY_SCALE)

        if mutation_roll >= self.probability_ppm:
            return validated_value

        change = round(
            rng.gauss(
                0.0,
                float(self.standard_deviation),
            )
        )

        return validated_value + change
