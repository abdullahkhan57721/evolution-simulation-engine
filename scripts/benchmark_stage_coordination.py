#!/usr/bin/env python3
"""Microbenchmark high-event-count StageCoordinator dispatch with pyperf."""

from __future__ import annotations

import attrs
import pyperf

from evo_engine.engine import SimulationState, StageCoordinator
from evo_engine.resolvers import AcceptAll

_EVENT_COUNT = 1_000


@attrs.define(slots=True)
class _BenchmarkState:
    """Minimal copyable state for kernel orchestration benchmarks."""

    applied: int = 0

    def copy(self) -> _BenchmarkState:
        """Return an independent state copy."""
        return _BenchmarkState(applied=self.applied)


@attrs.frozen(slots=True, kw_only=True)
class _BenchmarkEvent:
    """Represent one prebuilt generic benchmark event."""

    step_index: int
    token: int


@attrs.frozen(slots=True, kw_only=True)
class _PlainBatchProcess:
    """Return a fixed event batch without post-resolution materialization."""

    events: tuple[_BenchmarkEvent, ...]

    @property
    def event_type(self) -> type[_BenchmarkEvent]:
        """Return the benchmark event type."""
        return _BenchmarkEvent

    def propose_events(self, simulation_state: SimulationState) -> list[_BenchmarkEvent]:
        """Return the fixed proposal batch."""
        del simulation_state
        return list(self.events)

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: _BenchmarkEvent,
        /,
    ) -> None:
        """Apply one benchmark event with minimal state work."""
        del event
        simulation_state.world.applied += 1


@attrs.frozen(slots=True, kw_only=True)
class _MaterializingBatchProcess(_PlainBatchProcess):
    """Return a fixed event batch and materialize every resolved event."""

    def materialize_event(
        self,
        simulation_state: SimulationState,
        event: _BenchmarkEvent,
        /,
    ) -> _BenchmarkEvent:
        """Return the already-materialized benchmark event."""
        del simulation_state
        return event


def _build_events() -> tuple[_BenchmarkEvent, ...]:
    return tuple(
        _BenchmarkEvent(step_index=0, token=token) for token in range(_EVENT_COUNT)
    )


def _build_stage(*, materializing: bool) -> tuple[StageCoordinator, SimulationState]:
    events = _build_events()
    process = (
        _MaterializingBatchProcess(events=events)
        if materializing
        else _PlainBatchProcess(events=events)
    )
    return (
        StageCoordinator(processes=(process,), resolver=AcceptAll()),
        SimulationState(world=_BenchmarkState()),
    )


def main() -> None:
    """Benchmark plain and materializing stage dispatch for 1,000 events."""
    plain_stage, plain_state = _build_stage(materializing=False)
    materializing_stage, materializing_state = _build_stage(materializing=True)

    runner = pyperf.Runner(
        metadata={
            "scenario": "domain-neutral-stage-dispatch",
            "events_per_coordinate": _EVENT_COUNT,
        }
    )
    runner.bench_func(
        "stage_coordinate.plain_1000",
        plain_stage.coordinate,
        plain_state,
    )
    runner.bench_func(
        "stage_coordinate.materialized_1000",
        materializing_stage.coordinate,
        materializing_state,
    )


if __name__ == "__main__":
    main()
