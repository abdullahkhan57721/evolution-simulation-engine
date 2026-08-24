"""Models that determine the behavioral purpose of movement attempts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.behavior.purposes import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    validate_behavioral_purpose,
)
from evo_engine.validation import attrs_validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class MovementIntentModel(Protocol):
    """Determine why an organism is attempting movement."""

    def determine_purpose(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> str:
        """Return the behavioral purpose of one movement attempt.

        Args:
            organism: Organism considering movement.
            simulation_state: Current simulation state.

        Returns:
            Extensible behavioral-purpose name for the movement attempt.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FixedMovementIntent:
    """Assign the same behavioral purpose to every movement attempt.

    Random undirected movement defaults to exploration. Simulations may use a
    different purpose, such as energy acquisition or survival, when a movement
    pattern represents a correspondingly motivated action.

    Attributes:
        behavioral_purpose: Purpose assigned to each movement attempt.
    """

    behavioral_purpose: str = EXPLORATION

    def __attrs_post_init__(self) -> None:
        """Validate the configured behavioral purpose."""
        validate_behavioral_purpose(
            self.behavioral_purpose,
            name="behavioral_purpose",
        )

    def determine_purpose(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> str:
        """Return the configured movement purpose.

        Args:
            organism: Organism considering movement.
            simulation_state: Current simulation state.

        Returns:
            Configured behavioral-purpose name.
        """
        return self.behavioral_purpose


@attrs.frozen(slots=True, kw_only=True)
class EnergyThresholdMovementIntent:
    """Choose movement purpose from the organism's current energy.

    Energy strictly below ``energy_threshold`` selects ``low_energy_purpose``.
    Energy at or above the threshold selects ``otherwise_purpose``. The default
    configuration therefore makes depleted organisms forage while sufficiently
    energized organisms explore.

    This model determines motivation only. It does not decide whether the
    behavior is permitted, what environmental targets can be perceived, or how
    movement is performed.

    Attributes:
        energy_threshold: Energy below which the low-energy purpose is selected.
        low_energy_purpose: Purpose selected below the threshold.
        otherwise_purpose: Purpose selected at or above the threshold.
    """

    energy_threshold: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    low_energy_purpose: str = ENERGY_ACQUISITION
    otherwise_purpose: str = EXPLORATION

    def __attrs_post_init__(self) -> None:
        """Validate configured movement purposes."""
        validate_behavioral_purpose(
            self.low_energy_purpose,
            name="low_energy_purpose",
        )
        validate_behavioral_purpose(
            self.otherwise_purpose,
            name="otherwise_purpose",
        )

    def determine_purpose(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> str:
        """Return the purpose selected from current organism energy.

        Args:
            organism: Organism considering movement.
            simulation_state: Current simulation state.

        Returns:
            Low-energy purpose below the threshold; otherwise the configured
            non-low-energy purpose.
        """
        if organism.energy < self.energy_threshold:
            return self.low_energy_purpose

        return self.otherwise_purpose


def determine_movement_purpose(
    movement_intent_model: MovementIntentModel,
    organism: Organism,
    *,
    simulation_state: SimulationState,
) -> str:
    """Return a validated purpose from a movement-intent model.

    Args:
        movement_intent_model: Model deciding why movement is being attempted.
        organism: Organism considering movement.
        simulation_state: Current simulation state.

    Returns:
        Validated behavioral-purpose name.

    Raises:
        TypeError: If the model returns a non-string purpose.
        ValueError: If the model returns a blank purpose.
    """
    purpose = movement_intent_model.determine_purpose(
        organism,
        simulation_state=simulation_state,
    )
    return validate_behavioral_purpose(
        purpose,
        name="movement_intent_model.determine_purpose return value",
    )
