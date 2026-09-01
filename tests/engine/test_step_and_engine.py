"""Tests for domain-neutral step coordination, stopping, and engine execution."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.configuration import Dependency
from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    SimulationState,
    StageCoordinator,
)
from evo_engine.resolvers import AcceptAll
from tests.engine.helpers import CounterState, IncrementEvent, IncrementProcess


def test_sequential_step_runs_stages_in_order_and_increments_index() -> None:
    """Test ordered stage execution and post-step index advancement."""
    simulation = Simulation(initial_world_state=CounterState())
    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(IncrementProcess(),),
                resolver=AcceptAll(),
            ),
            StageCoordinator(
                processes=(IncrementProcess(amount=2),),
                resolver=AcceptAll(),
            ),
        )
    )

    next_state = coordinator.coordinate(simulation.state)

    assert next_state.step_index == 1
    assert next_state.world.value == 3
    assert simulation.state.step_index == 0
    assert simulation.state.world.value == 0


def test_failed_step_leaves_authoritative_state_unchanged() -> None:
    """Test transactional rollback when a stage raises."""
    simulation = Simulation(initial_world_state=CounterState(value=1))

    @attrs.frozen(slots=True)
    class FailingStage:
        def coordinate(
            self,
            simulation_state: SimulationState,
            *,
            stage_index: int = 0,
        ) -> None:
            del stage_index
            simulation_state.world.value = 99
            raise RuntimeError("stage failed")

    coordinator = SequentialStepCoordinator(
        stages=(FailingStage(),),  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError, match="stage failed"):
        coordinator.coordinate(simulation.state)

    assert simulation.state.step_index == 0
    assert simulation.state.world.value == 1


@pytest.mark.parametrize(
    ("step_index", "max_steps", "expected"),
    [
        (0, 0, True),
        (0, 1, False),
        (1, 1, True),
        (2, 1, True),
    ],
)
def test_max_steps(
    step_index: int,
    max_steps: int,
    expected: bool,
) -> None:
    """Test the maximum-step stopping boundary."""
    state = SimulationState(
        world=CounterState(),
        step_index=step_index,
    )

    assert MaxSteps(max_steps=max_steps).should_stop(state) is expected


def test_simulation_engine_runs_until_stopping_condition() -> None:
    """Test end-to-end engine iteration."""
    simulation = Simulation(initial_world_state=CounterState())
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(IncrementProcess(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=3),
    )

    engine.run(simulation)

    assert simulation.state.step_index == 3
    assert simulation.state.world.value == 3


def test_runtime_engine_does_not_preflight_declared_dependencies() -> None:
    """Test static dependency validation remains a compiler responsibility."""
    dependency = Dependency(category="service", name="quota")

    @attrs.frozen(slots=True)
    class RequirementDeclaringProcess:
        @property
        def required_dependencies(self) -> frozenset[Dependency]:
            return frozenset({dependency})

        @property
        def event_type(self) -> type[IncrementEvent]:
            return IncrementEvent

        def propose_events(
            self,
            simulation_state: SimulationState,
        ) -> list[IncrementEvent]:
            return [
                IncrementEvent(
                    step_index=simulation_state.step_index,
                    amount=1,
                )
            ]

        def apply_event(
            self,
            simulation_state: SimulationState,
            event: IncrementEvent,
            /,
        ) -> None:
            simulation_state.world.value += event.amount

    simulation = Simulation(initial_world_state=CounterState())
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(RequirementDeclaringProcess(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=0),
    )

    engine.run(simulation)

    assert simulation.state.step_index == 0
