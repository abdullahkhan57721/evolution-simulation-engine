"""Models that determine the behavioral purpose of movement attempts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.behavior.purposes import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    validate_behavioral_purpose,
)
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.life_history import (
    EnergyThresholdSource,
    determine_energy_threshold,
    validate_energy_threshold_source,
)

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


@runtime_checkable
class MovementIntentCondition(Protocol):
    """Determine whether one prioritized movement-intent rule applies."""

    def matches(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the condition currently matches the organism.

        Args:
            organism: Organism considering movement.
            simulation_state: Current simulation state.

        Returns:
            Whether the associated movement-intent rule should apply.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class MovementIntentRule:
    """Associate one movement purpose with a condition.

    Attributes:
        behavioral_purpose: Purpose selected when ``condition`` matches.
        condition: State-dependent condition controlling the rule.
    """

    behavioral_purpose: str
    condition: MovementIntentCondition

    def __attrs_post_init__(self) -> None:
        """Validate the rule purpose and condition."""
        validate_behavioral_purpose(
            self.behavioral_purpose,
            name="behavioral_purpose",
        )

        if not callable(getattr(self.condition, "matches", None)):
            raise TypeError("condition must provide a callable matches method.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by the configured condition."""
        return collect_required_traits(self.condition)


@attrs.frozen(slots=True, kw_only=True)
class PrioritizedMovementIntent:
    """Select the first movement purpose whose ordered condition matches.

    Rules are evaluated in tuple order with short-circuiting. If no rule
    matches, ``fallback_purpose`` is returned. This keeps movement motivation
    separate from behavior selection: after this model chooses a purpose, the
    Movement process still asks the simulation's BehaviorSelectionModel whether
    that purpose may be attempted.

    Attributes:
        rules: Ordered nonempty movement-intent rules.
        fallback_purpose: Purpose selected when no rule matches.
    """

    rules: tuple[MovementIntentRule, ...] = attrs.field(
        validator=attrs.validators.instance_of(tuple),
    )
    fallback_purpose: str = EXPLORATION

    def __attrs_post_init__(self) -> None:
        """Validate ordered rules and fallback purpose."""
        if not self.rules:
            raise ValueError("rules must contain at least one movement-intent rule.")

        for index, rule in enumerate(self.rules):
            if not isinstance(rule, MovementIntentRule):
                raise TypeError(f"rules[{index}] must be a MovementIntentRule.")

        validate_behavioral_purpose(
            self.fallback_purpose,
            name="fallback_purpose",
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the union of traits required by ordered rules."""
        return collect_required_traits(*self.rules)

    def determine_purpose(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> str:
        """Return the first matching rule purpose or the fallback purpose.

        Args:
            organism: Organism considering movement.
            simulation_state: Current simulation state.

        Returns:
            Purpose from the highest-priority matching rule, otherwise the
            configured fallback purpose.

        Raises:
            TypeError: If a condition returns a non-Boolean value.
        """
        for index, rule in enumerate(self.rules):
            decision = rule.condition.matches(
                organism,
                simulation_state=simulation_state,
            )

            if type(decision) is not bool:
                raise TypeError(
                    f"rules[{index}].condition.matches must return a Boolean."
                )

            if decision:
                return rule.behavioral_purpose

        return self.fallback_purpose


@attrs.frozen(slots=True, kw_only=True)
class EnergyBelowThresholdMovementCondition:
    """Match organisms whose current energy is below a threshold source.

    Attributes:
        energy_threshold: Fixed value or organism-specific threshold model.
    """

    energy_threshold: EnergyThresholdSource

    def __attrs_post_init__(self) -> None:
        """Validate the configured energy-threshold source."""
        validate_energy_threshold_source(
            self.energy_threshold,
            name="energy_threshold",
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by the configured threshold model."""
        return collect_required_traits(self.energy_threshold)

    def matches(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether current energy is strictly below the threshold.

        Args:
            organism: Organism considering movement.
            simulation_state: Current simulation state.

        Returns:
            Whether current energy is below the resolved threshold.
        """
        energy_threshold = determine_energy_threshold(
            self.energy_threshold,
            organism,
            simulation_state=simulation_state,
            name="energy_threshold",
        )
        return organism.energy < energy_threshold


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
    """Choose movement purpose from current energy and a threshold source.

    Energy strictly below the resolved ``energy_threshold`` selects
    ``low_energy_purpose``. Energy at or above it selects ``otherwise_purpose``.
    The threshold may be fixed or organism-specific. The default purposes make
    depleted organisms forage while sufficiently energized organisms explore.

    This model determines motivation only. It does not decide whether the
    behavior is permitted, what environmental targets can be perceived, or how
    movement is performed.

    Attributes:
        energy_threshold: Fixed value or model determining when low-energy
            movement intent is active.
        low_energy_purpose: Purpose selected below the threshold.
        otherwise_purpose: Purpose selected at or above the threshold.
    """

    energy_threshold: EnergyThresholdSource
    low_energy_purpose: str = ENERGY_ACQUISITION
    otherwise_purpose: str = EXPLORATION

    def __attrs_post_init__(self) -> None:
        """Validate the threshold source and configured movement purposes."""
        validate_energy_threshold_source(
            self.energy_threshold,
            name="energy_threshold",
        )
        validate_behavioral_purpose(
            self.low_energy_purpose,
            name="low_energy_purpose",
        )
        validate_behavioral_purpose(
            self.otherwise_purpose,
            name="otherwise_purpose",
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by the configured threshold model."""
        return collect_required_traits(self.energy_threshold)

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
        energy_threshold = determine_energy_threshold(
            self.energy_threshold,
            organism,
            simulation_state=simulation_state,
            name="energy_threshold",
        )

        if organism.energy < energy_threshold:
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
