"""Starvation simulation process."""

from __future__ import annotations

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators
from evo_engine.world.carcass import Carcass


class Starvation:
    """Represent the Starvation simulation process."""

    @property
    def event_type(self) -> type[Starvation.Event]:
        """Return the Starvation event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a proposed Starvation event.

        Attributes:
            step_index: Simulation step associated with the event.
            organism_id: ID of the starving organism.
            x: Horizontal coordinate where starvation occurs.
            y: Vertical coordinate where starvation occurs.
            carcass_resource_units: Resource units left in the carcass.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        organism_id: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        x: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        y: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        carcass_resource_units: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )

        @property
        def deceased_organism_ids(self) -> tuple[int, ...]:
            """Return the organism biologically killed by starvation."""
            return (self.organism_id,)

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Starvation.Event]:
        """Propose Starvation events for organisms with no energy.

        Carcass resource units are derived from the starving organism's body
        mass.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Starvation events.
        """
        events: list[Starvation.Event] = []

        for organism in simulation_state.world.organisms.values():
            if organism.energy != 0:
                continue

            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    organism_id=organism.id,
                    x=organism.x,
                    y=organism.y,
                    carcass_resource_units=organism.body_mass,
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Starvation.Event,
    ) -> None:
        """Apply a resolved Starvation event.

        The organism is removed from the active world and replaced by a
        carcass containing the recorded resource units.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Starvation event to apply.
        """
        world = simulation_state.world

        world.remove_organism(resolved_event.organism_id)

        if resolved_event.carcass_resource_units == 0:
            return

        carcass = Carcass(
            x=resolved_event.x,
            y=resolved_event.y,
            resource_units=resolved_event.carcass_resource_units,
        )

        world.add_carcass(carcass)
