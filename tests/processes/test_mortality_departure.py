"""Tests separating biological mortality from structural entity departure."""

from __future__ import annotations

from evo_engine.processes import MaximumAgeMortality, Predation, Starvation
from evo_engine.spatial.neighborhoods import SameCell
from evo_engine.world import Organism, WorldState
from tests.helpers import add_organism, make_state


class RecordingOrganismDeparture:
    """Record structural departures while preserving normal world removal."""

    def __init__(self) -> None:
        self.references: list[int] = []

    def depart(
        self,
        reference: int,
        *,
        state: WorldState,
    ) -> Organism:
        self.references.append(reference)
        return state.remove_organism(reference)


def test_starvation_delegates_departure_but_retains_death_semantics() -> None:
    """Test starvation causes death while departure only performs removal."""
    state = make_state()
    victim = add_organism(state, energy=0, body_mass=2)
    departure = RecordingOrganismDeparture()
    event = Starvation.Event(
        step_index=0,
        organism_id=victim.id,
        x=victim.x,
        y=victim.y,
        carcass_resource_units=0,
    )

    Starvation(departure_model=departure).apply_event(state, event)

    assert departure.references == [victim.id]
    assert victim.id not in state.world.organisms
    assert event.deceased_organism_ids == (victim.id,)


def test_maximum_age_mortality_delegates_structural_departure() -> None:
    """Test maximum-age death delegates only the state-removal mechanism."""
    state = make_state()
    victim = add_organism(state, age=5)
    departure = RecordingOrganismDeparture()
    event = MaximumAgeMortality.Event(
        step_index=0,
        organism_id=victim.id,
        x=victim.x,
        y=victim.y,
        carcass_resource_units=0,
    )

    MaximumAgeMortality(departure_model=departure).apply_event(state, event)

    assert departure.references == [victim.id]
    assert victim.id not in state.world.organisms
    assert event.deceased_organism_ids == (victim.id,)


def test_predation_delegates_prey_departure_but_retains_kill_semantics() -> None:
    """Test predation owns biological killing while departure removes prey."""
    state = make_state()
    predator = add_organism(state, energy=10)
    prey = add_organism(state, energy=10)
    departure = RecordingOrganismDeparture()
    event = Predation.Event(
        step_index=0,
        predator_id=predator.id,
        prey_id=prey.id,
        x=prey.x,
        y=prey.y,
        predator_energy_gain=0,
        carcass_resource_units=0,
        preference_score=0,
    )
    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=0,
        departure_model=departure,
    )

    process.apply_event(state, event)

    assert departure.references == [prey.id]
    assert prey.id not in state.world.organisms
    assert event.deceased_organism_ids == (prey.id,)
