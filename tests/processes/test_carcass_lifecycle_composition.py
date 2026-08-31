"""Tests for process composition with generic carcass lifecycle policies."""

from __future__ import annotations

from evo_engine.processes import (
    Decomposition,
    MaximumAgeMortality,
    Predation,
    Starvation,
)
from evo_engine.spatial.neighborhoods import SameCell
from evo_engine.world import Carcass, WorldState
from tests.helpers import add_organism, make_state


class RecordingCarcassAccess:
    """Expose carcasses while recording individual resolution."""

    def __init__(self, *entities: Carcass) -> None:
        self._entities = tuple(entities)
        self.references: list[int] = []

    def get(self, reference: int, *, state: WorldState) -> Carcass:
        self.references.append(reference)
        return state.carcasses[reference]

    def entities(self, *, state: WorldState) -> tuple[Carcass, ...]:
        del state
        return self._entities


class RecordingCarcassReference:
    """Record carcasses whose references are derived."""

    def __init__(self) -> None:
        self.entities: list[Carcass] = []

    def reference(self, entity: Carcass, *, state: WorldState) -> int:
        self.entities.append(entity)
        assert state.carcasses[entity.id] is entity
        return entity.id


class RecordingCarcassDeparture:
    """Record carcass departures while delegating world removal."""

    def __init__(self) -> None:
        self.references: list[int] = []

    def depart(self, reference: int, *, state: WorldState) -> Carcass:
        self.references.append(reference)
        return state.remove_carcass(reference)


class RecordingCarcassAdmission:
    """Record carcass admission requests without mutating world membership."""

    def __init__(self) -> None:
        self.entities: list[Carcass] = []
        self.states: list[WorldState] = []

    def admit(self, entity: Carcass, *, state: WorldState) -> None:
        self.entities.append(entity)
        self.states.append(state)


def test_decomposition_uses_generic_carcass_lifecycle_policies() -> None:
    """Test decomposition delegates carcass reads, references, and departure."""
    state = make_state()
    carcass = Carcass(x=1, y=1, resource_units=3)
    state.world.add_carcass(carcass)
    access = RecordingCarcassAccess(carcass)
    reference = RecordingCarcassReference()
    departure = RecordingCarcassDeparture()
    process = Decomposition(
        amount=3,
        access_model=access,
        reference_model=reference,
        departure_model=departure,
    )

    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert reference.entities == [carcass]
    assert access.references == [carcass.id]
    assert departure.references == [carcass.id]
    assert not state.world.carcasses
    assert state.world.resources[(1, 1)] == 3


def test_starvation_delegates_carcass_admission() -> None:
    """Test starvation does not directly insert its resulting carcass."""
    state = make_state()
    organism = add_organism(state, energy=0, body_mass=4, x=1, y=2)
    admission = RecordingCarcassAdmission()
    process = Starvation(carcass_admission_model=admission)
    event = process.propose_events(state)[0]

    process.apply_event(state, event)

    assert organism.id not in state.world.organisms
    assert not state.world.carcasses
    assert len(admission.entities) == 1
    assert admission.states == [state.world]
    assert (admission.entities[0].x, admission.entities[0].y) == (1, 2)
    assert admission.entities[0].resource_units == 4


def test_maximum_age_mortality_delegates_carcass_admission() -> None:
    """Test age mortality delegates resulting carcass membership."""
    state = make_state()
    organism = add_organism(state, age=5, body_mass=6, x=2, y=1)
    admission = RecordingCarcassAdmission()
    process = MaximumAgeMortality(
        maximum_age=5,
        carcass_admission_model=admission,
    )
    event = process.propose_events(state)[0]

    process.apply_event(state, event)

    assert organism.id not in state.world.organisms
    assert not state.world.carcasses
    assert len(admission.entities) == 1
    assert admission.states == [state.world]
    assert admission.entities[0].resource_units == 6


def test_predation_delegates_carcass_admission() -> None:
    """Test predation delegates admission of unconsumed prey biomass."""
    state = make_state()
    predator = add_organism(state, energy=10, body_mass=5)
    prey = add_organism(state, energy=10, body_mass=4)
    admission = RecordingCarcassAdmission()
    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=50,
        carcass_admission_model=admission,
    )
    event = Predation.Event(
        step_index=0,
        predator_id=predator.id,
        prey_id=prey.id,
        x=prey.x,
        y=prey.y,
        predator_energy_gain=2,
        carcass_resource_units=2,
        preference_score=0,
    )

    process.apply_event(state, event)

    assert prey.id not in state.world.organisms
    assert predator.energy == 12
    assert not state.world.carcasses
    assert len(admission.entities) == 1
    assert admission.states == [state.world]
    assert admission.entities[0].resource_units == 2
