"""Tests for core process composition with generic organism policies."""

from __future__ import annotations

from evo_engine.energetics import (
    FixedLocomotionCost,
    FixedMetabolicCost,
    LinearGrowthCost,
)
from evo_engine.genetics.builtin_traits import ADULT_BODY_MASS, MAX_SPEED
from evo_engine.growth import FixedGrowthRate
from evo_engine.processes import (
    Aging,
    Growth,
    Metabolism,
    Movement,
    ResourceConsumption,
)
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.spatial.movement_patterns import UniformRandom
from evo_engine.world import Organism, WorldState
from tests.helpers import add_organism, make_integer_architecture, make_state


class RecordingOrganismAccess:
    """Expose selected organisms while recording individual resolution."""

    def __init__(self, *entities: Organism) -> None:
        self._entities = tuple(entities)
        self.references: list[int] = []

    def get(self, reference: int, *, state: WorldState) -> Organism:
        self.references.append(reference)
        return state.organisms[reference]

    def entities(self, *, state: WorldState) -> tuple[Organism, ...]:
        del state
        return self._entities


class RecordingOrganismReference:
    """Record organisms whose state-local references are derived."""

    def __init__(self) -> None:
        self.entities: list[Organism] = []

    def reference(self, entity: Organism, *, state: WorldState) -> int:
        self.entities.append(entity)
        assert state.organisms[entity.id] is entity
        return entity.id


def test_aging_delegates_organism_access_and_reference() -> None:
    """Test aging does not enumerate or resolve organisms through world storage."""
    state = make_state()
    excluded = add_organism(state)
    selected = add_organism(state)
    access = RecordingOrganismAccess(selected)
    reference = RecordingOrganismReference()
    process = Aging(
        access_model=access,
        reference_model=reference,
    )

    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert event.organism_id == selected.id
    assert reference.entities == [selected]
    assert access.references == [selected.id]
    assert excluded.age == 0
    assert selected.age == 1


def test_metabolism_delegates_organism_access_and_reference() -> None:
    """Test metabolism delegates entity enumeration, reference, and lookup."""
    state = make_state()
    excluded = add_organism(state, energy=10)
    selected = add_organism(state, energy=10)
    access = RecordingOrganismAccess(selected)
    reference = RecordingOrganismReference()
    process = Metabolism(
        cost_model=FixedMetabolicCost(amount=3),
        access_model=access,
        reference_model=reference,
    )

    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert event.organism_id == selected.id
    assert reference.entities == [selected]
    assert access.references == [selected.id]
    assert excluded.energy == 10
    assert selected.energy == 7


def test_growth_delegates_organism_access_and_reference() -> None:
    """Test growth scopes proposal and application through entity policies."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    state = make_state(genetic_architecture=architecture)
    excluded = add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 10},
        body_mass=5,
        energy=10,
    )
    selected = add_organism(
        state,
        trait_values={ADULT_BODY_MASS: 10},
        body_mass=5,
        energy=10,
    )
    access = RecordingOrganismAccess(selected)
    reference = RecordingOrganismReference()
    process = Growth(
        growth_model=FixedGrowthRate(amount_per_timestep=2),
        growth_cost_model=LinearGrowthCost(energy_per_body_mass_unit=1),
        access_model=access,
        reference_model=reference,
    )

    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert event.organism_id == selected.id
    assert reference.entities == [selected]
    assert access.references == [selected.id]
    assert (excluded.body_mass, excluded.energy) == (5, 10)
    assert (selected.body_mass, selected.energy) == (7, 8)


def test_resource_consumption_delegates_organism_access_and_reference() -> None:
    """Test feeding delegates organism enumeration, reference, and lookup."""
    state = make_state()
    excluded = add_organism(state, energy=10, x=0, y=0)
    selected = add_organism(state, energy=10, x=1, y=1)
    state.domain_state.add_resources(x=1, y=1, amount=3)
    access = RecordingOrganismAccess(selected)
    reference = RecordingOrganismReference()
    process = ResourceConsumption(
        requested_amount=3,
        access_model=access,
        reference_model=reference,
    )

    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert event.organism_id == selected.id
    assert reference.entities == [selected]
    assert access.references == [selected.id]
    assert excluded.energy == 10
    assert selected.energy == 13
    assert (1, 1) not in state.domain_state.resources


def test_movement_delegates_organism_access_and_reference() -> None:
    """Test movement delegates organism read access while retaining world motion."""
    architecture = make_integer_architecture(MAX_SPEED)
    state = make_state(
        width=5,
        height=5,
        genetic_architecture=architecture,
    )
    excluded = add_organism(
        state,
        trait_values={MAX_SPEED: 0},
        x=0,
        y=0,
    )
    selected = add_organism(
        state,
        trait_values={MAX_SPEED: 0},
        x=2,
        y=2,
    )
    access = RecordingOrganismAccess(selected)
    reference = RecordingOrganismReference()
    process = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=2),
        access_model=access,
        reference_model=reference,
    )

    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert event.organism_id == selected.id
    assert reference.entities == [selected]
    assert access.references == [selected.id]
    assert (excluded.x, excluded.y) == (0, 0)
    assert (selected.x, selected.y) == (2, 2)
