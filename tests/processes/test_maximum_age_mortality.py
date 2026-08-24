"""Tests for maximum-age mortality."""

from __future__ import annotations

from evo_engine.genetics import MAXIMUM_AGE
from evo_engine.life_history import DevelopmentalMaximumAge
from evo_engine.processes import MaximumAgeMortality
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_fixed_maximum_age_only_proposes_at_or_above_limit() -> None:
    """Test deterministic fixed-age mortality eligibility."""
    state = make_state()
    younger = add_organism(state, age=4)
    at_limit = add_organism(state, age=5)
    above_limit = add_organism(state, age=6)

    events = MaximumAgeMortality(maximum_age=5).propose_events(state)

    assert [event.organism_id for event in events] == [
        at_limit.id,
        above_limit.id,
    ]
    assert younger.id not in {event.organism_id for event in events}


def test_developmental_maximum_age_varies_by_organism() -> None:
    """Test individual developmental lifespans alter mortality timing."""
    architecture = make_integer_architecture(MAXIMUM_AGE)
    state = make_state(genetic_architecture=architecture)
    shorter_lived = add_organism(
        state,
        trait_values={MAXIMUM_AGE: 5},
        age=5,
    )
    longer_lived = add_organism(
        state,
        trait_values={MAXIMUM_AGE: 8},
        age=5,
    )
    process = MaximumAgeMortality()

    events = process.propose_events(state)

    assert events == [
        MaximumAgeMortality.Event(
            step_index=0,
            organism_id=shorter_lived.id,
            x=0,
            y=0,
            carcass_resource_units=shorter_lived.body_mass,
        )
    ]
    assert longer_lived.id not in {event.organism_id for event in events}
    assert process.required_traits == frozenset({MAXIMUM_AGE})


def test_maximum_age_mortality_removes_organism_and_creates_carcass() -> None:
    """Test age mortality converts current organism biomass into a carcass."""
    state = make_state()
    organism = add_organism(
        state,
        age=5,
        body_mass=7,
        x=2,
        y=3,
    )
    process = MaximumAgeMortality(maximum_age=5)
    event = process.propose_events(state)[0]

    process.apply_event(state, event)

    assert organism.id not in state.world.organisms
    carcass = next(iter(state.world.carcasses.values()))
    assert (carcass.x, carcass.y) == (2, 3)
    assert carcass.resource_units == 7


def test_maximum_age_mortality_uses_current_body_mass() -> None:
    """Test age-death carcass biomass follows mutable physical state."""
    architecture = make_integer_architecture(MAXIMUM_AGE)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MAXIMUM_AGE: 5},
        age=5,
        body_mass=3,
    )

    event = MaximumAgeMortality(
        maximum_age=DevelopmentalMaximumAge(),
    ).propose_events(state)[0]

    assert event.organism_id == organism.id
    assert event.carcass_resource_units == 3


def test_fixed_maximum_age_has_no_trait_requirement() -> None:
    """Test fixed lifespans do not force a genetic-architecture dependency."""
    assert MaximumAgeMortality(maximum_age=10).required_traits == frozenset()
