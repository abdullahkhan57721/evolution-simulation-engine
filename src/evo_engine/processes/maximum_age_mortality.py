"""Maximum-age mortality simulation process."""

from __future__ import annotations

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.life_history import (
    DevelopmentalMaximumAge,
    MaximumAgeSource,
    determine_maximum_age,
    validate_maximum_age_source,
)
from evo_engine.validation import attrs_validators
from evo_engine.world.carcass import Carcass


@attrs.frozen(slots=True, kw_only=True)
class MaximumAgeMortality:
    """Remove organisms that have reached their configured maximum age.

    Attributes:
        maximum_age: Fixed or organism-specific maximum-age source.
    """

    maximum_age: MaximumAgeSource = attrs.field(
        factory=DevelopmentalMaximumAge,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the configured maximum-age source."""
        validate_maximum_age_source(self.maximum_age)

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by the configured maximum-age source."""
        return collect_required_traits(self.maximum_age)

    @property
    def event_type(self) -> type[MaximumAgeMortality.Event]:
        """Return the maximum-age mortality event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a proposed maximum-age mortality event.

        Attributes:
            step_index: Simulation step associated with the event.
            organism_id: ID of the organism that reached maximum age.
            x: Horizontal coordinate where death occurs.
            y: Vertical coordinate where death occurs.
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
            """Return the organism biologically killed by maximum age."""
            return (self.organism_id,)

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[MaximumAgeMortality.Event]:
        """Propose deaths for organisms at or above maximum age.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed maximum-age mortality events.
        """
        events: list[MaximumAgeMortality.Event] = []

        for organism in simulation_state.world.organisms.values():
            maximum_age = determine_maximum_age(
                self.maximum_age,
                organism,
                simulation_state=simulation_state,
            )
            if organism.age < maximum_age:
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
        resolved_event: MaximumAgeMortality.Event,
    ) -> None:
        """Apply a resolved maximum-age mortality event.

        The organism is removed from the active world and replaced by a
        carcass containing its current body mass as resource units.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved maximum-age mortality event to apply.
        """
        world = simulation_state.world
        world.remove_organism(resolved_event.organism_id)

        if resolved_event.carcass_resource_units == 0:
            return

        world.add_carcass(
            Carcass(
                x=resolved_event.x,
                y=resolved_event.y,
                resource_units=resolved_event.carcass_resource_units,
            )
        )
