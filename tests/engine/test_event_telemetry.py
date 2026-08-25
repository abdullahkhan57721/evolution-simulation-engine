"""Tests for SimulationEngine committed event telemetry integration."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    StageCoordinator,
)
from evo_engine.observation import EventRecorder
from evo_engine.resolvers import AcceptAll
from evo_engine.telemetry import ResourcesChanged
from evo_engine.world import WorldState
from tests.helpers import make_empty_architecture


@attrs.frozen(slots=True, kw_only=True)
class AddResourceProcess:
    """Add one resource unit for telemetry tests."""

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Resource-addition event."""

        step_index: int
        amount: int = 1

    @property
    def event_type(self) -> type[Event]:
        """Return event type."""
        return self.Event

    def propose_events(self, simulation_state):
        """Propose one resource addition."""
        return [self.Event(step_index=simulation_state.step_index)]

    def apply_event(self, simulation_state, event) -> None:
        """Apply one resource addition."""
        simulation_state.world.add_resources(x=0, y=0, amount=event.amount)


@attrs.frozen(slots=True, kw_only=True)
class FailingProcess:
    """Raise after mutating the transactional working world."""

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Failing event."""

        step_index: int

    @property
    def event_type(self) -> type[Event]:
        """Return event type."""
        return self.Event

    def propose_events(self, simulation_state):
        """Propose one failing event."""
        return [self.Event(step_index=simulation_state.step_index)]

    def apply_event(self, simulation_state, event) -> None:
        """Mutate then fail so transaction rollback can be verified."""
        simulation_state.world.add_resources(x=0, y=0, amount=100)
        raise RuntimeError("failed telemetry step")


def _simulation() -> Simulation:
    architecture = make_empty_architecture()
    return Simulation(
        initial_world_state=WorldState(width=1, height=1),
        genetic_architecture=architecture,
    )


def test_engine_records_applied_events_only_after_commit() -> None:
    """Test telemetry preserves committed step, process, event, and world effects."""
    recorder = EventRecorder()
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(AddResourceProcess(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=2),
        telemetry_observers=(recorder,),
    )
    simulation = _simulation()

    engine.run(simulation)

    assert tuple(step.completed_step_index for step in recorder.steps) == (1, 2)
    assert len(recorder.events) == 2
    first = recorder.events[0]
    assert first.event_step_index == 0
    assert first.stage_index == 0
    assert first.process_name == "AddResourceProcess"
    assert first.world_mutations == (ResourcesChanged(x=0, y=0, before=0, after=1),)
    assert simulation.state.world.resources[(0, 0)] == 2


def test_failed_transaction_produces_no_committed_telemetry() -> None:
    """Test events from a failed working copy never reach telemetry observers."""
    recorder = EventRecorder()
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(AddResourceProcess(),),
                    resolver=AcceptAll(),
                ),
                StageCoordinator(
                    processes=(FailingProcess(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=1),
        telemetry_observers=(recorder,),
    )
    simulation = _simulation()

    with pytest.raises(RuntimeError, match="failed telemetry step"):
        engine.run(simulation)

    assert recorder.steps == ()
    assert simulation.state.step_index == 0
    assert simulation.state.world.resources == {}
