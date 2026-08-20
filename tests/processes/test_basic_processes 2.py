"""Tests for basic simulation processes."""

from __future__ import annotations

import pytest

from evo_engine.energetics import FixedLocomotionCost, FixedMetabolicCost
from evo_engine.processes import (
    Aging,
    Decomposition,
    Metabolism,
    Movement,
    ResourceConsumption,
    ResourceGeneration,
    Starvation,
)
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.spatial.movement_patterns import UniformRandom
from evo_engine.world import Carcass
from tests.helpers import (
    add_organism,
    make_integer_architecture,
    make_state,
)


def test_aging_proposes_one_event_per_active_organism() -> None:
    """Test aging proposal cardinality and IDs."""
    state = make_state()
    add_organism(state)
    add_organism(state)

    events = Aging().propose_events(state)

    assert [event.organism_id for event in events] == [0, 1]


def test_aging_apply_increments_target_age() -> None:
    """Test aging application."""
    state = make_state()
    organism = add_organism(
        state,
        age=4,
    )
    event = Aging.Event(
        step_index=0,
        organism_id=organism.id,
    )

    Aging().apply_event(
        state,
        event,
    )

    assert organism.age == 5


def test_metabolism_records_model_cost() -> None:
    """Test metabolic proposals carry the model-decided cost."""
    state = make_state()
    organism = add_organism(state)

    events = Metabolism(
        cost_model=FixedMetabolicCost(
            amount=7,
        ),
    ).propose_events(state)

    assert events == [
        Metabolism.Event(
            step_index=0,
            organism_id=organism.id,
            energy_cost=7,
        )
    ]


def test_metabolism_clamps_energy_at_zero() -> None:
    """Test metabolic expenditure cannot make energy negative."""
    state = make_state()
    organism = add_organism(
        state,
        energy=3,
    )

    Metabolism(
        cost_model=FixedMetabolicCost(
            amount=10,
        ),
    ).apply_event(
        state,
        Metabolism.Event(
            step_index=0,
            organism_id=organism.id,
            energy_cost=10,
        ),
    )

    assert organism.energy == 0


def test_resource_generation_honors_number_of_deposits() -> None:
    """Test every configured deposit produces its own event."""
    state = make_state(
        width=3,
        height=4,
        seed=5,
    )
    process = ResourceGeneration(
        amount=2,
        number_of_deposits=4,
    )

    events = process.propose_events(state)

    assert len(events) == 4
    assert all(event.amount == 2 for event in events)
    assert all(0 <= event.x < 3 and 0 <= event.y < 4 for event in events)


def test_resource_generation_apply_accumulates_resources() -> None:
    """Test generated resources enter sparse world storage."""
    state = make_state()
    process = ResourceGeneration(
        amount=3,
        number_of_deposits=1,
    )
    event = ResourceGeneration.Event(
        step_index=0,
        x=1,
        y=2,
        amount=3,
    )

    process.apply_event(
        state,
        event,
    )
    process.apply_event(
        state,
        event,
    )

    assert state.world.resources[(1, 2)] == 6


def test_resource_consumption_proposes_at_organism_location() -> None:
    """Test resource requests are spatially localized."""
    state = make_state()
    organism = add_organism(
        state,
        x=2,
        y=3,
    )

    events = ResourceConsumption(
        requested_amount=5,
    ).propose_events(state)

    assert events == [
        ResourceConsumption.Event(
            step_index=0,
            organism_id=organism.id,
            x=2,
            y=3,
            amount=5,
        )
    ]


def test_resource_consumption_transfers_resources_to_energy() -> None:
    """Test resource consumption conserves the recorded transfer."""
    state = make_state()
    organism = add_organism(
        state,
        energy=10,
        x=1,
        y=1,
    )
    state.world.add_resources(
        x=1,
        y=1,
        amount=4,
    )

    ResourceConsumption(
        requested_amount=4,
    ).apply_event(
        state,
        ResourceConsumption.Event(
            step_index=0,
            organism_id=organism.id,
            x=1,
            y=1,
            amount=4,
        ),
    )

    assert organism.energy == 14
    assert (1, 1) not in state.world.resources


def test_decomposition_limits_event_to_remaining_carcass_resources() -> None:
    """Test decomposition does not overdraw a carcass."""
    state = make_state()
    carcass = Carcass(
        x=1,
        y=1,
        resource_units=3,
    )
    state.world.add_carcass(carcass)

    event = Decomposition(
        amount=10,
    ).propose_events(state)[0]

    assert event.amount == 3


