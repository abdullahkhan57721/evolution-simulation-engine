"""Reusable models for fixed and developmental energy thresholds."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeAlias, runtime_checkable

import attrs

from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class EnergyThresholdModel(Protocol):
    """Determine an organism-specific nonnegative energy threshold."""

    def determine_threshold(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return an organism-specific energy threshold.

        Args:
            organism: Organism whose threshold is being determined.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative integer energy threshold.
        """
        ...


EnergyThresholdSource: TypeAlias = int | EnergyThresholdModel


@attrs.frozen(slots=True, kw_only=True)
class FixedEnergyThreshold:
    """Return one fixed energy threshold for every organism.

    Attributes:
        threshold: Nonnegative fixed energy threshold.
    """

    threshold: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def determine_threshold(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the configured fixed threshold.

        Args:
            organism: Organism whose threshold is being determined.
            simulation_state: Current simulation state.

        Returns:
            Configured threshold.
        """
        return self.threshold


@attrs.frozen(slots=True, kw_only=True)
class DevelopmentalEnergyThreshold:
    """Read an organism-specific energy threshold from developmental targets.

    Attributes:
        trait_name: Developmental-profile trait storing the threshold.
    """

    trait_name: str = attrs.field(
        validator=attrs_validators.validate_str,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the configured trait name."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the developmental trait required by this threshold model."""
        return frozenset({self.trait_name})

    def determine_threshold(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's nonnegative developmental threshold.

        Args:
            organism: Organism whose threshold is being determined.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative developmental threshold.

        Raises:
            KeyError: If the configured trait is absent.
            TypeError: If the developmental target is not an integer.
            ValueError: If the developmental target is negative.
        """
        return validators.validate_int_ge(
            organism.developmental_profile.int_value(self.trait_name),
            bound=0,
            name=f"developmental_profile[{self.trait_name!r}]",
        )


def validate_energy_threshold_source(
    value: object,
    *,
    name: str = "energy_threshold",
) -> None:
    """Validate a fixed threshold or threshold model.

    Args:
        value: Threshold source to validate.
        name: Human-readable value name used in validation messages.

    Raises:
        TypeError: If value is neither a nonnegative integer nor a threshold
            model.
        ValueError: If a fixed integer threshold is negative.
    """
    if type(value) is int:
        validators.validate_int_ge(
            value,
            bound=0,
            name=name,
        )
        return

    if not callable(getattr(value, "determine_threshold", None)):
        raise TypeError(
            f"{name} must be a nonnegative integer or provide a callable "
            "determine_threshold method."
        )


def determine_energy_threshold(
    threshold_source: EnergyThresholdSource,
    organism: Organism,
    *,
    simulation_state: SimulationState,
    name: str = "energy_threshold",
) -> int:
    """Return a validated energy threshold from a fixed value or model.

    Args:
        threshold_source: Fixed threshold or model used to determine one.
        organism: Organism whose threshold is being determined.
        simulation_state: Current simulation state.
        name: Human-readable threshold name used in validation messages.

    Returns:
        Validated nonnegative integer threshold.

    Raises:
        TypeError: If the source or returned threshold has an invalid type.
        ValueError: If a threshold is negative.
    """
    validate_energy_threshold_source(
        threshold_source,
        name=name,
    )

    if type(threshold_source) is int:
        return threshold_source

    threshold = threshold_source.determine_threshold(
        organism,
        simulation_state=simulation_state,
    )
    return validators.validate_int_ge(
        threshold,
        bound=0,
        name=f"{name} model return value",
    )
