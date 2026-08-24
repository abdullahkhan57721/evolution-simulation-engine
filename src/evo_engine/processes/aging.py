"""Aging simulation process."""

from __future__ import annotations

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators


class Aging:
    """Represent the Aging simulation process."""

    @property
    def event_type(self) -> type[Aging.Event]:
        """Return the Aging event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a proposed Aging event.

        Attributes:
            step_index: Simulation step associated with the event.
            organism_id: ID of the organism targeted by the event.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        organism_id: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Aging.Event]:
        """Propose Aging events for eligible organisms.

        An Aging event is proposed for each active organism.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Aging events.
        """
        events: list[Aging.Event] = []

        for organism in simulation_state.world.organisms.values():
            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    organism_id=organism.id,
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Aging.Event,
    ) -> None:
        """Apply a resolved Aging event.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Aging event to apply.
        """
        organism = simulation_state.world.organisms[resolved_event.organism_id]

        organism.age += 1
