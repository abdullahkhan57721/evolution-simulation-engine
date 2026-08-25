"""Domain-neutral characteristic access and dependency declarations.

Evolutionary systems often distinguish between inherited information and the
operative characteristics that downstream processes act on. A characteristic
source provides that boundary without prescribing whether a value comes from
raw inherited state, developmental realization, current state, environmental
context, or another domain-specific representation.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

EntityT = TypeVar("EntityT", contravariant=True)
ContextT = TypeVar("ContextT", contravariant=True)
CharacteristicValueT = TypeVar("CharacteristicValueT", covariant=True)


class CharacteristicSource(Protocol[EntityT, ContextT, CharacteristicValueT]):
    """Return a named operative characteristic for an evolving entity."""

    def value_for(
        self,
        entity: EntityT,
        characteristic_name: str,
        *,
        context: ContextT,
    ) -> CharacteristicValueT:
        """Return one named characteristic.

        Args:
            entity: Evolving entity whose characteristic is requested.
            characteristic_name: Domain-defined characteristic identifier.
            context: Current domain-specific evaluation context.

        Returns:
            Characteristic value supplied by this source.
        """
        ...


@runtime_checkable
class CharacteristicRequirementProvider(Protocol):
    """Declare named operative characteristics required by a component."""

    @property
    def required_characteristics(self) -> frozenset[str]:
        """Return characteristic names required by the component."""
        ...


def validate_required_characteristics(
    required_characteristics: object,
    *,
    name: str = "required_characteristics",
) -> frozenset[str]:
    """Return a validated frozen set of nonblank characteristic names.

    Args:
        required_characteristics: Candidate frozen set of characteristic names.
        name: Human-readable name used in validation errors.

    Returns:
        Validated characteristic names.

    Raises:
        TypeError: If the collection or any item has an invalid type.
        ValueError: If any characteristic name is blank.
    """
    if type(required_characteristics) is not frozenset:
        raise TypeError(
            f"{name} must be a frozenset; received {required_characteristics!r}."
        )

    for characteristic_name in required_characteristics:
        if type(characteristic_name) is not str:
            raise TypeError(
                f"{name} items must be strings; received {characteristic_name!r}."
            )
        if not characteristic_name.strip():
            raise ValueError(f"{name} must not contain blank names.")

    return required_characteristics


def collect_required_characteristics(*components: object) -> frozenset[str]:
    """Return the union of characteristic requirements declared by components.

    Args:
        components: Configured components that may declare requirements.

    Returns:
        Union of all declared characteristic names.
    """
    required: set[str] = set()

    for component in components:
        if not isinstance(component, CharacteristicRequirementProvider):
            continue
        required.update(
            validate_required_characteristics(
                component.required_characteristics,
                name=f"{type(component).__name__}.required_characteristics",
            )
        )

    return frozenset(required)
