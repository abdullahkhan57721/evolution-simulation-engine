"""Small renderer-neutral scientific encoding values shared by presentation media."""

from __future__ import annotations

import attrs

from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class ContinuousTraitEncoding:
    """Define one continuous scientific trait mapping shared across renderers.

    This value records scientific presentation meaning only. It deliberately
    contains no renderer objects, colors, camera instructions, easing, or scene
    choreography.

    Attributes:
        trait_name: Committed trait name used to look up authoritative values.
        label: Human-readable scientific label used in legends and annotations.
        lower_bound: Inclusive lower bound of the shared visual scale.
        upper_bound: Inclusive upper bound of the shared visual scale.
    """

    trait_name: str = attrs.field(validator=attrs_validators.validate_str)
    label: str = attrs.field(validator=attrs_validators.validate_str)
    lower_bound: int = attrs.field()
    upper_bound: int = attrs.field()

    def __attrs_post_init__(self) -> None:
        """Validate semantic labels and scale bounds."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")
        if not self.label.strip():
            raise ValueError("label must not be empty or whitespace-only.")
        lower = validators.validate_int(self.lower_bound, name="lower_bound")
        upper = validators.validate_int(self.upper_bound, name="upper_bound")
        if upper <= lower:
            raise ValueError("upper_bound must be greater than lower_bound.")

    def normalize(self, value: int) -> float:
        """Return the authoritative trait value normalized to the shared scale.

        Args:
            value: Committed integer trait value.

        Returns:
            Value in the inclusive interval ``[0.0, 1.0]``.

        Raises:
            ValueError: If ``value`` lies outside the configured scale.
        """
        validated = validators.validate_int(value, name="value")
        if validated < self.lower_bound or validated > self.upper_bound:
            raise ValueError(
                f"value {validated} must lie within "
                f"[{self.lower_bound}, {self.upper_bound}]."
            )
        return (validated - self.lower_bound) / (self.upper_bound - self.lower_bound)
