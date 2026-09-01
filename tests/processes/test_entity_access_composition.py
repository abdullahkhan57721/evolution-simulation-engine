"""Tests for lifecycle composition with read-only entity access."""

from __future__ import annotations

from evo_engine.processes import MaximumAgeMortality, Predation, Starvation
from evo_engine.spatial.neighborhoods import SameCell
from evo_engine.world import Organism, WorldState
from tests.helpers import add_organism, make_state


class RecordingOrganismAccess:
    """Expose selected organisms and record individual resolutions."""

    def __init__(self, *entities: Organism) -> None:
        self._entities = tuple(entities)
        self.references: list[int] = []

    def get(self, reference: int, *, state: WorldState) -> Organism:
        self.references.append(reference)
        return state.organisms[reference]

    def entities(self, *, state: WorldState) -> tuple[Organism, ...]:
        del state
        return self._entities


def test_starvation_enumerates_through_access_model() -> None:
    """Test starvation observes only entities supplied by read access."""
    state = make_state()
    visible = add_organism(state, energy=0)
    hidden = add_organism(state, energy=0)
    access = RecordingOrganismAccess(visible)

    events = Starvation(access_model=access).propose_events(state)

    assert [event.organism_id for event in events] == [visible.id]
    assert hidden.id not in {event.organism_id for event in events}


def test_maximum_age_enumerates_through_access_model() -> None:
    """Test age mortality observes only entities supplied by read access."""
    state = make_state()
    visible = add_organism(state, age=5)
    hidden = add_organism(state, age=5)
    access = RecordingOrganismAccess(visible)

    events = MaximumAgeMortality(
        maximum_age=5,
        access_model=access,
    ).propose_events(state)

    assert [event.organism_id for event in events] == [visible.id]
    assert hidden.id not in {event.organism_id for event in events}


def test_predation_resolves_predator_through_access_model() -> None:
    """Test predation application delegates individual entity resolution."""
    state = make_state()
    predator = add_organism(state, energy=10)
    prey = add_organism(state, energy=10)
    access = RecordingOrganismAccess(predator, prey)
    event = Predation.Event(
        step_index=0,
        predator_id=predator.id,
        prey_id=prey.id,
        x=prey.x,
        y=prey.y,
        predator_energy_gain=4,
        carcass_resource_units=0,
        preference_score=0,
    )
    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=0,
        access_model=access,
    )

    process.apply_event(state, event)

    assert access.references == [predator.id]
    assert predator.energy == 14
    assert prey.id not in state.domain_state.organisms
