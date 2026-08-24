"""Reusable fixed and developmental maximum-age models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeAlias, cast, runtime_checkable

import attrs

from evo_engine.genetics import MAXIMUM_AGE
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class MaximumAgeModel(Protocol):
    """Determine an organism-specific positive maximum age."""

    def determine_maximum_age(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return an organism-specific maximum age.

        Args:
            organism: Organism whose maximum age is being determined.
            simulation_state: Current simulation state.

        Returns:
            Positive integer maximum age.
        """
        ...


MaximumAgeSource: TypeAlias = int | MaximumAgeModel


@attrs.frozen(slots=True, kw_only=True)
class FixedMaximumAge:
    """Return one fixed maximum age for every organism.

    Attributes:
        maximum_age: Positive fixed maximum age.
    """

    maximum_age: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )

    def determine_maximum_age(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the configured maximum age.

        Args:
            organism: Organism whose maximum age is being determined.
            simulation_state: Current simulation state.

        Returns:
            Configured maximum age.
        """
        return self.maximum_age


@attrs.frozen(slots=True, kw_only=True)
class DevelopmentalMaximumAge:
    """Read maximum age from an organism's developmental profile.

    Attributes:
        trait_name: Developmental-profile trait storing maximum age.
    """

    trait_name: str = attrs.field(
        default=MAXIMUM_AGE,
        validator=attrs_validators.validate_str,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the configured trait name."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the developmental trait required by this lifespan model."""
        return frozenset({self.trait_name})

    def determine_maximum_age(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's positive developmental maximum age.

        Args:
            organism: Organism whose maximum age is being determined.
            simulation_state: Current simulation state.

        Returns:
            Positive developmental maximum age.

        Raises:
            KeyError: If the configured trait is absent.
            TypeError: If the developmental target is not an integer.
            ValueError: If the developmental target is less than one.
        """
        return validators.validate_int_ge(
            organism.developmental_profile.int_value(self.trait_name),
            bound=1,
            name=f"developmental_profile[{self.trait_name!r}]",
        )


def validate_maximum_age_source(
    value: object,
    *,
    name: str = "maximum_age",
) -> None:
    """Validate a fixed maximum age or maximum-age model.

    Args:
        value: Maximum-age source to validate.
        name: Human-readable value name used in validation messages.

    Raises:
        TypeError: If value is neither a positive integer nor a maximum-age
            model.
        ValueError: If a fixed integer maximum age is less than one.
    """
    if type(value) is int:
        validators.validate_int_ge(
            value,
            bound=1,
            name=name,
        )
        return

    if not callable(getattr(value, "determine_maximum_age", None)):
        raise TypeError(
            f"{name} must be a positive integer or provide a callable "
            "determine_maximum_age method."
        )


def determine_maximum_age(
    maximum_age_source: MaximumAgeSource,
    organism: Organism,
    *,
    simulation_state: SimulationState,
    name: str = "maximum_age",
) -> int:
    """Return a validated maximum age from a fixed value or model.

    Args:
        maximum_age_source: Fixed maximum age or model used to determine one.
        organism: Organism whose maximum age is being determined.
        simulation_state: Current simulation state.
        name: Human-readable value name used in validation messages.

    Returns:
        Validated positive integer maximum age.

    Raises:
        TypeError: If the source or returned maximum age has an invalid type.
        ValueError: If a maximum age is less than one.
    """
    validate_maximum_age_source(
        maximum_age_source,
        name=name,
    )

    if type(maximum_age_source) is int:
        return maximum_age_source

    maximum_age_model = cast(MaximumAgeModel, maximum_age_source)
    maximum_age = maximum_age_model.determine_maximum_age(
        organism,
        simulation_state=simulation_state,
    )
    return validators.validate_int_ge(
        maximum_age,
        bound=1,
        name=f"{name} model return value",
    )
