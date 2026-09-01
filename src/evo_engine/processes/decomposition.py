"""Decomposition simulation process."""

from __future__ import annotations

import attrs

from evo_engine.access import EntityAccessModel
from evo_engine.departure import EntityDepartureModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.reference import EntityReferenceModel
from evo_engine.validation import attrs_validators
from evo_engine.world.access import WorldCarcassAccess
from evo_engine.world.carcass import Carcass
from evo_engine.world.departure import WorldCarcassDeparture
from evo_engine.world.reference import WorldCarcassReference
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class Decomposition:
    """Represent the Decomposition simulation process.

    Carcass storage mechanics are delegated through the same domain-neutral
    access, reference, and departure contracts used by other entity types.

    Attributes:
        amount: Maximum carcass resource units decomposed per carcass per step.
        access_model: Policy providing read-only access to active carcasses.
        reference_model: Policy deriving references for active carcasses.
        departure_model: Policy removing exhausted carcasses from world state.
    """

    amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    access_model: EntityAccessModel[int, WorldState, Carcass] = attrs.field(
        factory=WorldCarcassAccess,
    )
    reference_model: EntityReferenceModel[Carcass, WorldState, int] = attrs.field(
        factory=WorldCarcassReference,
    )
    departure_model: EntityDepartureModel[int, WorldState, Carcass] = attrs.field(
        factory=WorldCarcassDeparture,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured carcass lifecycle policies."""
        for policy, method_name, policy_name in (
            (self.access_model, "get", "access_model"),
            (self.access_model, "entities", "access_model"),
            (self.reference_model, "reference", "reference_model"),
            (self.departure_model, "depart", "departure_model"),
        ):
            if not callable(getattr(policy, method_name, None)):
                raise TypeError(
                    f"{policy_name} must provide a callable {method_name} method."
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
            carcass_id: Reference of the decomposing carcass.
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
        world = simulation_state.domain_state
        events: list[Decomposition.Event] = []

        for carcass in self.access_model.entities(state=world):
            amount = min(
                self.amount,
                carcass.resource_units,
            )

            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    carcass_id=self.reference_model.reference(
                        carcass,
                        state=world,
                    ),
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
        A carcass is removed through the configured departure policy when no
        resource units remain.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Decomposition event to apply.
        """
        world = simulation_state.domain_state
        carcass = self.access_model.get(
            resolved_event.carcass_id,
            state=world,
        )

        if resolved_event.amount > 0:
            carcass.resource_units -= resolved_event.amount

            world.add_resources(
                x=resolved_event.x,
                y=resolved_event.y,
                amount=resolved_event.amount,
            )

        if carcass.resource_units == 0:
            self.departure_model.depart(
                resolved_event.carcass_id,
                state=world,
            )
