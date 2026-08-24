"""Canonical behavioral-purpose names and validation helpers.

Behavioral purposes are plain strings rather than an enum so simulations may
introduce custom purposes without modifying the engine. The constants in this
module provide a shared vocabulary for common built-in behavior.
"""

from __future__ import annotations

from evo_engine.validation import validators

ENERGY_ACQUISITION = "energy_acquisition"
SURVIVAL = "survival"
SOMATIC_INVESTMENT = "somatic_investment"
REPRODUCTION = "reproduction"
EXPLORATION = "exploration"

BUILTIN_BEHAVIORAL_PURPOSES = frozenset(
    {
        ENERGY_ACQUISITION,
        SURVIVAL,
        SOMATIC_INVESTMENT,
        REPRODUCTION,
        EXPLORATION,
    }
)


def validate_behavioral_purpose(
    value: object,
    *,
    name: str = "behavioral_purpose",
) -> str:
    """Validate and return a behavioral-purpose name.

    Args:
        value: Behavioral-purpose value to validate.
        name: Human-readable value name used in validation messages.

    Returns:
        Validated nonblank behavioral-purpose string.

    Raises:
        TypeError: If value is not a string.
        ValueError: If value is empty or contains only whitespace.
    """
    purpose = validators.validate_str(
        value,
        name=name,
    )

    if not purpose.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")

    return purpose
