"""Aging simulation process."""

from __future__ import annotations

import attrs

from evo_engine.access import EntityAccessModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.reference import EntityReferenceModel
from evo_engine.validation import attrs_validators
from evo_engine.world.access import WorldOrganismAccess
from evo_engine.world.organism import Organism
from evo_engine.world.reference import WorldOrganismReference
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class Aging:
    """Represent the Aging simulation process.

    Read access and reference derivation are delegated so aging retains only
    the biological meaning of increasing organism age.

    Attributes:
        access_model: Policy providing read-only access to active organisms.
        reference_model: Policy deriving stable references for active organisms.
    """

    access_model: EntityAccessModel[int, WorldState, Organism] = attrs.field(
        factory=WorldOrganismAccess,
    )
    reference_model: EntityReferenceModel[Organism, WorldState, int] = attrs.field(
        factory=WorldOrganismReference,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured entity policies."""
        for policy, method_name, policy_name in (
            (self.access_model, "get", "access_model"),
            (self.access_model, "entities", "access_model"),
            (self.reference_model, "reference", "reference_model"),
        ):
            if not callable(getattr(policy, method_name, None)):
                raise TypeError(
                    f"{policy_name} must provide a callable {method_name} method."
                )

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
        world = simulation_state.domain_state

        for organism in self.access_model.entities(state=world):
            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    organism_id=self.reference_model.reference(
                        organism,
                        state=world,
                    ),
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
        organism = self.access_model.get(
            resolved_event.organism_id,
            state=simulation_state.domain_state,
        )

        organism.age += 1
