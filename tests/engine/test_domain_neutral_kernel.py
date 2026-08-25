"""Tests proving the simulation kernel does not require biological state."""

from __future__ import annotations

from collections.abc import Sequence

import attrs

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEvent,
    SimulationState,
    StageCoordinator,
)


@attrs.define(slots=True)
class _CounterState:
    value: int = 0

    def copy(self) -> _CounterState:
        return _CounterState(value=self.value)


@attrs.frozen(slots=True, kw_only=True)
class _IncrementEvent:
    step_index: int


@attrs.frozen(slots=True)
class _IncrementProcess:
    @property
    def event_type(self) -> type[_IncrementEvent]:
        return _IncrementEvent

    def propose_events(self, simulation_state: SimulationState) -> list[_IncrementEvent]:
        return [_IncrementEvent(step_index=simulation_state.step_index)]

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: _IncrementEvent,
        /,
    ) -> None:
        simulation_state.world.value += 1


@attrs.frozen(slots=True)
class _AcceptAll:
    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> Sequence[SimulationEvent]:
        return proposed_events


def test_kernel_runs_nonbiological_transactional_state() -> None:
    """Test core execution works with an arbitrary copyable state object."""
    simulation = Simulation(
        initial_world_state=_CounterState(),
        seed=7,
        selection_pressure="frequency_dependent",
    )
    stage = StageCoordinator(
        processes=(_IncrementProcess(),),
        resolver=_AcceptAll(),
    )
    coordinator = SequentialStepCoordinator(stages=(stage,))

    from evo_engine.engine import SimulationEngine

    engine = SimulationEngine(
        step_coordinator=coordinator,
        stopping_condition=MaxSteps(max_steps=3),
    )
    engine.run(simulation)

    assert simulation.state.world.value == 3
    assert simulation.state.step_index == 3
    assert simulation.context.require("selection_pressure") == "frequency_dependent"


def test_kernel_context_accepts_arbitrary_domain_services() -> None:
    """Test the kernel stores domain configuration without assigning semantics."""
    service = object()
    simulation = Simulation(
        initial_world_state=_CounterState(),
        heritable_state_schema=service,
    )

    assert simulation.context.require("heritable_state_schema") is service
    assert simulation.heritable_state_schema is service
