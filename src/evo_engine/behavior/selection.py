"""Models that determine whether organisms attempt behavioral purposes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.behavior.purposes import (
    ENERGY_ACQUISITION,
    SURVIVAL,
    validate_behavioral_purpose,
)
from evo_engine.energetics.thresholds import (
    EnergyThresholdSource,
    determine_energy_threshold,
    validate_energy_threshold_source,
)
from evo_engine.genetics.requirements import collect_required_traits

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class BehaviorSelectionModel(Protocol):
    """Decide whether an organism attempts a behavioral purpose.

    Implementations are shared simulation configuration. They should make
    decisions from their arguments rather than mutate hidden internal state.
    """

    def allows_behavior(
        self,
        organism: Organism,
        *,
        behavioral_purpose: str,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether an organism attempts a behavioral purpose.

        Args:
            organism: Organism considering the behavior.
            behavioral_purpose: Extensible purpose name for the behavior.
            simulation_state: Current simulation state.

        Returns:
            Whether the behavior should be attempted.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class UnrestrictedBehavior:
    """Allow every behavioral purpose for every organism."""

    def allows_behavior(
        self,
        organism: Organism,
        *,
        behavioral_purpose: str,
        simulation_state: SimulationState,
    ) -> bool:
        """Allow the requested behavior.

        Args:
            organism: Organism considering the behavior.
            behavioral_purpose: Purpose of the behavior.
            simulation_state: Current simulation state.

        Returns:
            Always ``True``.
        """
        return True


@attrs.frozen(slots=True, kw_only=True)
class EnergyConservationBehavior:
    """Suppress nonessential behavior below an energy threshold.

    ``energy_threshold`` may be a nonnegative integer or an organism-specific
    threshold model. At or above the resolved threshold, all behavioral
    purposes are allowed. Below it, only purposes in
    ``allowed_low_energy_purposes`` are allowed. By default, depleted organisms
    may still attempt energy acquisition and survival behavior.

    Attributes:
        energy_threshold: Fixed value or model determining the energy below
            which conservation behavior is active.
        allowed_low_energy_purposes: Purposes allowed while energy is low.
    """

    energy_threshold: EnergyThresholdSource
    allowed_low_energy_purposes: frozenset[str] = attrs.field(
        factory=lambda: frozenset(
            {
                ENERGY_ACQUISITION,
                SURVIVAL,
            }
        ),
        validator=attrs.validators.instance_of(frozenset),
    )

    def __attrs_post_init__(self) -> None:
        """Validate the threshold source and low-energy behavioral purposes."""
        validate_energy_threshold_source(
            self.energy_threshold,
            name="energy_threshold",
        )

        for purpose in self.allowed_low_energy_purposes:
            validate_behavioral_purpose(
                purpose,
                name="allowed_low_energy_purposes item",
            )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by the configured threshold model."""
        return collect_required_traits(self.energy_threshold)

    def allows_behavior(
        self,
        organism: Organism,
        *,
        behavioral_purpose: str,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the behavior is allowed at current energy.

        Args:
            organism: Organism considering the behavior.
            behavioral_purpose: Purpose of the behavior.
            simulation_state: Current simulation state.

        Returns:
            ``True`` when energy is not low or the purpose remains allowed in
            conservation mode; otherwise ``False``.
        """
        energy_threshold = determine_energy_threshold(
            self.energy_threshold,
            organism,
            simulation_state=simulation_state,
            name="energy_threshold",
        )

        if organism.energy >= energy_threshold:
            return True

        return behavioral_purpose in self.allowed_low_energy_purposes


def behavior_is_allowed(
    organism: Organism,
    *,
    behavioral_purpose: str,
    simulation_state: SimulationState,
) -> bool:
    """Return a validated behavior-selection decision for an organism.

    Args:
        organism: Organism considering the behavior.
        behavioral_purpose: Purpose of the behavior.
        simulation_state: Current simulation state and behavior-selection
            configuration.

    Returns:
        Validated behavior-selection decision.

    Raises:
        TypeError: If the configured model does not return a Boolean or if the
            purpose is not a string.
        ValueError: If the purpose is blank.
    """
    validated_purpose = validate_behavioral_purpose(behavioral_purpose)
    decision = simulation_state.behavior_selection_model.allows_behavior(
        organism,
        behavioral_purpose=validated_purpose,
        simulation_state=simulation_state,
    )

    if type(decision) is not bool:
        raise TypeError(
            "behavior_selection_model.allows_behavior must return a Boolean."
        )

    return decision
