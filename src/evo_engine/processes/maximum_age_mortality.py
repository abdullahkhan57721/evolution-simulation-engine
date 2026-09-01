"""Maximum-age mortality simulation process."""

from __future__ import annotations

import attrs

from evo_engine.access import EntityAccessModel
from evo_engine.admission import EntityAdmissionModel
from evo_engine.departure import EntityDepartureModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.life_history import (
    DevelopmentalMaximumAge,
    MaximumAgeSource,
    determine_maximum_age,
    validate_maximum_age_source,
)
from evo_engine.reference import EntityReferenceModel
from evo_engine.validation import attrs_validators
from evo_engine.world.access import WorldOrganismAccess
from evo_engine.world.admission import WorldCarcassAdmission
from evo_engine.world.carcass import Carcass
from evo_engine.world.departure import WorldOrganismDeparture
from evo_engine.world.organism import Organism
from evo_engine.world.reference import WorldOrganismReference
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class MaximumAgeMortality:
    """Kill organisms that have reached their configured maximum age.

    Biological mortality semantics remain on this process and its events.
    Read access, reference derivation, structural removal, and carcass admission
    are delegated independently so the process does not own world storage or
    identity mechanics.

    Attributes:
        maximum_age: Fixed or organism-specific maximum-age source.
        access_model: Policy providing read-only access to active organisms.
        reference_model: Policy deriving world references for active organisms.
        departure_model: Policy removing a deceased organism from active world
            state during mechanical application.
        carcass_admission_model: Policy admitting the resulting carcass to world
            state when death leaves biomass behind.
    """

    maximum_age: MaximumAgeSource = attrs.field(
        factory=DevelopmentalMaximumAge,
    )
    access_model: EntityAccessModel[int, WorldState, Organism] = attrs.field(
        factory=WorldOrganismAccess,
    )
    reference_model: EntityReferenceModel[Organism, WorldState, int] = attrs.field(
        factory=WorldOrganismReference,
    )
    departure_model: EntityDepartureModel[int, WorldState, Organism] = attrs.field(
        factory=WorldOrganismDeparture,
    )
    carcass_admission_model: EntityAdmissionModel[Carcass, WorldState] = attrs.field(
        factory=WorldCarcassAdmission,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured mortality policies."""
        validate_maximum_age_source(self.maximum_age)
        for policy, method_name, policy_name in (
            (self.access_model, "get", "access_model"),
            (self.access_model, "entities", "access_model"),
            (self.reference_model, "reference", "reference_model"),
            (self.departure_model, "depart", "departure_model"),
            (self.carcass_admission_model, "admit", "carcass_admission_model"),
        ):
            if not callable(getattr(policy, method_name, None)):
                raise TypeError(
                    f"{policy_name} must provide a callable {method_name} method."
                )

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
        world = simulation_state.domain_state

        for organism in self.access_model.entities(state=world):
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
                    organism_id=self.reference_model.reference(
                        organism,
                        state=world,
                    ),
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

        The mortality event remains the source of biological death semantics.
        Organism departure and resulting carcass admission are separate
        structural lifecycle operations.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved maximum-age mortality event to apply.
        """
        world = simulation_state.domain_state
        self.departure_model.depart(
            resolved_event.organism_id,
            state=world,
        )

        if resolved_event.carcass_resource_units == 0:
            return

        self.carcass_admission_model.admit(
            Carcass(
                x=resolved_event.x,
                y=resolved_event.y,
                resource_units=resolved_event.carcass_resource_units,
            ),
            state=world,
        )
