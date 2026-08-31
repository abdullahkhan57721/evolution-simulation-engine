"""Starvation simulation process."""

from __future__ import annotations

import attrs

from evo_engine.access import EntityAccessModel
from evo_engine.departure import EntityDepartureModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators
from evo_engine.world.access import WorldOrganismAccess
from evo_engine.world.carcass import Carcass
from evo_engine.world.departure import WorldOrganismDeparture
from evo_engine.world.organism import Organism
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class Starvation:
    """Kill organisms whose energy has reached zero.

    Biological mortality semantics remain on this process and its events. Read
    access and structural removal are delegated independently so the process
    does not own world storage mechanics.

    Attributes:
        access_model: Policy providing read-only access to active organisms.
        departure_model: Policy removing a deceased organism from active world
            state during mechanical application.
    """

    access_model: EntityAccessModel[int, WorldState, Organism] = attrs.field(
        factory=WorldOrganismAccess,
    )
    departure_model: EntityDepartureModel[int, WorldState, Organism] = attrs.field(
        factory=WorldOrganismDeparture,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured lifecycle policies."""
        for policy, method_name, policy_name in (
            (self.access_model, "get", "access_model"),
            (self.access_model, "entities", "access_model"),
            (self.departure_model, "depart", "departure_model"),
        ):
            if not callable(getattr(policy, method_name, None)):
                raise TypeError(
                    f"{policy_name} must provide a callable {method_name} method."
                )

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
        world = simulation_state.world

        for organism in self.access_model.entities(state=world):
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

        The mortality event remains the source of biological death semantics.
        Structural world departure is delegated separately, then a carcass is
        added when the recorded body mass yields resources.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Starvation event to apply.
        """
        world = simulation_state.world

        self.departure_model.depart(
            resolved_event.organism_id,
            state=world,
        )

        if resolved_event.carcass_resource_units == 0:
            return

        carcass = Carcass(
            x=resolved_event.x,
            y=resolved_event.y,
            resource_units=resolved_event.carcass_resource_units,
        )

        world.add_carcass(carcass)
