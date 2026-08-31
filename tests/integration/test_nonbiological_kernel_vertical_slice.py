"""End-to-end proof that the simulation kernel composes outside biology."""

from __future__ import annotations

import copy
import random
from collections.abc import Sequence

import attrs

from evo_engine.configuration import Dependency, SimulationSpec
from evo_engine.engine import (
    SequentialStepCoordinator,
    SimulationContext,
    SimulationEvent,
    SimulationState,
    StageCoordinator,
)
from evo_engine.resolvers import AcceptAll, resolve_capacity_preference_order
from evo_engine.telemetry import StepTelemetry


@attrs.frozen(slots=True, kw_only=True)
class Job:
    """Describe one pending manufacturing job."""

    name: str
    machine: str
    priority: int


@attrs.frozen(slots=True, kw_only=True)
class JobCompleted:
    """Record one committed job-completion effect."""

    job_name: str
    machine: str
    ticket: str


@attrs.frozen(slots=True, kw_only=True)
class JobAudited:
    """Record one committed audit effect."""

    job_name: str


@attrs.define(slots=True, kw_only=True)
class SchedulingState:
    """Represent a transactional scheduling domain with an effect journal."""

    pending_jobs: dict[str, Job] = attrs.field(factory=dict)
    completed_jobs: dict[str, str] = attrs.field(factory=dict)
    audited_jobs: set[str] = attrs.field(factory=set)
    _mutations: list[object] = attrs.field(factory=list, repr=False)

    @property
    def mutation_count(self) -> int:
        """Return the current transaction-local effect count."""
        return len(self._mutations)

    def mutations_since(self, checkpoint: int) -> tuple[object, ...]:
        """Return effects recorded after one journal checkpoint."""
        return tuple(self._mutations[checkpoint:])

    def complete_job(self, job_name: str, *, ticket: str) -> None:
        """Complete one pending job and record its committed effect."""
        job = self.pending_jobs.pop(job_name)
        self.completed_jobs[job_name] = ticket
        self._mutations.append(
            JobCompleted(
                job_name=job.name,
                machine=job.machine,
                ticket=ticket,
            )
        )

    def audit_job(self, job_name: str) -> None:
        """Audit one completed job and record its committed effect."""
        if job_name not in self.completed_jobs:
            raise ValueError(f"cannot audit incomplete job {job_name!r}.")
        self.audited_jobs.add(job_name)
        self._mutations.append(JobAudited(job_name=job_name))

    def copy(self) -> SchedulingState:
        """Return an independent transaction with a fresh effect journal."""
        copied = copy.deepcopy(self)
        copied._mutations.clear()
        return copied


@attrs.frozen(slots=True, kw_only=True)
class DispatchProposal:
    """Propose dispatch of one job onto a named machine."""

    step_index: int
    job_name: str
    machine: str
    priority: int


@attrs.frozen(slots=True, kw_only=True)
class DispatchEvent:
    """Represent an accepted dispatch after stochastic materialization."""

    step_index: int
    job_name: str
    machine: str
    ticket: str


@attrs.frozen(slots=True)
class DispatchProcess:
    """Propose, materialize, and apply job dispatches."""

    @property
    def event_type(self) -> type[DispatchProposal]:
        """Return the proposal type owned by this process."""
        return DispatchProposal

    def propose_events(
        self, simulation_state: SimulationState
    ) -> list[DispatchProposal]:
        """Propose every currently pending job from the stage-start state."""
        return [
            DispatchProposal(
                step_index=simulation_state.step_index,
                job_name=job.name,
                machine=job.machine,
                priority=job.priority,
            )
            for job in simulation_state.world.pending_jobs.values()
        ]

    def materialize_event(
        self,
        simulation_state: SimulationState,
        event: DispatchProposal,
        /,
    ) -> DispatchEvent:
        """Assign a deterministic-random ticket only after resolution."""
        prefix = simulation_state.context.require("ticket_prefix")
        if not isinstance(prefix, str):
            raise TypeError("ticket_prefix must be a string.")
        return DispatchEvent(
            step_index=event.step_index,
            job_name=event.job_name,
            machine=event.machine,
            ticket=f"{prefix}-{simulation_state.rng.randrange(1000, 10000)}",
        )

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: DispatchEvent,
        /,
    ) -> None:
        """Commit one accepted dispatch to scheduling state."""
        simulation_state.world.complete_job(event.job_name, ticket=event.ticket)


