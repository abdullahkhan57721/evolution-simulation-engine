"""Tests for domain-neutral committed effect telemetry."""

from __future__ import annotations

import copy
from collections.abc import Callable

import attrs

from evo_engine.engine import SimulationState, StageCoordinator
from evo_engine.resolvers import AcceptAll


@attrs.frozen(slots=True, kw_only=True)
class JobCompleted:
    """Nonbiological effect emitted by a scheduling state."""

    job_name: str


@attrs.define(slots=True, kw_only=True)
class SchedulingState:
    """Minimal transactional state with an application-effect journal."""

    completed_jobs: set[str] = attrs.field(factory=set)
    _effects: list[object] = attrs.field(factory=list, repr=False)

    @property
    def effect_count(self) -> int:
        """Return current transaction-local journal length."""
        return len(self._effects)

    def effects_since(self, checkpoint: int) -> tuple[object, ...]:
        """Return effects recorded after a journal checkpoint."""
        return tuple(self._effects[checkpoint:])

    def complete(self, job_name: str) -> None:
        """Complete a job and record its domain effect."""
        self.completed_jobs.add(job_name)
        self._effects.append(JobCompleted(job_name=job_name))

    def copy(self) -> SchedulingState:
        """Return a transactional copy with a fresh effect journal."""
        copied = copy.deepcopy(self)
        copied._effects.clear()
        return copied


@attrs.define(slots=True, kw_only=True)
class CountingSchedulingState:
    """Scheduling state exposing a counted stable effect-reader capability."""

    completed_jobs: set[str] = attrs.field(factory=set)
    _effects: list[object] = attrs.field(factory=list, repr=False)
    effect_reader_accesses: int = 0

    @property
    def effect_count(self) -> int:
        """Return current transaction-local journal length."""
        return len(self._effects)

    @property
    def effects_since(self) -> Callable[[int], tuple[object, ...]]:
        """Return the journal reader while counting capability resolution."""
        self.effect_reader_accesses += 1
        return self._read_effects_since

    def _read_effects_since(self, checkpoint: int) -> tuple[object, ...]:
        """Return effects recorded after a journal checkpoint."""
        return tuple(self._effects[checkpoint:])

    def complete(self, job_name: str) -> None:
        """Complete a job and record its domain effect."""
        self.completed_jobs.add(job_name)
        self._effects.append(JobCompleted(job_name=job_name))

    def copy(self) -> CountingSchedulingState:
        """Return a transactional copy with a fresh effect journal."""
        copied = copy.deepcopy(self)
        copied._effects.clear()
        return copied


@attrs.define(slots=True, kw_only=True)
class DelayedJournalSchedulingState:
    """Scheduling state whose effect checkpoint becomes available mid-stage."""

    completed_jobs: set[str] = attrs.field(factory=set)
    _effects: list[object] = attrs.field(factory=list, repr=False)
    journal_enabled: bool = False

    @property
    def effect_count(self) -> int | None:
        """Return the journal length only after the first completed job."""
        if not self.journal_enabled:
            return None
        return len(self._effects)

    def effects_since(self, checkpoint: int) -> tuple[object, ...]:
        """Return effects recorded after a journal checkpoint."""
        return tuple(self._effects[checkpoint:])

    def complete(self, job_name: str) -> None:
        """Complete a job, record its effect, and expose the journal."""
        self.completed_jobs.add(job_name)
        self._effects.append(JobCompleted(job_name=job_name))
        self.journal_enabled = True

    def copy(self) -> DelayedJournalSchedulingState:
        """Return a transactional copy with a fresh effect journal."""
        copied = copy.deepcopy(self)
        copied._effects.clear()
        return copied


@attrs.frozen(slots=True, kw_only=True)
class CompleteJob:
    """Nonbiological process completing configured scheduled jobs."""

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent one proposed job completion."""

        step_index: int
        job_name: str

    job_names: tuple[str, ...] = ("batch-7",)

    @property
    def event_type(self) -> type[Event]:
        """Return the process event type."""
        return self.Event

    def propose_events(self, simulation_state: SimulationState) -> list[Event]:
        """Propose configured job completions."""
        return [
            self.Event(step_index=simulation_state.step_index, job_name=job_name)
            for job_name in self.job_names
        ]

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: Event,
    ) -> None:
        """Apply the job completion to scheduling state."""
        simulation_state.domain_state.complete(event.job_name)


def test_stage_coordinator_records_arbitrary_domain_effects() -> None:
    """Test committed-effect capture without biological world types."""
    state = SimulationState(domain_state=SchedulingState())
    stage = StageCoordinator(
        processes=(CompleteJob(),),
        resolver=AcceptAll(),
    )

    applied = stage.coordinate(state)

    assert state.domain_state.completed_jobs == {"batch-7"}
    assert len(applied) == 1
    assert applied[0].effects == (JobCompleted(job_name="batch-7"),)


def test_stage_coordinator_resolves_effect_reader_once_per_stage() -> None:
    """Test repeated event capture reuses one stable effect-reader binding."""
    state = SimulationState(domain_state=CountingSchedulingState())
    stage = StageCoordinator(
        processes=(CompleteJob(job_names=("batch-7", "batch-8")),),
        resolver=AcceptAll(),
    )

    applied = stage.coordinate(state)

    assert state.domain_state.effect_reader_accesses == 1
    assert tuple(event.effects for event in applied) == (
        (JobCompleted(job_name="batch-7"),),
        (JobCompleted(job_name="batch-8"),),
    )


def test_stage_coordinator_rechecks_dynamic_effect_checkpoint_each_event() -> None:
    """Test a journal becoming available mid-stage is detected on the next event."""
    state = SimulationState(domain_state=DelayedJournalSchedulingState())
    stage = StageCoordinator(
        processes=(CompleteJob(job_names=("batch-7", "batch-8")),),
        resolver=AcceptAll(),
    )

    applied = stage.coordinate(state)

    assert state.domain_state.completed_jobs == {"batch-7", "batch-8"}
    assert tuple(event.effects for event in applied) == (
        (),
        (JobCompleted(job_name="batch-8"),),
    )
