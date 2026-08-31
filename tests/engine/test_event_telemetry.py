"""Tests for domain-neutral SimulationEngine telemetry integration."""

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
from evo_engine.telemetry import StepTelemetry

from tests.engine.helpers import CounterState, IncrementProcess


class RecordingTelemetryObserver:
    """Record selected committed step telemetry."""

    def __init__(self, *, minimum_step: int = 0) -> None:
        self.minimum_step = minimum_step
        self.records: list[StepTelemetry] = []

    def should_observe_telemetry(self, telemetry: StepTelemetry) -> bool:
        return telemetry.completed_step_index >= self.minimum_step

    def observe_telemetry(self, telemetry: StepTelemetry) -> None:
        self.records.append(telemetry)


def _engine(
    *,
    max_steps: int,
    telemetry_observers=(),
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
        telemetry_observers=telemetry_observers,
    )


def test_engine_emits_telemetry_only_for_committed_steps() -> None:
    """Test telemetry observers receive one record per committed step."""
    recorder = RecordingTelemetryObserver()
    simulation = Simulation(initial_world_state=CounterState())

    _engine(
        max_steps=2,
        telemetry_observers=(recorder,),
    ).run(simulation)

    assert tuple(record.completed_step_index for record in recorder.records) == (1, 2)
    assert tuple(
        record.events[0].event_step_index for record in recorder.records
    ) == (0, 1)
    assert simulation.state.world.value == 2


def test_failed_transaction_produces_no_committed_telemetry() -> None:
    """Test a failed working copy never reaches telemetry observers."""
    recorder = RecordingTelemetryObserver()
    simulation = Simulation(initial_world_state=CounterState())

    @attrs.frozen(slots=True, kw_only=True)
    class FailureEvent:
        step_index: int

    @attrs.frozen(slots=True)
    class FailingProcess:
        @property
        def event_type(self) -> type[FailureEvent]:
            return FailureEvent

        def propose_events(
            self,
            simulation_state: SimulationState,
        ) -> list[FailureEvent]:
            return [FailureEvent(step_index=simulation_state.step_index)]

        def apply_event(
            self,
            simulation_state: SimulationState,
            event: FailureEvent,
            /,
        ) -> None:
            del event
            simulation_state.world.value = 100
            raise RuntimeError("failed telemetry step")

    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(IncrementProcess(),),
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

    with pytest.raises(RuntimeError, match="failed telemetry step"):
        engine.run(simulation)

    assert recorder.records == []
    assert simulation.state.step_index == 0
    assert simulation.state.world.value == 0


def test_engine_respects_telemetry_observer_filter() -> None:
    """Test telemetry scheduling policy remains inside the observer."""
    recorder = RecordingTelemetryObserver(minimum_step=2)
    simulation = Simulation(initial_world_state=CounterState())

    _engine(
        max_steps=3,
        telemetry_observers=(recorder,),
    ).run(simulation)

    assert tuple(record.completed_step_index for record in recorder.records) == (2, 3)


def test_engine_rejects_non_telemetry_observer_component() -> None:
    """Test telemetry observer configuration is structurally validated."""
    with pytest.raises(TypeError, match=r"telemetry_observers\[0\]"):
        _engine(
            max_steps=0,
            telemetry_observers=(object(),),
        )
