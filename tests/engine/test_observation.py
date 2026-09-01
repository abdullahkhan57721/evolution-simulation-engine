"""Tests for SimulationEngine observer integration without domain fixtures."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    SimulationState,
    StageCoordinator,
)
from evo_engine.resolvers import AcceptAll
from tests.engine.helpers import CounterState, IncrementProcess


class RecordingObserver:
    """Record selected committed counter states."""

    def __init__(
        self,
        *,
        every_n_steps: int = 1,
        include_step_zero: bool = True,
    ) -> None:
        self.every_n_steps = every_n_steps
        self.include_step_zero = include_step_zero
        self.records: list[tuple[int, int]] = []

    def should_observe(
        self,
        domain_state: CounterState,
        *,
        step_index: int,
    ) -> bool:
        if step_index == 0 and not self.include_step_zero:
            return False
        return step_index % self.every_n_steps == 0

    def observe(
        self,
        domain_state: CounterState,
        *,
        step_index: int,
    ) -> None:
        self.records.append((step_index, domain_state.value))


def _incrementing_engine(
    *,
    max_steps: int,
    observers=(),
) -> SimulationEngine:
    return SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(IncrementProcess(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=max_steps),
        observers=observers,
    )


def test_engine_observes_step_zero_and_each_committed_step() -> None:
    """Test observers see the baseline and authoritative post-step states."""
    simulation = Simulation(initial_domain_state=CounterState())
    observer = RecordingObserver()

    _incrementing_engine(
        max_steps=2,
        observers=(observer,),
    ).run(simulation)

    assert observer.records == [
        (0, 0),
        (1, 1),
        (2, 2),
    ]


def test_engine_does_not_observe_failed_transactional_step() -> None:
    """Test observers never see a working state from a failed step."""
    simulation = Simulation(initial_domain_state=CounterState())
    observer = RecordingObserver()

    @attrs.frozen(slots=True)
    class FailingCoordinator:
        def coordinate(self, simulation_state: SimulationState) -> SimulationState:
            working_state = simulation_state.copy()
            working_state.domain_state.value = 99
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
    assert simulation.state.domain_state.value == 0


def test_engine_rejects_non_observer_component() -> None:
    """Test observer configuration is structurally validated."""
    with pytest.raises(TypeError, match=r"observers\[0\]"):
        _incrementing_engine(
            max_steps=0,
            observers=(object(),),
        )


def test_engine_respects_observer_owned_schedule() -> None:
    """Test scheduling policy remains inside the observer."""
    simulation = Simulation(initial_domain_state=CounterState())
    observer = RecordingObserver(
        every_n_steps=2,
        include_step_zero=False,
    )

    _incrementing_engine(
        max_steps=5,
        observers=(observer,),
    ).run(simulation)

    assert observer.records == [
        (2, 2),
        (4, 4),
    ]