def test_decomposition_transfers_resources_and_removes_empty_carcass() -> None:
    """Test carcass biomass becomes environmental resources."""
    state = make_state()
    carcass = Carcass(
        x=1,
        y=1,
        resource_units=3,
    )
    state.world.add_carcass(carcass)
    process = Decomposition(
        amount=3,
    )
    event = process.propose_events(state)[0]

    process.apply_event(
        state,
        event,
    )

    assert not state.world.carcasses
    assert state.world.resources[(1, 1)] == 3


def test_zero_resource_carcass_is_removed_by_decomposition() -> None:
    """Test cleanup of an already-empty carcass."""
    state = make_state()
    carcass = Carcass(
        x=1,
        y=1,
        resource_units=0,
    )
    state.world.add_carcass(carcass)
    process = Decomposition(
        amount=2,
    )
    event = process.propose_events(state)[0]

    assert event.amount == 0

    process.apply_event(
        state,
        event,
    )

    assert not state.world.carcasses


def test_starvation_only_proposes_for_zero_energy_organisms() -> None:
    """Test starvation mortality eligibility."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    starving = add_organism(
        state,
        trait_values={"adult_body_mass": 6},
        energy=0,
    )
    add_organism(
        state,
        trait_values={"adult_body_mass": 4},
        energy=1,
    )

    events = Starvation().propose_events(state)

    assert events == [
        Starvation.Event(
            step_index=0,
            organism_id=starving.id,
            x=0,
            y=0,
            carcass_resource_units=6,
        )
    ]


def test_starvation_removes_organism_and_creates_carcass() -> None:
    """Test starvation mortality mechanics."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"adult_body_mass": 7},
        energy=0,
        x=2,
        y=3,
    )
    event = Starvation().propose_events(state)[0]

    Starvation().apply_event(
        state,
        event,
    )

    assert organism.id not in state.world.organisms
    carcass = next(iter(state.world.carcasses.values()))
    assert (carcass.x, carcass.y) == (2, 3)
    assert carcass.resource_units == 7


def test_movement_uses_expressed_max_speed() -> None:
    """Test genetic-phenotype-driven movement capability."""
    architecture = make_integer_architecture("max_speed")
    state = make_state(
        width=10,
        height=10,
        genetic_architecture=architecture,
        seed=4,
    )
    organism = add_organism(
        state,
        trait_values={"max_speed": 0},
        x=5,
        y=5,
    )
    process = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(
            amount=3,
        ),
    )

    event = process.propose_events(state)[0]

    assert (event.dx, event.dy) == (0, 0)
    assert (event.new_x, event.new_y) == (
        organism.x,
        organism.y,
    )
    assert event.energy_cost == 0


def test_movement_apply_uses_world_controlled_movement() -> None:
    """Test application updates the target position."""
    architecture = make_integer_architecture("max_speed")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"max_speed": 1},
    )

    Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(
            amount=2,
        ),
    ).apply_event(
        state,
        Movement.Event(
            step_index=0,
            organism_id=organism.id,
            dx=1,
            dy=0,
            new_x=3,
            new_y=4,
            energy_cost=2,
        ),
    )

    assert (organism.x, organism.y) == (3, 4)
    assert organism.energy == 98


def test_movement_rejects_pattern_that_exceeds_max_speed() -> None:
    """Test Movement enforces max speed for custom movement patterns."""

    class TooFastPattern:
        def choose_displacement(self, *, rng, max_speed):
            return (max_speed, max_speed)

    architecture = make_integer_architecture("max_speed")
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={"max_speed": 2},
    )
    process = Movement(
        movement_pattern=TooFastPattern(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(
            amount=1,
        ),
    )

    with pytest.raises(ValueError, match="exceeds max_speed"):
        process.propose_events(state)


def test_movement_rejects_negative_expressed_max_speed() -> None:
    """Test the max-speed genetic phenotype semantic invariant."""
    architecture = make_integer_architecture("max_speed")
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={"max_speed": -1},
    )
    process = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(
            amount=3,
        ),
    )

    with pytest.raises(ValueError):
        process.propose_events(state)


def test_starvation_carcass_uses_current_body_mass() -> None:
    """Test carcass biomass follows physical state rather than adult target."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"adult_body_mass": 10},
        body_mass=3,
        energy=0,
    )

    event = Starvation().propose_events(state)[0]

    assert event.organism_id == organism.id
    assert event.carcass_resource_units == 3
