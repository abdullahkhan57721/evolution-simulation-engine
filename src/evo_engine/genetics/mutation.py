"""Mutation policies for genetic allele values."""

from __future__ import annotations

import math
import random
from typing import Generic, Protocol, TypeVar

import attrs

from evo_engine.evolution import VariationOperator
from evo_engine.validation import validators

ValueT = TypeVar("ValueT")

PROBABILITY_SCALE = 1_000_000


class MutationPolicy(VariationOperator[ValueT], Protocol[ValueT]):
    """Define biological mutation as a general evolutionary variation operator."""

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

    def vary(
        self,
        value: ValueT,
        *,
        rng: random.Random,
    ) -> ValueT:
        """Return the value unchanged through the general variation API."""
        return self.mutate(value, rng=rng)


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

    def vary(
        self,
        value: int,
        *,
        rng: random.Random,
    ) -> int:
        """Apply integer mutation through the general variation API."""
        return self.mutate(value, rng=rng)


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

    def vary(
        self,
        value: int,
        *,
        rng: random.Random,
    ) -> int:
        """Apply Gaussian mutation through the general variation API."""
        return self.mutate(value, rng=rng)


@attrs.frozen(slots=True, kw_only=True)
class UniformChoiceMutation(Generic[ValueT]):
    """Mutate among explicit categorical or discrete allele values.

    When mutation occurs, the result is sampled uniformly from configured
    choices other than the current value. This supports heritable categorical
    traits such as color, strategy labels, or symbolic states without requiring
    integer encoding.

    Attributes:
        probability_ppm: Mutation probability in parts per million.
        choices: Unique legal values available to the mutation policy.
    """

    probability_ppm: int
    choices: tuple[ValueT, ...]

    def __attrs_post_init__(self) -> None:
        """Validate categorical mutation configuration."""
        validators.validate_int_in_range(
            self.probability_ppm,
            lower=0,
            upper=PROBABILITY_SCALE,
            name="probability_ppm",
        )
        validators.validate_tuple(self.choices, name="choices")
        if not self.choices:
            raise ValueError("choices must contain at least one value.")
        for index, choice in enumerate(self.choices):
            if any(choice == previous for previous in self.choices[:index]):
                raise ValueError("choices must not contain duplicate values.")

    def mutate(
        self,
        value: ValueT,
        *,
        rng: random.Random,
    ) -> ValueT:
        """Return a potentially mutated categorical value.

        Args:
            value: Current value, which must occur in ``choices``.
            rng: Simulation random-number generator.

        Returns:
            Mutated or unchanged value.

        Raises:
            TypeError: If rng is invalid.
            ValueError: If value is not one of the configured choices.
        """
        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")
        if not any(value == choice for choice in self.choices):
            raise ValueError("value must be one of the configured choices.")
        if len(self.choices) == 1:
            return value

        mutation_roll = rng.randrange(PROBABILITY_SCALE)
        if mutation_roll >= self.probability_ppm:
            return value

        alternatives = tuple(choice for choice in self.choices if choice != value)
        return rng.choice(alternatives)

    def vary(
        self,
        value: ValueT,
        *,
        rng: random.Random,
    ) -> ValueT:
        """Apply categorical mutation through the general variation API."""
        return self.mutate(value, rng=rng)
