"""Models that select spatial targets for motivated movement."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.behavior.purposes import (
    ENERGY_ACQUISITION,
    validate_behavioral_purpose,
)
from evo_engine.behavior.sensory_range import (
    GeneticPhenotypeSensoryRange,
    SensoryRangeModel,
    determine_sensory_range,
)
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@attrs.frozen(slots=True, kw_only=True)
class MovementTarget:
    """Represent a world coordinate selected as a movement target.

    Attributes:
        x: Horizontal target coordinate.
        y: Vertical target coordinate.
    """

    x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@runtime_checkable
class MovementTargetModel(Protocol):
    """Select a spatial target for an organism's movement attempt."""

    def choose_target(
        self,
        organism: Organism,
        *,
        behavioral_purpose: str,
        simulation_state: SimulationState,
    ) -> MovementTarget | None:
        """Return a movement target or ``None`` when no target is selected.

        Args:
            organism: Organism attempting movement.
            behavioral_purpose: Purpose motivating the movement attempt.
            simulation_state: Current simulation state.

        Returns:
            Selected movement target, or ``None`` for untargeted movement.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class NoMovementTarget:
    """Never select a spatial target."""

    def choose_target(
        self,
        organism: Organism,
        *,
        behavioral_purpose: str,
        simulation_state: SimulationState,
    ) -> None:
        """Return no movement target.

        Args:
            organism: Organism attempting movement.
            behavioral_purpose: Purpose motivating the movement attempt.
            simulation_state: Current simulation state.

        Returns:
            Always ``None``.
        """
        return None


@attrs.frozen(slots=True, kw_only=True)
class NearestResourceTarget:
    """Target the nearest detectable environmental resource deposit.

    Direct squared Euclidean distance is used for both sensory-range filtering
    and nearest-target ranking. If multiple deposits are equally near, the
    deposit with more resource units is preferred; remaining ties are broken
    deterministically by coordinate.

    The model is active only for ``behavioral_purpose``. By default this is the
    engine's canonical energy-acquisition purpose, so exploratory or survival
    movement can compose a different targeting policy.

    Attributes:
        sensory_range_model: Model determining how far an organism can detect
            resource deposits.
        behavioral_purpose: Movement purpose for which resource targeting is
            active.
    """

    sensory_range_model: SensoryRangeModel = attrs.field(
        factory=GeneticPhenotypeSensoryRange,
    )
    behavioral_purpose: str = ENERGY_ACQUISITION

    def __attrs_post_init__(self) -> None:
        """Validate resource-targeting configuration."""
        if not callable(
            getattr(
                self.sensory_range_model,
                "determine_range",
                None,
            )
        ):
            raise TypeError(
                "sensory_range_model must provide a callable determine_range method."
            )

        validate_behavioral_purpose(
            self.behavioral_purpose,
            name="behavioral_purpose",
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by the configured sensory-range model."""
        return collect_required_traits(self.sensory_range_model)

    def choose_target(
        self,
        organism: Organism,
        *,
        behavioral_purpose: str,
        simulation_state: SimulationState,
    ) -> MovementTarget | None:
        """Return the nearest detectable resource target.

        Args:
            organism: Organism attempting movement.
            behavioral_purpose: Purpose motivating the movement attempt.
            simulation_state: Current simulation state.

        Returns:
            Nearest detectable resource coordinate, or ``None`` when targeting
            is inactive or no resource lies within sensory range.
        """
        if behavioral_purpose != self.behavioral_purpose:
            return None

        sensory_range = determine_sensory_range(
            self.sensory_range_model,
            organism,
            simulation_state=simulation_state,
        )
        maximum_distance_squared = sensory_range * sensory_range

        best_key: tuple[int, int, int, int] | None = None
        best_target: MovementTarget | None = None

        for (x, y), amount in simulation_state.world.resources.items():
            dx = x - organism.x
            dy = y - organism.y
            distance_squared = dx * dx + dy * dy

            if distance_squared > maximum_distance_squared:
                continue

            candidate_key = (
                distance_squared,
                -amount,
                x,
                y,
            )

            if best_key is None or candidate_key < best_key:
                best_key = candidate_key
                best_target = MovementTarget(
                    x=x,
                    y=y,
                )

        return best_target


def determine_movement_target(
    movement_target_model: MovementTargetModel,
    organism: Organism,
    *,
    behavioral_purpose: str,
    simulation_state: SimulationState,
) -> MovementTarget | None:
    """Return a validated target from a movement-target model.

    Args:
        movement_target_model: Model selecting a spatial movement target.
        organism: Organism attempting movement.
        behavioral_purpose: Purpose motivating the movement attempt.
        simulation_state: Current simulation state.

    Returns:
        Validated in-bounds target or ``None``.

    Raises:
        TypeError: If the model returns a value other than ``MovementTarget``
            or ``None``.
        ValueError: If the model returns a target outside the world.
    """
    validated_purpose = validate_behavioral_purpose(behavioral_purpose)
    target = movement_target_model.choose_target(
        organism,
        behavioral_purpose=validated_purpose,
        simulation_state=simulation_state,
    )

    if target is None:
        return None

    if not isinstance(target, MovementTarget):
        raise TypeError(
            "movement_target_model.choose_target must return MovementTarget or None."
        )

    world = simulation_state.world
    validators.validate_int_in_range(
        target.x,
        lower=0,
        upper=world.width - 1,
        name="movement target x",
    )
    validators.validate_int_in_range(
        target.y,
        lower=0,
        upper=world.height - 1,
        name="movement target y",
    )

    return target
