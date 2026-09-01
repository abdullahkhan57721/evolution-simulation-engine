"""Tests for domain-neutral StageCoordinator behavior."""

from __future__ import annotations

from collections.abc import Sequence

import attrs
import pytest

import evo_engine.engine.stage_coordinator as stage_coordinator_module
from evo_engine.engine import SimulationEvent, SimulationState, StageCoordinator
from evo_engine.resolvers import AcceptAll
from tests.engine.helpers import CounterState, IncrementProcess


def test_coordinate_proposes_resolves_and_applies() -> None:
    """Test the normal stage lifecycle for a simple process."""
    state = SimulationState(world=CounterState(value=10))

    StageCoordinator(
        processes=(IncrementProcess(),),
        resolver=AcceptAll(),
    ).coordinate(state)

    assert state.world.value == 11


def test_stage_rejects_duplicate_proposed_event_types() -> None:
    """Test unambiguous event-to-process ownership within a stage."""
    with pytest.raises(ValueError, match="unique event types"):
        StageCoordinator(
            processes=(
                IncrementProcess(),
                IncrementProcess(amount=2),
            ),
            resolver=AcceptAll(),
        )


def test_resolved_unknown_event_type_raises() -> None:
    """Test resolvers cannot inject events with no owning process."""
    state = SimulationState(world=CounterState())

    @attrs.frozen(slots=True, kw_only=True)
    class ForeignEvent:
        step_index: int

    @attrs.frozen(slots=True)
    class ForeignResolver:
        def resolve_events(
            self,
            simulation_state: SimulationState,
            proposed_events: Sequence[SimulationEvent],
        ) -> list[SimulationEvent]:
            del proposed_events
            return [ForeignEvent(step_index=simulation_state.step_index)]

    coordinator = StageCoordinator(
        processes=(IncrementProcess(),),
        resolver=ForeignResolver(),
    )

    with pytest.raises(RuntimeError, match="No process is registered"):
        coordinator.coordinate(state)


def test_all_events_materialize_before_any_apply() -> None:
    """Test materializers observe the same pre-application state."""
    state = SimulationState(world=CounterState(value=10))
    observations: list[int] = []

    @attrs.frozen(slots=True, kw_only=True)
    class Proposal:
        step_index: int
        amount: int

    @attrs.frozen(slots=True, kw_only=True)
    class Materialized:
        step_index: int
        amount: int
        observed_value: int

    @attrs.frozen(slots=True)
    class MaterializingProcess:
        @property
        def event_type(self) -> type[Proposal]:
            return Proposal

        def propose_events(
            self,
            simulation_state: SimulationState,
        ) -> list[Proposal]:
            return [
                Proposal(step_index=simulation_state.step_index, amount=1),
                Proposal(step_index=simulation_state.step_index, amount=1),
            ]

        def materialize_event(
            self,
            simulation_state: SimulationState,
            event: Proposal,
            /,
        ) -> Materialized:
            observations.append(simulation_state.world.value)
            return Materialized(
                step_index=event.step_index,
                amount=event.amount,
                observed_value=simulation_state.world.value,
            )

        def apply_event(
            self,
            simulation_state: SimulationState,
            event: Materialized,
            /,
        ) -> None:
            assert event.observed_value == 10
            simulation_state.world.value -= event.amount

    StageCoordinator(
        processes=(MaterializingProcess(),),
        resolver=AcceptAll(),
    ).coordinate(state)

    assert observations == [10, 10]
    assert state.world.value == 8


def test_materializer_capability_is_detected_once_per_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test runtime structural materializer checks stay out of the event hot path."""
    state = SimulationState(world=CounterState())

    class CountingMaterializerMeta(type):
        checks = 0

        def __instancecheck__(cls, instance: object) -> bool:
            cls.checks += 1
            return callable(getattr(instance, "materialize_event", None))

    class CountingMaterializer(metaclass=CountingMaterializerMeta):
        pass

    @attrs.frozen(slots=True, kw_only=True)
    class Proposal:
        step_index: int
        amount: int = 1

    @attrs.frozen(slots=True)
    class MaterializingProcess:
        @property
        def event_type(self) -> type[Proposal]:
            return Proposal

        def propose_events(
            self,
            simulation_state: SimulationState,
        ) -> list[Proposal]:
            return [
                Proposal(step_index=simulation_state.step_index),
                Proposal(step_index=simulation_state.step_index),
            ]

        def materialize_event(
            self,
            simulation_state: SimulationState,
            event: Proposal,
            /,
        ) -> Proposal:
            del simulation_state
            return event

        def apply_event(
            self,
            simulation_state: SimulationState,
            event: Proposal,
            /,
        ) -> None:
            simulation_state.world.value += event.amount

    monkeypatch.setattr(
        stage_coordinator_module,
        "EventMaterializer",
        CountingMaterializer,
    )
    coordinator = StageCoordinator(
        processes=(MaterializingProcess(),),
        resolver=AcceptAll(),
    )

    assert CountingMaterializerMeta.checks == 1

    coordinator.coordinate(state)
    coordinator.coordinate(state)

    assert state.world.value == 4
    assert CountingMaterializerMeta.checks == 1
