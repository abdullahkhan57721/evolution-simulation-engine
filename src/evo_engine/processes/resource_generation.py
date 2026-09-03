"""Resource Generation simulation process."""

from __future__ import annotations

import attrs

from evo_engine.ecology import ResourcePlacementModel, UniformResourcePlacement
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class ResourceGeneration:
    """Represent the Resource Generation simulation process.

    Attributes:
        amount: Resource units generated per deposit.
        number_of_deposits: Number of deposits per simulation step.
        placement_model: Ecological policy choosing each deposit coordinate.
    """

    amount: int = attrs.field(
        validator=attrs_validators.validate_int_gt(0),
    )
    number_of_deposits: int = attrs.field(
        validator=attrs_validators.validate_int_gt(0),
    )
    placement_model: ResourcePlacementModel = attrs.field(
        factory=UniformResourcePlacement,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the configured placement model contract."""
        if not callable(getattr(self.placement_model, "choose_position", None)):
            raise TypeError(
                "placement_model must provide a callable choose_position method."
            )

    @property
    def event_type(self) -> type[ResourceGeneration.Event]:
        """Return the Resource Generation event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a proposed Resource Generation event.

        Attributes:
            step_index: Simulation step associated with the event.
            x: Horizontal coordinate where resources are generated.
            y: Vertical coordinate where resources are generated.
            amount: Resource units to generate.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        x: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        y: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        amount: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[ResourceGeneration.Event]:
        """Propose Resource Generation events.

        Each configured deposit delegates coordinate selection to
        ``placement_model`` using the simulation-owned RNG.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Resource Generation events.
        """
        world = simulation_state.domain_state
        events: list[ResourceGeneration.Event] = []

        # Each deposit receives its own coordinate draw. Multiple deposits may
        # legitimately land on the same cell; application will accumulate them.
        for _ in range(self.number_of_deposits):
            x, y = self.placement_model.choose_position(
                width=world.width,
                height=world.height,
                rng=simulation_state.rng,
            )
            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    x=x,
                    y=y,
                    amount=self.amount,
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: ResourceGeneration.Event,
    ) -> None:
        """Apply a resolved Resource Generation event.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Resource Generation event to apply.
        """
        simulation_state.domain_state.add_resources(
            x=resolved_event.x,
            y=resolved_event.y,
            amount=resolved_event.amount,
        )
