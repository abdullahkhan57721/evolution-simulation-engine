"""Tests for feeding-aware resource consumption."""

from __future__ import annotations

import pytest

from evo_engine.feeding import (
    FixedAssimilationEfficiency,
    FixedIntakeCapacity,
    GeneticPhenotypeAssimilationEfficiency,
    GeneticPhenotypeIntakeCapacity,
)
from evo_engine.genetics import ASSIMILATION_EFFICIENCY, MAX_INTAKE_RATE
from evo_engine.processes import ResourceConsumption
from tests.helpers import add_organism, make_state


def test_resource_consumption_preserves_uncapped_full_assimilation_defaults() -> None:
    """Test simple simulations retain historical request and energy semantics."""
    state = make_state()
    organism = add_organism(
        state,
        energy=10,
        x=2,
        y=3,
    )
    state.world.add_resources(
        x=2,
        y=3,
        amount=5,
    )
    process = ResourceConsumption(
        requested_amount=5,
    )

    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert event.amount == 5
    assert organism.energy == 15
    assert (2, 3) not in state.world.resources


def test_resource_consumption_caps_behavioral_request_by_intake_capacity() -> None:
    """Test physiological intake capacity limits the proposal before resolution."""
    state = make_state()
    organism = add_organism(state)
    process = ResourceConsumption(
        requested_amount=9,
        intake_capacity_model=FixedIntakeCapacity(
            amount=4,
        ),
    )

    event = process.propose_events(state)[0]

    assert event.organism_id == organism.id
    assert event.amount == 4


def test_resource_consumption_assimilates_only_fraction_of_allocated_food() -> None:
    """Test consumed food and usable energy are distinct quantities."""
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
        amount=3,
    )
    process = ResourceConsumption(
        requested_amount=10,
        assimilation_model=FixedAssimilationEfficiency(
            efficiency_percent=50,
        ),
    )

    process.apply_event(
        state,
        ResourceConsumption.Event(
            step_index=0,
            organism_id=organism.id,
            x=1,
            y=1,
            amount=3,
        ),
    )

    assert organism.energy == 12
    assert (1, 1) not in state.world.resources


def test_resource_consumption_aggregates_feeding_trait_requirements() -> None:
    """Test feeding collaborators participate in engine preflight validation."""
    process = ResourceConsumption(
        requested_amount=10,
        intake_capacity_model=GeneticPhenotypeIntakeCapacity(),
        assimilation_model=GeneticPhenotypeAssimilationEfficiency(),
    )

    assert process.required_traits == frozenset(
        {
            MAX_INTAKE_RATE,
            ASSIMILATION_EFFICIENCY,
        }
    )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        (
            "intake_capacity_model",
            object(),
            "determine_capacity",
        ),
        (
            "assimilation_model",
            object(),
            "determine_energy_gain",
        ),
    ],
)
def test_resource_consumption_rejects_invalid_feeding_collaborators(
    field_name: str,
    value: object,
    message: str,
) -> None:
    """Test feeding collaborators satisfy their structural capabilities."""
    kwargs = {field_name: value}

    with pytest.raises(TypeError, match=message):
        ResourceConsumption(
            requested_amount=1,
            **kwargs,  # type: ignore[arg-type]
        )
