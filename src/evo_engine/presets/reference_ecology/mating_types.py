"""Mating-type defaults for the complete reference ecology."""

from __future__ import annotations

from evo_engine.reproduction import DifferentMatingTypes, RandomMatingType

REFERENCE_MATING_TYPES: tuple[str, ...] = ("type_a", "type_b")


def reference_founder_mating_type(index: int) -> str:
    """Return the deterministic balanced mating type for a founder index.

    Founder types cycle through the configured reference labels instead of
    consuming simulation RNG during world construction. With two types this
    produces equal counts for even populations and counts differing by at most
    one for odd populations.

    Args:
        index: Zero-based founder index.

    Returns:
        Reference mating-type label for the founder.
    """
    return REFERENCE_MATING_TYPES[index % len(REFERENCE_MATING_TYPES)]


def build_reference_mating_type_compatibility() -> DifferentMatingTypes:
    """Return the reference rule requiring unlike mating types."""
    return DifferentMatingTypes()


def build_reference_offspring_mating_type_model() -> RandomMatingType:
    """Return equal-probability offspring assignment across reference types."""
    return RandomMatingType(mating_types=REFERENCE_MATING_TYPES)
