"""Phenotype-trait dependency declarations and aggregation helpers."""

from __future__ import annotations

from typing import Protocol, cast, runtime_checkable

from evo_engine.validation import validators


@runtime_checkable
class TraitRequirementProvider(Protocol):
    """Expose phenotype traits required by a configured component."""

    @property
    def required_traits(self) -> frozenset[str]:
        """Return phenotype trait names required by the component."""
        ...


def validate_required_traits(
    required_traits: object,
    *,
    name: str = "required_traits",
) -> frozenset[str]:
    """Return validated phenotype-trait requirements.

    Args:
        required_traits: Required trait-name collection.
        name: Name used in validation messages.

    Returns:
        Validated frozen set of nonblank trait names.

    Raises:
        TypeError: If required_traits is not a frozenset or contains a
            non-string value.
        ValueError: If a trait name is blank.
    """
    if type(required_traits) is not frozenset:
        raise TypeError(f"{name} must be a frozenset; received {required_traits!r}.")

    frozen_traits = cast(
        frozenset[object],
        required_traits,
    )

    for trait_name in frozen_traits:
        validated_trait_name = validators.validate_str(
            trait_name,
            name=f"{name} item",
        )

        if not validated_trait_name.strip():
            raise ValueError(f"{name} must not contain empty or whitespace-only names.")

    return cast(
        frozenset[str],
        frozen_traits,
    )


def collect_required_traits(*components: object) -> frozenset[str]:
    """Return the union of trait requirements declared by components.

    Components that do not implement TraitRequirementProvider contribute no
    requirements. This keeps trait dependency declaration optional for simple
    engine components while allowing composed policies to aggregate their
    dependencies upward.

    Args:
        components: Configured engine components or policies.

    Returns:
        Union of all declared phenotype trait names.
    """
    required_traits: set[str] = set()

    for component in components:
        if not isinstance(component, TraitRequirementProvider):
            continue

        component_requirements = validate_required_traits(
            component.required_traits,
            name=f"{type(component).__name__}.required_traits",
        )
        required_traits.update(component_requirements)

    return frozenset(required_traits)
