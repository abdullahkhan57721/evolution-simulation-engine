"""Tests for lifecycle composition with entity reference derivation."""

from __future__ import annotations

from evo_engine.processes import MaximumAgeMortality, Predation, Starvation
from evo_engine.spatial.neighborhoods import SameCell
from evo_engine.world import Organism, WorldState
from tests.helpers import add_organism, make_state


class RecordingOrganismReference:
    """Record entities whose world references are requested."""

    def __init__(self) -> None:
        self.entities: list[Organism] = []

    def reference(
        self,
        entity: Organism,
        *,
        state: WorldState,
    ) -> int:
        assert state.organisms[entity.id] is entity
        self.entities.append(entity)
        return entity.id


def test_starvation_derives_event_reference_through_reference_model() -> None:
    """Test starvation delegates event-reference derivation."""
    state = make_state()
    starving = add_organism(state, energy=0)
    reference = RecordingOrganismReference()

    events = Starvation(reference_model=reference).propose_events(state)

    assert [event.organism_id for event in events] == [starving.id]
    assert reference.entities == [starving]


def test_maximum_age_derives_event_reference_through_reference_model() -> None:
    """Test age mortality delegates event-reference derivation."""
    state = make_state()
    deceased = add_organism(state, age=5)
    reference = RecordingOrganismReference()

    events = MaximumAgeMortality(
        maximum_age=5,
        reference_model=reference,
    ).propose_events(state)

    assert [event.organism_id for event in events] == [deceased.id]
    assert reference.entities == [deceased]


def test_predation_derives_predator_and_prey_references_through_model() -> None:
    """Test predation uses reference policy for pair identity and event IDs."""
    state = make_state()
    predator = add_organism(state, body_mass=8, x=0, y=0)
    prey = add_organism(state, body_mass=4, x=0, y=0)
    reference = RecordingOrganismReference()
    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=50,
        can_predate=lambda predator, prey, state: True,
        reference_model=reference,
    )

    events = process.propose_events(state)

    assert {(event.predator_id, event.prey_id) for event in events} == {
        (predator.id, prey.id),
        (prey.id, predator.id),
    }
    assert reference.entities.count(predator) == 4
    assert reference.entities.count(prey) == 4
