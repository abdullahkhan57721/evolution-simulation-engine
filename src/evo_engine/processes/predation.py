"""Predation simulation process."""

from __future__ import annotations

from collections.abc import Callable

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import validate_required_traits
from evo_engine.spatial.neighborhoods import Neighborhood
from evo_engine.validation import attrs_validators
from evo_engine.world.carcass import Carcass
from evo_engine.world.organism import Organism

CanPredate = Callable[
    [Organism, Organism, SimulationState],
    bool,
]

PreferenceFunction = Callable[
    [Organism, Organism, SimulationState],
    int,
]


def _larger_predator_can_predate(
    predator: Organism,
    prey: Organism,
    simulation_state: SimulationState,
) -> bool:
    """Return whether a predator is larger than its prey."""
    return predator.body_mass > prey.body_mass


def _neutral_preference(
    predator: Organism,
    prey: Organism,
    simulation_state: SimulationState,
) -> int:
    """Return a neutral predation preference score."""
    return 0


@attrs.frozen(slots=True, kw_only=True)
class Predation:
    """Represent the Predation simulation process.

    Attributes:
        neighborhood: Spatial neighborhood within which predation is possible.
        consumption_percent: Percentage of prey biomass consumed by a
            successful predator.
        can_predate: Function determining whether a predator may consume prey.
        preference_function: Function returning an integer preference score
            for a predator-prey pairing.
        required_traits: Genetic phenotype traits read by custom predation callbacks.
    """

    neighborhood: Neighborhood
    consumption_percent: int = attrs.field(
        validator=attrs_validators.validate_int_in_range(
            0,
            100,
        ),
    )
    can_predate: CanPredate = attrs.field(
        default=_larger_predator_can_predate,
        validator=attrs.validators.is_callable(),
    )
    preference_function: PreferenceFunction = attrs.field(
        default=_neutral_preference,
        validator=attrs.validators.is_callable(),
    )
    required_traits: frozenset[str] = attrs.field(
        factory=frozenset,
    )

    def __attrs_post_init__(self) -> None:
        """Validate explicitly declared genetic phenotype dependencies."""
        validate_required_traits(
            self.required_traits,
            name="required_traits",
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

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Predation.Event]:
        """Propose every spatially and biologically feasible predation event."""
        world = simulation_state.world
        organisms = tuple(world.organisms.values())
        events: list[Predation.Event] = []

        # Build the complete feasible interaction graph. Conflict resolution
        # remains a separate stage concern.
        for predator in organisms:
            for prey in organisms:
                event = self._propose_pair(
                    predator,
                    prey,
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
        simulation_state: SimulationState,
    ) -> Predation.Event | None:
        """Return one feasible predator-prey event or None."""
        if predator.id == prey.id:
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
            predator_id=predator.id,
            prey_id=prey.id,
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
        predator = world.organisms[resolved_event.predator_id]

        world.remove_organism(resolved_event.prey_id)
        predator.energy += resolved_event.predator_energy_gain

        if resolved_event.carcass_resource_units == 0:
            return

        world.add_carcass(
            Carcass(
                x=resolved_event.x,
                y=resolved_event.y,
                resource_units=resolved_event.carcass_resource_units,
            )
        )
