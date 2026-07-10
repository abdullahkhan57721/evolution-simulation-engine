from __future__ import annotations

import pytest

from evo_engine.event import AgingEvent
from evo_engine.events_proposer import AgingEventsProposer
from evo_engine.history import History
from evo_engine.organism import Organism
from evo_engine.state_updater import StateUpdater
from evo_engine.stopping_condition import StoppingCondition
from evo_engine.world_state import WorldState
from tests.engine_builders import build_basic_aging_engine

""" Testing the full pipeline """


@pytest.mark.parametrize(
    "initial_population, max_time_steps",
    [(10, 1), (2, 5), (17, 10)],
)
def test_engine_runs_simulation_to_max_time_steps(
    initial_population,
    max_time_steps,
):
    # Arrange
    engine = build_basic_aging_engine(
        initial_population=initial_population, max_time_steps=max_time_steps
    )

    # Act
    history = engine.run()

    # Assert
    assert engine.world_state.time_step == max_time_steps

    for organism in engine.world_state.organisms:
        assert organism.age == max_time_steps

    assert len(history.observations) != 0


""" Testing stopping_condition """


@pytest.mark.parametrize(
    "current_time_step, max_time_steps",
    [(0, 1), (0, 5), (1, 5), (3, 17)],
)
def test_stopping_condition_is_false_before_max_time_steps(
    current_time_step, max_time_steps
):
    # Arrange
    world_state = WorldState(time_step=current_time_step, organisms=[])
    history = History(observations=[])
    stopping_condition = StoppingCondition(max_time_steps=max_time_steps)

    # Act
    result = stopping_condition.is_met(world_state=world_state, history=history)

    # Assert
    assert result == False


@pytest.mark.parametrize(
    "current_time_step, max_time_steps",
    [(0, 0), (1, 1), (5, 5), (17, 17)],
)
def test_stopping_condition_is_true_at_max_time_steps(
    current_time_step, max_time_steps
):
    # Arrange
    world_state = WorldState(time_step=current_time_step, organisms=[])
    history = History(observations=[])
    stopping_condition = StoppingCondition(max_time_steps=max_time_steps)

    # Act
    result = stopping_condition.is_met(world_state=world_state, history=history)

    # Assert
    assert result == True


@pytest.mark.parametrize("current_time_step", [0, 1, 2, 17])
def test_world_state_advance_time_increases_time_step_by_one(current_time_step):
    # Arrange
    world_state = WorldState(time_step=current_time_step, organisms=[])

    # Act
    world_state.advance_time()

    # Assert
    assert world_state.time_step == current_time_step + 1


@pytest.mark.parametrize(
    "organisms",
    [
        [
            Organism(id=0),
            Organism(id=1),
        ],
        [
            Organism(id=3),
            Organism(id=23),
        ],
        [
            Organism(id=0),
            Organism(id=34),
            Organism(id=32),
        ],
    ],
)
def test_aging_events_proposer_proposes_one_aging_event_per_organism(
    organisms,
):
    world_state = WorldState(time_step=0, organisms=organisms)
    history = History(observations=[])
    proposer = AgingEventsProposer()

    events = proposer.propose(world_state=world_state, history=history)

    assert len(events) == len(organisms)


@pytest.mark.parametrize(
    "organisms, events",
    [
        (
            [Organism(id=1, age=2), Organism(id=17, age=3)],
            [
                AgingEvent(organism_id=1, time_step=4),
                AgingEvent(organism_id=17, time_step=4),
            ],
        ),
    ],
)
def test_state_updater_applies_aging_events(organisms, events):
    world_state = WorldState(time_step=4, organisms=organisms)
    state_updater = StateUpdater()

    updated_world_state = state_updater.apply(world_state=world_state, events=events)

    for updated_organism in updated_world_state.organisms:
        for organism in world_state.organisms:
            if updated_organism.id == organism.id:
                assert updated_organism.age == organism.age + 1
