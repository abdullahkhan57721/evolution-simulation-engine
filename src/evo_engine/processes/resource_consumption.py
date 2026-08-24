"""Resource Consumption simulation process."""

from __future__ import annotations

from typing import ClassVar

import attrs

from evo_engine.behavior import ENERGY_ACQUISITION, behavior_is_allowed
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class ResourceConsumption:
    """Represent the Resource Consumption simulation process.

    Attributes:
        requested_amount: Resource units requested by each eligible organism.
    """

    behavioral_purpose: ClassVar[str] = ENERGY_ACQUISITION

    requested_amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    @property
    def event_type(self) -> type[ResourceConsumption.Event]:
        """Return the Resource Consumption event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a Resource Consumption event."""

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
        amount: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[ResourceConsumption.Event]:
        """Propose behaviorally selected Resource Consumption events.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Resource Consumption events for organisms whose current
            behavior-selection model permits energy acquisition.
        """
        events: list[ResourceConsumption.Event] = []

        for organism in simulation_state.world.organisms.values():
            if not behavior_is_allowed(
                organism,
                behavioral_purpose=self.behavioral_purpose,
                simulation_state=simulation_state,
            ):
                continue

            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    organism_id=organism.id,
                    x=organism.x,
                    y=organism.y,
                    amount=self.requested_amount,
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: ResourceConsumption.Event,
    ) -> None:
        """Apply a resolved Resource Consumption event.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Resource Consumption event to apply.
        """
        simulation_state.world.remove_resources(
            x=resolved_event.x,
            y=resolved_event.y,
            amount=resolved_event.amount,
        )

        organism = simulation_state.world.organisms[resolved_event.organism_id]

        organism.energy += resolved_event.amount
