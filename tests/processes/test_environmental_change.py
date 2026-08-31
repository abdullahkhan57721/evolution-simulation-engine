"""Tests for the EnvironmentalChange process."""

from __future__ import annotations

import random

from evo_engine.ecology import (
    LinearEnvironmentalForcing,
    ScheduledEnvironmentalForcing,
)
from evo_engine.engine import SimulationState
from evo_engine.processes import EnvironmentalChange
from evo_engine.world import EnvironmentalField, EnvironmentalValueChanged, WorldState
from tests.helpers import make_empty_architecture


def _state() -> SimulationState:
    return SimulationState(
        world=WorldState(
            width=2,
            height=2,
            environmental_fields=(
                EnvironmentalField(name="temperature", default_value=20),
            ),
        ),
        genetic_architecture=make_empty_architecture(),
        rng=random.Random(1),
    )


def test_environmental_change_applies_global_forcing() -> None:
    """Test a global forcing event sets every world cell through WorldState."""
    state = _state()
    process = EnvironmentalChange(
        field_name="temperature",
        forcing=LinearEnvironmentalForcing(initial_value=25, change_per_step=1),
    )

    event = process.propose_events(state)[0]
    process.apply_event(state, event)

    assert event.value == 25
    assert all(
        state.world.environmental_value("temperature", x=x, y=y) == 25
        for y in range(2)
        for x in range(2)
    )
    assert len(state.world.mutations_since(0)) == 4
    assert all(
        isinstance(mutation, EnvironmentalValueChanged)
        for mutation in state.world.mutations_since(0)
    )


def test_environmental_change_can_target_spatial_patch() -> None:
    """Test environmental forcing can be restricted to selected coordinates."""
    state = _state()
    process = EnvironmentalChange(
        field_name="temperature",
        forcing=LinearEnvironmentalForcing(initial_value=30, change_per_step=0),
        coordinates=((1, 0), (1, 1)),
    )

    process.apply_event(state, process.propose_events(state)[0])

    assert state.world.environmental_value("temperature", x=0, y=0) == 20
    assert state.world.environmental_value("temperature", x=1, y=0) == 30
    assert state.world.environmental_value("temperature", x=1, y=1) == 30


def test_scheduled_environmental_change_emits_no_event_on_unscheduled_step() -> None:
    """Test disturbance schedules leave unlisted steps unchanged."""
    state = _state()
    process = EnvironmentalChange(
        field_name="temperature",
        forcing=ScheduledEnvironmentalForcing(schedule=((2, 35),)),
    )

    assert process.propose_events(state) == []

    state.step_index = 2
    assert len(process.propose_events(state)) == 1
