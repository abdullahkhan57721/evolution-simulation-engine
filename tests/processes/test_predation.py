"""Tests for the Predation process."""

from __future__ import annotations

import pytest

from evo_engine.processes import Predation
from evo_engine.spatial.neighborhoods import SameCell
from tests.helpers import (
    add_organism,
    make_integer_architecture,
    make_state,
)


def make_predation_state():
    """Return a state with one larger predator and one smaller prey."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    predator = add_organism(
        state,
        trait_values={"adult_body_mass": 10},
        energy=20,
        x=1,
        y=1,
    )
    prey = add_organism(
        state,
        trait_values={"adult_body_mass": 6},
        energy=20,
        x=1,
        y=1,
    )
    return state, predator, prey


def test_default_predation_rule_requires_larger_predator() -> None:
    """Test body-size-based default predation eligibility."""
    state, predator, prey = make_predation_state()

    events = Predation(
        neighborhood=SameCell(),
        consumption_percent=50,
    ).propose_events(state)

    assert len(events) == 1
    assert events[0].predator_id == predator.id
    assert events[0].prey_id == prey.id


def test_predation_records_integer_biomass_split() -> None:
    """Test prey biomass is partitioned between energy and carcass."""
    state, _, _ = make_predation_state()

    event = Predation(
        neighborhood=SameCell(),
        consumption_percent=50,
    ).propose_events(state)[0]

    assert event.predator_energy_gain == 3
    assert event.carcass_resource_units == 3


@pytest.mark.parametrize(
    ("can_predate", "preference_function"),
    [
        (
            lambda predator, prey, state: 1,
            lambda predator, prey, state: 0,
        ),
        (
            lambda predator, prey, state: True,
            lambda predator, prey, state: False,
        ),
    ],
)
def test_predation_requires_exact_callback_return_types(
    can_predate,
    preference_function,
) -> None:
    """Test strict custom predation-policy contracts."""
    state, _, _ = make_predation_state()

    with pytest.raises(TypeError):
        Predation(
            neighborhood=SameCell(),
            consumption_percent=50,
            can_predate=can_predate,
            preference_function=preference_function,
        ).propose_events(state)


def test_predation_can_use_custom_eligibility_and_preference() -> None:
    """Test domain-specific predation policies remain injectable."""
    state, predator, prey = make_predation_state()
    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=100,
        can_predate=lambda predator, prey, state: True,
        preference_function=lambda predator, prey, state: prey.id,
    )

    events = process.propose_events(state)

    assert len(events) == 2
    assert {(event.predator_id, event.prey_id) for event in events} == {
        (predator.id, prey.id),
        (prey.id, predator.id),
    }


def test_predation_apply_removes_prey_and_adds_energy_and_carcass() -> None:
    """Test mechanical application of a resolved predation event."""
    state, predator, prey = make_predation_state()
    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=50,
    )
    event = process.propose_events(state)[0]

    process.apply_event(
        state,
        event,
    )

    assert prey.id not in state.domain_state.organisms
    assert predator.energy == 23

    carcass = next(iter(state.domain_state.carcasses.values()))
    assert carcass.resource_units == 3
    assert (carcass.x, carcass.y) == (1, 1)


def test_full_consumption_creates_no_zero_resource_carcass() -> None:
    """Test zero biomass remainder is omitted from current world state."""
    state, _, prey = make_predation_state()
    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=100,
    )
    event = process.propose_events(state)[0]

    process.apply_event(
        state,
        event,
    )

    assert prey.id not in state.domain_state.organisms
    assert not state.domain_state.carcasses


def test_default_predation_uses_current_body_mass_not_adult_target() -> None:
    """Test developmental size changes affect predator-prey eligibility."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    predator = add_organism(
        state,
        trait_values={"adult_body_mass": 20},
        body_mass=4,
        x=0,
        y=0,
    )
    prey = add_organism(
        state,
        trait_values={"adult_body_mass": 5},
        body_mass=6,
        x=0,
        y=0,
    )

    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=50,
    )

    assert process.propose_events(state) == [
        Predation.Event(
            step_index=0,
            predator_id=prey.id,
            prey_id=predator.id,
            x=0,
            y=0,
            predator_energy_gain=2,
            carcass_resource_units=2,
            preference_score=0,
        )
    ]
