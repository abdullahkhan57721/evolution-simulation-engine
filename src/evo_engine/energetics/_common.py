"""Shared helpers for energetic cost models."""

from __future__ import annotations

import math

from evo_engine.validation import validators


def validate_finite_number(
    value: object,
    *,
    name: str,
) -> int | float:
    """Validate and return a finite numerical value.

    Args:
        value: Value to validate.
        name: Human-readable value name used in error messages.

    Returns:
        Validated integer or float.

    Raises:
        TypeError: If value is not an integer or float.
        ValueError: If value is not finite.
    """
    number = validators.validate_number(
        value,
        name=name,
    )

    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite; received {number!r}.")

    return number


def round_nonnegative_cost(
    value: int | float,
    *,
    minimum_cost: int,
) -> int:
    """Round a nonnegative model result to an integer energy cost.

    Nonnegative half-integers are rounded upward rather than using Python's
    bankers rounding. The configured minimum is applied after rounding.

    Args:
        value: Raw nonnegative cost produced by a model.
        minimum_cost: Inclusive minimum integer cost.

    Returns:
        Rounded integer energy cost.

    Raises:
        ValueError: If value is negative or non-finite.
    """
    finite_value = validate_finite_number(
        value,
        name="cost",
    )

    if finite_value < 0:
        raise ValueError(f"cost must be nonnegative; received {finite_value!r}.")

    rounded_cost = math.floor(finite_value + 0.5)

    return max(
        minimum_cost,
        rounded_cost,
    )
