"""Spatial environmental field definitions for simulated worlds."""

from __future__ import annotations

import math

import attrs

from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentalField:
    """Define one named finite scalar environmental variable.

    The field definition is immutable configuration. Spatial values are owned by
    ``WorldState`` so they participate in transactional world copying and event
    mutation journaling. Cells without an explicit override use
    ``default_value``.

    Attributes:
        name: Unique nonblank field name within a world.
        default_value: Finite numerical value used at cells without an override.
    """

    name: str = attrs.field(validator=attrs_validators.validate_str)
    default_value: int | float

    def __attrs_post_init__(self) -> None:
        """Validate field naming and numerical defaults."""
        if not self.name.strip():
            raise ValueError("name must not be empty or whitespace-only.")
        self.validate_value(self.default_value, name="default_value")

    def validate_value(self, value: object, *, name: str = "value") -> int | float:
        """Return a validated finite numerical field value.

        Args:
            value: Candidate scalar value.
            name: Validation name used in error messages.

        Returns:
            Validated integer or float.

        Raises:
            TypeError: If value is not an integer or float, excluding Boolean.
            ValueError: If value is non-finite.
        """
        number = validators.validate_number(value, name=name)
        if not math.isfinite(number):
            raise ValueError(f"{name} must be finite; received {number!r}.")
        return number