@attrs.frozen(slots=True)
class MachineCapacityResolver:
    """Allow one accepted job per machine in each dispatch stage."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> Sequence[SimulationEvent]:
        """Resolve job competition with the public generic capacity algorithm."""
        del simulation_state
        return resolve_capacity_preference_order(
            proposed_events,
            event_type=DispatchProposal,
            preference_score=lambda event: event.priority,
            participant_keys=lambda event: (event.machine,),
            max_events_per_key=1,
            resolver_name=type(self).__name__,
        )


@attrs.frozen(slots=True, kw_only=True)
class AuditEvent:
    """Represent one audit of a completed job."""

    step_index: int
    job_name: str


@attrs.frozen(slots=True)
class AuditProcess:
    """Audit completed jobs in a second stage."""

    @property
    def event_type(self) -> type[AuditEvent]:
        """Return the audit event type."""
        return AuditEvent

    def propose_events(self, simulation_state: SimulationState) -> list[AuditEvent]:
        """Propose audits for completed jobs not yet audited."""
        return [
            AuditEvent(
                step_index=simulation_state.step_index,
                job_name=job_name,
            )
            for job_name in simulation_state.world.completed_jobs
            if job_name not in simulation_state.world.audited_jobs
        ]

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: AuditEvent,
        /,
    ) -> None:
        """Commit one audit."""
        simulation_state.world.audit_job(event.job_name)


@attrs.frozen(slots=True, kw_only=True)
class AllJobsAudited:
    """Stop when all work is complete, with a defensive step limit."""

    max_steps: int = 10

    def should_stop(self, simulation_state: SimulationState) -> bool:
        """Return whether all jobs are audited or the defensive limit is reached."""
        world = simulation_state.world
        all_done = (
            not world.pending_jobs and set(world.completed_jobs) == world.audited_jobs
        )
        return all_done or simulation_state.step_index >= self.max_steps


@attrs.frozen(slots=True, kw_only=True)
class StateSnapshot:
    """Store one immutable observer snapshot."""

    step_index: int
    pending: tuple[str, ...]
    completed: tuple[str, ...]
    audited: tuple[str, ...]


@attrs.define(slots=True)
class SchedulingObserver:
    """Record committed scheduling state snapshots."""

    snapshots: list[StateSnapshot] = attrs.field(factory=list)

    def should_observe(self, world_state: object, *, step_index: int) -> bool:
        """Observe every committed state, including step zero."""
        del world_state, step_index
        return True

    def observe(self, world_state: object, *, step_index: int) -> None:
        """Record one immutable snapshot."""
        if not isinstance(world_state, SchedulingState):
            raise TypeError("SchedulingObserver requires SchedulingState.")
        self.snapshots.append(
            StateSnapshot(
                step_index=step_index,
                pending=tuple(world_state.pending_jobs),
                completed=tuple(world_state.completed_jobs),
                audited=tuple(sorted(world_state.audited_jobs)),
            )
        )


@attrs.define(slots=True)
class SchedulingTelemetryObserver:
    """Record every committed step telemetry record."""

    records: list[StepTelemetry] = attrs.field(factory=list)

    def should_observe_telemetry(self, telemetry: StepTelemetry) -> bool:
        """Observe every committed telemetry record."""
        del telemetry
        return True

    def observe_telemetry(self, telemetry: StepTelemetry) -> None:
        """Record one committed step telemetry record."""
        self.records.append(telemetry)


def test_complete_nonbiological_simulation_uses_public_kernel_contracts() -> None:
    """Run a useful foreign-domain simulation through the complete kernel stack."""
    initial_state = SchedulingState(
        pending_jobs={
            "lathe-high": Job(name="lathe-high", machine="lathe", priority=5),
            "lathe-low": Job(name="lathe-low", machine="lathe", priority=3),
            "mill": Job(name="mill", machine="mill", priority=4),
        }
    )
    state_observer = SchedulingObserver()
    telemetry_observer = SchedulingTelemetryObserver()
    machine_dependencies = frozenset(
        {
            Dependency(category="machine", name="lathe"),
            Dependency(category="machine", name="mill"),
        }
    )
    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(DispatchProcess(),),
                resolver=MachineCapacityResolver(),
            ),
            StageCoordinator(
                processes=(AuditProcess(),),
                resolver=AcceptAll(),
            ),
        )
    )
    compiled = SimulationSpec(
        initial_world_state=initial_state,
        step_coordinator=coordinator,
        stopping_condition=AllJobsAudited(),
        seed=17,
        context=SimulationContext.from_mapping({"ticket_prefix": "JOB"}),
        observers=(state_observer,),
        telemetry_observers=(telemetry_observer,),
        required_dependencies=machine_dependencies,
        provided_dependencies=machine_dependencies,
    ).compile()

    assert compiled.dependency_report.missing == frozenset()

    compiled.engine.run(compiled.simulation)

    final_state = compiled.simulation.state
    assert final_state.step_index == 2
    assert final_state.world.pending_jobs == {}
    assert tuple(final_state.world.completed_jobs) == (
        "lathe-high",
        "mill",
        "lathe-low",
    )
    assert final_state.world.audited_jobs == {"lathe-high", "mill", "lathe-low"}

    expected_rng = random.Random(17)
    expected_tickets = tuple(
        f"JOB-{expected_rng.randrange(1000, 10000)}" for _ in range(3)
    )
    assert tuple(final_state.world.completed_jobs.values()) == expected_tickets

    assert tuple(snapshot.step_index for snapshot in state_observer.snapshots) == (
        0,
        1,
        2,
    )
    assert state_observer.snapshots[1].pending == ("lathe-low",)
    assert state_observer.snapshots[1].completed == ("lathe-high", "mill")
    assert state_observer.snapshots[1].audited == ("lathe-high", "mill")

    assert tuple(
        record.completed_step_index for record in telemetry_observer.records
    ) == (
        1,
        2,
    )
    assert tuple(
        event.stage_index for event in telemetry_observer.records[0].events
    ) == (0, 0, 1, 1)
    assert tuple(
        event.process_name for event in telemetry_observer.records[0].events
    ) == ("DispatchProcess", "DispatchProcess", "AuditProcess", "AuditProcess")
    assert all(
        len(event.effects) == 1
        for record in telemetry_observer.records
        for event in record.events
    )

    assert tuple(initial_state.pending_jobs) == ("lathe-high", "lathe-low", "mill")
    assert initial_state.completed_jobs == {}
    assert initial_state.audited_jobs == set()
