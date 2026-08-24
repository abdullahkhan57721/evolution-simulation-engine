"""Tests for SimulationEngine observer integration."""

from __future__ import annotations

import pytest

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    StageCoordinator,
)
from evo_engine.observation import PopulationRecorder
from evo_engine.processes import Aging
from evo_engine.resolvers import AcceptAll
from evo_engine.world import WorldState
from tests.helpers import make_empty_architecture, make_organism


class RecordingObserver:
    """Record committed step index and first-organism age for engine tests."""

    def __init__(self) -> None:
        self.records: list[tuple[int, int]] = []

    def should_observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> bool:
        return True

    def observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> None:
        self.records.append(
            (
                step_index,
                world_state.organisms[0].age,
            )
        )


def _aging_engine(
    *,
    max_steps: int,
    observers=(),
) -> SimulationEngine:
    return SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(Aging(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=max_steps),
        observers=observers,
    )


def _simulation_with_one_organism() -> Simulation:
    architecture = make_empty_architecture()
    world = WorldState(width=1, height=1)
    world.add_organism(
        make_organism(
            genetic_architecture=architecture,
        )
    )
    return Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
    )


def test_engine_observes_step_zero_and_each_committed_step() -> None:
    """Test observers see the baseline and only authoritative post-step states."""
    simulation = _simulation_with_one_organism()
    observer = RecordingObserver()
    engine = _aging_engine(
        max_steps=2,
        observers=(observer,),
    )

    engine.run(simulation)

    assert observer.records == [
        (0, 0),
        (1, 1),
        (2, 2),
    ]


def test_engine_does_not_observe_failed_transactional_step() -> None:
    """Test observers never see a working state from a failed step."""
    simulation = _simulation_with_one_organism()
    observer = RecordingObserver()

    class FailingCoordinator:
        def coordinate(self, simulation_state):
            simulation_state.world.organisms[0].age = 99
            raise RuntimeError("failed step")

    engine = SimulationEngine(
        step_coordinator=FailingCoordinator(),
        stopping_condition=MaxSteps(max_steps=1),
        observers=(observer,),
    )

    with pytest.raises(RuntimeError, match="failed step"):
        engine.run(simulation)

    assert observer.records == [(0, 0)]
    assert simulation.state.step_index == 0
    assert simulation.state.world.organisms[0].age == 0


def test_engine_preflights_observer_trait_requirements_before_observation() -> None:
    """Test observer trait dependencies fail before step zero is recorded."""
    simulation = _simulation_with_one_organism()
    recorder = PopulationRecorder(
        trait_names=("missing_trait",),
    )
    engine = _aging_engine(
        max_steps=0,
        observers=(recorder,),
    )

    with pytest.raises(ValueError, match="missing_trait"):
        engine.run(simulation)

    assert recorder.observations == ()
    assert simulation.state.step_index == 0


def test_engine_rejects_non_observer_component() -> None:
    """Test observer configuration is structurally validated."""
    with pytest.raises(TypeError, match=r"observers\[0\]"):
        _aging_engine(
            max_steps=0,
            observers=(object(),),
        )


def test_engine_respects_observer_schedule() -> None:
    """Test observer-specific scheduling remains outside engine policy."""
    simulation = _simulation_with_one_organism()
    recorder = PopulationRecorder(
        every_n_steps=2,
        include_step_zero=False,
    )
    engine = _aging_engine(
        max_steps=5,
        observers=(recorder,),
    )

    engine.run(simulation)

    assert tuple(
        observation.step_index for observation in recorder.observations
    ) == (2, 4)
