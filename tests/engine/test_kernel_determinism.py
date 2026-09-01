"""Determinism tests for the frozen domain-neutral simulation kernel."""

from __future__ import annotations

import attrs

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    SimulationState,
    StageCoordinator,
)
from evo_engine.resolvers import AcceptAll
from tests.engine.helpers import CounterState


@attrs.frozen(slots=True, kw_only=True)
class _SampleEvent:
    step_index: int
    amount: int


@attrs.frozen(slots=True)
class _RandomIncrementProcess:
    @property
    def event_type(self) -> type[_SampleEvent]:
        return _SampleEvent

    def propose_events(self, simulation_state: SimulationState) -> list[_SampleEvent]:
        return [
            _SampleEvent(
                step_index=simulation_state.step_index,
                amount=simulation_state.rng.randint(1, 100),
            )
        ]

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: _SampleEvent,
        /,
    ) -> None:
        simulation_state.domain_state.value += event.amount
        simulation_state.domain_state.notes.append(str(event.amount))


def _run(seed: int) -> CounterState:
    simulation = Simulation(initial_domain_state=CounterState(), seed=seed)
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(_RandomIncrementProcess(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=8),
    )
    engine.run(simulation)
    return simulation.state.domain_state


def test_same_seed_reproduces_identical_kernel_outcome() -> None:
    """Test transactional RNG ownership preserves same-seed reproducibility."""
    first = _run(seed=1729)
    second = _run(seed=1729)

    assert first.value == second.value
    assert first.notes == second.notes
