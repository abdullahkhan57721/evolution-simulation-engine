"""Decomposition simulation process."""

from __future__ import annotations

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class Decomposition:
    """Represent the Decomposition simulation process.

    Attributes:
        amount: Maximum carcass resource units decomposed per carcass per step.
    """

    amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    @property
    def event_type(self) -> type[Decomposition.Event]:
        """Return the Decomposition event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a proposed Decomposition event.

        Attributes:
            step_index: Simulation step associated with the event.
            carcass_id: ID of the decomposing carcass.
            x: Horizontal coordinate of the carcass.
            y: Vertical coordinate of the carcass.
            amount: Resource units decomposed during the event.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        carcass_id: int = attrs.field(
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
    ) -> list[Decomposition.Event]:
        """Propose Decomposition events for carcasses.

        Each carcass decomposes by up to the configured amount. Carcasses
        containing no resource units receive a zero-amount event so they can
        be removed during application.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Decomposition events.
        """
        events: list[Decomposition.Event] = []

        for carcass in simulation_state.world.carcasses.values():
            amount = min(
                self.amount,
                carcass.resource_units,
            )

            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    carcass_id=carcass.id,
                    x=carcass.x,
                    y=carcass.y,
                    amount=amount,
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Decomposition.Event,
    ) -> None:
        """Apply a resolved Decomposition event.

        Decomposed carcass resource units become environmental resource units.
        A carcass is removed when no resource units remain.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Decomposition event to apply.
        """
        world = simulation_state.world

        carcass = world.carcasses[resolved_event.carcass_id]

        if resolved_event.amount > 0:
            carcass.resource_units -= resolved_event.amount

            world.add_resources(
                x=resolved_event.x,
                y=resolved_event.y,
                amount=resolved_event.amount,
            )

        if carcass.resource_units == 0:
            world.remove_carcass(resolved_event.carcass_id)
