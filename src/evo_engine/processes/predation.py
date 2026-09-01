"""Predation simulation process."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

import attrs

from evo_engine.access import EntityAccessModel
from evo_engine.admission import EntityAdmissionModel
from evo_engine.behavior import ENERGY_ACQUISITION, behavior_is_allowed
from evo_engine.departure import EntityDepartureModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import (
    collect_required_traits,
    validate_required_traits,
)
from evo_engine.predation import LargerPredatorEligibility, NeutralPredationPreference
from evo_engine.reference import EntityReferenceModel
from evo_engine.spatial.neighborhoods import Neighborhood
from evo_engine.validation import attrs_validators
from evo_engine.world.access import WorldOrganismAccess
from evo_engine.world.admission import WorldCarcassAdmission
from evo_engine.world.carcass import Carcass
from evo_engine.world.departure import WorldOrganismDeparture
from evo_engine.world.organism import Organism
from evo_engine.world.reference import WorldOrganismReference
from evo_engine.world.world_state import WorldState

CanPredate = Callable[
    [Organism, Organism, SimulationState],
    bool,
]

PreferenceFunction = Callable[
    [Organism, Organism, SimulationState],
    int,
]


@attrs.frozen(slots=True, kw_only=True)
class Predation:
    """Represent the Predation simulation process.

    Callable biological policies may optionally expose ``required_traits``.
    Those nested requirements are aggregated automatically with explicitly
    declared callback dependencies, preserving support for ordinary functions
    and lambdas while enabling structured trait-aware policies.

    Predation retains the biological meaning of killing prey. Read access,
    reference derivation, structural removal, and carcass admission are
    delegated independently so the process does not own world storage or
    identity mechanics and generic departure remains independent of death.

    Attributes:
        neighborhood: Spatial neighborhood within which predation is possible.
        consumption_percent: Percentage of prey biomass consumed by a
            successful predator.
        can_predate: Callable determining whether a predator may consume prey.
        preference_function: Callable returning an integer preference score
            for a predator-prey pairing.
        required_traits: Additional genetic phenotype traits read by opaque
            custom callbacks. Trait-aware policy objects contribute their own
            requirements automatically.
        access_model: Policy providing read-only access to active organisms.
        reference_model: Policy deriving world references for active organisms.
        departure_model: Policy removing killed prey from active world state
            during mechanical application.
        carcass_admission_model: Policy admitting unconsumed prey biomass as a
            carcass when any remains.
    """

    behavioral_purpose: ClassVar[str] = ENERGY_ACQUISITION

    neighborhood: Neighborhood
    consumption_percent: int = attrs.field(
        validator=attrs_validators.validate_int_in_range(
            0,
            100,
        ),
    )
    can_predate: CanPredate = attrs.field(
        factory=LargerPredatorEligibility,
        validator=attrs.validators.is_callable(),
    )
    preference_function: PreferenceFunction = attrs.field(
        factory=NeutralPredationPreference,
        validator=attrs.validators.is_callable(),
    )
    required_traits: frozenset[str] = attrs.field(
        factory=frozenset,
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
        """Validate policies and aggregate genetic phenotype dependencies."""
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

        declared_requirements = validate_required_traits(
            self.required_traits,
            name="required_traits",
        )
        nested_requirements = collect_required_traits(
            self.can_predate,
            self.preference_function,
        )
        object.__setattr__(
            self,
            "required_traits",
            declared_requirements | nested_requirements,
        )

    @property
    def event_type(self) -> type[Predation.Event]:
        """Return the Predation event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a possible Predation event."""

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        predator_id: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        prey_id: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        x: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        y: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        predator_energy_gain: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        carcass_resource_units: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        preference_score: int = attrs.field(
            validator=attrs_validators.validate_int,
        )

        @property
        def deceased_organism_ids(self) -> tuple[int, ...]:
            """Return the prey organism biologically killed by predation."""
            return (self.prey_id,)

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Predation.Event]:
        """Propose behaviorally selected, feasible predation events."""
        world = simulation_state.world
        organisms = self.access_model.entities(state=world)
        references: tuple[int, ...] | None = None
        events: list[Predation.Event] = []

        for predator_index, predator in enumerate(organisms):
            if not behavior_is_allowed(
                predator,
                behavioral_purpose=self.behavioral_purpose,
                simulation_state=simulation_state,
            ):
                continue

            if references is None:
                references = tuple(
                    self.reference_model.reference(organism, state=world)
                    for organism in organisms
                )
            predator_id = references[predator_index]

            for prey, prey_id in zip(organisms, references, strict=True):
                event = self._propose_pair(
                    predator,
                    prey,
                    predator_id=predator_id,
                    prey_id=prey_id,
                    simulation_state=simulation_state,
                )
                if event is not None:
                    events.append(event)

        return events

    def _propose_pair(
        self,
        predator: Organism,
        prey: Organism,
        *,
        predator_id: int,
        prey_id: int,
        simulation_state: SimulationState,
    ) -> Predation.Event | None:
        """Return one feasible predator-prey event or None."""
        if predator_id == prey_id:
            return None

        if not self._within_neighborhood(
            predator,
            prey,
            simulation_state=simulation_state,
        ):
            return None

        if not self._validated_can_predate(
            predator,
            prey,
            simulation_state=simulation_state,
        ):
            return None

        preference_score = self._validated_preference_score(
            predator,
            prey,
            simulation_state=simulation_state,
        )

        predator_energy_gain = prey.body_mass * self.consumption_percent // 100

        return self.Event(
            step_index=simulation_state.step_index,
            predator_id=predator_id,
            prey_id=prey_id,
            x=prey.x,
            y=prey.y,
            predator_energy_gain=predator_energy_gain,
            carcass_resource_units=(prey.body_mass - predator_energy_gain),
            preference_score=preference_score,
        )

    def _within_neighborhood(
        self,
        predator: Organism,
        prey: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether prey lies inside the configured predation neighborhood."""
        world = simulation_state.world
        return self.neighborhood.contains(
            center_x=predator.x,
            center_y=predator.y,
            other_x=prey.x,
            other_y=prey.y,
            width=world.width,
            height=world.height,
        )

    def _validated_can_predate(
        self,
        predator: Organism,
        prey: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return a validated biological eligibility decision."""
        can_predate = self.can_predate(
            predator,
            prey,
            simulation_state,
        )

        if type(can_predate) is not bool:
            raise TypeError("can_predate must return a Boolean.")

        return can_predate

    def _validated_preference_score(
        self,
        predator: Organism,
        prey: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return a validated integer predator preference score."""
        preference_score = self.preference_function(
            predator,
            prey,
            simulation_state,
        )

        if type(preference_score) is not int:
            raise TypeError("preference_function must return an integer.")

        return preference_score

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Predation.Event,
    ) -> None:
        """Apply a resolved Predation event."""
        world = simulation_state.world
        predator = self.access_model.get(
            resolved_event.predator_id,
            state=world,
        )

        self.departure_model.depart(
            resolved_event.prey_id,
            state=world,
        )
        predator.energy += resolved_event.predator_energy_gain

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
